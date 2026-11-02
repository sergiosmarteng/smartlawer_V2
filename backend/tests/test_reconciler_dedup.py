"""Dedup de claims no reconciler — regressão contra a reanálise de produção.

Em 2026-11-02 a reanálise de real_pi4.pdf gerou 19 claims para ~12-13 pedidos
reais: o reconciler agrupava por título literal, então cada paráfrase entre
lotes sobrepostos criava um pedido novo.

A regra nova só funde quando um conjunto de tokens CONTÉM o outro. Isso é
conservador por construção: termos diferentes nunca se contêm.
"""

from app.core.reconciler import (
    _claim_tokens,
    normalize_for_match,
    reconcile_extractions,
)

# Títulos exatos do artefato 27458429 (reanálise de produção, 2026-11-02).
PRODUCTION_TITLES = [
    "Gratuidade de Justiça",
    "Indenização por Danos Materiais",
    "Reparação por danos materiais e lucros cessantes",
    "Danos extrapatrimoniais (morais)",
    "Danos estéticos",
    "Pensão vitalícia",
    "Indenização normativa – CCT",
    "Honorários advocatícios",
    "Controle difuso de constitucionalidade dos arts. 790-B e 791-A da CLT",
    "Justiça Gratuita por critério de renda",
    "Notificação da Reclamada",
    "Indenização por danos materiais e lucros cessantes",
    "Indenização por danos extrapatrimoniais (morais)",
    "Pensão mensal vitalícia",
    "Indenização prevista na CCT",
    "Constituição de Capital",
    "Processamento pelo procedimento comum",
    "Honorários sucumbenciais",
    "Procedência Total",
]


def _claim(title, *, number=None, refs=("bloco-1",), occurrences=1):
    return {
        "id": "c1",
        "title": title,
        "original_number": number,
        "source_refs": list(refs),
        "occurrences": occurrences,
    }


def _reconcile(*claims, batch=0):
    return reconcile_extractions([{"batch_index": batch, "claims": list(claims)}])


def test_normalization_strips_accents_punctuation_and_case():
    assert normalize_for_match("Indenização por Danos MATERIAIS (graves).") == (
        "indenizacao por danos materiais graves"
    )
    assert normalize_for_match(None) == ""


def test_lead_ins_do_not_distinguish_claims():
    """'Indenização por X' e 'Reparação por X' são o mesmo pedido."""
    assert _claim_tokens("Indenização por danos morais") == _claim_tokens(
        "Reparação por danos morais"
    )


def test_production_titles_collapse_to_fourteen():
    out = _reconcile(*[_claim(t) for t in PRODUCTION_TITLES])

    assert len(out["claims"]) == 14, [
        c["title"] for c in out["claims"]
    ]


def test_moral_and_esthetic_damages_never_merge():
    """Risco jurídico: fundir pedidos distintos é pior que duplicar."""
    out = _reconcile(
        _claim("Danos morais"),
        _claim("Danos estéticos"),
    )
    assert len(out["claims"]) == 2


def test_pension_variants_merge_into_richer_title():
    out = _reconcile(
        _claim("Pensão vitalícia"),
        _claim("Pensão mensal vitalícia"),
    )
    assert len(out["claims"]) == 1
    assert out["claims"][0]["title"] == "Pensão mensal vitalícia"


def test_merge_unions_source_refs_and_occurrences():
    out = _reconcile(
        _claim("Danos morais", refs=["b1", "b2"]),
        _claim("Indenização por danos morais", refs=["b2", "b3"], occurrences=2),
    )
    assert len(out["claims"]) == 1
    assert out["claims"][0]["source_refs"] == ["b1", "b2", "b3"]
    assert out["claims"][0]["occurrences"] == 3


def test_different_original_numbers_never_merge():
    out = _reconcile(
        _claim("Pensão vitalícia", number="1"),
        _claim("Pensão vitalícia", number="2"),
    )
    assert len(out["claims"]) == 2


def test_same_number_merges_even_with_different_titles():
    out = _reconcile(
        _claim("Danos morais", number="Pedido 3"),
        _claim("Indenização por dano moral", number="item 3."),
    )
    assert len(out["claims"]) == 1
    assert out["claims"][0]["source_refs"]


def test_claims_without_meaningful_tokens_never_merge():
    """Título vazio ou só com aberturas não pode colar em tudo."""
    out = _reconcile(
        _claim(""),
        _claim("Pedido de indenização"),
    )
    assert len(out["claims"]) == 2


def test_facts_dedupe_by_normalized_statement_and_author():
    extractions = [
        {
            "batch_index": 0,
            "facts": [
                {"id": "f1", "statement": "Genitores separados de fato.",
                 "asserted_by": "Autor", "source_refs": ["b1"]},
            ],
        },
        {
            "batch_index": 1,
            "facts": [
                {"id": "f2", "statement": "genitores separados de fato",
                 "asserted_by": "autor", "source_refs": ["b9"]},
                {"id": "f3", "statement": "Genitores separados de fato.",
                 "asserted_by": "Réu", "source_refs": ["b9"]},
            ],
        },
    ]
    out = reconcile_extractions(extractions)

    assert len(out["facts"]) == 2, "autor e réu devem permanecer separados"
    authors = {f["asserted_by"].casefold() for f in out["facts"]}
    assert authors == {"autor", "réu"}
