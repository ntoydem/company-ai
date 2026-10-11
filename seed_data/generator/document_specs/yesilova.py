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
        # Düzeltme D (11.10.2026, Naci onaylı): equity cümlesi bu round'da YAZDIRILMIYOR
        # (T-13.1 — Tansu'nun cevabı bekleniyor, "özkaynakla inşa" ile "equity+2023-YS=capex"
        # aritmetiği arasındaki çelişki netleşmeden) — `prose_suppress_facts` ile equity
        # token'ı LLM'e hiç önerilmiyor. T-13.1 cevaplanınca bu alan kaldırılacak.
        section_headings_en=[
            "1. Recitals",
            "2. The Facility",
            "3. Repayment",
            "4. Financial Covenants",
            "5. Governing Law",
        ],
        prose_guidance_en=(
            "Section 1 (Recitals): state the project's total capex figure using "
            "[[capex]], and state that the plant was constructed and brought into "
            "operation BEFORE this Facility existed (past tense for construction and "
            "operation). Do not use the words 'entirely', 'solely', 'only', or the "
            "phrase 'no third-party debt' anywhere. Do not mention equity or any "
            "sponsor capital contribution at all in this generation. Do not describe "
            "how, why, or by whom this financing was initiated — no application, "
            "request, or negotiation language; state only that the Facility is a "
            "subsequent, partial term loan. Section 2 (The Facility): never mention "
            "capex here. Never invent a specific substantive provision not backed by "
            "a token."
        ),
        prose_suppress_facts=frozenset({"equity"}),
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
    ),
}
