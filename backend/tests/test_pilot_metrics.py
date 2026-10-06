"""Tests for the frozen pilot rubric aggregator (piloto §7-§8)."""

import sys
from pathlib import Path

import pytest
import tomllib

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "evals"))

from pilot_metrics import aggregate, verdict

EVALS_DIR = Path(__file__).resolve().parents[1] / "evals"


def _case(**overrides):
    base = {
        "id": "doc-1",
        "secoes": {
            "visao_geral": {"utilidade": 4, "precisao_factual": 4,
                            "cobertura": 4, "limitacoes_explicitas": True},
            "pedidos": {"completude": 4, "fontes_resolvidas": 4,
                        "valores_extraidos": 4},
            "provas": {"identificacao": 4, "matriz_pedido_x_prova": 4},
            "direito": {"pertinencia": 4, "verificacao": 4},
            "calculos": {"corretude": 4, "reproducao": 4,
                         "erro_grave": False},
            "estrategia_acoes": {"utilidade": 4, "cobertura_risco": 4},
            "revisao": {"facilidade_correcao": 4, "historico_versoes": 4},
        },
        "estado_honesto": {"progresso_coerente": True, "falha_anunciada": True},
        "falha_provedor": False,
        "afirmacao_sem_fonte": False,
        "tese_inventada": False,
        "custos": {"tempo_primeira_info_util_min": 5.0,
                   "tempo_conclusao_min": 20.0, "custo_usd": 1.5},
        "incidentes": [],
    }
    base.update(overrides)
    return base


def test_rubric_toml_matches_piloto_thresholds():
    with open(EVALS_DIR / "rubric_pilot_v1.toml", "rb") as f:
        rubric = tomllib.load(f)
    assert rubric["version"] == "v1"
    assert rubric["frozen"] is True
    go = rubric["thresholds"]["go"]
    assert go["utilidade_media_min"] == 3.5
    assert go["afirmacao_sem_fonte_max_pct"] == 10
    assert go["erro_calculo_grave_max_pct"] == 5
    assert go["incidentes_privacidade_max"] == 0
    assert "utilidade" in rubric["dimensions"]["visao_geral"]


def test_all_good_cases_verdict_go():
    cases = [_case(id=f"doc-{i}") for i in range(1, 6)]
    agg = aggregate(cases, custo_cap_usd=2.0)
    assert agg["n"] == 5
    assert agg["media_utilidade"] == 4.0
    assert agg["pct_limitacoes_explicitas"] == 100.0
    assert agg["custo_mediano_usd"] == 1.5
    assert verdict(agg, custo_cap_usd=2.0)["decisao"] == "Go"


def test_bad_cases_verdict_nongo_with_reasons():
    cases = [_case(id="doc-1")]
    cases.append(_case(
        id="doc-2",
        afirmacao_sem_fonte=True,
        secoes={
            "visao_geral": {"utilidade": 2, "precisao_factual": 2,
                            "cobertura": 2, "limitacoes_explicitas": False},
            "calculos": {"corretude": 2, "reproducao": 2, "erro_grave": True},
            "tese_inventada": True,
        },
    ))
    agg = aggregate(cases, custo_cap_usd=2.0)
    result = verdict(agg, custo_cap_usd=2.0)
    assert result["decisao"] == "Não-go"
    assert result["motivos"], "non-go exige motivos registrados"


def test_empty_cases_raises():
    with pytest.raises(ValueError):
        aggregate([])
