# Eval sonucu — d3_eval — 2026-10-17

`DEMO_TODAY`: 2026-10-06 · `EMBEDDINGS_ENABLED`: False · puanlayıcı v2.2

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| ambiguous | ≥%80 | ❌ %0.0 | 0/1 (toplam 1) | 0 |
| comparison | ≥%100 | ✅ %100.0 | 2/2 (toplam 2) | 0 |
| document | ≥%80 | ✅ %100.0 | 2/2 (toplam 2) | 0 |
| isolation | ≥%100 | ✅ %100.0 | 1/1 (toplam 1) | 0 |
| temporal | ≥%80 | ✅ %100.0 | 1/1 (toplam 1) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ✅ 7/7

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü
**Router düşüşü (sınıflandırma çağrısı boş/hatalı → DOCUMENT_QUERY, S0-a):** 0/7
**Keşif sayacı — beklenen belge gösterildi (tüm sorular):** 6/6
**Keşif sayacı — listede yabancı proje var (tüm sorular):** 1/4 — ANK-ISO-002
**Keşif sayacı — beklenen belge gösterildi (discovery):** 0/0
**Keşif sayacı — listede yabancı proje var (discovery):** 0/0
**Liste kapsamı (opt-in `expected_items`, V21 R6):** 0/0 öğe (0 ölçülebilir soru)
**Sabit 'bulamadım' cümlesiyle geçen soru (answer_policy: either dahil):** 0/6 geçen

## Başarısız sorular

- **GEN-DSC-003-F** (ambiguous): ifade kontrolü: yasak ifade: ['Kızılova', 'Boztepe'] — cevap: “Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **IZM-DEV-001** (document): unformattable expected_answer type: str
- **IZM-DEV-007** (document): unformattable expected_answer type: list
- **GEN-DSC-003-F** (ambiguous): no_literal_expected_answer
