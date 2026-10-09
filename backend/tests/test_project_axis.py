"""Adım 4 (ADR-030, 09.10.2026; `docs/plans/ADIM4_PLAN.md`): `classify_project_axis` is a
pure function — no DB, no session — so every outcome is tested directly on the
distribution it reads."""

from __future__ import annotations

from app.services.assist import ProjectAxisDecision, classify_project_axis

DEFAULT = {"disambig_spread": 0.5, "dominant_share": 0.75}


def test_named_wins_outright_regardless_of_distribution() -> None:
    # even a perfectly even, two-project distribution is irrelevant once one project is named
    decision = classify_project_axis({"IZM_RES": 5, "ANK_RES": 5}, {"IZM_RES"}, **DEFAULT)
    assert decision == ProjectAxisDecision("named", "IZM_RES")


def test_two_or_more_named_projects_is_none_not_disambiguate() -> None:
    """Ü-3's own multi-project path (GEN-CMP-001/002/003): never asks to disambiguate."""
    decision = classify_project_axis(
        {"ANK_RES": 6, "IZM_RES": 1}, {"ANK_RES", "IZM_RES"}, **DEFAULT
    )
    assert decision == ProjectAxisDecision("none")


def test_close_distribution_is_disambiguate_with_every_close_code() -> None:
    decision = classify_project_axis({"ANK_RES": 4, "IZM_RES": 3}, set(), **DEFAULT)
    assert decision.kind == "disambiguate"
    assert decision.codes == ("ANK_RES", "IZM_RES")
    assert decision.project_code is None


def test_three_way_close_distribution_lists_only_the_close_codes() -> None:
    # ANK_RES/IZM_RES are close (3 ≥ 0.5×4); KZL_RES (1 < 0.5×4 = 2.0) is not listed
    decision = classify_project_axis(
        {"ANK_RES": 4, "IZM_RES": 3, "KZL_RES": 1}, set(), disambig_spread=0.5, dominant_share=0.9
    )
    assert decision.kind == "disambiguate"
    assert decision.codes == ("ANK_RES", "IZM_RES")


def test_dominant_share_fires_when_one_project_clearly_leads() -> None:
    # ANK-NEG-004 shape: 6 Ankara / 1 İzmir, total 7 → share ≈ 0.857 ≥ 0.75
    decision = classify_project_axis({"ANK_RES": 6, "IZM_RES": 1}, set(), **DEFAULT)
    assert decision == ProjectAxisDecision("dominant", "ANK_RES")


def test_gap_between_the_two_thresholds_is_none() -> None:
    # second/top = 0.4 < 0.5 (not disambiguate); share = 5/(5+2) ≈ 0.714 < 0.75 (not dominant)
    decision = classify_project_axis({"ANK_RES": 5, "IZM_RES": 2}, set(), **DEFAULT)
    assert decision == ProjectAxisDecision("none")


def test_single_project_or_no_candidates_is_none() -> None:
    assert classify_project_axis({"ANK_RES": 5}, set(), **DEFAULT) == ProjectAxisDecision("none")
    assert classify_project_axis({}, set(), **DEFAULT) == ProjectAxisDecision("none")
    assert classify_project_axis({None: 5}, set(), **DEFAULT) == ProjectAxisDecision("none")


def test_company_level_candidates_never_count_toward_either_threshold() -> None:
    # None (company-level) documents sit alongside the two projects but are not a project
    decision = classify_project_axis({"ANK_RES": 6, "IZM_RES": 1, None: 20}, set(), **DEFAULT)
    assert decision == ProjectAxisDecision("dominant", "ANK_RES")


def test_thresholds_are_read_from_the_caller_not_hardcoded() -> None:
    # a looser dominant threshold turns the "gap" case above into dominant
    decision = classify_project_axis(
        {"ANK_RES": 5, "IZM_RES": 2}, set(), disambig_spread=0.5, dominant_share=0.7
    )
    assert decision == ProjectAxisDecision("dominant", "ANK_RES")


def test_project_distribution_counts_by_code() -> None:
    from datetime import date
    from uuid import uuid4

    from app.services.assist import AvailableDocument

    def card(code: str | None) -> AvailableDocument:
        return AvailableDocument(uuid4(), "t", "d", date(2024, 1, 1), code, None)

    cards = [card("ANK_RES"), card("ANK_RES"), card("IZM_RES"), card(None)]
    from app.services.assist import project_distribution

    assert project_distribution(cards) == {"ANK_RES": 2, "IZM_RES": 1, None: 1}
