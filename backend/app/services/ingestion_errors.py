"""Ingestion failure code → the plain Turkish line the user sees (Tansu Not 7, §2).

The ocr-worker stores a closed code in `documents.ingestion_error` (`ocr-worker/worker/
errors.py`): `no_text`, `encrypted`, `corrupt`, `unknown`. `unsupported` never reaches the
worker — the upload endpoint refuses it with 415 — but is mapped for completeness. Anything
else (including the pre-Not 7 sentence "Belge işlenirken bir hata oluştu.") gets the
generic line. The raw code is for admin/audit only (`DocumentDetailResponse.ingestion_error`
for admin); every other response carries `reason`.

Supported formats are PDF, PNG/JPG, Excel (xlsx/xlsm) and CSV — not Word (Tansu's note
said "PDF, Word veya Excel"; corrected here, Naci 06.10.2026).
"""

from __future__ import annotations

REASONS: dict[str, str] = {
    "no_text": "Taranmış sayfalarda okunabilir metin bulunamadı. Daha net bir tarama yükleyin.",
    "encrypted": "Belge parola korumalı olduğu için açılamadı. Parolasız halini yükleyin.",
    "corrupt": "Dosya bozuk görünüyor, açılamadı. Dosyayı kontrol edip tekrar yükleyin.",
    "unsupported": "Bu dosya türü desteklenmiyor. PDF, resim (PNG/JPG), Excel veya CSV yükleyin.",
}
GENERIC_REASON = "Belge okunamadı. Dosyayı kontrol edip tekrar yükleyin."


def reason_for(code: str | None) -> str | None:
    """None stays None (no failure); a known code maps; anything else is the generic line —
    never the stored text itself."""
    if code is None:
        return None
    return REASONS.get(code, GENERIC_REASON)
