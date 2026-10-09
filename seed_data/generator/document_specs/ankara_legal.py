"""Karatepe RES — Hukuk belge spec'leri (Phase 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-LEG-001": DocumentSpec(
        doc_id="DOC-ANK-LEG-001",
        family="report",
        subtitle_tr="",
        subtitle_en="Karatepe RES — Legal Opinion on Conditions Precedent",
        section_headings_tr=[],
        section_headings_en=["1. Scope of Review", "2. Conclusion"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-LEG-002": DocumentSpec(
        doc_id="DOC-ANK-LEG-002",
        family="report",
        subtitle_tr="Karatepe RES — Hukuki İnceleme Notu",
        subtitle_en="",
        section_headings_tr=["İnceleme Kapsamı", "Değerlendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-ANK-LEG-003": DocumentSpec(
        doc_id="DOC-ANK-LEG-003",
        family="report",
        subtitle_tr="Karatepe RES — Sözleşme Uyum Değerlendirmesi",
        subtitle_en="",
        section_headings_tr=["Değerlendirme Kapsamı", "Sonuç"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
}
