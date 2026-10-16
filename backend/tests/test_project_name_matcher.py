"""İş Emri 2026-10-16T3 (ADR-033) — the project-name matcher itself: ASCII/case-insensitive,
word-bounded, RES/GES/"Santral(i)" never distinctive alone. `assist.named_project_codes`
(recognition) and `project_narrowing.unknown_project_names` (rejection), table-driven against
the four defects T1 §B5 measured (`scripts/t1/b5_alias_vectors.py`, 36/45):

  (a) ASCII spelling ("Kizilova") was refused as unknown even though the project exists;
  (b) a lower/mixed-case name word ("bursa RES") was neither recognised nor rejected — it
      passed through to the router/LLM untouched;
  (c) "RES"/"GES" alone was treated as a project's "specific" word whenever only one active
      project happened to carry that suffix — "X GES" then always named that project;
  (d) `named_project_codes` matched by substring, not whole word — "test" matched inside
      "testi".

Narrowing (`narrow_allowed`), authorization and the scorer are untouched; this file only
exercises the matcher. See `test_project_narrowing.py` for the gate/narrowing behaviour and
its own (unchanged) `test_unknown_project_names_reads_the_projects_table` /
`test_inactive_project_is_never_named_known_or_visible` regression coverage."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.project import Project
from app.services import project_narrowing as narrowing
from app.services.assist import named_project_codes


@pytest.fixture
def projects(db_session: Session) -> dict[str, Project]:
    rows = {
        "ANK_RES": Project(name="Karatepe RES", code="ANK_RES"),
        "IZM_RES": Project(name="Kızılova RES", code="IZM_RES"),
        "YSV_RES": Project(name="Yeşilova RES", code="YSV_RES"),
        "BOZ_RES": Project(name="Boztepe RES", code="BOZ_RES"),
        "AKY_GES": Project(name="Akyar GES", code="AKY_GES"),
        # active (unlike the deactivated TEST_PRJ of test_project_narrowing.py) — needed to
        # actually exercise the word-boundary fix (an inactive project's words are filtered
        # out before the boundary check ever runs).
        "TST_ACT": Project(name="Test Project", code="TST_ACT"),
    }
    db_session.add_all(rows.values())
    db_session.commit()
    return rows


# ---------------------------------------------------------------- (a) ASCII / case fold


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Kizilova RES'in COD tarihi nedir?", {"IZM_RES"}),
        ("KIZILOVA RES COD tarihi nedir?", {"IZM_RES"}),
        ("kizilova COD tarihi nedir?", {"IZM_RES"}),
        ("Yesilova RES'in kredi bakiyesi nedir?", {"YSV_RES"}),
        ("YEŞİLOVA RES kredi bakiyesi nedir?", {"YSV_RES"}),
        ("yesilova kredi bakiyesi nedir?", {"YSV_RES"}),
        ("KARATEPE res kapasitesi nedir?", {"ANK_RES"}),
        ("boztepe DSRA bakiyesi nedir?", {"BOZ_RES"}),
    ],
)
def test_ascii_and_case_insensitive_recognition(
    projects: dict[str, Project], db_session: Session, question: str, expected: set[str]
) -> None:
    assert named_project_codes(db_session, question) == expected


# ---------------------------------------------------------------- (b) Turkish suffixes


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Karatepe'nin kapasitesi nedir?", {"ANK_RES"}),
        ("Karatepe RES'in kapasitesi nedir?", {"ANK_RES"}),
        ("Kızılova'daki ÇED durumu nedir?", {"IZM_RES"}),
        ("Yeşilova'nın kredi bakiyesi nedir?", {"YSV_RES"}),
        ("Boztepe'de DSRA bakiyesi nedir?", {"BOZ_RES"}),
        ("Karatepe projesinde kaç çalışan var?", {"ANK_RES"}),
        ("Akyar'ın kamulaştırma notu nerede?", {"AKY_GES"}),
        ("Kızılova RES'in, kapasitesi nedir?", {"IZM_RES"}),
    ],
)
def test_turkish_suffixes_still_recognised(
    projects: dict[str, Project], db_session: Session, question: str, expected: set[str]
) -> None:
    assert named_project_codes(db_session, question) == expected


# ---------------------------------------------------------------- (c) RES/GES suffix alone


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        # ambiguous suffix (project is RES, question says GES) — current, safe-side
        # behaviour is unchanged by this fix: the distinctive word still names the project,
        # independently of which suffix the user typed (Tansu kararı gerekiyor — see
        # ADR-033 and the report; not decided here).
        ("Boztepe GES kapasitesi nedir?", {"BOZ_RES"}),
        # the critical regression: "ges" alone must never drag in the one GES-suffixed
        # project (Akyar) for an unrelated/unregistered name.
        ("Güneşalan GES'in belgeleri var mı?", set()),
        ("Manisa GES'in COD tarihi nedir?", set()),
        # Akyar's own distinctive word still matches it.
        ("Akyar GES kamulaştırma notu nerede?", {"AKY_GES"}),
    ],
)
def test_res_ges_suffix_never_distinctive_alone(
    projects: dict[str, Project], db_session: Session, question: str, expected: set[str]
) -> None:
    assert named_project_codes(db_session, question) == expected


# ---------------------------------------------------------------- (d) word boundary


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("Kredi covenant testi sonucu nedir?", set()),
        ("Performans testi raporu nerede?", set()),
        ("Testçi bir rapor var mı?", set()),
        ("Test Project'in belgeleri nerede?", {"TST_ACT"}),
        ("Test Project belgeleri nerede?", {"TST_ACT"}),
    ],
)
def test_word_boundary_not_substring(
    projects: dict[str, Project], db_session: Session, question: str, expected: set[str]
) -> None:
    assert named_project_codes(db_session, question) == expected


# ---------------------------------------------------------------- unknown-project rejection,
# ASCII/case variants (unknown_project_names must still flag an unregistered name regardless
# of spelling/case, and a known project's ASCII/mis-cased spelling must NOT be flagged)


@pytest.mark.parametrize(
    ("question", "expected_unknown"),
    [
        ("bursa RES'in kapasitesi nedir?", ["bursa RES"]),
        ("Bursa Res kapasitesi nedir?", ["Bursa Res"]),
        ("BURSA RES kapasitesi nedir?", ["BURSA RES"]),
        ("bursa ges'in kapasitesi nedir?", ["bursa ges"]),
    ],
)
def test_unknown_project_rejected_regardless_of_case(
    projects: dict[str, Project], db_session: Session, question: str, expected_unknown: list[str]
) -> None:
    assert narrowing.unknown_project_names(db_session, question) == expected_unknown
    assert named_project_codes(db_session, question) == set()


@pytest.mark.parametrize(
    "question",
    [
        "Kizilova RES'in kapasitesi nedir?",
        "KIZILOVA RES'in kapasitesi nedir?",
        "boztepe RES'in kapasitesi nedir?",
    ],
)
def test_known_project_ascii_or_case_variant_is_not_unknown(
    projects: dict[str, Project], db_session: Session, question: str
) -> None:
    assert narrowing.unknown_project_names(db_session, question) == []
