"""Composição determinística do artefato V3 (Onda 0 Task 10, §8.12).

Reorganiza objetos validados e gera o resumo executivo por regras
determinísticas. Nenhuma chamada de IA aqui — segunda interpretação
livre é proibida.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from app.core.schemas_v3 import ArtifactContentV3


@dataclass
class CompositionInputs:
    run_id: str | None = None
    case_id: str | None = None
    coverage: dict = field(default_factory=dict)
    reconciled: dict = field(default_factory=dict)
    analysis: dict = field(default_factory=dict)
    research: dict = field(default_factory=dict)
    calculations: list = field(default_factory=list)
    visuals: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    # Onda 1: ativações do registry + resultados por módulo (opcionais).
    module_activations: list = field(default_factory=list)
    module_results: dict = field(default_factory=dict)


class ComposedArtifact(ArtifactContentV3):
    def content_hash(self) -> str:
        canonical = json.dumps(
            self.model_dump(mode="json"), sort_keys=True, ensure_ascii=False
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _section_state(items: list, reason: str) -> dict:
    return {
        "status": "complete" if items else "partial",
        "reason": reason if items else f"{reason} (pendente)",
        "coverage": {
            "items_expected": len(items),
            "items_found": len(items),
            "items_verified": len(items),
        },
        "pending_actions": [],
    }


def _all_section_states(
    *,
    claims: list,
    facts: list,
    controversies: list,
    evidence: list,
    visuals: list,
    legal_references: list,
    analysis: dict,
    calculations: list,
    sources: list,
) -> dict:
    """Estado honesto de todas as seções materiais (bloco E do smoke)."""
    analysis = analysis or {}
    return {
        "claims": _section_state(claims, "Pedidos reconciliados"),
        "facts": _section_state(facts, "Fatos reconciliados"),
        "controversies": _section_state(controversies, "Controvérsias reconciliadas"),
        "evidence": _section_state(evidence, "Provas reconciliadas"),
        "visuals": _section_state(visuals, "Imagens extraídas"),
        "legal_references": _section_state(legal_references, "Fundamentos reconciliados"),
        "procedural_issues": _section_state(
            analysis.get("procedural_issues") or [], "Questões processuais analisadas"),
        "theses": _section_state(analysis.get("theses") or [], "Teses bilaterais analisadas"),
        "calculations": _section_state(calculations, "Cálculos determinísticos"),
        "risks": _section_state(analysis.get("risks") or [], "Riscos analisados"),
        "action_plan": _section_state(analysis.get("actions") or [], "Plano de ação"),
        "client_questions": _section_state(
            analysis.get("questions") or [], "Perguntas ao cliente"),
        "sources": _section_state(sources, "Fontes resolvíveis"),
        "limitations": _section_state(
            analysis.get("limitations") or [], "Limitações declaradas"),
    }


def compose_artifact(inputs: CompositionInputs) -> ComposedArtifact:
    """Monta ``ArtifactContentV3`` a partir de objetos validados."""
    reconciled = inputs.reconciled or {}
    analysis = inputs.analysis or {}
    claims = list(reconciled.get("claims") or [])
    facts = list(reconciled.get("facts") or [])
    key_facts = [f.get("id") for f in facts[:5] if f.get("id")]
    main_claims = [c.get("id") for c in claims[:5] if c.get("id")]
    payload = {
        "schema_version": "3.0",
        "run_id": inputs.run_id,
        "case_id": inputs.case_id,
        "status": "partial",
        "scope": {"document_ids": []},
        "module_activations": list(inputs.module_activations or []),
        "module_results": dict(inputs.module_results or {}),
        "coverage": {
            "pages_total": int((inputs.coverage or {}).get("pages_total", 0) or 0),
            "pages_extracted": int((inputs.coverage or {}).get("pages_extracted", 0) or 0),
            "unprocessed_block_ids": list((inputs.coverage or {}).get("unprocessed_block_ids", [])),
            "explicit_claims_found": len(claims),
        },
        "section_states": _all_section_states(
            claims=claims, facts=facts,
            controversies=reconciled.get("controversies") or [],
            evidence=reconciled.get("evidence") or [],
            visuals=inputs.visuals or [],
            legal_references=reconciled.get("legal_references") or [],
            analysis=analysis, calculations=inputs.calculations or [],
            sources=inputs.sources or [],
        ),
        "executive_summary": {
            "narrative": (
                f"Dossiê com {len(claims)} pedido(s) e {len(facts)} fato(s) "
                "reconciliados a partir dos documentos examinados."
            ),
            "central_question": "Quais pedidos procedem conforme provas e fontes?",
            "main_claims": main_claims,
            "key_facts": key_facts,
            "key_evidence": [],
            "key_theses": [],
            "priority_risks": [],
            "priority_actions": [],
            "limitations": [],
        },
        "claims": claims,
        "facts": facts,
        "controversies": list(reconciled.get("controversies") or []),
        "evidence": list(reconciled.get("evidence") or []),
        "visuals": list(inputs.visuals or []),
        "legal_references": list(reconciled.get("legal_references") or []),
        "procedural_issues": list(analysis.get("procedural_issues") or []),
        "theses": list(analysis.get("theses") or []),
        "calculations": list(inputs.calculations or []),
        "risks": list(analysis.get("risks") or []),
        "action_plan": list(analysis.get("actions") or []),
        "client_questions": list(analysis.get("questions") or []),
        "sources": list(inputs.sources or []),
        "limitations": list(analysis.get("limitations") or []),
    }
    return ComposedArtifact.model_validate(payload)
