# Eval sonucu — gemini-3.5-flash-lite — 2026-10-08

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| discovery | ≥%80 | ❌ %50.0 | 2/4 (toplam 5) | 1 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ✅ 4/4

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü

## Başarısız sorular

- **GEN-DSC-006-M** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-008-M** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”

## Puanlanamayan sorular (istek hatası)

- **GEN-DSC-011-K** (discovery): http 503 after 3 retries

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **GEN-DSC-001-M** (discovery): expect_no_answer
- **GEN-DSC-006-M** (discovery): expect_no_answer
- **GEN-DSC-008-M** (discovery): expect_no_answer
- **GEN-DSC-007-K** (discovery): expect_no_answer
