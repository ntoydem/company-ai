"""Yeşilova RES — Finans belge spec'leri (Adım 5 İş 4b, 10.10.2026)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    "DOC-YSV-FIN-001": DocumentSpec(
        doc_id="DOC-YSV-FIN-001",
        family="letter",
        subtitle_tr="Yeşilova RES — Taksit #11 Banka Faiz Bildirimi",
        subtitle_en="",
        section_headings_tr=["Faiz Tutarı", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları", "Onaylayan: Yetkili İmza"],
        subject_label_tr="Taksit #11 Faiz Bildirimi — [[project_name]]",
    ),
    "DOC-YSV-FIN-002": DocumentSpec(
        doc_id="DOC-YSV-FIN-002",
        family="letter",
        subtitle_tr="Yeşilova RES — Annex F Talep E-postası",
        subtitle_en="",
        section_headings_tr=["Talep", "Son Tarih"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları"],
        subject_label_tr="Annex F Raporlama Talebi — [[project_name]]",
    ),
    "DOC-YSV-FIN-003": DocumentSpec(
        doc_id="DOC-YSV-FIN-003",
        family="letter",
        subtitle_tr="Yeşilova RES — DSRA Hesap Ekstresi",
        subtitle_en="",
        section_headings_tr=["Hesap Bakiyesi", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları"],
        subject_label_tr="DSRA Hesap Ekstresi — [[project_name]]",
    ),
    "DOC-YSV-FIN-004": DocumentSpec(
        doc_id="DOC-YSV-FIN-004",
        family="letter",
        subtitle_tr="Yeşilova RES — Borç Servis Hesabı Ekstresi",
        subtitle_en="",
        section_headings_tr=["Hesap Bakiyesi", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları"],
        subject_label_tr="Borç Servis Hesabı Ekstresi — [[project_name]]",
    ),
    "DOC-YSV-FIN-005": DocumentSpec(
        doc_id="DOC-YSV-FIN-005",
        family="letter",
        subtitle_tr="Yeşilova RES — Sigorta Zeyilnamesi",
        subtitle_en="",
        section_headings_tr=["Poliçe Bilgileri", "Zeyilname"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili İmza"],
        # "Sigorta" kelimesi bilerek yok — hemen önündeki 1-4 büyük harfli kelimeyle
        # birlikte G2'nin isim deseniyle yanlış eşleşiyordu ("Ara Dönem Sigorta" bile
        # tetikliyordu, noktalama/tire ile ayrılmadığı her yerde; bkz. ADIM5 İş 4b raporu).
        subject_label_tr="Zeyilname Bildirimi — [[project_name]]",
    ),
    "DOC-YSV-FIN-006": DocumentSpec(
        doc_id="DOC-YSV-FIN-006",
        family="letter",
        subtitle_tr="Yeşilova RES — Bankaya Giden İşletme Bütçesi",
        subtitle_en="",
        section_headings_tr=["Bütçe Kapsamı", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları", "Onaylayan: Yetkili İmza"],
        subject_label_tr="İşletme Bütçesi — [[project_name]]",
    ),
}
