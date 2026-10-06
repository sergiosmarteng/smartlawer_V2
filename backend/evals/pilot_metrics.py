"""Agregador do piloto 50 execuções (rubrica congelada v1).

Puro stdlib (statistics): recebe lista de casos avaliados e devolve
métricas agregadas + veredito Go / Não-go contra os thresholds de
`rubric_pilot_v1.toml` (§8 do plano do piloto). Sem I/O de rede ou DB.
"""

from __future__ import annotations

import statistics
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11 (não suportado em prod)
    tomllib = None  # type: ignore[assignment]

EVALS_DIR = Path(__file__).resolve().parent
RUBRIC_PATH = EVALS_DIR / "rubric_pilot_v1.toml"

_NUMERIC_AXES = (
    ("visao_geral", "utilidade"),
    ("visao_geral", "precisao_factual"),
    ("visao_geral", "cobertura"),
    ("pedidos", "completude"),
    ("pedidos", "fontes_resolvidas"),
    ("pedidos", "valores_extraidos"),
    ("provas", "identificacao"),
    ("provas", "matriz_pedido_x_prova"),
    ("direito", "pertinencia"),
    ("direito", "verificacao"),
    ("calculos", "corretude"),
    ("calculos", "reproducao"),
    ("estrategia_acoes", "utilidade"),
    ("estrategia_acoes", "cobertura_risco"),
    ("revisao", "facilidade_correcao"),
    ("revisao", "historico_versoes"),
)


def load_rubric(path: Path | None = None) -> dict:
    """Carrega e valida minimamente a rubrica congelada."""
    if tomllib is None:
        raise RuntimeError("tomllib indisponível (exige Python 3.11+)")
    with open(path or RUBRIC_PATH, "rb") as f:
        rubric = tomllib.load(f)
    if rubric.get("version") != "v1" or rubric.get("frozen") is not True:
        raise ValueError("rubrica precisa ser v1 e frozen=true")
    go = rubric["thresholds"]["go"]
    for key in ("utilidade_media_min", "afirmacao_sem_fonte_max_pct",
                "erro_calculo_grave_max_pct", "incidentes_privacidade_max"):
        if key not in go:
            raise ValueError(f"threshold ausente na rubrica: {key}")
    return rubric


def _pct(part: int, total: int) -> float:
    return round(100.0 * part / total, 2) if total else 0.0


def aggregate(cases: list[dict], custo_cap_usd: float = 100.0) -> dict:
    """Agrega N casos avaliados em métricas do §8 (métricas agregadas)."""
    if not cases:
        raise ValueError("sem casos avaliados")
    n = len(cases)
    values: dict[str, list[float]] = {}
    for section, field in _NUMERIC_AXES:
        vals = []
        for case in cases:
            try:
                vals.append(float(case["secoes"][section][field]))
            except (KeyError, TypeError, ValueError):
                continue
        if vals:
            values[f"{section}.{field}"] = vals
    utilidades = values.get("visao_geral.utilidade", [])
    custos = [float(c["custos"]["custo_usd"]) for c in cases
              if "custos" in c and "custo_usd" in c["custos"]]
    agg: dict = {
        "n": n,
        "media_utilidade": round(statistics.fmean(utilidades), 2) if utilidades else 0.0,
        "medias_por_eixo": {
            k: round(statistics.fmean(v), 2) for k, v in values.items()
        },
        "pct_limitacoes_explicitas": _pct(
            sum(1 for c in cases
                if c.get("secoes", {}).get("visao_geral", {}).get("limitacoes_explicitas")),
            n),
        "pct_falha_provedor": _pct(sum(1 for c in cases if c.get("falha_provedor")), n),
        "pct_progresso_coerente": _pct(
            sum(1 for c in cases
                if c.get("estado_honesto", {}).get("progresso_coerente")),
            n),
        "pct_afirmacao_sem_fonte": _pct(
            sum(1 for c in cases if c.get("afirmacao_sem_fonte")), n),
        "pct_erro_calculo_grave": _pct(
            sum(1 for c in cases
                if c.get("secoes", {}).get("calculos", {}).get("erro_grave")),
            n),
        "pct_tese_inventada": _pct(sum(1 for c in cases if c.get("tese_inventada")), n),
        "incidentes_privacidade": sum(
            1 for c in cases for i in c.get("incidentes", [])
            if isinstance(i, dict) and i.get("severidade") == "privacidade"),
        "custo_mediano_usd": round(statistics.median(custos), 2) if custos else 0.0,
        "custo_cap_usd": custo_cap_usd,
    }
    return agg


def verdict(agg: dict, custo_cap_usd: float = 100.0) -> dict:
    """Veredito Go / Não-go (§8). Non-go sempre com motivos registrados."""
    rubric = load_rubric()
    go = rubric["thresholds"]["go"]
    nongo = rubric["thresholds"]["nongo"]
    motivos: list[str] = []
    if agg["media_utilidade"] < go["utilidade_media_min"]:
        motivos.append(f"utilidade média {agg['media_utilidade']} < {go['utilidade_media_min']}")
    if agg["media_utilidade"] <= nongo["utilidade_media_max"]:
        motivos.append(f"utilidade média {agg['media_utilidade']} <= {nongo['utilidade_media_max']} (não-go duro)")
    if agg["pct_afirmacao_sem_fonte"] > go["afirmacao_sem_fonte_max_pct"]:
        motivos.append(f"afirmação sem fonte {agg['pct_afirmacao_sem_fonte']}% > {go['afirmacao_sem_fonte_max_pct']}%")
    if agg["pct_afirmacao_sem_fonte"] >= nongo["afirmacao_sem_fonte_min_pct"]:
        motivos.append("afirmação sem fonte acima do limite de não-go")
    if agg["pct_erro_calculo_grave"] > go["erro_calculo_grave_max_pct"]:
        motivos.append(f"erro grave de cálculo {agg['pct_erro_calculo_grave']}% > {go['erro_calculo_grave_max_pct']}%")
    if agg["pct_tese_inventada"] >= nongo["tese_inventada_min_pct"]:
        motivos.append(f"teses inventadas detectadas ({agg['pct_tese_inventada']}%)")
    if agg["incidentes_privacidade"] > go["incidentes_privacidade_max"]:
        motivos.append(f"incidentes de privacidade: {agg['incidentes_privacidade']}")
    if agg["custo_mediano_usd"] > custo_cap_usd:
        motivos.append(f"custo mediano {agg['custo_mediano_usd']} > cap {custo_cap_usd}")
    if agg["custo_mediano_usd"] > nongo["custo_mult_max"] * custo_cap_usd:
        motivos.append("custo explodiu (>2x do cap)")
    decisao = "Não-go" if motivos else "Go"
    return {"decisao": decisao, "motivos": motivos, "n": agg["n"]}
