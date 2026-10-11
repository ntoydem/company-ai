"""Karatepe RES — Development/lisans belge spec'leri (Phase 3.1 + 5.1)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    "DOC-ANK-DEV-001": DocumentSpec(
        doc_id="DOC-ANK-DEV-001",
        family="letter",
        subtitle_tr="Karatepe RES Rüzgar Enerjisi Üretim Tesisi",
        subtitle_en="",
        section_headings_tr=["Lisans Kapsamı", "Kapasite ve Teknik Bilgiler", "Yükümlülükler"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Üretim Lisansı — [[project_name]]",
    ),
    "DOC-ANK-DEV-002": DocumentSpec(
        doc_id="DOC-ANK-DEV-002",
        family="letter",
        subtitle_tr="Karatepe RES Üretim Lisansı Tadili",
        subtitle_en="",
        # Düzeltme (11.10.2026, Naci): başlık, ilk/güncel değer ikisini de anlatacak
        # şekilde genişletildi — 7->8 türbin, 21->24 MW (yeni token'lar).
        section_headings_tr=[
            "Tadil Gerekçesi",
            "Kapasite ve Türbin Sayısı Değişikliği",
            "Yürürlük",
        ],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Lisanslama Uzmanı", "Onaylayan: Kurum Yetkilisi"],
        subject_label_tr="Üretim Lisansı Tadili — [[project_name]]",
    ),
    "DOC-ANK-DEV-003": DocumentSpec(
        doc_id="DOC-ANK-DEV-003",
        family="agreement",
        subtitle_tr="Karatepe RES Şebeke Bağlantı Anlaşması",
        subtitle_en="",
        section_headings_tr=["1. Bağlantı Kapsamı", "2. Yürürlük ve Genel Hükümler"],
        section_headings_en=[],
        signature_roles_tr=["İmza: [[spv_name]] Yetkilisi", "İmza: [[counterparty]] Yetkilisi"],
    ),
    "DOC-ANK-DEV-004": DocumentSpec(
        doc_id="DOC-ANK-DEV-004",
        family="letter",
        subtitle_tr="Karatepe RES İnşaat İzinleri",
        subtitle_en="",
        section_headings_tr=["Ruhsat Kapsamı", "Yürürlük"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="Yapı Ruhsatı — [[project_name]]",
    ),
    "DOC-ANK-DEV-005": DocumentSpec(
        doc_id="DOC-ANK-DEV-005",
        family="letter",
        subtitle_tr="Karatepe RES Çevresel Değerlendirme",
        subtitle_en="",
        section_headings_tr=["Değerlendirme Kapsamı", "Karar"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: İlgili Birim", "Onaylayan: Yetkili Makam"],
        subject_label_tr="ÇED Olumlu Kararı — [[project_name]]",
    ),
    "DOC-ANK-DEV-006": DocumentSpec(
        doc_id="DOC-ANK-DEV-006",
        family="agreement",
        subtitle_tr="Karatepe RES Saha Kullanım Hakkı",
        subtitle_en="",
        section_headings_tr=["1. Kullanım Hakkının Kapsamı", "2. Yürürlük ve Genel Hükümler"],
        section_headings_en=[],
        # Düzeltme (11.10.2026, Naci onaylı): eski üretim [[counterparty]] token'ını
        # SPV'nin kendisine düşürüp kendiyle-sözleşme cümleleri yazmıştı (imza sayfası
        # da aynı şirketi iki kez imzalatıyordu). T-13.2 (Tansu, 11.10.2026) karşı
        # tarafı verdi — Karatepe Köyü tüzel kişiliği — artık gerçek bir isim var.
        signature_roles_tr=["İmza: [[spv_name]] Yetkilisi", "İmza: [[counterparty]] Muhtarı"],
        prose_guidance_tr=(
            "Belge yürürlükte/imzalanmış statüsünde; kullanım hakkının [[spv_name]] "
            "için [[counterparty]] tarafından tesis edildiğini geçmiş zamanla anlat. "
            "Token'la verilmeyen somut bir hüküm icat etme."
        ),
    ),
}
