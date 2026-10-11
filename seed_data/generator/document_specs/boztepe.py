"""Boztepe RES — Finans belge spec'leri (İş Emri 2026-10-11 Adım 4, Boztepe PF-2)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    "DOC-BOZ-FIN-001": DocumentSpec(
        doc_id="DOC-BOZ-FIN-001",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Boztepe RES Wind Power Project — Term Loan Facility (2024-BZ)",
        section_headings_tr=[],
        section_headings_en=[
            "1. Recitals",
            "2. The Facility",
            "3. Repayment",
            "4. Financial Covenants",
            "5. Governing Law",
        ],
        prose_guidance_en=(
            "Section 1 (Recitals): the plant reached commercial operation on "
            "[[cod_actual]], BEFORE this Facility existed. The 2024-BZ facility "
            "([[total_debt]]), signed on [[signed_date]], was raised AFTER completion "
            "and is NOT a construction loan — do not describe its purpose, origin, or "
            "how/why/by whom it was initiated; no application, request, or negotiation "
            "language. Do not mention any construction-period condition precedent "
            "(EPC, environmental approval, equity contribution, construction "
            "insurance) — this facility agreement has none of these. Do not state any "
            "capex, equity, or sponsor-contribution figure — none is available; do not "
            "invent one. Do not state any phase-specific MW or turbine count. "
            "Section 2 (The Facility): state the interest rate using "
            "[[effective_rate_pct_en]]. You may optionally mention the DSRA "
            "([[dsra_balance]]) as a fixed amount equal to six periods of debt "
            "service. Section 3 (Repayment): state the repayment structure using the "
            "token [[repayment_profile_en]] — do not also restate the dates or "
            "amounts it already contains in your own words elsewhere in this "
            "document. Section 4 (Financial Covenants): state the covenant using "
            "[[dscr_covenant]] as a MINIMUM REQUIREMENT ONLY — do not state or imply "
            "any historical test result, pass/fail outcome, or test date; no DSCR "
            "test history exists for this facility and none may be invented. "
            "Section 5 (Governing Law): a standard governing-law clause, no new "
            "facts. Never invent a specific substantive provision not backed by a "
            "token."
        ),
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Borrower) — Authorized Signatory",
            "For and on behalf of [[counterparty]] (Lender) — Authorized Signatory",
        ],
    ),
    "DOC-BOZ-FIN-002": DocumentSpec(
        doc_id="DOC-BOZ-FIN-002",
        family="letter",
        subtitle_tr="Boztepe RES — Aylık Faiz Bildirimi",
        subtitle_en="",
        section_headings_tr=["Faiz Tutarı", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları", "Onaylayan: Yetkili İmza"],
        subject_label_tr="Aylık Faiz Bildirimi — [[project_name]]",
    ),
    "DOC-BOZ-FIN-003": DocumentSpec(
        doc_id="DOC-BOZ-FIN-003",
        family="letter",
        subtitle_tr="Boztepe RES — DSRA Hesap Ekstresi",
        subtitle_en="",
        section_headings_tr=["Hesap Bakiyesi", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları"],
        subject_label_tr="DSRA Hesap Ekstresi — [[project_name]]",
    ),
    # İş Emri 2026-10-11-B (Hukuk partisi, T-12.3) — imar planı değişikliği iptali davası.
    "DOC-BOZ-LEG-001": DocumentSpec(
        doc_id="DOC-BOZ-LEG-001",
        family="letter",
        subtitle_tr="İmar Planı Değişikliği İptali — Dava Dilekçesi",
        subtitle_en="",
        section_headings_tr=["Dava Konusu", "Talep"],
        section_headings_en=[],
        subject_label_tr="İmar Planı İptali — [[case_number]]",
        signature_roles_tr=["Davacı Vekili"],
        prose_guidance_tr=(
            "Bu belge [[court]]'na hitaben yazılmış bir dava dilekçesidir. Davacı "
            "[[plaintiff]], davalı [[defendant]]. Dava konusu [[legal_subject]]. "
            "Dava [[filed_date]] tarihinde açılmıştır. Resmi bir idare hukuku "
            "dilekçesi üslubu kullan; davanın sonucu hakkında yorum yapma."
        ),
    ),
    "DOC-BOZ-LEG-002": DocumentSpec(
        doc_id="DOC-BOZ-LEG-002",
        family="letter",
        subtitle_tr="İmar Planı Değişikliği İptali — Belediye Savunması",
        subtitle_en="",
        section_headings_tr=["Savunma Gerekçesi", "Sonuç ve İstem"],
        section_headings_en=[],
        subject_label_tr="İmar Planı İptali — [[case_number]]",
        signature_roles_tr=["Davalı Vekili"],
        prose_guidance_tr=(
            "Bu belge [[court]]'na hitaben [[defendant]] tarafından sunulan bir "
            "savunma dilekçesidir. Dava konusu [[legal_subject]]. Savunma "
            "[[defense_date]] tarihinde sunulmuştur. İmar planının planlama "
            "esaslarına ve şehircilik ilkelerine uygun olduğu savunulur. Davanın "
            "sonucu hakkında yorum yapma."
        ),
    ),
    # İçerik notu (token değil, guidance ile): YD reddinin gerekçesi — plan yürürlükte,
    # mevcut santral işletmesini/kredi servisini etkilemiyor, çevresinde ileride kısıt
    # riski doğuruyor (NACI_CEVAP §1).
    "DOC-BOZ-LEG-003": DocumentSpec(
        doc_id="DOC-BOZ-LEG-003",
        family="report",
        subtitle_tr="İmar Planı Değişikliği İptali — Yürütmeyi Durdurma Talebinin Reddi",
        subtitle_en="",
        section_headings_tr=["Karar Gerekçesi", "Sonraki Süreç"],
        section_headings_en=[],
        signature_roles_tr=["Mahkeme Kalemi"],
        prose_guidance_tr=(
            "Bu belge [[court]]'nun [[case_number]] sayılı dosyasında "
            "[[stay_request_rejected_date]] tarihinde verdiği yürütmeyi durdurma "
            "(YD) talebinin reddi kararının özetidir. Gerekçe: imar planı "
            "yürürlükte kalmaya devam etmektedir; mevcut santralin işletmesini ve "
            "kredi servisini şu an için etkilememektedir; ancak sahanın çevresinde "
            "ileride bir kısıt riski doğurabileceği not edilmiştir — bu olguyu "
            "aktar (token değil, doğrudan anlat). Dosyanın bir sonraki duruşması "
            "[[next_hearing]] tarihindedir. Nötr, resmi bir üslup kullan."
        ),
    ),
    "DOC-BOZ-LEG-004": DocumentSpec(
        doc_id="DOC-BOZ-LEG-004",
        family="report",
        subtitle_tr="İmar Planı Değişikliği İptali — Bilirkişi Keşif Tutanağı",
        subtitle_en="",
        section_headings_tr=["Keşif Kaydı", "Sonraki Süreç"],
        section_headings_en=[],
        signature_roles_tr=["Bilirkişi Heyeti"],
        prose_guidance_tr=(
            "Bu belge [[court]]'nun [[case_number]] sayılı dosyasında "
            "[[expert_site_visit_date]] tarihinde yapılan bilirkişi keşfinin "
            "tutanağıdır. Keşif konusu [[legal_subject]]. Bilirkişi raporu henüz "
            "hazırlanmamıştır, beklenmektedir — bu olguyu aktar (token değil). "
            "Dosyanın bir sonraki duruşması [[next_hearing]] tarihindedir. Teknik/"
            "saha tespiti diliyle, nötr bir üslup kullan."
        ),
    ),
}
