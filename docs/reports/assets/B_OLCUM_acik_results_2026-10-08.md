# Eval sonucu — gemini-3.5-flash-lite — 2026-10-08

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| discovery | ≥%80 | ❌ %61.5 | 8/13 (toplam 13) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ✅ 13/13

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü

## Başarısız sorular

- **GEN-DSC-001** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-006** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-007** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Ankara RES Kullanılabilirlik Garantisi Uyum Raporu', 'Arazi Edinim Durum Raporu', 'Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu', 'Rüzgar Ölçüm Kampanyası Raporu', 'ÇED Süreci Durum Yazısı']) — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-008** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-011** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Financial Model 2026']) — cevap: “Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Ankara projesinin ilk kredi ödeme tutarı 1.000.000 kadardır.”

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **GEN-DSC-001** (discovery): expect_no_answer
- **GEN-DSC-002** (discovery): expect_no_answer
- **GEN-DSC-003** (discovery): expect_no_answer
- **GEN-DSC-004** (discovery): expect_no_answer
- **GEN-DSC-005** (discovery): expect_no_answer
- **GEN-DSC-006** (discovery): expect_no_answer
- **GEN-DSC-007** (discovery): expect_no_answer
- **GEN-DSC-008** (discovery): expect_no_answer
- **GEN-DSC-009** (discovery): expect_no_answer
- **GEN-DSC-010** (discovery): expect_no_answer
- **GEN-DSC-011** (discovery): expect_no_answer
- **GEN-DSC-012** (discovery): expect_no_answer
- **GEN-DSC-013** (discovery): expect_no_answer
