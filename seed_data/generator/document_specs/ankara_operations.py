"""Karatepe RES — Operation belge spec'leri (Phase 3.1 + 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec, ExtraTable

SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-OPS-001": DocumentSpec(
        doc_id="DOC-ANK-OPS-001",
        family="report",
        subtitle_tr="Karatepe RES — Aylık Üretim Raporu",
        subtitle_en="",
        section_headings_tr=["Genel Değerlendirme", "Performans Özeti"],
        section_headings_en=[],
        extra_table=ExtraTable(
            heading_tr="Aylık Üretim Verileri (son 6 ay)", heading_en="", kind="monthly_production"
        ),
        signature_roles_tr=["Hazırlayan: Saha Operasyon Mühendisi", "Kontrol Eden: İşletme Müdürü"],
    ),
    "DOC-ANK-OPS-004": DocumentSpec(
        doc_id="DOC-ANK-OPS-004",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — O&M Agreement",
        section_headings_tr=[],
        section_headings_en=["1. Scope of Services", "2. Term and Termination"],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-OPS-005": DocumentSpec(
        doc_id="DOC-ANK-OPS-005",
        family="report",
        subtitle_tr="Karatepe RES — Bakım Raporu",
        subtitle_en="",
        section_headings_tr=["Olay Özeti", "Üretime Etkisi"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-ANK-OPS-006": DocumentSpec(
        doc_id="DOC-ANK-OPS-006",
        family="report",
        subtitle_tr="Karatepe RES — Aylık Üretim Raporu",
        subtitle_en="",
        section_headings_tr=["Genel Değerlendirme", "Performans Özeti"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-ANK-OPS-007": DocumentSpec(
        doc_id="DOC-ANK-OPS-007",
        family="report",
        subtitle_tr="Karatepe RES — Aylık Üretim Raporu",
        subtitle_en="",
        section_headings_tr=["Genel Değerlendirme", "Performans Özeti"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-ANK-OPS-008": DocumentSpec(
        doc_id="DOC-ANK-OPS-008",
        family="report",
        subtitle_tr="Karatepe RES — Yıllık Performans Değerlendirme Notu",
        subtitle_en="",
        section_headings_tr=["Genel Değerlendirme", "Sonuç"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-ANK-OPS-009": DocumentSpec(
        doc_id="DOC-ANK-OPS-009",
        family="letter",
        # "RES"/"[[project_name]]" directly followed by "Sigorta" would false-positive the
        # N1/G2 company-name-pattern scan ("Karatepe RES Sigorta" reads like "<Name> Sigorta");
        # the em dash breaks the whitespace-only adjacency the pattern requires (Phase 5.1).
        subtitle_tr="Karatepe RES — Sigorta Yenileme",
        subtitle_en="",
        section_headings_tr=["Yenileme Kapsamı", "Yürürlük"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="[[project_name]] — Sigorta Yenileme Bildirimi",
    ),
    "DOC-ANK-OPS-010": DocumentSpec(
        doc_id="DOC-ANK-OPS-010",
        family="report",
        subtitle_tr="",
        subtitle_en="Karatepe RES — Availability Guarantee Compliance Report",
        section_headings_tr=[],
        section_headings_en=["1. Guarantee Terms", "2. Compliance Assessment"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-OPS-011": DocumentSpec(
        doc_id="DOC-ANK-OPS-011",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Spare Parts Supply Agreement",
        section_headings_tr=[],
        section_headings_en=["1. Scope of Supply", "2. Term and Termination"],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-OPS-012": DocumentSpec(
        doc_id="DOC-ANK-OPS-012",
        family="report",
        subtitle_tr="Karatepe RES — Yıllık Bakım Planı",
        subtitle_en="",
        section_headings_tr=["Planlama Kapsamı", "Takvim"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
}
