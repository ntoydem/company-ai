from datetime import date

from app.services.answer_prompt import (
    NO_ANSWER_TEXT,
    SYSTEM_PROMPT,
    describe_chain,
    is_no_answer,
    parse_citations,
)
from app.services.version_chain import ChainPosition


def _position(**overrides: object) -> ChainPosition:
    base: dict[str, object] = {
        "position": 1,
        "chain_length": 1,
        "in_force": True,
        "is_current": True,
        "is_initial": True,
        "has_predecessor": False,
        "has_successor": False,
        "supersedes_title": None,
        "superseded_by_title": None,
    }
    base.update(overrides)
    return ChainPosition(**base)  # type: ignore[arg-type]


def test_system_prompt_contains_fixed_strings_and_rules() -> None:
    assert NO_ANSWER_TEXT in SYSTEM_PROMPT
    assert "belgelerde sebep belirtilmemiş" in SYSTEM_PROMPT
    assert "Türkçe" in SYSTEM_PROMPT and "[K1]" in SYSTEM_PROMPT
    assert "İzmir RES" in SYSTEM_PROMPT  # project isolation rule
    assert date.today().isoformat() not in SYSTEM_PROMPT  # wall clock never enters the prompt


def test_parse_citations_unique_in_order_and_grouped() -> None:
    assert parse_citations("A [K2]. B [K1]. C [K2].") == ["K2", "K1"]
    assert parse_citations("X [K1, K3] Y [K03]") == ["K1", "K3"]
    assert parse_citations("no citations") == []


def test_is_no_answer_tolerates_wrapping() -> None:
    assert is_no_answer(NO_ANSWER_TEXT)
    assert is_no_answer(
        "Üzgünüm.  Mevcut şirket kaynaklarında bu soruyu güvenilir\nşekilde "
        "cevaplamak için yeterli bilgi BULAMADIM."
    )
    assert not is_no_answer("Minimum DSCR 1,20x [K1].")


def test_describe_chain_labels() -> None:
    assert describe_chain(_position()) == "GÜNCEL (zincirde tek belge)"
    assert (
        describe_chain(
            _position(
                chain_length=2,
                position=2,
                is_initial=False,
                has_predecessor=True,
                supersedes_title="Facility",
            )
        )
        == 'GÜNCEL — "Facility" belgesini değiştirir'
    )
    assert (
        describe_chain(
            _position(
                chain_length=2,
                is_current=False,
                has_successor=True,
                superseded_by_title="Amendment 01",
            )
        )
        == 'İLK HALKA (güncel değil) — "Amendment 01" tarafından değiştirilmiş'
    )
    assert describe_chain(_position(is_current=False, has_successor=True)) == (
        "İLK HALKA (güncel değil) — erişiminiz olmayan bir belge tarafından değiştirilmiş"
    )
    assert describe_chain(_position(is_current=False, in_force=False)) == "YÜRÜRLÜKTE DEĞİL"
