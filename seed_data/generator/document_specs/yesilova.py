"""Yeşilova RES — Finans belge spec'leri (Adım 5 İş 4b, 10.10.2026)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec, ExtraTable

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
    # Adım 5 PF-1 LLM üretim planı (11.10.2026) — LLM prose (gerçek Gemini çağrısı).
    "DOC-YSV-FIN-009": DocumentSpec(
        doc_id="DOC-YSV-FIN-009",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Yeşilova RES Wind Power Project — Term Loan Facility (2023-YS)",
        section_headings_tr=[],
        # Düzeltme B (11.10.2026, Naci onaylı): başlıklar artık NÖTR — talimat
        # `prose_guidance_en`'e taşındı (DocumentSpec'in yeni alanı), asla render edilmez.
        # Önceki iki deneme (Gemini: 429 kota fırtınası; Claude: capex/equity "2. The
        # Facility"ye sızdı, başlığın kendisine talimat gömülünce de 82 karaktere kadar
        # çıkan parantez PDF'e basıldı) bu ayrımın gerekliliğini gösterdi.
        # Düzeltme (11.10.2026, Naci onaylı — T-13.1=A cevaplandı, NACI_CEVAP_2026-10-11.md
        # §2): equity GERİ EKLENDİ, kurgu netleşti — sponsor fonuyla inşa edildi, 2023-YS
        # sonradan alınmış KISMİ kredi (inşaat kredisi değil), amacı sponsor fonunun
        # (ortak cari hesabı) geri ödenmesi, sermaye azaltımı YAPILMADI.
        section_headings_en=[
            "1. Recitals",
            "2. The Facility",
            "3. Repayment",
            "4. Financial Covenants",
            "5. Governing Law",
        ],
        prose_guidance_en=(
            "Section 1 (Recitals): the plant was constructed and brought into "
            "operation BEFORE this Facility existed, funded by sponsor equity — state "
            "the total capex using [[capex]] and the net sponsor contribution using "
            "[[equity]]. The 2023-YS facility ([[total_debt]]) was raised AFTER "
            "completion and is NOT a construction loan — its purpose was to repay "
            "part of the sponsor's own current-account funding; no capital reduction "
            "took place. Do not use the words 'entirely', 'solely', 'only', or the "
            "phrase 'no third-party debt'. Do not describe how, why, or by whom this "
            "financing was initiated — no application, request, or negotiation "
            "language. Do not mention any construction-period condition precedent "
            "(EPC, environmental approval, equity contribution, construction "
            "insurance) — the facility agreement has none of these. Do not state any "
            "phase-specific MW or turbine count. Section 2 (The Facility): never "
            "mention capex or equity here. You may optionally mention the DSRA "
            "([[dsra_balance]]) as a fixed amount equal to six periods of debt "
            "service. Never invent a specific substantive provision not backed by a "
            "token."
        ),
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Borrower) — Authorized Signatory",
            "For and on behalf of [[counterparty]] (Lender) — Authorized Signatory",
        ],
    ),
    "DOC-YSV-FIN-010": DocumentSpec(
        doc_id="DOC-YSV-FIN-010",
        family="report",
        subtitle_tr="",
        subtitle_en="Yeşilova RES — Annex F Compliance Report (Reporting Year 2025)",
        section_headings_tr=[],
        section_headings_en=["1. Purpose and Scope", "2. Compliance Summary"],
        extra_table=ExtraTable(
            heading_tr="",
            heading_en="3. Covenant Test History",
            kind="covenant_tests",
            ledger_key="yesilova_res",
        ),
        signature_roles_en=["Prepared by: Finance Officer", "Reviewed by: Lender's Agent"],
        # Düzeltme (11.10.2026, Naci onaylı): belge `status: draft` (henüz gönderilmedi,
        # yesilova_res.yaml:337 notu) ama önceki üretim "Released under version
        # [[version_label]]" ve "disclosures have been delivered to [[counterparty]]"
        # yazmıştı — taslak bir belgenin kendi gönderildiğini söylemesi çelişki.
        prose_guidance_en=(
            "This report is a DRAFT — it has not yet been sent, delivered, released, or "
            "disclosed to anyone. Never use the words 'delivered', 'released', or "
            "'disclosed', and never write the phrase 'version 2025' as a narrative "
            "statement (the version/status are already shown in the header). The "
            "reporting period is the 2025 year only ([[annex_f_reporting_year]]/[[dscr]] "
            "both refer to 2025) — do not mention any other instalment, payment, or "
            "event dated in 2026. Never invent a specific substantive provision not "
            "backed by a token. Write all numbers in English format (comma thousands "
            "separator). In the compliance summary, state by its exact name using the "
            "token [[missing_guarantee_letter_name]] that this document is still "
            "outstanding/not yet provided — do not describe its amount, bank, or any "
            "other detail, only that it has not been submitted."
        ),
    ),
}
