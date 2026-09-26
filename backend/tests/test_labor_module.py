"""V2 T08 — módulo trabalhista (aceite do plano)."""

from app.modules import get_module
from app.modules.labor import DESCRIPTOR
from app.modules.labor.checklist import WORK_ACCIDENT_MATRIX, evaluate_matrix
from app.modules.labor.findings import run_all_detectors
from app.modules.labor.theses import build_probation_plan, build_theses


def _artifact():
    return {
        "claims": [
            {"id": "claim-5", "title": "Reparação material", "category": "material",
             "period": "vencidas+vincendas", "requested_relief": "parcelas mensais",
             "related_claims": [{"claim_id": "claim-8", "relation": "overlaps"}]},
            {"id": "claim-8", "title": "Pensão mensal", "category": "pensao",
             "period": "ajuizamento", "requested_relief": "pensão vitalícia",
             "related_claims": [{"claim_id": "claim-5", "relation": "overlaps"}]},
            {"id": "claim-8b", "title": "Pensão (corpo)", "category": "pensao",
             "period": "evento", "requested_relief": "desde o evento",
             "related_claims": []},
            {"id": "claim-9", "title": "Indenização coletiva CCT cláusula 19",
             "category": "coletiva", "requested_relief": "13 salários normativos",
             "related_claims": []},
        ],
        "facts": [
            {"declared_years": 31, "start_age": 33, "end_age": 65},
        ],
        "evidence": [
            {"id": "foto-lesao", "kind": "photo", "presence_status": "examined"},
            {"id": "foto-equip", "kind": "photo", "presence_status": "examined"},
            {"id": "pericia-req", "kind": "pericia_medica", "presence_status": "proposed"},
        ],
    }


def test_module_descriptor_registered():
    assert DESCRIPTOR["module_id"] == "labor"
    assert DESCRIPTOR["version"] == "1.0"
    assert get_module("labor") is DESCRIPTOR
    assert "relacao_trabalho" in DESCRIPTOR["required_sections"]


def test_matrix_covers_seven_dimensions():
    assert len(WORK_ACCIDENT_MATRIX) == 7
    results = evaluate_matrix(
        {
            "seguranca": {"treinamento": ["trein-src"]},
            "evento": {"dinamica": ["foto-equip"]},
        }
    )
    by_key = {(r.dimension, r.item): r for r in results}
    assert by_key[("seguranca", "treinamento")].status == "documented"
    assert by_key[("seguranca", "manutencao")].status == "missing"
    assert by_key[("seguranca", "manutencao")].action  # lacuna vira ação


def test_detectors_find_all_benchmark_patterns():
    findings = run_all_detectors(_artifact())
    codes = {f.code for f in findings}
    assert "PENSION_TERM_DIVERGENCE" in codes  # evento x ajuizamento
    assert "PENSION_VITALICIA_VS_CAP" in codes  # vitalícia x limite
    assert "PERIOD_ARITHMETIC_MISMATCH" in codes  # 31 x 32
    assert "POSSIBLE_OVERLAP" in codes  # ped.5 x ped.8
    assert "MISSING_CCT" in codes  # CCT citada, não examinada
    assert "PHOTO_NOT_DIAGNOSIS" in codes  # fotos sem laudo
    for finding in findings:
        assert finding.impact and finding.suggested_action and finding.missing_info


def test_theses_are_bilateral_with_adverse_refs():
    matrix = evaluate_matrix(
        {
            "evento": {"dinamica": ["foto-equip"]},
            "seguranca": {},
            "nexo_dano": {"lesao": ["foto-lesao"]},
        }
    )
    evidence = _artifact()["evidence"]
    drafts = build_theses(matrix, evidence)
    sides = {d.represented_side for d in drafts}
    assert {"claimant", "respondent"} <= sides
    claimant = next(d for d in drafts if d.represented_side == "claimant")
    assert claimant.adverse_refs  # provas desfavoráveis expostas
    assert claimant.counterargument
    assert claimant.limitations
    respondent = next(d for d in drafts if d.represented_side == "respondent")
    assert "culpa exclusiva" not in respondent.conclusion
    assert respondent.limitations


def test_probation_plan_neutral_and_linked():
    plan = build_probation_plan([], affected_claim_ids=["claim-8"])
    addressees = {q.addressee for q in plan["questions"]}
    assert {"cliente", "seguranca", "perito_medico", "perito_seguranca"} == addressees
    for quesito in plan["quesitos"]:
        assert quesito.controversy
        assert quesito.affected_claim_ids == ["claim-8"]
        lowered = quesito.text.casefold()
        assert "comprova" not in lowered and "confirma" not in lowered
    assert any("CCT" in doc for doc in plan["documents"])
