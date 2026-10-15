# Eval sonucu — s0d_C_sonnet_answer — 2026-10-13

`DEMO_TODAY`: 2026-10-06 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| authorization | ≥%100 | ✅ %100.0 | 1/1 (toplam 1) | 0 |
| comparison | ≥%100 | ❌ %66.7 | 2/3 (toplam 3) | 0 |
| data | ≥%80 | ✅ %100.0 | 2/2 (toplam 2) | 0 |
| discovery | ≥%80 | ❌ %0.0 | 0/2 (toplam 2) | 0 |
| document | ≥%80 | ❌ %70.8 | 17/24 (toplam 24) | 0 |
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
- **ANK-ISO-002** (isolation): yasak kaynak geldi: ['ÇED Süreci Durum Yazısı'] — cevap: “Karatepe RES'in üretim lisansı vardır: Karatepe RES Üretim Lisansı 15.06.2020 tarihlidir ve Karatepe RES Enerji Üretim A.Ş.'ye verilmiştir [K2]. Bu lisans daha sonra 10.02.2021 tarihli Licence Amendme”
- **GEN-GEN-001** (document): answered=True bekleniyordu=False — cevap: “Kaynaklarda DSCR için bir tanım yazmıyor. DSCR'nin açılımı "debt service coverage ratio" olarak geçiyor ve bir kredi sözleşmesi taahhüdü (covenant) kapsamında kullanılıyor [K9]. Bu oran, bir kaynakta,”
- **ANK-COR-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-CMP-001** (comparison): beklenen değer metinde bulunamadı — cevap: “Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır.  Karatepe RES Üretim Lisansı 15.06.2020 tarihli olup lisansa ilişkin faaliyetler 15.06.2020 itibarıyla geçerlilik kazanm”
- **ANK-NEG-003** (document): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Soru hangi sözleşmeyi kastettiğini belirtmiyor; kaynaklarda birden fazla projenin kredi sözleşmesi ve her biri için farklı bilgiler var. Vade bilgisi geçen kaynaklar şunlardır:  Boztepe RES kredisinin”
- **ANK-NEG-004** (document): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Karatepe RES Üretim Lisansı 15.06.2020 tarihinde onaylanmıştır ve aynı tarihte yürürlüğe girmiştir [K18]. Lisansın belge tarihi ve yürürlük tarihi 15.06.2020 olarak kayıtlıdır [K9].  Bu lisans, 10.02.”
- **GEN-DSC-002** (discovery): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Evet, kaynaklarda sözleşmeler var; hangi projeyi sormak istediğiniz belirtilmediği için her projenin sözleşmesini ayrı ayrı yazıyorum.  Karatepe RES için güncel sözleşme, 15.03.2025 tarihli ve yürürlü”
- **GEN-DSC-010** (discovery): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Kaynaklarda şu teminat belgeleri geçmektedir:  Karatepe RES Security Agreement (Share Pledge), 01.12.2021 tarihli, Belge No DOC-ANK-FIN-011: Karatepe RES Enerji Üretim A.Ş. hisseleri üzerinde Security”

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
