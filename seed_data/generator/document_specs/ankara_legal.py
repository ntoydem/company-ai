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
    # İş Emri 2026-10-11-B (Hukuk partisi, T-12.1) — kamulaştırma/irtifak bedeli davası.
    "DOC-ANK-LEG-004": DocumentSpec(
        doc_id="DOC-ANK-LEG-004",
        family="letter",
        subtitle_tr="Kamulaştırma ve İrtifak Bedeli Tespiti — Dava Dilekçesi",
        subtitle_en="",
        section_headings_tr=["Dava Konusu", "Talep"],
        section_headings_en=[],
        subject_label_tr="İrtifak Bedeli Tespiti — [[case_number]]",
        signature_roles_tr=["Davacı Vekili"],
        prose_guidance_tr=(
            "Bu belge [[court]]'na hitaben yazılmış bir dava dilekçesidir. Davacı "
            "[[plaintiff]], davalı [[defendant]]. Dava konusu [[legal_subject]]. "
            "İdarenin belirlediği bedel [[amount_offered]], davacının talebi "
            "[[amount_claimed]]. Dava [[filed_date]] tarihinde açılmıştır. Resmi, "
            "hukuki bir dilekçe üslubu kullan. Davanın sonucu veya güçlü/zayıf "
            "yönleri hakkında yorum yapma — yalnız talebi ve gerekçesini aktar."
        ),
    ),
    "DOC-ANK-LEG-005": DocumentSpec(
        doc_id="DOC-ANK-LEG-005",
        family="letter",
        subtitle_tr="Kamulaştırma ve İrtifak Bedeli Tespiti — İdare Savunması",
        subtitle_en="",
        section_headings_tr=["Savunma Gerekçesi", "Sonuç ve İstem"],
        section_headings_en=[],
        subject_label_tr="İrtifak Bedeli Tespiti — [[case_number]]",
        signature_roles_tr=["Davalı Vekili"],
        prose_guidance_tr=(
            "Bu belge [[court]]'na hitaben [[defendant]] tarafından sunulan bir "
            "savunma dilekçesidir. Dava konusu [[legal_subject]]. İdarenin "
            "belirlediği bedel [[amount_offered]], davacı [[plaintiff]]'nin talebi "
            "[[amount_claimed]]. Savunma [[defense_date]] tarihinde sunulmuştur. "
            "Resmi bir savunma dilekçesi üslubu kullan; davanın sonucu hakkında "
            "yorum yapma."
        ),
    ),
    "DOC-ANK-LEG-006": DocumentSpec(
        doc_id="DOC-ANK-LEG-006",
        family="report",
        subtitle_tr="Kamulaştırma ve İrtifak Bedeli Tespiti — Bilirkişi Raporu",
        subtitle_en="",
        section_headings_tr=["İnceleme Kapsamı", "Değerlendirme ve Sonuç"],
        section_headings_en=[],
        signature_roles_tr=["Bilirkişi Heyeti"],
        prose_guidance_tr=(
            "Bu belge [[court]]'nun [[case_number]] sayılı dosyasında görevli "
            "bilirkişi heyetinin raporudur. İnceleme konusu [[legal_subject]]. "
            "Heyetin bulduğu değer [[amount_expert]]. Rapor [[expert_report_date]] "
            "tarihinde sunulmuştur. Teknik/değerleme dilinde, nötr bir üslup kullan; "
            "hangi tarafın haklı olduğu hakkında yorum yapma."
        ),
    ),
    # Kronoloji (prose'a token yerine guidance ile taşınan, tarih/tutar/isim olmayan tek
    # olgu): 10.01.2026 duruşmasında idarenin ek bilirkişi talebi reddedildi (NACI_CEVAP §1).
    "DOC-ANK-LEG-007": DocumentSpec(
        doc_id="DOC-ANK-LEG-007",
        family="report",
        subtitle_tr="Kamulaştırma ve İrtifak Bedeli Tespiti — Duruşma Tutanağı",
        subtitle_en="",
        section_headings_tr=["Duruşma Kaydı", "Alınan Kararlar"],
        section_headings_en=[],
        signature_roles_tr=["Zabıt Kâtibi"],
        prose_guidance_tr=(
            "Bu belge [[court]]'nun [[case_number]] sayılı dosyasında "
            "[[hearing_record_date]] tarihinde yapılan duruşmanın tutanağıdır. "
            "Duruşmada idarenin ek bilirkişi incelemesi talebi reddedilmiştir — bu "
            "olguyu aktar (bu bir token değil, doğrudan anlat). Dosyanın bir sonraki "
            "duruşması [[next_hearing]] tarihine bırakılmıştır (nihai beyanlar için). "
            "Resmi bir duruşma tutanağı üslubu kullan, nötr ve kısa."
        ),
    ),
    # ÖNCEDEN VERİLMİŞ KARAR 3 (.eml desteği yok): e-posta çıktısı düzeninde PDF, mevcut
    # `letter` ailesiyle — altyapı değişikliği YOK. Kaynak dosya: Kamulaştırma_Itiraz_
    # Sureci.eml (15.09.2026).
    "DOC-ANK-LEG-008": DocumentSpec(
        doc_id="DOC-ANK-LEG-008",
        family="letter",
        subtitle_tr="Mahkeme Kalemi E-postası — Dava Süreci Güncellemesi",
        subtitle_en="",
        section_headings_tr=["E-posta İçeriği"],
        section_headings_en=[],
        subject_label_tr="[[case_number]] Sayılı Dosya — Süreç Güncellemesi",
        signature_roles_tr=["Gönderen: [[court]] Yazı İşleri Müdürlüğü"],
        prose_guidance_tr=(
            "Bu belge bir e-postanın yazıcı çıktısıdır — gövde bir e-posta gibi "
            "yazılmalı (kısa, doğrudan, 'Sayın ilgili,' ile başlayıp bir imza "
            "satırıyla bitmeli; resmi bir dilekçe üslubu DEĞİL). E-posta "
            "[[court_clerk_email_date]] tarihinde [[court]] yazı işleri "
            "müdürlüğünden [[case_number]] sayılı dosya hakkında gönderilmiştir. "
            "İçerik yalnız bir sonraki duruşma tarihinin ([[next_hearing]]) "
            "taraflara bildirilmesinden ibarettir — başka hiçbir ayrıntı icat etme."
        ),
    ),
    # ÖNCEDEN VERİLMİŞ KARAR 3 (aynı). Kaynak dosya: Dava_Dosyasi_Guncelleme.eml
    # (10.09.2026).
    "DOC-ANK-LEG-009": DocumentSpec(
        doc_id="DOC-ANK-LEG-009",
        family="letter",
        subtitle_tr="Karşı Taraf Vekili E-postası — Dava Dosyası Güncellemesi",
        subtitle_en="",
        section_headings_tr=["E-posta İçeriği"],
        section_headings_en=[],
        subject_label_tr="[[case_number]] Sayılı Dosya — Dava Güncellemesi",
        signature_roles_tr=["Gönderen: [[defendant]] Vekili"],
        prose_guidance_tr=(
            "Bu belge bir e-postanın yazıcı çıktısıdır — gövde bir e-posta gibi "
            "yazılmalı (kısa, doğrudan; resmi bir dilekçe üslubu DEĞİL). E-posta "
            "[[opposing_counsel_email_date]] tarihinde [[defendant]] vekili "
            "tarafından [[case_number]] sayılı dosya hakkında gönderilmiştir. "
            "Vekili ROL olarak an (özel bir avukat adı İCAT ETME). İçerik genel bir "
            "dosya güncellemesinden ibarettir — somut yeni bir iddia/belge icat etme."
        ),
    ),
}
