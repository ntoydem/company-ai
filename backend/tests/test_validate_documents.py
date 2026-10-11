"""`seed_data/generator/validate_documents.py` — P1/P2 prose rules and the G-checks
against the real generated manifest."""

from __future__ import annotations

from pathlib import Path

from seed_data.generator.document_specs._base import DocumentSpec
from seed_data.generator.validate_documents import (
    MAX_HEADING_CHARS,
    MAX_HEADING_WORDS,
    check_heading_hygiene,
    check_number_format_consistency,
    check_prose_document,
    scan_prose_text,
    validate_generated,
    validate_prose,
)

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "seed_data" / "documents" / "manifest.json"


def test_real_prose_and_manifest_validate_clean() -> None:
    """Kabul kriteri: gerçek isim yok (validator) — committed prose + üretilen 84 belge."""
    prose_report = validate_prose()
    assert prose_report.errors == []
    generated_report = validate_generated(MANIFEST_PATH)
    assert generated_report.errors == []


def test_clause_numbering_does_not_trigger_number_check() -> None:
    """Ek not: "Madde 12.3" gibi madde/bölüm referansları P1'i tetiklememeli. `\\d{3,}`
    yalnızca 3+ ardışık haneyi eşleştirir; "12" ve "3" ayrı ayrı 1-2 hane olduğundan
    hiçbir eşleşme oluşmaz. Yalnızca 100+ maddeli bir belge (burada hiçbiri yok) veya
    açıkça 3+ haneli bir madde numarası (örn. "Madde 123") bunu tetikler — ikinci durum
    kasıtlı olarak burada da doğrulanıyor, gerçek bir sayı sızıntısından ayırt edilemez
    olduğu için."""
    assert scan_prose_text("Bu husus Madde 12.3 uyarınca düzenlenmiştir.") == []
    assert scan_prose_text("See Clause 5.2 and Clause 7 above.") == []
    assert scan_prose_text("Madde 123 kapsamında değerlendirilir.") != []


def test_currency_and_company_name_are_caught() -> None:
    assert any(
        "para birimi" in issue
        for issue in scan_prose_text("Tutar 50000 EUR olarak belirlenmiştir.")
    )
    assert any(
        "şirket adı" in issue
        for issue in scan_prose_text("Taraf olarak Gerçek Bir Şirket A.Ş. yer almaktadır.")
    )


def test_placeholder_is_stripped_before_number_scan() -> None:
    assert scan_prose_text("Kapasite [[capacity_mw]] olarak belirlenmiştir.") == []


def test_unknown_placeholder_is_rejected() -> None:
    prose = {
        "sections": [
            {
                "heading": "Lisans Kapsamı",
                "paragraphs": ["Kapasite [[not_a_real_field]] olarak belirlenmiştir."],
            },
            {"heading": "Kapasite ve Teknik Bilgiler", "paragraphs": ["Metin."]},
            {"heading": "Yükümlülükler", "paragraphs": ["Metin."]},
        ]
    }
    errors = check_prose_document("DOC-ANK-DEV-001", prose, known_placeholders={"capacity_mw"})
    assert any("bilinmeyen [[not_a_real_field]]" in e for e in errors)


def test_section_count_mismatch_is_rejected() -> None:
    prose = {"sections": [{"heading": "Lisans Kapsamı", "paragraphs": ["Metin."]}]}
    errors = check_prose_document("DOC-ANK-DEV-001", prose, known_placeholders=set())
    assert any("bölüm üretildi" in e for e in errors)


def test_real_document_specs_headings_pass_hygiene_gate() -> None:
    """DOC-YSV-FIN-009 düzeltmesi (11.10.2026) sonrası: hiçbir başlık talimat sızdırmıyor."""
    assert check_heading_hygiene() == []


def _fake_spec(heading: str) -> DocumentSpec:
    return DocumentSpec(
        doc_id="DOC-TEST-001",
        family="letter",
        subtitle_tr="",
        subtitle_en="",
        section_headings_tr=[],
        section_headings_en=[heading],
    )


def test_overlong_heading_is_rejected(monkeypatch) -> None:
    heading = "1. The Facility (a Separate, Later, Partial Financing; Never Capex or Equity Here)"
    assert len(heading) > MAX_HEADING_CHARS
    monkeypatch.setattr(
        "seed_data.generator.validate_documents.SPECS", {"DOC-TEST-001": _fake_spec(heading)}
    )
    errors = check_heading_hygiene()
    assert any("karakter" in e for e in errors)


def test_too_many_words_in_heading_is_rejected(monkeypatch) -> None:
    heading = "1. A Heading With Clearly Too Many Words In It For Comfort"
    assert len(heading.split()) > MAX_HEADING_WORDS
    monkeypatch.setattr(
        "seed_data.generator.validate_documents.SPECS", {"DOC-TEST-001": _fake_spec(heading)}
    )
    errors = check_heading_hygiene()
    assert any("kelime" in e for e in errors)


def test_imperative_word_in_heading_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr(
        "seed_data.generator.validate_documents.SPECS",
        {"DOC-TEST-001": _fake_spec("1. The Facility (Never Mention Capex)")},
    )
    errors = check_heading_hygiene()
    assert any("emir kipi" in e for e in errors)


def test_meta_comment_pattern_in_heading_is_rejected(monkeypatch) -> None:
    monkeypatch.setattr(
        "seed_data.generator.validate_documents.SPECS",
        {"DOC-TEST-001": _fake_spec("1. Recitals (Past Tense: Already Built)")},
    )
    errors = check_heading_hygiene()
    assert any("meta-yorum" in e for e in errors)


def test_legitimate_short_parenthetical_heading_passes(monkeypatch) -> None:
    monkeypatch.setattr(
        "seed_data.generator.validate_documents.SPECS",
        {"DOC-TEST-001": _fake_spec("2. The Facility (Supplementary Financing)")},
    )
    assert check_heading_hygiene() == []


def test_tr_grouped_number_in_en_document_is_rejected() -> None:
    """DOC-YSV-FIN-009 olayı: `repayment_profile` TR biçiminde (98.000) yazılmıştı."""
    errors = check_number_format_consistency("DOC-X", "en", "Equal principal (98.000 USD).")
    assert any("TR-biçimi" in e for e in errors)


def test_en_grouped_number_in_tr_document_is_rejected() -> None:
    errors = check_number_format_consistency("DOC-X", "tr", "Toplam tutar 26,400,000 USD.")
    assert any("EN-biçimi" in e for e in errors)


def test_correctly_formatted_numbers_pass_both_languages() -> None:
    assert check_number_format_consistency("DOC-X", "en", "Total capex is 26,400,000 USD.") == []
    assert check_number_format_consistency("DOC-X", "tr", "Toplam capex 26.400.000 USD.") == []


def test_decimal_ratios_and_percentages_do_not_false_positive() -> None:
    """1.15x / %0,80 gibi ondalık oranlar gruplu sayı sanılmamalı (3 hane şartı)."""
    assert check_number_format_consistency("DOC-X", "en", "DSCR covenant of 1.15x.") == []
    assert check_number_format_consistency("DOC-X", "tr", "Oran %0,80 olarak hesaplanır.") == []
