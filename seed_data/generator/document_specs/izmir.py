"""Kızılova RES — belge spec'leri (Phase 3.1 + 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec, ExtraTable

SPECS: dict[str, DocumentSpec] = {
    "DOC-IZM-DEV-001": DocumentSpec(
        doc_id="DOC-IZM-DEV-001",
        family="letter",
        subtitle_tr="Kızılova RES Rüzgar Enerjisi Projesi",
        subtitle_en="",
        section_headings_tr=["Önlisans Kapsamı", "Süreç ve Yükümlülükler"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Önlisans — [[project_name]]",
    ),
    "DOC-IZM-DEV-002": DocumentSpec(
        doc_id="DOC-IZM-DEV-002",
        family="report",
        subtitle_tr="Kızılova RES — Arazi Edinim Durum Raporu",
        subtitle_en="",
        section_headings_tr=["Arazi Edinim Süreci", "Güncel Durum"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Arazi ve İzinler Uzmanı", "Kontrol Eden: Proje Müdürü"],
    ),
    "DOC-IZM-DEV-003": DocumentSpec(
        doc_id="DOC-IZM-DEV-003",
        family="letter",
        subtitle_tr="Kızılova RES ÇED Süreci",
        subtitle_en="",
        section_headings_tr=["Süreç Durumu", "Bekleyen Adımlar"],
        section_headings_en=[],
        extra_table=ExtraTable(
            heading_tr="Bekleyen Kritik Adımlar",
            heading_en="",
            kind="pending_steps",
            ledger_key="izmir_res",
        ),
        signature_roles_tr=["Hazırlayan: Çevre ve İzinler Uzmanı", "Onaylayan: Proje Müdürü"],
        subject_label_tr="ÇED Süreci Durum Bilgisi — [[project_name]]",
    ),
    "DOC-IZM-DEV-004": DocumentSpec(
        doc_id="DOC-IZM-DEV-004",
        family="report",
        subtitle_tr="Kızılova RES — Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu",
        subtitle_en="",
        section_headings_tr=[
            "Rüzgar Kaynağı Değerlendirmesi",
            "Ön Fizibilite Sonuçları",
            "Öneriler",
        ],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Teknik Danışman", "Kontrol Eden: Proje Müdürü"],
    ),
    "DOC-IZM-DEV-005": DocumentSpec(
        doc_id="DOC-IZM-DEV-005",
        family="letter",
        subtitle_tr="Kızılova RES Şebeke Bağlantısı",
        subtitle_en="",
        section_headings_tr=["Başvuru Kapsamı", "Süreç"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="Bağlantı Görüşü Başvurusu — [[project_name]]",
    ),
    "DOC-IZM-DEV-006": DocumentSpec(
        doc_id="DOC-IZM-DEV-006",
        family="report",
        subtitle_tr="Kızılova RES — Halkın Katılımı Toplantısı",
        subtitle_en="",
        section_headings_tr=["Toplantı Özeti", "Alınan Görüşler"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-IZM-DEV-007": DocumentSpec(
        doc_id="DOC-IZM-DEV-007",
        family="report",
        subtitle_tr="Kızılova RES — Rüzgar Ölçüm Kampanyası Raporu",
        subtitle_en="",
        section_headings_tr=["Ölçüm Kapsamı", "Sonuçlar"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-IZM-DEV-008": DocumentSpec(
        doc_id="DOC-IZM-DEV-008",
        family="letter",
        subtitle_tr="Kızılova RES Askeri Yasak Bölge Görüşü",
        subtitle_en="",
        section_headings_tr=["Talep Kapsamı", "Süreç"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="Askeri Yasak Bölgeler Ön Görüş Talebi — [[project_name]]",
    ),
    "DOC-IZM-LEG-001": DocumentSpec(
        doc_id="DOC-IZM-LEG-001",
        family="report",
        subtitle_tr="Kızılova RES — Arazi Mülkiyeti Hukuki İnceleme Notu",
        subtitle_en="",
        section_headings_tr=["İnceleme Kapsamı", "Değerlendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-IZM-LEG-002": DocumentSpec(
        doc_id="DOC-IZM-LEG-002",
        family="agreement",
        subtitle_tr="Kızılova RES Kira/İrtifak Hakkı Sözleşmesi (Taslak)",
        subtitle_en="",
        section_headings_tr=["1. Hakkın Kapsamı", "2. Yürürlük ve Genel Hükümler"],
        section_headings_en=[],
        # Düzeltme (11.10.2026, Naci onaylı): eski üretim [[counterparty]]'yi SPV'ye
        # düşürüp "... ile ... arasında akdedilmiştir" yazmıştı, HEM belge draft olduğu
        # halde kesinleşmiş dil kullanmıştı. T-13.2 (Tansu, 11.10.2026) 3 malik verdi.
        # İş Emri 2026-10-11 Adım 1: [[parties_list]] SPV'yi DE içerir ("malikler =
        # parties_list" demek SPV'yi de malik gösterirdi) — yeni [[counterparty_list]]
        # (SPV HARİÇ) kullanılıyor; [[counterparty]] hâlâ suppress (3 malikten yalnız
        # birini seçer).
        signature_roles_tr=["İmza: [[spv_name]] Yetkilisi"],
        prose_suppress_facts=frozenset({"counterparty", "parties_list"}),
        prose_guidance_tr=(
            "Bu belge TASLAKTIR, henüz imzalanmamıştır — 'akdedilmiştir', 'bağlayıcı "
            "nitelik kazanacaktır', 'yürürlüğe girmiştir' gibi KESİNLEŞMİŞ/tamamlanmış "
            "ifadeler YASAK; 'taslak', 'imzalanacak', 'imza için hazırlanmıştır' gibi "
            "taslak/ileri-zaman dili kullan. Karşı taraf 3 parsel malikidir — bunlardan "
            "söz ederken SADECE [[counterparty_list]] kullan (yalnız malikleri listeler, "
            "SPV'yi dahil etmez), örn. '[[spv_name]] ile [[counterparty_list]] arasında'. "
            "[[parties_list]] ve [[counterparty]] KULLANMA (ikisi de SPV'yi malik gibi "
            "gösterir veya yalnız birini seçer). Token'la verilmeyen somut bir hüküm "
            "icat etme."
        ),
    ),
    "DOC-IZM-LEG-003": DocumentSpec(
        doc_id="DOC-IZM-LEG-003",
        family="report",
        subtitle_tr="Kızılova RES — Şirket Yapısı Hukuki Görüşü",
        subtitle_en="",
        section_headings_tr=["İnceleme Kapsamı", "Değerlendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    # İş Emri 2026-10-12-F Adım 2: [[pre_licence_date]] zaten facts'te vardı ama yönerge
    # olmadan LLM tarihi dolaylı anıyordu ("15.01.2025 tarihli idari kararlar") — "önlisans
    # tarihi" ifadesiyle AÇIKÇA eşlemiyordu (IZM-DEV-011). Değer metni, sadece bağlama yazılış.
    "DOC-IZM-LEG-004": DocumentSpec(
        doc_id="DOC-IZM-LEG-004",
        family="report",
        subtitle_tr="Kızılova RES — Önlisans Süre Uzatımı Değerlendirmesi",
        subtitle_en="",
        section_headings_tr=["Değerlendirme Kapsamı", "Sonuç"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
        prose_guidance_tr=(
            "Değerlendirme Kapsamı bölümünde önlisans tarihini açıkça belirt: "
            '"önlisans tarihi [[pre_licence_date]]\'dir" gibi bir cümleyle, yalnızca '
            "dolaylı bir idari karar referansı olarak değil."
        ),
    ),
    # İş Emri 2026-10-11-B (Hukuk partisi, T-12.4) — ABC İnşaat'a gönderilen ihtarname.
    "DOC-IZM-LEG-005": DocumentSpec(
        doc_id="DOC-IZM-LEG-005",
        family="letter",
        subtitle_tr="Yüklenici İhtilafı — Noter İhtarnamesi",
        subtitle_en="",
        section_headings_tr=["İhtar Konusu", "Talep ve Sonuç"],
        section_headings_en=[],
        subject_label_tr="[[contract_ref]] — Teslim Gecikmesi İhtarı",
        signature_roles_tr=["İhtarı Gönderen: Hukuk Danışmanlığı"],
        prose_guidance_tr=(
            "Bu belge [[recipient]]'e noter kanalıyla gönderilen bir ihtarnamedir. "
            "Konu: [[legal_subject]]. Paketin sözleşme iş programındaki teslim "
            "tarihi [[original_due_date]] idi, teslim edilmedi. Talep: paketin "
            "[[demanded_date]]'e kadar teslimi. Aksi halde sözleşmedeki gecikme "
            "cezası (günlük sözleşme bedelinin [[penalty_rate_pct]]'i, tavan "
            "[[penalty_cap_pct]]) işletilecek ve hakedişlerden mahsup edilecektir "
            "— ancak ceza hakkının şu an için SAKLI TUTULDUĞUNU, bir TUTAR "
            "TALEP EDİLMEDİĞİNİ açıkça belirt. İhtarname [[notice_sent_date]] "
            "tarihinde gönderilmiştir. Resmi, ihtarname üslubu kullan."
        ),
    ),
    # İş Emri 2026-10-11-B (T-12.4b) — yalnız talep yazısı, sonuç/karar belgesi YOK.
    "DOC-IZM-LEG-006": DocumentSpec(
        doc_id="DOC-IZM-LEG-006",
        family="letter",
        subtitle_tr="Mera Tahsis Değişikliği Talebi",
        subtitle_en="",
        section_headings_tr=["Talep"],
        section_headings_en=[],
        subject_label_tr="Mera Tahsis Değişikliği Talebi",
        signature_roles_tr=["Hazırlayan: İlgili Birim"],
        prose_guidance_tr=(
            "Bu belge [[recipient]]'e hitaben yazılmış bir mera tahsis değişikliği "
            "talep yazısıdır. Talep [[notice_sent_date]] tarihinde gönderilmiştir. "
            "Komisyonun bu talebi görüşeceği bir sonraki toplantı tarihi "
            "[[next_meeting]]'dir. Henüz bir karar/sonuç alınmadığını belirt — "
            "bir sonuç icat etme. Resmi, kurumsal bir talep yazısı üslubu kullan."
        ),
    ),
    "DOC-IZM-ADM-001": DocumentSpec(
        doc_id="DOC-IZM-ADM-001",
        family="letter",
        subtitle_tr="Kızılova RES Geliştirme Bütçesi",
        subtitle_en="",
        section_headings_tr=["Bütçe Kapsamı", "Onay"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="Geliştirme Bütçesi Onayı — [[project_name]]",
    ),
    "DOC-IZM-ADM-002": DocumentSpec(
        doc_id="DOC-IZM-ADM-002",
        family="report",
        subtitle_tr="Kızılova RES — Saha Güvenliği ve İdari Düzenlemeler Notu",
        subtitle_en="",
        section_headings_tr=["Düzenleme Kapsamı", "Değerlendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    "DOC-IZM-ADM-003": DocumentSpec(
        doc_id="DOC-IZM-ADM-003",
        family="report",
        subtitle_tr="Kızılova RES — Proje Maliyet Takip Notu",
        subtitle_en="",
        section_headings_tr=["Maliyet Kapsamı", "Değerlendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Kontrol Eden: Departman Yöneticisi"],
    ),
    # Adım 5 İş 4b (10.10.2026): kodla (0 LLM) — prose hand-authored.
    "DOC-IZM-FIN-001": DocumentSpec(
        doc_id="DOC-IZM-FIN-001",
        family="letter",
        subtitle_tr="Kızılova RES — Taahhüt Komisyonu Bildirimi",
        subtitle_en="",
        section_headings_tr=["Taahhüt Komisyonu", "Bilgilendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları", "Onaylayan: Yetkili İmza"],
        subject_label_tr="Taahhüt Komisyonu Bildirimi — [[project_name]]",
    ),
    "DOC-IZM-FIN-002": DocumentSpec(
        doc_id="DOC-IZM-FIN-002",
        family="letter",
        subtitle_tr="Kızılova RES — EPC Avans Teminat Mektubu",
        subtitle_en="",
        section_headings_tr=["Teminat Mektubu", "Geçerlilik"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Kredi Operasyonları", "Onaylayan: Yetkili İmza"],
        subject_label_tr="EPC Avans Teminat Mektubu — [[project_name]]",
    ),
    "DOC-IZM-FIN-003": DocumentSpec(
        doc_id="DOC-IZM-FIN-003",
        family="letter",
        subtitle_tr="Kızılova RES — Avans Faturası",
        subtitle_en="",
        section_headings_tr=["Fatura Bilgileri", "Ödeme Koşulları"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Muhasebe", "Onaylayan: Yetkili İmza"],
        subject_label_tr="Avans Faturası — [[project_name]]",
    ),
    # Adım 5 PF-1 LLM üretim planı (11.10.2026) — LLM prose (ilk gerçek Gemini çağrısı).
    "DOC-IZM-FIN-004": DocumentSpec(
        doc_id="DOC-IZM-FIN-004",
        family="agreement",
        subtitle_tr="",
        subtitle_en="Kızılova RES — Signed, Undrawn Term Loan Facility (2026-KZ)",
        section_headings_tr=[],
        section_headings_en=[
            "1. Definitions and Interpretation",
            "2. The Facility",
            "3. Conditions Precedent to Drawdown",
            "4. Commitment Fee",
            "5. Governing Law",
        ],
        signature_roles_en=[
            "For and on behalf of [[spv_name]] (Borrower) — Authorized Signatory",
            "For and on behalf of [[counterparty]] (Lender) — Authorized Signatory",
        ],
    ),
}
