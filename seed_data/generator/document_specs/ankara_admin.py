"""Ankara RES — Mali/İdari belge spec'leri (Phase 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-ADM-001": DocumentSpec(
        doc_id="DOC-ANK-ADM-001",
        family="letter",
        subtitle_tr="Ankara RES İşletme Bütçesi",
        subtitle_en="",
        section_headings_tr=["Bütçe Kapsamı", "Onay"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="Yıllık İşletme Bütçesi Onayı — [[project_name]]",
    ),
    "DOC-ANK-ADM-002": DocumentSpec(
        doc_id="DOC-ANK-ADM-002",
        family="report",
        subtitle_tr="Ankara RES — Sigorta Programı Gözden Geçirme Notu",
        subtitle_en="",
        section_headings_tr=["Gözden Geçirme Kapsamı", "Değerlendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
}
