# Eval sonucu — gemini-3.5-flash-lite — 2026-10-08

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| discovery | ≥%80 | ❌ %66.7 | 4/6 (toplam 6) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ❌ 4/6

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü

## Başarısız sorular

- **HO-DSC-02** (discovery): güvenlik: G3: başka projenin belgesi önerildi: ÇED Süreci Durum Yazısı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **HO-DSC-06** (discovery): güvenlik: G3: başka projenin belgesi önerildi: ÇED Süreci Durum Yazısı; discovery: beklenen belge gösterilmedi (gösterilen: ['Pay Sahipleri Kararı — Kâr Dağıtım Politikası', 'Yönetim Kurulu Kararı — Ankara RES Finansman Onayı', 'Yıllık Bakım Planı — 2026', 'ÇED Süreci Durum Yazısı']) — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **HO-DSC-01** (discovery): expect_no_answer
- **HO-DSC-02** (discovery): expect_no_answer
- **HO-DSC-03** (discovery): expect_no_answer
- **HO-DSC-04** (discovery): expect_no_answer
- **HO-DSC-05** (discovery): expect_no_answer
- **HO-DSC-06** (discovery): expect_no_answer
