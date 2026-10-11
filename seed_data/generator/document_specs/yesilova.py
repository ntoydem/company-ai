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
        # Düzeltme (11.10.2026, Naci): başlık 1 "Recitals" oldu — capex/equity'nin yalnız
        # arka plan cümlesinde (kredinin sonradan gelen kısmi finansman olduğu, inşaatı
        # finanse eden ana kaynağın özkaynak olduğu) geçmesini, "2. The Facility"nin
        # kredinin capex'i finanse ettiği gibi yanlış bir ilişki kurmasını önlemek için.
        # 1. deneme capex/equity'yi yine 2. bölüme kaydırmıştı (yanlış bölüm + "özkaynak
        # katkısı harcamaların finansmanı amacıyla" ilişkisi). Başlıklar 11.10.2026'da
        # güçlendirilip tek yeniden deneme hakkı kullanıldı, ancak Gemini ~10 dk boyunca
        # (3 ayrı çağrı denemesi) sürekli 429 döndürdüğü için üretim TAMAMLANAMADI — bu
        # bir içerik reddi değil, altyapı/kota sorunu; prose elle düzeltilmedi, başlıklar
        # mevcut (ilk denemeden kalan) prose ile eşleşmesi için eski haline döndürüldü.
        # Açık kalan iş: docs/reports/ADIM5_PF1_URETIM_RAPORU.md.
        section_headings_en=[
            "1. Recitals and Definitions",
            "2. The Facility (Supplementary Financing)",
            "3. Repayment",
            "4. Financial Covenants",
            "5. Governing Law",
        ],
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
