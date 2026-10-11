"""Akyar GES — Hukuk belge spec'leri (İş Emri 2026-10-11-B, Hukuk partisi, T-12.5b)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    # Dava YOK — bir ön değerlendirme/müzakere notu (NACI_CEVAP_2026-10-11.md §1).
    # Malikin ismi kaynakta yok — ROL olarak anılır, isim icat edilmedi.
    "DOC-AKY-LEG-001": DocumentSpec(
        doc_id="DOC-AKY-LEG-001",
        family="report",
        subtitle_tr="Kamulaştırma Ön Değerlendirme Notu",
        subtitle_en="",
        section_headings_tr=["Süreç Özeti", "Değerlendirme"],
        section_headings_en=[],
        signature_roles_tr=["Hazırlayan: Hukuk Danışmanlığı"],
        prose_guidance_tr=(
            "Bu belge, arazi malikiyle sürmekte olan bir kamulaştırma öncesi "
            "müzakere sürecinin iç değerlendirme notudur — bir dava DEĞİLDİR. "
            "Malikten yalnız ROLÜYLE ('malik') bahset — özel bir ad İCAT ETME. "
            "Değerleme raporu [[valuation_date]] tarihlidir. Malikle görüşme "
            "[[meeting_date]] tarihinde yapılmış ve malik talep ettiği bedeli "
            "artırmıştır — tutarı belirtme (kaynakta sayısal değer yok), yalnız "
            "bu olguyu aktar. Bir sonraki görüşme [[next_meeting]] tarihindedir. "
            "Nötr, iç rapor üslubu kullan; müzakerenin sonucu hakkında yorum "
            "yapma veya bir kamulaştırma kararı icat etme."
        ),
    ),
}
