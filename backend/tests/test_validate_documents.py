"""`seed_data/generator/validate_documents.py` — P1/P2 prose rules and the G-checks
against the real generated manifest."""

from __future__ import annotations

from pathlib import Path

from seed_data.generator.validate_documents import (
    check_prose_document,
    scan_prose_text,
    validate_generated,
    validate_prose,
)

MANIFEST_PATH = Path(__file__).resolve().parent.parent / "seed_data" / "documents" / "manifest.json"


def test_real_prose_and_manifest_validate_clean() -> None:
    """Kabul kriteri: gerçek isim yok (validator) — committed prose + üretilen 15 belge."""
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
