"""Karatepe RES — Finans belge spec'leri (Phase 3.1 + 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec, ExtraTable

SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-FIN-001": DocumentSpec(
        doc_id="DOC-ANK-FIN-001",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Term Loan Facility (Draft)",
        section_headings_tr=[],
        section_headings_en=[
            "1. Definitions and Interpretation",
            "2. The Facility",
            "3. Conditions Precedent",
            "4. Status of this Draft",
        ],
        has_revision_history=True,
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Borrower) — Draft, not yet executed",
            "For and on behalf of [[counterparty]] (Lender) — Draft, not yet executed",
        ],
    ),
    "DOC-ANK-FIN-002": DocumentSpec(
        doc_id="DOC-ANK-FIN-002",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Term Loan Facility (V01)",
        section_headings_tr=[],
        section_headings_en=[
            "1. Definitions and Interpretation",
            "2. The Facility",
            "3. Status of this Draft",
        ],
        has_revision_history=True,
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-003": DocumentSpec(
        doc_id="DOC-ANK-FIN-003",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Term Loan Facility (V02)",
        section_headings_tr=[],
        section_headings_en=[
            "1. Definitions and Interpretation",
            "2. The Facility",
            "3. Status of this Draft",
        ],
        has_revision_history=True,
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-004": DocumentSpec(
        doc_id="DOC-ANK-FIN-004",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Term Loan Facility",
        section_headings_tr=[],
        section_headings_en=[
            "1. Definitions and Interpretation",
            "2. The Facility",
            "3. Conditions Precedent",
            "4. Repayment and Prepayment",
            "5. Financial Covenants",
            "6. Representations and Warranties",
            "7. Governing Law",
        ],
        has_revision_history=True,
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Borrower) — Authorized Signatory",
            "For and on behalf of [[counterparty]] (Lender) — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-005": DocumentSpec(
        doc_id="DOC-ANK-FIN-005",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Amendment No. 1 to the Karatepe RES Facility Agreement",
        section_headings_tr=[],
        # Adım 5: bu belgenin prose içeriği DOC-ANK-FIN-006 ile değiştirildi (bkz. o dosyadaki not).
        section_headings_en=[
            "1. Background",
            "2. Amendments to the Original Agreement",
            "3. Continuing Effect",
            "4. Governing Law",
        ],
        has_revision_history=True,
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Borrower) — Authorized Signatory",
            "For and on behalf of [[counterparty]] (Lender) — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-006": DocumentSpec(
        doc_id="DOC-ANK-FIN-006",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Amendment No. 2 to the Karatepe RES Facility Agreement",
        section_headings_tr=[],
        # Adım 5: bu belgenin prose içeriği DOC-ANK-FIN-005 ile değiştirildi (bkz. o dosyadaki not).
        section_headings_en=[
            "1. Background",
            "2. Amendments to the Original Agreement",
            "3. Continuing Effect",
            "4. Representations",
            "5. Governing Law",
        ],
        has_revision_history=True,
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Borrower) — Authorized Signatory",
            "For and on behalf of [[counterparty]] (Lender) — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-007": DocumentSpec(
        doc_id="DOC-ANK-FIN-007",
        family="report",
        subtitle_tr="",
        subtitle_en="Karatepe RES — Quarterly Covenant Compliance Report",
        section_headings_tr=[],
        section_headings_en=[
            "1. Purpose and Scope",
            "2. Compliance Summary",
            "3. Outstanding Debt Position",
        ],
        extra_table=ExtraTable(
            heading_tr="", heading_en="4. Covenant Test History", kind="covenant_tests"
        ),
        signature_roles_en=["Prepared by: Finance Officer", "Reviewed by: Lender's Agent"],
    ),
    "DOC-ANK-FIN-010": DocumentSpec(
        doc_id="DOC-ANK-FIN-010",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Common Terms Agreement",
        section_headings_tr=[],
        section_headings_en=["1. Common Definitions", "2. Relationship Between Finance Documents"],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-011": DocumentSpec(
        doc_id="DOC-ANK-FIN-011",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Security Agreement (Share Pledge)",
        section_headings_tr=[],
        section_headings_en=["1. Pledge of Shares", "2. Governing Law"],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-012": DocumentSpec(
        doc_id="DOC-ANK-FIN-012",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Account Pledge Agreement",
        section_headings_tr=[],
        section_headings_en=["1. Pledge of Project Accounts", "2. Governing Law"],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-013": DocumentSpec(
        doc_id="DOC-ANK-FIN-013",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Insurance Assignment Agreement",
        section_headings_tr=[],
        section_headings_en=["1. Assignment of Insurance Proceeds", "2. Governing Law"],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] — Authorized Signatory",
            "For and on behalf of [[counterparty]] — Authorized Signatory",
        ],
    ),
    "DOC-ANK-FIN-014": DocumentSpec(
        doc_id="DOC-ANK-FIN-014",
        family="letter",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Facility Drawdown",
        section_headings_tr=[],
        section_headings_en=["Drawdown Request", "Payment Instructions"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Approved by: Authorized Representative",
        ],
        subject_label_tr="Drawdown Notice — Tranche 1 — [[project_name]]",
        reference_label_tr="Ref.",
    ),
    "DOC-ANK-FIN-015": DocumentSpec(
        doc_id="DOC-ANK-FIN-015",
        family="letter",
        subtitle_tr="",
        subtitle_en="Karatepe RES Wind Power Project — Covenant Waiver",
        section_headings_tr=[],
        section_headings_en=["Background", "Waiver"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Approved by: Authorized Representative",
        ],
        subject_label_tr="Waiver Letter — Q4 2024 Covenant Test — [[project_name]]",
        reference_label_tr="Ref.",
    ),
    "DOC-ANK-FIN-016": DocumentSpec(
        doc_id="DOC-ANK-FIN-016",
        family="report",
        subtitle_tr="",
        subtitle_en="Karatepe RES — Quarterly Covenant Compliance Report (Q4 2024)",
        section_headings_tr=[],
        section_headings_en=["1. Purpose and Scope", "2. Compliance Summary"],
        signature_roles_en=[
            "Prepared by: Responsible Department",
            "Reviewed by: Department Manager",
        ],
    ),
    # Adım 5 İş 4b (10.10.2026): kodla (0 LLM) — prose hand-authored, generate_prose.py
    # bu ikisine hiç dokunmaz (prose/*.yaml'daki hand_edited notu).
    "DOC-ANK-FIN-017": DocumentSpec(
        doc_id="DOC-ANK-FIN-017",
        family="letter",
        subtitle_tr="Karatepe RES Wind Power Project — Faiz Oranı Bildirimi",
        subtitle_en="",
        section_headings_tr=["Faiz Oranı Belirleme", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları", "Onaylayan: Yetkili İmza"],
        subject_label_tr="Faiz Belirleme Bildirimi — [[project_name]]",
        reference_label_tr="Sayı",
    ),
    "DOC-ANK-FIN-018": DocumentSpec(
        doc_id="DOC-ANK-FIN-018",
        family="letter",
        subtitle_tr="Karatepe RES Wind Power Project — Teminat Mektubu Yenileme Bildirimi",
        subtitle_en="",
        section_headings_tr=["Teminat Mektubu", "Yenileme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları", "Onaylayan: Yetkili İmza"],
        subject_label_tr="Teminat Mektubu Yenileme Bildirimi — [[project_name]]",
        reference_label_tr="Sayı",
    ),
}
