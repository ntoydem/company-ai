# Eval sonucu — gemini-3.5-flash-lite — 2026-09-25

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| data | ≥%80 | ❌ %33.3 | 1/3 (toplam 3) | 0 |
| document | ≥%80 | ❌ %69.6 | 16/23 (toplam 23) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| isolation | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| mixed | ≥%80 | ✅ %100.0 | 2/2 (toplam 2) | 0 |
| temporal | ≥%80 | ✅ %88.9 | 8/9 (toplam 9) | 0 |

**Genel sonuç:** ❌ en az bir kategori eşiği altında

## Başarısız sorular

- **ANK-FIN-003** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”
- **ANK-FIN-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”
- **ANK-FIN-010** (document): eksik kaynak: ['Covenant Compliance Report Q2 2026'] — cevap: “Ankara RES'in son covenant testi sonucu pass olarak gerçekleşmiştir.”
- **ANK-FIN-011** (document): answered=False bekleniyordu=True; eksik kaynak: ['Covenant Compliance Report Q2 2026']; beklenen değer metinde bulunamadı — cevap: “Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”
- **ANK-EPC-004** (temporal): eksik kaynak: ['EPC Contract'] — cevap: “Ankara RES'in ticari işletme tarihi (COD), ilk beklenen tarih olan 30 Haziran 2023'ten 15 Ekim 2023'e ertelenmiştir [K9]. Belgelerde bu sapmanın sebebi şebeke bağlantı çalışmaları (grid connection wor”
- **IZM-DEV-005** (document): eksik kaynak: ['İzmir RES Önlisans Belgesi'] — cevap: “Mevcut kaynaklarda İzmir RES için üretim lisansının henüz alınmadığı, bekleyen kritik adımlar arasında üretim lisansının da yer aldığı belirtilmektedir [K29]. İzmir RES projesi kapsamında bugüne kadar”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-007** (document): eksik kaynak: ['İzmir RES Önlisans Belgesi', 'Arazi Edinim Durum Raporu'] — cevap: “İzmir RES projesinde önlisans (18.01.2024) ve arazi edinimi (02.04.2024 itibarıyla) adımları tamamlanmıştır [K1].”
- **ANK-DAT-002** (data): beklenen değer metinde bulunamadı — cevap: “Ankara RES Ağustos 2026 üretimi 13.538 MWh olarak gerçekleşmiştir.”
- **ANK-DAT-003** (data): answered=False bekleniyordu=True; eksik kaynak: ['Financial Model 2026']; beklenen değer metinde bulunamadı — cevap: “Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **ANK-FIN-008** (temporal): unformattable expected_answer type: str
- **ANK-FIN-009** (document): unformattable expected_answer type: list
- **ANK-EPC-002** (document): unformattable expected_answer type: str
- **ANK-FIN-010** (document): unformattable expected_answer type: str
- **ANK-FIN-012** (temporal): unformattable expected_answer type: str
- **ANK-EPC-004** (temporal): unformattable expected_answer type: str
- **IZM-DEV-001** (document): unformattable expected_answer type: str
- **IZM-DEV-004** (document): unformattable expected_answer type: list
- **IZM-DEV-005** (document): unformattable expected_answer type: NoneType
- **IZM-DEV-006** (document): unformattable expected_answer type: NoneType
- **IZM-DEV-007** (document): unformattable expected_answer type: list
- **IZM-DEV-008** (document): unformattable expected_answer type: list
- **GEN-HAL-001** (hallucination): expect_no_answer
- **GEN-HAL-002** (hallucination): expect_no_answer
- **GEN-HAL-003** (hallucination): expect_no_answer
- **GEN-HAL-004** (hallucination): expect_no_answer
- **IZM-ISO-004** (isolation): unformattable expected_answer type: NoneType
- **ANK-AUT-001** (authorization): expect_no_answer
- **ANK-AUT-002** (authorization): expect_no_answer
- **ANK-AUT-003** (authorization): expect_no_answer
- **ANK-MIX-002** (mixed): unformattable expected_answer type: dict
