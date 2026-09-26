# Eval sonucu — gemini-3.5-flash-lite — 2026-09-26

`DEMO_TODAY`: 2026-09-15 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| data | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| document | ≥%80 | ✅ %80.0 | 24/30 (toplam 30) | 0 |
| general | ≥%80 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| isolation | ≥%100 | ❌ %75.0 | 3/4 (toplam 4) | 0 |
| mixed | ≥%80 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| temporal | ≥%80 | ❌ %60.0 | 6/10 (toplam 10) | 0 |

**Genel sonuç:** ❌ en az bir kategori eşiği altında

## Başarısız sorular

- **ANK-DEV-004** (temporal): eksik kaynak: ['Ankara RES Üretim Lisansı'] — cevap: “Ankara RES'in ilk lisans kapasitesi 48 MW değerindedir [K1].”
- **ANK-FIN-005** (document): beklenen değer metinde bulunamadı — cevap: “Ankara RES kredisinin faiz bazı baseline index, marjı ise 3,25%'tir [K37].”
- **ANK-OPS-001** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Aylık Üretim Raporu — Ağustos 2026']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-EPC-004** (temporal): eksik kaynak: ['EPC Contract'] — cevap: “Ankara RES'in ticari işletme tarihi (COD) başlangıçta beklenen 30.06.2023 tarihinden 15.10.2023 tarihine ertelenmiştir [K23]. Bu sapmanın sebebi şebeke bağlantı çalışmaları olarak belirtilmiştir [K23]”
- **IZM-DEV-003** (document): beklenen değer metinde bulunamadı — cevap: “İzmir RES projesi kapsamında yürütülen çevresel etki değerlendirmesi çalışmaları devam etmektedir [K1]. Çevresel Etki Değerlendirme süreçlerinin eksiksiz tamamlanması gerekmektedir [K14].”
- **IZM-DEV-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-005** (document): answered=False bekleniyordu=True; eksik kaynak: ['İzmir RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-007** (document): eksik kaynak: ['İzmir RES Önlisans Belgesi', 'Arazi Edinim Durum Raporu'] — cevap: “İzmir RES projesinde önlisans (18.01.2024) ve arazi edinimi (02.04.2024 itibarıyla) adımları tamamlanmıştır [K1].”
- **ANK-ISO-002** (isolation): answered=False bekleniyordu=True; eksik kaynak: ['Ankara RES Üretim Lisansı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-011** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Önlisans Süre Uzatımı Hukuki Değerlendirmesi']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **ANK-FIN-008** (temporal): unformattable expected_answer type: str
- **ANK-FIN-009** (document): unformattable expected_answer type: list
- **ANK-EPC-002** (document): unformattable expected_answer type: str
- **ANK-FIN-010** (data): unformattable expected_answer type: str
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
- **GEN-GEN-001** (general): general: no ledger-backed expected value
- **GEN-GEN-002** (general): general: no ledger-backed expected value
- **GEN-GEN-003** (general): general: no ledger-backed expected value
- **ANK-MIX-003** (mixed): unformattable expected_answer type: dict
- **ANK-FIN-015** (document): unformattable expected_answer type: int
- **ANK-OPS-002** (document): unformattable expected_answer type: str
- **ANK-COR-001** (document): unformattable expected_answer type: int
