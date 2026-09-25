"""Ankara RES — EPC/Construction belge spec'leri (Phase 3.1 + 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-EPC-001": DocumentSpec(
        doc_id="DOC-ANK-EPC-001",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Ankara RES Wind Power Project — EPC Contract",
        section_headings_tr=[],
        section_headings_en=[
            "1. Scope of Works",
            "2. Contract Price and Payment",
            "3. Programme and Milestones",
            "4. Defects Liability and Warranties",
            "5. Governing Law",
        ],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Employer) — Authorized Signatory",
            "For and on behalf of [[counterparty]] (Contractor) — Authorized Signatory",
        ],
    ),
    "DOC-ANK-EPC-002": DocumentSpec(
        doc_id="DOC-ANK-EPC-002",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Provisional Acceptance & Commercial Operation Certificate",
        section_headings_tr=[],
        section_headings_en=[
            "1. Confirmation of Commercial Operation",
            "2. Acceptance Testing Summary",
        ],
        signature_roles_en=[
            "Contractor's Representative",
            "Independent Engineer",
            "Owner's Representative",
        ],
    ),
    "DOC-ANK-EPC-003": DocumentSpec(
        doc_id="DOC-ANK-EPC-003",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — EPC Change Order 01 (COD Deferral)",
        section_headings_tr=[],
        section_headings_en=["1. Background", "2. Revised Schedule"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-EPC-004": DocumentSpec(
        doc_id="DOC-ANK-EPC-004",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Mechanical Completion Certificate",
        section_headings_tr=[],
        section_headings_en=["1. Scope of Works Completed", "2. Confirmation"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-EPC-005": DocumentSpec(
        doc_id="DOC-ANK-EPC-005",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Independent Engineer's Completion Report",
        section_headings_tr=[],
        section_headings_en=["1. Purpose and Scope", "2. Findings"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-EPC-006": DocumentSpec(
        doc_id="DOC-ANK-EPC-006",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Punch List Closure Confirmation",
        section_headings_tr=[],
        section_headings_en=["1. Outstanding Items Reviewed", "2. Confirmation"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-EPC-007": DocumentSpec(
        doc_id="DOC-ANK-EPC-007",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Construction All Risks Insurance Policy Summary",
        section_headings_tr=[],
        section_headings_en=["1. Coverage Summary", "2. Policy Period"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-EPC-008": DocumentSpec(
        doc_id="DOC-ANK-EPC-008",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Performance Test Results Report",
        section_headings_tr=[],
        section_headings_en=["1. Test Methodology", "2. Results"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-EPC-009": DocumentSpec(
        doc_id="DOC-ANK-EPC-009",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Warranty & Defects Liability Certificate",
        section_headings_tr=[],
        section_headings_en=["1. Defects Liability Period", "2. Confirmation"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    "DOC-ANK-EPC-010": DocumentSpec(
        doc_id="DOC-ANK-EPC-010",
        family="letter",
        subtitle_tr="Ankara RES Şebeke Bağlantısı",
        subtitle_en="",
        section_headings_tr=["Bağlantı Kapsamı", "Onay"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="Şebeke Bağlantı Tamamlama Belgesi — [[project_name]]",
    ),
}
