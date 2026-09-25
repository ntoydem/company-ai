# Eval sonucu — gemini-3.5-flash-lite — 2026-09-25

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| data | ≥%80 | ❌ %66.7 | 2/3 (toplam 3) | 0 |
| document | ≥%80 | ✅ %82.6 | 19/23 (toplam 23) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| isolation | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| mixed | ≥%80 | ✅ %100.0 | 2/2 (toplam 2) | 0 |
| temporal | ≥%80 | ✅ %88.9 | 8/9 (toplam 9) | 0 |

**Genel sonuç:** ❌ en az bir kategori eşiği altında

## Başarısız sorular

- **ANK-FIN-010** (document): eksik kaynak: ['Covenant Compliance Report Q2 2026'] — cevap: “Belgelere göre: Ankara RES için minimum borç servisi karşılama oranı (DSCR) eşik değeri 1,20x seviyesindedir [K10]. Bu değer Facility Agreement Amendment 01 ile önceki 1,25x seviyesinden değiştirilmiş”
- **ANK-EPC-004** (temporal): eksik kaynak: ['EPC Contract'] — cevap: “Ankara RES'in ticari işletme tarihi (COD), ilk beklenen tarih olan 30.06.2023'ten 15.10.2023 tarihine ertelenmiştir [K9]. Belgelerde bu ertelemenin sebebi şebeke bağlantı çalışmaları (grid connection ”
- **IZM-DEV-005** (document): eksik kaynak: ['İzmir RES Önlisans Belgesi'] — cevap: “İzmir RES projesi için henüz üretim lisansı alınmamıştır; ÇED Süreci Durum Yazısı belgesinde üretim lisansı, bekleyen kritik adımlar arasında yer almaktadır [K29]. Proje kapsamında bugüne kadar önlisa”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-007** (document): eksik kaynak: ['İzmir RES Önlisans Belgesi', 'Arazi Edinim Durum Raporu'] — cevap: “İzmir RES projesinde bugüne kadar önlisans (18.01.2024) ve arazi edinimi (02.04.2024 itibarıyla) adımları tamamlanmıştır [K1].”
- **ANK-DAT-003** (data): eksik kaynak: ['Financial Model 2026'] — cevap: “Ankara RES'in 20.07.2026 tarihi itibarıyla toplam kalan kredi borcu 44.100.000 EUR'dur [K1].”

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
