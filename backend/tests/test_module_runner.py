"""Onda 1 fundação — runner de módulos com falha isolada.

- Módulo saudável produz `module_results[module_id]` sem tocar o núcleo.
- Falha de um módulo vira `blocked` + limitação; universal intacto.
- Flags desligadas excluem o módulo da resolução.
"""

from app.core.module_runner import run_module_analyses


class _OkModule:
    module_id = "family"
    version = "1.0.0"
    supported_areas = ("family",)

    def analyze(self, case_data: dict) -> dict:
        assert case_data["facts"], "módulo lê o reconciliado"
        return {
            "module_id": "family",
            "module_version": "1.0.0",
            "status": "complete",
            "reason": "ok",
            "issue_assessments": [{
                "issue_key": "child_support.need_capacity",
                "status": "partial",
                "conclusion": "c",
                "supporting_source_refs": ["src-1"],
            }],
            "calculation_ids": [],
            "limitations": [],
        }


class _BoomModule:
    module_id = "consumer"
    version = "1.0.0"
    supported_areas = ("consumer",)

    def analyze(self, case_data: dict) -> dict:
        raise RuntimeError("provedor caiu no meio do módulo")


def _case_data():
    return {
        "claims": [{"id": "claim-1"}],
        "facts": [{"id": "f1"}],
        "sources": [{"id": "src-1"}],
    }


def test_healthy_module_produces_results_without_touching_core():
    results, limitations = run_module_analyses(
        modules=[_OkModule()], case_data=_case_data())
    assert set(results) == {"family"}
    assert results["family"]["issue_assessments"][0]["issue_key"] == \
        "child_support.need_capacity"
    assert limitations == []
    assert _case_data()["claims"] == [{"id": "claim-1"}]


def test_failing_module_becomes_blocked_with_limitation():
    results, limitations = run_module_analyses(
        modules=[_OkModule(), _BoomModule()], case_data=_case_data())
    assert results["family"]["status"] == "complete"
    assert results["consumer"]["status"] == "blocked"
    assert results["consumer"]["reason"]
    assert any("consumer" in lim["message"] for lim in limitations)


def test_disabled_modules_are_excluded_from_resolution():
    from app.core.classification import ClassificationResult
    from app.core.module_registry import LegalModuleRegistry

    registry = LegalModuleRegistry.with_defaults()
    registry.register(_OkModule())
    classification = ClassificationResult(
        primary_area="family", related_areas=[], source="model")
    assert [m.module_id for m in registry.resolve(classification)] == \
        ["universal", "family"]
    assert [m.module_id for m in
            registry.resolve(classification, enabled={"universal"})] == ["universal"]
