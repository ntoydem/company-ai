# Eval sonucu — gemini-3.5-flash — 2026-09-25

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

**Koşu yarıda kesildi:** 5 ardışık istek hatası (ANK-EPC-002'de durdu) — günlük kota tükenmiş olabilir, bkz. Gemini konsolu

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| document | ≥%80 | ❌ %50.0 | 4/8 (toplam 11) | 3 |
| temporal | ≥%80 | ✅ %100.0 | 3/3 (toplam 5) | 2 |

**Genel sonuç:** ❌ en az bir kategori eşiği altında

## Başarısız sorular

- **ANK-DEV-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Ankara RES Üretim Lisansı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-003** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”

## Puanlanamayan sorular (istek hatası)

- **ANK-FIN-007** (temporal): http 503 after 3 retries
- **ANK-FIN-008** (temporal): http 503 after 3 retries
- **ANK-FIN-009** (document): http 503 after 3 retries
- **ANK-EPC-001** (document): http 503 after 3 retries
- **ANK-EPC-002** (document): http 503 after 3 retries
