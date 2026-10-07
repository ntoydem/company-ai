import uuid
from datetime import date

from app.models.document import Document, DocumentStatus
from app.repositories.document_chunk_repo import RetrievedChunk
from app.services.answer_prompt import (
    COMPARISON_NOTICE,
    NO_ANSWER_TEXT,
    SYSTEM_PROMPT,
    PromptSource,
    describe_chain,
    format_source,
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


def test_rule_10_forbids_cross_project_comparison_with_the_fixed_notice() -> None:
    """Ü-3 (Balbal Anayasası v2.0): several projects → separate sentences per project, no
    comparison/ranking/difference; an explicit comparison request gets the fixed notice first."""
    assert "10. Soru birden fazla projeyi" in SYSTEM_PROMPT
    assert "karşılaştırma, sıralama" in SYSTEM_PROMPT
    assert COMPARISON_NOTICE in SYSTEM_PROMPT
    assert COMPARISON_NOTICE == (
        "Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır."
    )


def _source(**overrides: object) -> PromptSource:
    document = Document(
        title="Sigorta Yenileme Bildirimi",
        document_type="Insurance Notice",
        document_date=date(2024, 1, 10),
        counterparty="STU Sigorta",
        status=DocumentStatus.executed,
        tags=[],
        effective_date=date(2024, 1, 10),
        expiration_date=overrides.pop("expiration_date", None),  # type: ignore[arg-type]
        version=1,
    )
    chunk = RetrievedChunk(
        id=uuid.uuid4(),
        document_id=uuid.uuid4(),
        chunk_index=0,
        page_number=1,
        text="metin",
        rank=1.0,
    )
    return PromptSource(ref="K1", chunk=chunk, document=document, position=_position())


def test_format_source_adds_the_expiration_line_only_when_the_document_has_one() -> None:
    """ADR-026: the model reads a ready-made sentence, it never computes the date
    difference itself (rule 3/8) — and an older source without `expiration_date` keeps
    its exact previous text (no empty line is ever inserted)."""
    without = format_source(_source(), date(2026, 9, 15))
    assert "Süre:" not in without

    with_one = format_source(_source(expiration_date=date(2025, 1, 9)), date(2026, 9, 15))
    assert "Süre: 09.01.2025 tarihinde sona erdi (1 yıl 8 ay önce)" in with_one
    assert (
        with_one.replace("Süre: 09.01.2025 tarihinde sona erdi (1 yıl 8 ay önce)\n", "") == without
    )


def test_rule_12_asks_one_question_on_ambiguity_only_in_the_assist_prompt() -> None:
    """Tansu decision (a), 07.10.2026: an ambiguous question → the fixed sentence + one
    SORU: line, never an enumeration; version chains, named scope, "tüm/hepsi/listele" and
    multi-project questions are excluded. Flag off: today's prompt, byte-identical."""
    from app.services.answer_prompt import SYSTEM_PROMPT_ASSIST

    rule = SYSTEM_PROMPT_ASSIST.split("\n12. ", 1)[1]
    assert "birini seçme ve hepsini sıralama" in rule
    assert "sürüm zinciri" in rule and '"son"' in rule and '"güncel"' in rule
    assert '"tüm"' in rule and '"hepsi"' in rule and '"listele"' in rule
    assert (
        "birden fazla projeyi ADIYLA" in rule
    )  # revision 1: sources from two projects ≠ exclusion
    assert "adayları listeleme" in rule and "tek başına kapsam vermez" in rule
    assert "dönem" in rule and "farklı dönemler" not in rule  # Naci (c): no bare "periods"
    assert "\n12. " not in SYSTEM_PROMPT
