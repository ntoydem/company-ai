"""Structural plan for the 15 Phase 3.1 documents (docs/plans/PHASE_3_1_PLAN.md §1.2/§2).

Everything here is Python-authored structure (section headings, table choices, signature
roles) — never a fact value. `generate_prose.py` asks the LLM to fill each heading with
placeholder-only paragraphs; `generate_documents.py` appends Python-built tables (no LLM
involved for numbers) and renders the whole thing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Family = Literal["agreement", "letter", "report"]


@dataclass(frozen=True)
class ExtraTable:
    heading_tr: str
    heading_en: str
    kind: Literal["covenant_tests", "monthly_production", "pending_steps"]


@dataclass(frozen=True)
class DocumentSpec:
    doc_id: str
    family: Family
    subtitle_tr: str
    subtitle_en: str
    section_headings_tr: list[str]
    section_headings_en: list[str]
    has_revision_history: bool = False
    extra_table: ExtraTable | None = None
    signature_roles_tr: list[str] = field(default_factory=list)
    signature_roles_en: list[str] = field(default_factory=list)
    reference_label_tr: str = "Sayı"
    subject_label_tr: str = "Konu"


SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-DEV-001": DocumentSpec(
        doc_id="DOC-ANK-DEV-001",
        family="letter",
        subtitle_tr="Ankara RES Rüzgar Enerjisi Üretim Tesisi",
        subtitle_en="",
        section_headings_tr=["Lisans Kapsamı", "Kapasite ve Teknik Bilgiler", "Yükümlülükler"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Üretim Lisansı — [[project_name]]",
    ),
    "DOC-ANK-DEV-002": DocumentSpec(
        doc_id="DOC-ANK-DEV-002",
        family="letter",
        subtitle_tr="Ankara RES Üretim Lisansı Tadili",
        subtitle_en="",
        section_headings_tr=["Tadil Gerekçesi", "Güncellenen Kapasite Bilgisi", "Yürürlük"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Üretim Lisansı Tadili — [[project_name]]",
    ),
    "DOC-ANK-FIN-001": DocumentSpec(
        doc_id="DOC-ANK-FIN-001",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Ankara RES Wind Power Project — Term Loan Facility (Draft)",
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
    "DOC-ANK-FIN-004": DocumentSpec(
        doc_id="DOC-ANK-FIN-004",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Ankara RES Wind Power Project — Term Loan Facility",
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
        subtitle_en="Amendment No. 1 to the Ankara RES Facility Agreement",
        section_headings_tr=[],
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
    "DOC-ANK-FIN-006": DocumentSpec(
        doc_id="DOC-ANK-FIN-006",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Amendment No. 2 to the Ankara RES Facility Agreement",
        section_headings_tr=[],
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
    "DOC-ANK-FIN-007": DocumentSpec(
        doc_id="DOC-ANK-FIN-007",
        family="report",
        subtitle_tr="",
        subtitle_en="Ankara RES — Quarterly Covenant Compliance Report",
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
    "DOC-ANK-OPS-001": DocumentSpec(
        doc_id="DOC-ANK-OPS-001",
        family="report",
        subtitle_tr="Ankara RES — Aylık Üretim Raporu",
        subtitle_en="",
        section_headings_tr=["Genel Değerlendirme", "Performans Özeti"],
        section_headings_en=[],
        extra_table=ExtraTable(
            heading_tr="Aylık Üretim Verileri (son 6 ay)", heading_en="", kind="monthly_production"
        ),
        signature_roles_tr=["Hazırlayan: Saha Operasyon Mühendisi", "Kontrol Eden: İşletme Müdürü"],
    ),
    "DOC-IZM-DEV-001": DocumentSpec(
        doc_id="DOC-IZM-DEV-001",
        family="letter",
        subtitle_tr="İzmir RES Rüzgar Enerjisi Projesi",
        subtitle_en="",
        section_headings_tr=["Önlisans Kapsamı", "Süreç ve Yükümlülükler"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Önlisans — [[project_name]]",
    ),
    "DOC-IZM-DEV-002": DocumentSpec(
        doc_id="DOC-IZM-DEV-002",
        family="report",
        subtitle_tr="İzmir RES — Arazi Edinim Durum Raporu",
        subtitle_en="",
        section_headings_tr=["Arazi Edinim Süreci", "Güncel Durum"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Arazi ve İzinler Uzmanı", "Kontrol Eden: Proje Müdürü"],
    ),
    "DOC-IZM-DEV-003": DocumentSpec(
        doc_id="DOC-IZM-DEV-003",
        family="letter",
        subtitle_tr="İzmir RES ÇED Süreci",
        subtitle_en="",
        section_headings_tr=["Süreç Durumu", "Bekleyen Adımlar"],
        section_headings_en=[],
        extra_table=ExtraTable(
            heading_tr="Bekleyen Kritik Adımlar", heading_en="", kind="pending_steps"
        ),
        signature_roles_tr=["Hazırlayan: Çevre ve İzinler Uzmanı", "Onaylayan: Proje Müdürü"],
        subject_label_tr="ÇED Süreci Durum Bilgisi — [[project_name]]",
    ),
    "DOC-IZM-DEV-004": DocumentSpec(
        doc_id="DOC-IZM-DEV-004",
        family="report",
        subtitle_tr="İzmir RES — Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu",
        subtitle_en="",
        section_headings_tr=[
            "Rüzgar Kaynağı Değerlendirmesi",
            "Ön Fizibilite Sonuçları",
            "Öneriler",
        ],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Teknik Danışman", "Kontrol Eden: Proje Müdürü"],
    ),
    "DOC-CO-ADM-001": DocumentSpec(
        doc_id="DOC-CO-ADM-001",
        family="letter",
        subtitle_tr="Yönetim Kurulu Kararı",
        subtitle_en="",
        section_headings_tr=["Karar Gerekçesi", "Alınan Karar"],
        section_headings_en=[],
        signature_roles_tr=["Yönetim Kurulu Başkanı", "Yönetim Kurulu Üyesi"],
        subject_label_tr="Ankara RES Finansman Onayı",
    ),
}
