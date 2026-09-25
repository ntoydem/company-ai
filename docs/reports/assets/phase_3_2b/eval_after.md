# Eval sonucu — gemini-3.5-flash-lite — 2026-09-25

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| document | ≥%80 | ❌ %69.6 | 16/23 (toplam 23) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| isolation | ≥%100 | ❌ %75.0 | 3/4 (toplam 4) | 0 |
| temporal | ≥%80 | ❌ %66.7 | 6/9 (toplam 9) | 0 |

**Genel sonuç:** ❌ en az bir kategori eşiği altında

## Başarısız sorular

- **ANK-DEV-001** (document): beklenen değer metinde bulunamadı — cevap: “Ankara RES sahasında yürütülecek faaliyetler 15.06.2020 tarihinde onaylanan hükümlere tabidir ve faaliyetlerin 15.06.2020 itibarıyla geçerlilik kazandığı resmen ilan edilmiştir [K1].”
- **ANK-FIN-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-003** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-007** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-012** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement Amendment 01'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-EPC-004** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['EPC Contract', 'Provisional Acceptance & COD Certificate'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-005** (document): eksik kaynak: ['İzmir RES Önlisans Belgesi'] — cevap: “Mevcut şirket kaynaklarında İzmir RES için üretim lisansı alındığına dair bir bilgi bulunmamaktadır; aksine ÇED Süreci Durum Yazısı belgesinde üretim lisansı "bekleyen kritik adımlar" arasında yer alm”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-007** (document): eksik kaynak: ['İzmir RES Önlisans Belgesi'] — cevap: “İzmir RES projesinde arazi edinimine ilişkin tüm idari süreçler DOC-IZM-DEV-002 standartlarına uygun olarak başarıyla sonuçlandırılmıştır [K4]. Edinilen parsellerin tapu devir işlemleri resmen tescil ”
- **ANK-ISO-003** (isolation): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”

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
