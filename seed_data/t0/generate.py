"""Phase 0.2 test fixtures — NOT the Phase 3.1 truth-ledger generator.

Produces three PDFs under seed_data/t0/ used by the backend's and ocr-worker's test
suites: a digital "Facility Agreement" (DSCR covenant 1,25x, tenor 12 yıl), a digital
"Amendment 01" (DSCR covenant 1,20x, tenor 14 yıl), and a scanned/image-only copy of the
Facility Agreement (no text layer) for exercising the OCR path.

All figures are fictional placeholders (DEMO banner on every page); no truth ledger
exists yet (Phase 2.1). Run inside the backend container:

    docker compose run --rm backend python seed_data/t0/generate.py
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

OUT_DIR = Path(__file__).parent
TEMPLATE_DIR = OUT_DIR / "templates"
SCAN_DPI = 200

FACILITY_AGREEMENT_PAGES = [
    {"cover": True},
    {
        "heading": "1. Definitions and Interpretation",
        "paragraphs": [
            'In this Agreement: "Borrower" means ABC Enerji Üretim A.Ş., a company '
            "incorporated under the laws of the Republic of Türkiye, developer and "
            'operator of the Ankara RES wind power project. "Lender" means PQR Bank '
            'A.Ş. "Facility" means the term loan facility made available under this '
            'Agreement. "Financial Year" means each twelve-month period ending 31 '
            "December. Headings are for convenience only and do not affect "
            "interpretation. Words importing the singular include the plural and vice "
            "versa, and references to any party include its successors and permitted "
            "assigns.",
            "This is a fictional demonstration document prepared for software testing "
            "purposes only. All names, amounts, dates and figures are synthetic "
            "placeholders and do not describe any real transaction.",
        ],
    },
    {
        "heading": "2. The Facility",
        "paragraphs": [
            "Subject to the terms of this Agreement, the Lender agrees to make "
            "available to the Borrower a term loan facility in an aggregate principal "
            "amount to be drawn in one or more advances for the purpose of financing "
            "the construction and commissioning of the Ankara RES wind power project "
            "and associated grid connection works.",
            "The tenor of the Facility is 12 (twelve) years from the Effective Date, "
            "inclusive of a construction and ramp-up period, after which the Facility "
            "shall be repaid in full in accordance with the repayment schedule set out "
            "in Schedule 3.",
            "Interest shall accrue on the outstanding principal amount at a floating "
            "rate determined by reference to the applicable reference rate plus a "
            "margin, payable quarterly in arrear on each Payment Date.",
        ],
    },
    {
        "heading": "3. Conditions Precedent",
        "paragraphs": [
            "The obligation of the Lender to make the Facility available is subject to "
            "the Borrower delivering, in form and substance satisfactory to the "
            "Lender, its constitutional documents, all material project permits and "
            "licences, an independent engineer's report, insurance confirmations and "
            "such other documents as are customary for a project of this nature.",
            "No advance shall be made unless the Lender is satisfied, acting "
            "reasonably, that no Default has occurred and is continuing and that the "
            "representations and warranties in Clause 6 remain true in all material "
            "respects.",
        ],
    },
    {
        "heading": "4. Repayment and Prepayment",
        "paragraphs": [
            "The Borrower shall repay the Facility in consecutive quarterly "
            "instalments in accordance with the amortisation profile set out in "
            "Schedule 3, commencing on the first Payment Date following the "
            "commercial operation date of the Project.",
            "The Borrower may voluntarily prepay all or part of the Facility on any "
            "Payment Date, subject to prior written notice and payment of any "
            "applicable breakage costs.",
        ],
    },
    {
        "heading": "5. Financial Covenants",
        "paragraphs": [
            "The Borrower shall ensure that, in respect of each Calculation Period "
            "ending on or after the first Payment Date, the Debt Service Coverage "
            "Ratio (DSCR) for the Project is not less than 1,25x.",
            "The DSCR covenant referred to above shall be tested quarterly by "
            "reference to the Borrower's management accounts and confirmed annually "
            "by reference to audited financial statements. A breach of this covenant "
            "which is not remedied within the applicable cure period shall constitute "
            "an Event of Default under Clause 8.",
            "For the avoidance of doubt, the minimum DSCR covenant level set out in "
            "this Clause 5 is 1,25x and applies for so long as any amount remains "
            "outstanding under the Facility, unless amended in writing by the parties.",
        ],
    },
    {
        "heading": "6. Representations and Warranties",
        "paragraphs": [
            "The Borrower represents and warrants to the Lender, on the date of this "
            "Agreement and on each date an advance is requested, that it is duly "
            "incorporated and validly existing, that this Agreement constitutes its "
            "legal, valid and binding obligation, and that it holds all material "
            "permits necessary to construct and operate the Project.",
            "The Borrower further represents that no litigation, arbitration or "
            "administrative proceeding is pending or threatened which would be "
            "reasonably likely to have a material adverse effect on its ability to "
            "perform its obligations under this Agreement.",
        ],
    },
    {
        "heading": "7. Governing Law and Signatures",
        "paragraphs": [
            "This Agreement and any non-contractual obligations arising out of or in "
            "connection with it shall be governed by, and construed in accordance "
            "with, the laws of the Republic of Türkiye.",
            "IN WITNESS WHEREOF the parties have executed this Agreement as a deed on "
            "the date first written above.",
            "For and on behalf of ABC Enerji Üretim A.Ş. (Borrower)  —  signature "
            "block (fictional, DEMO document).",
            "For and on behalf of PQR Bank A.Ş. (Lender)  —  signature block "
            "(fictional, DEMO document).",
        ],
    },
]

AMENDMENT_01_PAGES = [
    {"cover": True},
    {
        "heading": "1. Background",
        "paragraphs": [
            'This Amendment Agreement No. 1 (the "Amendment") is supplemental to, and '
            "amends, the Facility Agreement dated as the EXECUTED facility agreement "
            "between ABC Enerji Üretim A.Ş. as Borrower and PQR Bank A.Ş. as Lender in "
            "respect of the financing of the Ankara RES wind power project (the "
            '"Original Agreement").',
            "The parties have agreed to amend certain terms of the Original Agreement "
            "as set out in this Amendment, in particular the financial covenants and "
            "the tenor of the Facility, following a review of the Project's "
            "operating performance.",
            "This is a fictional demonstration document prepared for software testing "
            "purposes only. All names, amounts, dates and figures are synthetic "
            "placeholders and do not describe any real transaction.",
        ],
    },
    {
        "heading": "2. Amendments to the Original Agreement",
        "paragraphs": [
            "With effect from the date of this Amendment, Clause 2 (The Facility) of "
            "the Original Agreement is amended so that the tenor of the Facility is "
            "14 (fourteen) years from the Effective Date, in place of the 12-year "
            "tenor originally agreed.",
            "With effect from the date of this Amendment, Clause 5 (Financial "
            "Covenants) of the Original Agreement is amended so that the minimum "
            "Debt Service Coverage Ratio (DSCR) covenant is 1,20x, in place of the "
            "1,25x minimum DSCR covenant originally agreed, tested quarterly on the "
            "same basis as under the Original Agreement.",
            "For the avoidance of doubt, from the date of this Amendment the "
            "applicable minimum DSCR covenant under the Facility is 1,20x, and the "
            "applicable tenor of the Facility is 14 years.",
        ],
    },
    {
        "heading": "3. Continuing Effect",
        "paragraphs": [
            "Save as expressly amended by this Amendment, the Original Agreement "
            "remains in full force and effect and the parties confirm their "
            "respective obligations under it.",
            "This Amendment and the Original Agreement shall be read and construed as "
            'one document, and references in the Original Agreement to "this '
            'Agreement" shall, from the date of this Amendment, be read as references '
            "to the Original Agreement as amended by this Amendment.",
        ],
    },
    {
        "heading": "4. Representations",
        "paragraphs": [
            "The Borrower confirms that the representations and warranties set out in "
            "Clause 6 of the Original Agreement remain true and accurate in all "
            "material respects as at the date of this Amendment, by reference to the "
            "facts and circumstances then existing.",
        ],
    },
    {
        "heading": "5. Governing Law and Signatures",
        "paragraphs": [
            "This Amendment shall be governed by, and construed in accordance with, "
            "the laws of the Republic of Türkiye.",
            "IN WITNESS WHEREOF the parties have executed this Amendment as a deed on "
            "the date first written above.",
            "For and on behalf of ABC Enerji Üretim A.Ş. (Borrower)  —  signature "
            "block (fictional, DEMO document).",
            "For and on behalf of PQR Bank A.Ş. (Lender)  —  signature block "
            "(fictional, DEMO document).",
        ],
    },
]


def _render_pdf(
    *, title: str, subtitle: str, meta: dict[str, str], pages: list[dict], out_path: Path
) -> None:
    env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)
    template = env.get_template("document.html")
    html = template.render(title=title, subtitle=subtitle, meta=meta, pages=pages)
    HTML(string=html, base_url=str(TEMPLATE_DIR)).write_pdf(str(out_path))
    print(f"yazıldı: {out_path}")


def _make_scanned_copy(source_pdf: Path, out_path: Path) -> None:
    """Rasterize every page of `source_pdf` and rebuild a PDF with no text layer,
    so ocrmypdf has real OCR work to do (ADR-006's `--skip-text` assumes exactly
    this: pages with no existing text layer)."""
    source = pymupdf.open(source_pdf)
    scanned = pymupdf.open()
    for page in source:
        pixmap = page.get_pixmap(dpi=SCAN_DPI)
        # `insert_image(..., pixmap=...)` embeds raw, uncompressed samples (a single A4
        # page at 200 DPI is ~11 MB uncompressed) — JPEG-encode first, like a real
        # scanner's output, to keep the file a realistic size.
        jpeg_bytes = pixmap.tobytes("jpeg", jpg_quality=85)
        image_page = scanned.new_page(width=pixmap.width, height=pixmap.height)
        image_page.insert_image(image_page.rect, stream=jpeg_bytes)
    scanned.save(out_path, deflate=True)
    scanned.close()
    source.close()
    print(f"yazıldı (görüntü/taranmış): {out_path}")


def main() -> None:
    facility_path = OUT_DIR / "facility_agreement.pdf"
    amendment_path = OUT_DIR / "amendment_01.pdf"
    scanned_path = OUT_DIR / "facility_agreement_scanned.pdf"

    _render_pdf(
        title="FACILITY AGREEMENT",
        subtitle="Ankara RES Wind Power Project — Term Loan Facility",
        meta={
            "Status": "EXECUTED",
            "Borrower": "ABC Enerji Üretim A.Ş.",
            "Lender": "PQR Bank A.Ş.",
            "Facility tenor": "12 years",
            "Minimum DSCR covenant": "1,25x",
            "Document date": "01.06.2023",
        },
        pages=FACILITY_AGREEMENT_PAGES,
        out_path=facility_path,
    )
    _render_pdf(
        title="AMENDMENT AGREEMENT NO. 1",
        subtitle="Amendment to the Ankara RES Facility Agreement",
        meta={
            "Status": "EXECUTED",
            "Amends": "Facility Agreement (EXECUTED, 01.06.2023)",
            "Revised facility tenor": "14 years",
            "Revised minimum DSCR covenant": "1,20x",
            "Document date": "15.03.2025",
        },
        pages=AMENDMENT_01_PAGES,
        out_path=amendment_path,
    )
    _make_scanned_copy(facility_path, scanned_path)


if __name__ == "__main__":
    main()
