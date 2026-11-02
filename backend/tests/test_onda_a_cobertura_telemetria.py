"""Onda A — cobertura explícita, teto de lotes e telemetria de custo.

Cada teste aqui corresponde a um defeito concreto encontrado na validação
do plano Jev (2026-11-01):

1. ``structured_extractor`` cortava em 4.000 *chars* contra um orçamento
   de ~32.000 chars do planejador → ~7/8 do lote descartado em silêncio.
2. ``max_batches`` nunca era passado no caminho real → teto desligado.
3. O caminho V3 nunca gravava ``run.usage`` → custo imensurável.
4. ``MAX_RUN_USD`` existia só em documentação → nenhum teto de verdade.
"""

import pytest

from app.models.analysis_run import AnalysisRun
from app.models.document import Document
from app.models.document_revision import DocumentRevision
from app.models.source_block import SourceBlock

OMISSION_MARKER_FRAGMENT = "trecho omitido por orcamento"


class _RecordingProvider:
    """Provedor falso que registra prompts e reporta uso real de tokens."""

    def __init__(self, payload=None, model="gpt-4-turbo", usage=None):
        self.prompts: list[str] = []
        self.model = model
        self._payload = payload if payload is not None else {
            "claims": [], "facts": [], "evidence": [], "legal_references": [],
        }
        self.usage = usage or {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0}

    def complete_json(self, prompt):
        self.prompts.append(prompt)
        return self._payload

    def usage_snapshot(self):
        return dict(self.usage)


class _AnalysisProvider:
    def __init__(self, model="gpt-4-turbo", usage=None):
        self.model = model
        self.usage = usage or {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0}

    def analyze(self, payload):
        return {
            "procedural_issues": [], "theses": [], "risks": [],
            "actions": [], "questions": [], "limitations": [],
        }

    def usage_snapshot(self):
        return dict(self.usage)


def _batch(text):
    return {
        "batch_index": 0,
        "block_ids": ["b1"],
        "blocks": [{"id": "b1", "normalized_text": text}],
    }


# --------------------------------------------------------------------------
# 1. Corte de texto coerente com o orçamento do planejador
# --------------------------------------------------------------------------


def test_batch_within_budget_is_not_truncated():
    """20.000 chars cabem no orçamento de 8.000 tokens (~32.000 chars).

    O código anterior cortava em 4.000 chars e perdia o final do lote —
    exatamente onde o rol de pedidos costuma estar.
    """
    from app.core.structured_extractor import extract_batch

    body = "corpo do lote com fatos materiais. " * 570  # ~20.000 chars
    tail = "PEDIDO FINAL: guarda compartilhada, pagina 35."
    provider = _RecordingProvider()

    result = extract_batch(
        _batch(body + "\n" + tail), provider=provider, budget_tokens=8000
    )

    prompt = provider.prompts[0]
    assert tail in prompt, "final do lote foi descartado apesar do orçamento permitir"
    assert OMISSION_MARKER_FRAGMENT not in prompt
    assert result.text_coverage["truncated"] is False
    assert result.text_coverage["omitted_chars"] == 0


def test_oversized_batch_truncates_explicitly_and_keeps_tail():
    """Acima do orçamento: marca a omissão e preserva início e fim."""
    from app.core.structured_extractor import extract_batch

    head = "INICIO DE LOTE. " * 5000      # ~80.000 chars
    tail = "PEDIDO FINAL: pensao alimenticia, pagina 35."
    provider = _RecordingProvider()

    result = extract_batch(
        _batch(head + "\n" + tail), provider=provider, budget_tokens=1000
    )

    prompt = provider.prompts[0]
    assert tail in prompt, "cauda (pedidos finais) nunca pode cair em silêncio"
    assert OMISSION_MARKER_FRAGMENT in prompt
    assert result.text_coverage["truncated"] is True
    assert result.text_coverage["omitted_chars"] > 0


def test_extraction_reports_text_coverage():
    from app.core.structured_extractor import BatchExtraction, extract_batch

    result = extract_batch(
        _batch("conteudo curto"), provider=_RecordingProvider(), budget_tokens=8000
    )
    assert isinstance(result, BatchExtraction)
    assert result.text_coverage["tokens_total"] > 0
    assert result.text_coverage["budget_tokens"] == 8000


# --------------------------------------------------------------------------
# 2. Teto de lotes aplicado no caminho real
# --------------------------------------------------------------------------


