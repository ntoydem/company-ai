"""Demirci RES — Hukuk belge spec'leri (İş Emri 2026-10-11-B, Hukuk partisi, T-12.5)."""

from __future__ import annotations

from seed_data.generator.document_specs._base import DocumentSpec

SPECS: dict[str, DocumentSpec] = {
    # Sonuç belgesi ÜRETİLMEDİ — kurumun cevabı henüz yok (NACI_CEVAP_2026-10-11.md §1).
    "DOC-DMR-LEG-001": DocumentSpec(
        doc_id="DOC-DMR-LEG-001",
        family="letter",
        subtitle_tr="TEA Olumsuz Görüşüne İtiraz Dilekçesi",
        subtitle_en="",
        section_headings_tr=["İtiraz Gerekçesi", "Talep"],
        section_headings_en=[],
        subject_label_tr="[[prior_decision_ref]] — TEA İtirazı",
        signature_roles_tr=["Hazırlayan: İlgili Birim"],
        prose_guidance_tr=(
            "Bu belge [[recipient]]'e hitaben yazılmış bir itiraz dilekçesidir. "
            "[[prior_decision_date]] tarihli [[prior_decision_ref]] sayılı TEA "
            "olumsuz görüşüne itiraz edilmektedir. İtiraz gerekçesi: "
            "[[objection_reason]]. İtiraz [[objection_date]] tarihinde yapılmıştır. "
            "Kurumun cevabı için beklenen tarih [[expected_response_date]]'dir — "
            "henüz bir cevap/sonuç alınmadığını belirt, bir sonuç icat etme. "
            "Resmi, kurumsal bir itiraz dilekçesi üslubu kullan."
        ),
    ),
}
