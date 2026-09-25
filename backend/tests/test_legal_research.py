"""V2 T07 — pesquisa verificável (aceite do plano)."""

from app.core.legal_research import (
    MODE_CURRENT,
    MODE_HISTORIC,
    STATUS_AMBIGUOUS,
    STATUS_EXPIRED,
    STATUS_POSTERIOR,
    STATUS_UNVERIFIED,
    STATUS_VERIFIED,
    FetchedSource,
    UnavailableSourceError,
    check_temporal,
    extract_citations,
    verify_citations,
)


def test_extractor_preserves_literal_and_flags_ambiguity():
    text = (
        "Nos termos do art. 5º da CF/88 e da Lei nº 13.467/2017, "
        "conforme Súmula 331 do TST. Também art. 5 prevê algo."
    )
    found = extract_citations(text)
    literals = [c.literal for c in found]
    assert any("13.467/2017" in lit for lit in literals)
    assert any("331" in lit for lit in literals)
    # "art. 5" isolado, sem instrumento no contexto → revisão.
    ambiguous = [c for c in found if c.literal.casefold() == "art. 5"]
    assert ambiguous and ambiguous[0].needs_review is True
    assert ambiguous[0].presumed_instrument is None
    # Com instrumento próximo, sem revisão.
    cf = [c for c in found if "5º" in c.literal]
    assert cf and cf[0].presumed_instrument is not None


def test_unavailable_source_never_becomes_authority():
    citations = extract_citations("Conforme art. 7º da CF/88.")

    def boom(_literal):
        raise UnavailableSourceError("timeout no tribunal")

    verifications, limitations = verify_citations(citations, boom)
    assert verifications
    assert all(v.status == STATUS_UNVERIFIED for v in verifications)
    assert all(v.fetched is None for v in verifications)
    assert len(limitations) == len(verifications)


def test_expired_norm_flags_fact_date():
    fetched = FetchedSource(
        citation="MP 808/2017", effective_from="2017-11-14", effective_to="2018-04-23"
    )
    assert (
        check_temporal(fetched, fact_date="2018-05-30", mode=MODE_HISTORIC)
        == STATUS_EXPIRED
    )
    assert (
        check_temporal(fetched, fact_date="2018-01-10", mode=MODE_HISTORIC)
        == STATUS_VERIFIED
    )


def test_posterior_thesis_does_not_join_piece():
    fetched = FetchedSource(
        citation="Tema 932", decision_dates=["2019-09-12", "2020-06-24"]
    )
    assert (
        check_temporal(fetched, piece_date="2019-11-19", mode=MODE_CURRENT)
        == STATUS_POSTERIOR
    )
    assert (
        check_temporal(fetched, piece_date="2021-01-01", mode=MODE_CURRENT)
        == STATUS_VERIFIED
    )


def test_mixed_verification_keeps_layers_separate():
    citations = extract_citations("Lei nº 13.467/2017 e art. 9.")

    def fetch(literal):
        if "13.467" in literal:
            return FetchedSource(citation=literal, url="https://example.invalid/lei")
        return None

    verifications, limitations = verify_citations(
        citations, fetch, piece_date="2019-11-19"
    )
    by_status = {v.citation: v.status for v in verifications}
    assert by_status.get("Lei nº 13.467/2017") == STATUS_VERIFIED
    ambiguous = [v for v in verifications if v.status == STATUS_AMBIGUOUS]
    assert ambiguous  # art. 9 sem instrumento: ambíguo, não confirmado
    assert limitations  # cada pendência vira ação, não silêncio