def _revision_with_blocks(db_session, make_user, texts):
    user = make_user()
    document = Document(
        user_id=user.id, filename="onda-a.pdf", file_path="/tmp/onda-a.pdf",
        content_type="application/pdf", status="uploaded",
    )
    db_session.add(document)
    db_session.commit()
    db_session.refresh(document)

    revision = DocumentRevision(
        document_id=document.id, user_id=user.id, sha256="sha-onda-a", pages_total=2,
    )
    db_session.add(revision)
    db_session.commit()
    db_session.refresh(revision)

    for index, text in enumerate(texts):
        db_session.add(
            SourceBlock(
                revision_id=revision.id,
                user_id=user.id,
                block_uid=f"b{index:03d}",
                page_number=1,
                block_type="text",
                reading_order=index,
                original_text=text,
                normalized_text=text,
            )
        )
    db_session.commit()

    run = AnalysisRun(
        user_id=user.id, document_id=document.id,
        status=AnalysisRun.RUNNING, snapshot={},
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return user, document, revision, run


def test_real_path_enforces_batch_cap_and_reports_partial(
    db_session, make_user, monkeypatch
):
    from app.core.pipeline.orchestrator import execute_real_stages

    texts = [f"Bloco {i} com fatos e pedidos relevantes. " * 12 for i in range(6)]
    _user, _document, _revision, run = _revision_with_blocks(
        db_session, make_user, texts
    )
    monkeypatch.setattr("app.core.config.settings.COVERAGE_MAX_BATCHES", 1)

    result = execute_real_stages(
        db_session,
        run=run,
        struct_provider=_RecordingProvider(),
        analysis_provider=_AnalysisProvider(),
        max_batch_tokens=60,
    )

    coverage = result["coverage"]
    assert coverage["budget_exceeded"] is True
    assert coverage["batches_planned"] == 1
    assert coverage["unprocessed_block_ids"], "blocos não processados devem ser listados"
    codes = {lim.get("code") for lim in result["analysis"]["limitations"]}
    assert "BUDGET_EXCEEDED" in codes, "parcialidade precisa ser explícita no artefato"


# --------------------------------------------------------------------------
# 3. Telemetria de tokens e custo
# --------------------------------------------------------------------------


def test_usage_and_cost_sums_real_tokens():
    from app.core.pipeline.orchestrator import usage_and_cost

    struct = _RecordingProvider(usage={"calls": 3, "prompt_tokens": 30000, "completion_tokens": 6000})
    analysis = _AnalysisProvider(usage={"calls": 1, "prompt_tokens": 7000, "completion_tokens": 2500})

    status = usage_and_cost(struct, analysis)

    assert status["calls"] == 4
    assert status["prompt_tokens"] == 37000
    assert status["completion_tokens"] == 8500
    assert status["tokens_total"] == 45500
    assert status["cost_known"] is True
    # gpt-4-turbo: US$ 10/Mtok entrada + US$ 30/Mtok saída.
    assert status["cost_usd"] == pytest.approx(0.37 + 0.255, abs=1e-6)


def test_unknown_model_reports_unavailable_cost_instead_of_guessing():
    from app.core.pipeline.orchestrator import usage_and_cost

    provider = _RecordingProvider(
        model="modelo-inexistente-9",
        usage={"calls": 1, "prompt_tokens": 1000, "completion_tokens": 100},
    )

    status = usage_and_cost(provider)

    assert status["cost_known"] is False
    assert status["cost_usd"] is None


# --------------------------------------------------------------------------
# 4. Teto de orçamento real (MAX_RUN_USD)
# --------------------------------------------------------------------------


def test_budget_guard_stops_run_before_overspending():
    from app.core.coverage_planner import BudgetExceededError
    from app.core.pipeline.orchestrator import _enforce_run_budget

    expensive = _RecordingProvider(
        usage={"calls": 1, "prompt_tokens": 2_000_000, "completion_tokens": 0}
    )

    with pytest.raises(BudgetExceededError) as excinfo:
        _enforce_run_budget(expensive, max_usd=1.0, stage="lote 0")
    assert excinfo.value.code == "BUDGET_EXCEEDED"


def test_budget_guard_does_not_block_on_unpriced_model():
    from app.core.pipeline.orchestrator import _enforce_run_budget

    unpriced = _RecordingProvider(
        model="modelo-inexistente-9",
        usage={"calls": 1, "prompt_tokens": 5_000_000, "completion_tokens": 0},
    )

    status = _enforce_run_budget(unpriced, max_usd=0.01, stage="lote 0")

    assert status["cost_known"] is False


def test_token_cap_protects_runs_with_unpriced_model():
    """Modelo fora da tabela de preços não pode deixar o guarda inerte.

    O modelo de produção (gemini-3-flash-preview) não está precificado, então
    MAX_RUN_USD sozinho nunca bloquearia. O teto de tokens vale sempre.
    """
    from app.core.coverage_planner import BudgetExceededError
    from app.core.pipeline.orchestrator import _enforce_run_budget

    unpriced = _RecordingProvider(
        model="modelo-inexistente-9",
        usage={"calls": 1, "prompt_tokens": 5_000_000, "completion_tokens": 0},
    )

    with pytest.raises(BudgetExceededError) as excinfo:
        _enforce_run_budget(
            unpriced, max_usd=100.0, max_tokens=1_000_000, stage="lote 0"
        )
    assert "tokens" in str(excinfo.value)


def test_real_path_aborts_when_run_budget_exceeded(
    db_session, make_user, monkeypatch
):
    from app.core.coverage_planner import BudgetExceededError
    from app.core.pipeline.orchestrator import execute_real_stages

    _user, _document, _revision, run = _revision_with_blocks(
        db_session, make_user, ["Bloco com conteudo juridico relevante. " * 20]
    )
    monkeypatch.setattr("app.core.config.settings.MAX_RUN_USD", 0.01)

    overspending = _RecordingProvider(
        usage={"calls": 1, "prompt_tokens": 1_000_000, "completion_tokens": 0}
    )

    with pytest.raises(BudgetExceededError):
        execute_real_stages(
            db_session,
            run=run,
            struct_provider=overspending,
            analysis_provider=_AnalysisProvider(),
        )


# --------------------------------------------------------------------------
# 5. Telemetria persistida no caminho V3
# --------------------------------------------------------------------------


def test_v3_pipeline_persists_usage(db_session, make_user, monkeypatch):
    """Antes, com V3 ligado o bloco de usage nunca rodava (v2 artefato None)."""
    import app.core.pipeline.orchestrator as orchestrator

    _user, _document, _revision, run = _revision_with_blocks(
        db_session, make_user, ["A parte A requer guarda compartilhada. " * 10]
    )

    struct = _RecordingProvider(
        usage={"calls": 1, "prompt_tokens": 1200, "completion_tokens": 300}
    )
    analysis = _AnalysisProvider(
        usage={"calls": 1, "prompt_tokens": 800, "completion_tokens": 200}
    )

    original_execute = orchestrator.execute_real_stages

    def wrapped(db, *, run, **kwargs):
        return original_execute(
            db, run=run, struct_provider=struct, analysis_provider=analysis
        )

    monkeypatch.setattr(orchestrator, "execute_real_stages", wrapped)

    orchestrator.run_universal_pipeline(db_session, run_id=run.id)

    db_session.refresh(run)
    assert run.usage is not None, "caminho V3 continua sem telemetria"
    assert run.usage["source"] == "v3_pipeline"
    assert run.usage["calls"] == 2
    assert run.usage["prompt_tokens"] == 2000
    assert run.usage["tokens_total"] == 2500
    assert run.usage["cost"] == "estimated"
    assert run.usage["cost_usd"] > 0


def test_v1_legacy_call_is_added_to_v3_usage(db_session, make_user):
    """A chamada V1 duplicada precisa aparecer — senão a economia é inflada."""
    from app.tasks.document_tasks import merge_v1_usage_into_run

    _user, _document, _revision, run = _revision_with_blocks(
        db_session, make_user, ["Bloco irrelevante."]
    )
    run.usage = {
        "source": "v3_pipeline", "calls": 2, "prompt_tokens": 1000,
        "completion_tokens": 200, "tokens_total": 1200,
        "cost_usd": 0.016, "cost": "estimated",
    }
    db_session.commit()

    analyzer = _RecordingProvider(
        usage={"calls": 1, "prompt_tokens": 28000, "completion_tokens": 1500}
    )
    merged = merge_v1_usage_into_run(db_session, run=run, analyzer=analyzer)

    assert merged["calls"] == 3
    assert merged["prompt_tokens"] == 29000
    assert merged["completion_tokens"] == 1700
    assert merged["tokens_total"] == 30700
    assert merged["v1_legacy"]["prompt_tokens"] == 28000
    assert merged["cost_usd"] == pytest.approx(0.016 + 0.28 + 0.045, abs=1e-6)
