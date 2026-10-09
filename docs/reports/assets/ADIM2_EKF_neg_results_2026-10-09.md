# Eval sonucu — ekf_neg — 2026-10-09

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| document | ≥%80 | ❌ %75.0 | 3/4 (toplam 4) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ❌ 3/4

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü

## Başarısız sorular

- **ANK-NEG-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['Ankara RES Üretim Lisansı']; güvenlik: G3: başka projenin belgesi önerildi: ÇED Süreci Durum Yazısı; G3: yasak kaynak assist'te: İzmir RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Ankara RES: Monthly Production 2026 (05.09.2026); Aylık Üretim Raporu — Ağustos 2026 (05.09.2026); Aylık Üretim Raporu — Haziran 2025”

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **CO-NEG-005** (document): unformattable expected_answer type: str
- **GEN-AMB-003-F** (document): unformattable expected_answer type: list
