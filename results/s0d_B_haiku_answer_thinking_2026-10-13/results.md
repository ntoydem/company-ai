# Eval sonucu — s0d_B_haiku_answer_thinking — 2026-10-13

`DEMO_TODAY`: 2026-10-06 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| authorization | ≥%100 | ✅ %100.0 | 1/1 (toplam 1) | 0 |
| comparison | ≥%100 | ❌ %33.3 | 1/3 (toplam 3) | 0 |
| data | ≥%80 | ✅ %100.0 | 2/2 (toplam 2) | 0 |
| discovery | ≥%80 | ❌ %0.0 | 0/2 (toplam 2) | 0 |
| document | ≥%80 | ❌ %75.0 | 18/24 (toplam 24) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 1/1 (toplam 1) | 0 |
| isolation | ≥%100 | ❌ %50.0 | 1/2 (toplam 2) | 0 |
| temporal | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ✅ 39/39

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü
**Router düşüşü (sınıflandırma çağrısı boş/hatalı → DOCUMENT_QUERY, S0-a):** 0/39

## Başarısız sorular

- **IZM-DEV-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-005** (document): answered=False bekleniyordu=True; eksik kaynak: ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-ISO-002** (isolation): yasak kaynak geldi: ['ÇED Süreci Durum Yazısı'] — cevap: “Üretim lisansı bulunan proje Karatepe RES'tir. Karatepe RES Üretim Lisansı, 15.06.2020 tarihinde Karatepe RES Enerji Üretim A.Ş. unvanına verilmiştir ve yürürlük tarihi 15.06.2020'dir [K2]. Belgenin d”
- **ANK-COR-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-CMP-002** (comparison): beklenen değer metinde bulunamadı — cevap: “Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır.  Karatepe RES Üretim Lisansı'nın tarihi ve yürürlük tarihi 15.06.2020'dir [K22][K54].  Kızılova RES Önlisans Belgesi'nin”
- **GEN-CMP-003** (comparison): ifade kontrolü: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] — cevap: “Belgelere göre: **Karatepe RES:** Güncel kurulu güç 24 MW'tır [K69]. Bu değer, Licence Amendment 01 (Kapasite Tadili) ile önceki 21 MW seviyesinden değiştirilmiştir [K69]. 24 MW değeri, 15.10.2023 tar”
- **ANK-NEG-003** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-NEG-004** (document): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Karatepe RES için Üretim Lisansı'nın yürürlük tarihi 15.06.2020'dir [K9]. Lisansın faaliyetlerinin bu tarih itibarıyla geçerlilik kazandığı resmen ilan edilmiştir [K18].  Kızılova RES için ise ÇED Sür”
- **GEN-DSC-002** (discovery): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Evet, kaynaklarda güncel durumda olan sözleşmeler bulunuyor. Bunlar proje bazında aşağıdadır.  Yeşilova RES için Yeşilova RES Facility Agreement (2023-YS) bulunmaktadır; tarihi 03.06.2023 ve durumu ex”
- **GEN-DSC-010** (discovery): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Kaynaklarda Karatepe RES için iki, Kızılova RES için bir teminat belgesi yer alıyor.  Karatepe RES için 01.12.2021 tarihli, DOC-ANK-FIN-011 numaralı Security Agreement (Share Pledge) bulunuyor; bu bel”

## Değer kontrolü atlanan sorular (yalnızca kaynak+answered ile puanlandı)

Bu sorular `passed` sayılmış olabilir ama cevabın içeriği (sayı/tarih/liste) metin olarak doğrulanmadı — bkz. `docs/plans/PHASE_4_1_PLAN.md` §2/SORU 1.

- **ANK-FIN-008** (temporal): unformattable expected_answer type: str
- **ANK-FIN-009** (document): unformattable expected_answer type: list
- **ANK-EPC-002** (document): unformattable expected_answer type: str
- **IZM-DEV-001** (document): unformattable expected_answer type: str
- **IZM-DEV-004** (document): unformattable expected_answer type: list
- **IZM-DEV-005** (document): unformattable expected_answer type: NoneType
- **IZM-DEV-006** (document): unformattable expected_answer type: NoneType
- **GEN-HAL-001** (hallucination): expect_no_answer
- **ANK-AUT-001** (authorization): expect_no_answer
- **GEN-GEN-001** (document): expect_no_answer
- **GEN-GEN-002** (document): expect_no_answer
- **ANK-FIN-015** (document): unformattable expected_answer type: int
- **ANK-OPS-002** (document): unformattable expected_answer type: str
- **CO-NEG-005** (document): unformattable expected_answer type: str
- **GEN-DSC-002** (discovery): expect_no_answer
- **GEN-DSC-010** (discovery): expect_no_answer
