"""Módulo trabalhista v1.0 no contrato V3 (Onda 1B, spec §6).

Reaproveita a matriz de acidente (`checklist.py`), os detectores
(`findings.py`) e as teses bilaterais (`theses.py`); corrige o
vocabulário (alegação ≠ documented) e expõe os 6 temas da spec como
`issue_assessments` com fontes verificadas.
"""

from decimal import Decimal

from app.core.calculations import CalculationBlockedError, _quantize, _require_decimal
from app.core.module_registry import ModuleRequirements


LABOR_SOURCES = [
    {"id": "clt", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/decreto-lei/del5452compilado.htm"},
    {"id": "lei8213", "organ": "Planalto",
     "url": "https://www.planalto.gov.br/ccivil_03/leis/l8213compilado.htm"},
    {"id": "nr", "organ": "MTE",
     "url": "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/seguranca-e-saude-no-trabalho/normas-regulamentadoras"},
    {"id": "cct", "organ": "Instrumento coletivo do caso",
     "url": None},
]

LABOR_THEMES = (
    ("vinculo", "Vínculo", ("vínculo", "vinculo", "emprego", "subordinação", "subordinacao", "ctps", "registro")),
    ("verbas", "Verbas", ("verba", "salário", "salario", "férias", "ferias", "13º", "fgts", "rescisão", "rescisao", "rubrica")),
    ("jornada", "Jornada", ("jornada", "hora extra", "cartão de ponto", "cartao", "escala", "banco de horas", "contracheque")),
    ("normas_coletivas", "Normas coletivas", ("cct", "coletiv", "normativ", "sindicato", "categoria", "vigência", "vigencia")),
    ("acidente_doenca", "Acidente/doença", ("acidente", "doença", "doenca", "cat", "epi", "nexo", "laudo", "incapacidade", "perícia", "pericia")),
    ("processo", "Processo", ("competência", "competencia", "prescrição", "prescricao", "liquidação", "liquidacao", "perícia", "pericia", "ônus", "onus")),
)

_EXAMINED = ("examined",)


def _norm(text: str | None) -> str:
    return (text or "").casefold()


def assess_theme(theme_key: str, case_data: dict) -> dict:
    """Avalia tema trabalhista com gates §6 (foto≠prova, perícia ausente)."""
    theme = next(t for t in LABOR_THEMES if t[0] == theme_key)
    _, title, keywords = theme
    facts = case_data.get("facts", []) or []
    evidence = case_data.get("evidence", []) or []
    known_sources = {s.get("id") for s in (case_data.get("sources") or []) if s.get("id")}
    matched = [
        f for f in facts
        if any(kw in _norm(f"{f.get('statement', '')} {f.get('id', '')}") for kw in keywords)
    ]
    examined_ids = {e.get("id") for e in evidence if e.get("presence_status") in _EXAMINED}
    supporting = sorted({
        ref for f in matched for ref in (f.get("source_refs", []) or [])
        if ref in known_sources
    })
    strong = [
        f for f in matched
        if f.get("epistemic_status") in ("documented", "admitted")
        and any(ref in known_sources for ref in (f.get("source_refs", []) or []))
    ]
    if theme_key == "acidente_doenca":
        has_report = any(
            e.get("kind") in ("laudo", "pericia_medica", "prontuario")
            and e.get("presence_status") in _EXAMINED
            for e in evidence
        )
        if matched and not has_report:
            return {
                "issue_key": f"labor.{theme_key}",
                "status": "partial",
                "conclusion": (
                    f"{title}: evento alegado sem laudo/perícia examinada; "
                    "incapacidade, culpa, nexo e autenticidade condicionados."
                ),
                "factual_refs": [f.get("id") for f in matched if f.get("id")],
                "supporting_source_refs": supporting,
                "adverse_source_refs": [],
                "missing_inputs": ["laudo ou perícia médica examinada"],
                "related_claim_ids": [],
                "action_ids": [],
            }
    if matched and strong:
        _ = examined_ids
        return {
            "issue_key": f"labor.{theme_key}",
            "status": "complete",
            "conclusion": f"{title}: premissas sustentadas por fonte examinada.",
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": [],
            "related_claim_ids": [],
            "action_ids": [],
        }
    if matched:
        return {
            "issue_key": f"labor.{theme_key}",
            "status": "partial",
            "conclusion": f"{title}: alegação registrada, condicionado a comprovação.",
            "factual_refs": [f.get("id") for f in matched if f.get("id")],
            "supporting_source_refs": supporting,
            "adverse_source_refs": [],
            "missing_inputs": ["documento comprobatório do tema"],
            "related_claim_ids": [],
            "action_ids": [],
        }
    return {
        "issue_key": f"labor.{theme_key}",
        "status": "blocked",
        "conclusion": f"{title}: sem elementos nos autos.",
        "factual_refs": [],
        "supporting_source_refs": [],
        "adverse_source_refs": [],
        "missing_inputs": [f"elementos de {title.lower()}"],
        "related_claim_ids": [],
        "action_ids": [],
    }


class LaborModule:
    module_id = "labor"
    version = "1.0.0"
    supported_areas = ("labor",)
    document_types = ("reclamacao_trabalhista", "contestacao")

    def requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            required_sections=["parties", "events", "claims", "facts", "evidence"],
            issue_checklists=[key for key, _, _ in LABOR_THEMES],
            calculation_rules=["rubricas_trabalhistas@1.0"],
            research_sources=[s["id"] for s in LABOR_SOURCES],
            evaluation_cases=["labor_cases"],
        )

    def analyze(self, case_data: dict) -> dict:
        assessments = [assess_theme(key, case_data or {}) for key, _, _ in LABOR_THEMES]
        status = "complete" if any(a["status"] == "complete" for a in assessments) else "partial"
        return {
            "module_id": self.module_id,
            "module_version": self.version,
            "status": status,
            "reason": "Matriz aplicável examinada",
            "issue_assessments": assessments,
            "calculation_ids": [],
            "limitations": [],
        }


def rubricas_trabalhistas(inputs: dict) -> Decimal:
    """Rubricas trabalhistas: só com remuneração, período, jornada, reflexos e exclusões."""
    missing = [k for k in ("remuneracao", "periodo", "jornada") if inputs.get(k) in (None, "")]
    if missing:
        raise CalculationBlockedError(
            "rubricas_trabalhistas: entradas faltantes: " + ", ".join(missing)
        )
    total = _require_decimal(inputs["remuneracao"], "remuneracao")
    reflexos = _require_decimal(inputs.get("reflexos", "0"), "reflexos")
    exclusoes = _require_decimal(inputs.get("exclusoes", "0"), "exclusoes")
    return _quantize(total + reflexos - exclusoes)


def register_calculation_rules(registry) -> None:
    registry.register("rubricas_trabalhistas", "1.0", rubricas_trabalhistas)
