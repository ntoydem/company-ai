"""Karatepe RES — Development/lisans belge spec'leri (Phase 3.1 + 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-DEV-001": DocumentSpec(
        doc_id="DOC-ANK-DEV-001",
        family="letter",
        subtitle_tr="Karatepe RES Rüzgar Enerjisi Üretim Tesisi",
        subtitle_en="",
        section_headings_tr=["Lisans Kapsamı", "Kapasite ve Teknik Bilgiler", "Yükümlülükler"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Üretim Lisansı — [[project_name]]",
    ),
    "DOC-ANK-DEV-002": DocumentSpec(
        doc_id="DOC-ANK-DEV-002",
        family="letter",
        subtitle_tr="Karatepe RES Üretim Lisansı Tadili",
        subtitle_en="",
        section_headings_tr=["Tadil Gerekçesi", "Güncellenen Kapasite Bilgisi", "Yürürlük"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Üretim Lisansı Tadili — [[project_name]]",
    ),
    "DOC-ANK-DEV-003": DocumentSpec(
        doc_id="DOC-ANK-DEV-003",
        family="agreement",
        subtitle_tr="Karatepe RES Şebeke Bağlantı Anlaşması",
        subtitle_en="",
        section_headings_tr=["1. Bağlantı Kapsamı", "2. Yürürlük ve Genel Hükümler"],
        section_headings_en=[],
        signature_roles_tr=["İmza: [[spv_name]] Yetkilisi", "İmza: [[counterparty]] Yetkilisi"],
    ),
    "DOC-ANK-DEV-004": DocumentSpec(
        doc_id="DOC-ANK-DEV-004",
        family="letter",
        subtitle_tr="Karatepe RES İnşaat İzinleri",
        subtitle_en="",
        section_headings_tr=["Ruhsat Kapsamı", "Yürürlük"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="Yapı Ruhsatı — [[project_name]]",
    ),
    "DOC-ANK-DEV-005": DocumentSpec(
        doc_id="DOC-ANK-DEV-005",
        family="letter",
        subtitle_tr="Karatepe RES Çevresel Değerlendirme",
        subtitle_en="",
        section_headings_tr=["Değerlendirme Kapsamı", "Karar"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="ÇED Olumlu Kararı — [[project_name]]",
    ),
    "DOC-ANK-DEV-006": DocumentSpec(
        doc_id="DOC-ANK-DEV-006",
        family="agreement",
        subtitle_tr="Karatepe RES Saha Kullanım Hakkı",
        subtitle_en="",
        section_headings_tr=["1. Kullanım Hakkının Kapsamı", "2. Yürürlük ve Genel Hükümler"],
        section_headings_en=[],
        signature_roles_tr=["İmza: [[spv_name]] Yetkilisi", "İmza: [[counterparty]] Yetkilisi"],
    ),
}
