# Eval sonucu — excel_paket_haiku — 2026-10-13

`DEMO_TODAY`: 2026-10-06 · `EMBEDDINGS_ENABLED`: False

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| ambiguous | ≥%80 | ❌ %16.7 | 1/6 (toplam 6) | 0 |
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| comparison | ≥%100 | ❌ %0.0 | 0/3 (toplam 3) | 0 |
| data | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| discovery | ≥%80 | ❌ %16.7 | 3/18 (toplam 18) | 0 |
| document | ≥%80 | ❌ %30.8 | 12/39 (toplam 39) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| isolation | ≥%100 | ❌ %25.0 | 1/4 (toplam 4) | 0 |
| mixed | ≥%80 | ❌ %66.7 | 2/3 (toplam 3) | 0 |
| temporal | ≥%80 | ❌ %54.5 | 6/11 (toplam 11) | 0 |
| term_mismatch | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ❌ 97/99

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü
**Router düşüşü (sınıflandırma çağrısı boş/hatalı → DOCUMENT_QUERY, S0-a):** 0/99

## Başarısız sorular

- **ANK-DEV-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Karatepe RES Üretim Lisansı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-DEV-004** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Karatepe RES Üretim Lisansı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-002** (document): beklenen değer metinde bulunamadı — cevap: “Karatepe RES'in toplam finansman tutarı 14.000.000 USD'dir [K11][K64]. Bu tutar, Garanti BBVA'nın yerel banka olarak tamamını sağladığı bir finansman yapısı olarak tanımlanmaktadır [K64].  Not: Bu değ”
- **ANK-FIN-003** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-005** (document): eksik kaynak: ['Facility Agreement'] — cevap: “Karatepe RES için güncel faiz bilgisi kaynaklarda şöyle yer alıyor:  Taban endeks üzerine uygulanan marj %2,9 olarak teyit edilmektedir [K1]. Bu marj, 25.09.2026 tarihli Garanti BBVA Faiz Belirleme Bi”
- **ANK-FIN-006** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement Amendment 02']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-008** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement Amendment 02'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-FIN-009** (document): answered=False bekleniyordu=True; eksik kaynak: ['Facility Agreement Amendment 01', 'Facility Agreement Amendment 02'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-EPC-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['EPC Contract']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-EPC-002** (document): answered=False bekleniyordu=True; eksik kaynak: ['EPC Contract'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-OPS-001** (temporal): eksik kaynak: ['Aylık Üretim Raporu — Ağustos 2026']; beklenen değer metinde bulunamadı — cevap: “Belgelere göre: Karatepe RES için COD (işletmeye alınma) tarihi, kaynaklarda şu şekilde belirtilmiştir:  Karatepe RES'in ticari işletme (COD) tarihi 15.10.2023'tür; bu tarih, sözleşmede ilk planlanan ”
- **ANK-FIN-011** (document): eksik kaynak: ['Covenant Compliance Report Q2 2026'] — cevap: “Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Karatepe RES için en son dönemdeki kalan kredi borcu bakiyesi 11.”
- **IZM-DEV-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-002** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-005** (document): answered=False bekleniyordu=True; eksik kaynak: ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; eksik kaynak: ['ÇED Süreci Durum Yazısı'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-ISO-001** (isolation): answered=False bekleniyordu=True; eksik kaynak: ['Kızılova RES Önlisans Belgesi', 'Rüzgar Kaynağı ve Ön Fizibilite Teknik Raporu']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-ISO-002** (isolation): yasak kaynak geldi: ['ÇED Süreci Durum Yazısı'] — cevap: “Karatepe RES Üretim Lisansı, Karatepe RES Enerji Üretim A.Ş. adına EPDK'dan alınmış ve 15.06.2020 tarihinde yürürlüğe girmiştir [K2]. Belgenin durumu "Tadil Edilmiş" olarak kayıtlıdır [K2][K12].  Lisa”
- **IZM-ISO-004** (isolation): answered=True bekleniyordu=False; yasak kaynak geldi: ['Facility Agreement'] — cevap: “Evet, Kızılova RES için finansman sözleşmesi imzalanmıştır.  Kızılova RES İmzalı-Kullanılmamış Kredi Sözleşmesi (2026-KZ), Kızılova RES Enerji Üretim A.Ş. ile Garanti BBVA arasında 05.10.2026 tarihind”
- **ANK-MIX-001** (mixed): eksik kaynak: ['Facility Agreement Amendment 01', 'Covenant Report (workbook)']; beklenen değer metinde bulunamadı — cevap: “Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: En son çeyreğin gerçekleşen DSCR değeri 1,37'dir.”
- **GEN-GEN-001** (document): answered=True bekleniyordu=False — cevap: “DSCR (Debt Service Coverage Ratio), borç servis karşılama oranı demektir. Kaynaklar bu terimi tanımlamamaktadır; yalnızca bir kredi kovenant rasyosu olarak kullanıldığını ve belirli projelerde değerle”
- **GEN-GEN-002** (document): answered=True bekleniyordu=False — cevap: “ÇED (Çevresel Etki Değerlendirmesi), projelerin çevre üzerindeki olası etkilerinin önceden belirlenip değerlendirildiği süreçtir. Kaynaklarda bu sürecin genel tanımı yer almamaktadır; ancak Kızılova R”
- **ANK-FIN-014** (document): eksik kaynak: ['Karatepe RES Covenant Compliance Report — Q4 2024'] — cevap: “Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Karatepe RES için Q4 2024 covenant workbook'unda hesaplanan gerçe”
- **ANK-FIN-015** (document): answered=False bekleniyordu=True; eksik kaynak: ['Karatepe RES Drawdown Notice — Tranche 1'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-DEV-006** (document): answered=False bekleniyordu=True; eksik kaynak: ['Karatepe RES ÇED Olumlu Kararı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-OPS-002** (document): answered=False bekleniyordu=True; eksik kaynak: ['Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-EPC-005** (document): answered=False bekleniyordu=True; eksik kaynak: ['Karatepe RES Performance Test Results Report']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-OPS-003** (document): eksik kaynak: ['Aylık Üretim Raporu — Aralık 2023'] — cevap: “Karatepe RES'in Aralık 2023 aylık üretimi 17.218 MWh'tır.”
- **ANK-COR-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **IZM-DEV-010** (document): answered=False bekleniyordu=True; eksik kaynak: ['Rüzgar Ölçüm Kampanyası Raporu']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-CMP-001** (comparison): beklenen değer metinde bulunamadı — cevap: “Karatepe RES için üretim lisansı tarihi kaynaklarda şu şekilde geçiyor: Üretim lisansı 15.06.2020 tarihinde yürürlüğe girmiştir [K22]. Bu belge, durumu "amended" olarak kayıtlı olan Karatepe RES Üreti”
- **GEN-CMP-002** (comparison): ifade kontrolü: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz']; yasak ifade: ['daha önce'] — cevap: “Karatepe RES üretim lisansı daha önce alınmıştır.  Karatepe RES üretim lisansı 15.06.2020 tarihinde yürürlüğe girmiştir [K22]. Kızılova RES önlisansı ise 18.01.2024 tarihli olup [K33] Kızılova RES Önl”
- **GEN-CMP-003** (comparison): ifade kontrolü: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] — cevap: “Belgelere göre: Karatepe RES için belgelerde kurulu güç 21 MW olarak geçmektedir [K2]. Karatepe RES Üretim Lisansı'nda toplam kurulu güç 21 MW olarak kayıtlıdır [K68]. Ancak Licence Amendment 01 (Kapa”
- **GEN-AMB-001** (ambiguous): answered=True bekleniyordu=False — cevap: “Sözleşmenin vadesi hangi sözleşme olduğuna bağlıdır; soruda hangi sözleşmenin kastedildiği belirtilmemiştir. Kaynaklarda yer alan sözleşmelerden birkaçının vade bilgisi şöyledir:  - Boztepe RES Facili”
- **GEN-AMB-002** (ambiguous): answered=True bekleniyordu=False; güvenlik: G2: cevap var, kaynak yok — cevap: “Soru hangi projeyi kastediyor belirsiz; "Raporda" ifadesi tek bir rapor işaret etmiyor. Kaynaklarda birden fazla proje ve DSCR değeri var. Ancak soru belirli bir projeyi ya da raporu tanımlamadığı içi”
- **GEN-AMB-003** (ambiguous): answered=True bekleniyordu=False — cevap: “Son tadil, Facility Agreement Amendment 02 (15.03.2025, versiyon AMD02) belgesidir ve Facility Agreement Amendment 01'i değiştirmektedir [K3].  Bu tadil ile minimum borç servis karşılama oranı (DSCR) ”
- **GEN-AMB-004** (ambiguous): answered=True bekleniyordu=False — cevap: “Kaynaklarda Karatepe RES için lisansın alındığını gösteren bir tarih var: Karatepe RES Üretim Lisansı 15.06.2020 tarihinde yürürlüğe girmiş ve bu tarih belgede "onaylanan hükümler"in geçerlilik kazand”
- **GEN-AMB-006** (ambiguous): answered=True bekleniyordu=False — cevap: “Soru "Hukuki inceleme notunda ne tespit edildi?" biçiminde belirli bir belgeye atıf yapıyor ve kaynaklarda birden fazla hukuki inceleme notu var. Hangi notun kastedildiği belirsiz olduğu için, "Arazi ”
- **ANK-OPS-004** (temporal): answered=False bekleniyordu=True; eksik kaynak: ['Sigorta Yenileme Bildirimi — İşletme Dönemi']; ifade kontrolü: eksik ifade: ['09.01.2025 tarihinde sona erdi']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **ANK-NEG-002** (document): beklenen değer metinde bulunamadı — cevap: “Evet. Karatepe RES finansmanında ihracat kredi kurumu katılımı yoktur. Facility Agreement — V02 belgesinde, toplam kredinin tamamının Garanti BBVA tarafından yerel banka olarak sağlandığı ve hiçbir ih”
- **ANK-NEG-003** (document): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Kaynaklarda birden fazla kredi sözleşmesi var; soru hangi sözleşmeyi kastettiğini belirtmiyor. Tek bir sözleşmeye ait vade için kesin cevap vermek yerine, her sözleşmenin vadesini ayrı ayrı aktarıyoru”
- **ANK-NEG-004** (document): answered=False bekleniyordu=True; eksik kaynak: ['Karatepe RES Üretim Lisansı']; beklenen değer metinde bulunamadı — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **CO-NEG-005** (document): answered=False bekleniyordu=True; eksik kaynak: ['Yönetim Kurulu Kararı — Denetim Komitesi Ataması'] — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-001** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-002** (discovery): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Soru "Sözleşme var mı?" olduğu için kaynaklarda sözleşme olduğunu gösteren belgeler vardır.  Güncel durumda, kaynaklarda şu sözleşmeler yer almaktadır: - Yeşilova RES Facility Agreement (2023-YS), dur”
- **GEN-DSC-004** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-006** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-007** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-008** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “Evet, bütçe dosyası mevcut. "Bankaya Giden İşletme Bütçesi" adlı belge (DOC-YSV-FIN-006, 10.09.2026 tarihli, Yeşilova RES Enerji Üretim A.Ş. tarafından Commerzbank AG'ye iletilmiş) kaynaklarda yer alı”
- **GEN-DSC-009** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-010** (discovery): yasak kaynak geldi: ['Kızılova RES'] — cevap: “Kaynaklarda teminat belgeleri şunlardır:  - Karatepe RES Security Agreement (Share Pledge), 01.12.2021 tarihli, Karatepe RES Enerji Üretim A.Ş. hisselerinin rehni; Security Trustee lehine. [K1] [K20] ”
- **GEN-DSC-011** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Financial Model 2026']) — cevap: “Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Ankara projesinin kredi ödemeleri tablosundaki ilk ödemenin topla”
- **GEN-DSC-013** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-001-M** (discovery): güvenlik: G2: cevap var, kaynak yok; discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Evet, kaynaklarda Karatepe RES için finansal belgeler bulunuyor. Ancak kaynaklarda "finansal model" olarak adlandırılan bir belge yer almıyor. Kaynaklardaki belgeler kredi anlaşması, teminat sözleşmel”
- **GEN-DSC-006-M** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-008-M** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “Evet, bütçe dosyası var. "Bankaya Giden İşletme Bütçesi" başlıklı belge (DOC-YSV-FIN-006, 10.09.2026 tarihli, Yeşilova RES Enerji Üretim A.Ş. tarafından Commerzbank AG'ye iletilmiş) kaynaklarda yer al”
- **GEN-DSC-007-K** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.”
- **GEN-DSC-011-K** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok); soru/seçenek yok — sabit cümle tek başına — cevap: “Belgelere göre: Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım.  Excel verisine göre: Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bu”

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
- **GEN-GEN-001** (document): expect_no_answer
- **GEN-GEN-002** (document): expect_no_answer
- **GEN-GEN-003** (document): expect_no_answer
- **ANK-MIX-003** (mixed): unformattable expected_answer type: dict
- **ANK-FIN-015** (document): unformattable expected_answer type: int
- **ANK-OPS-002** (document): unformattable expected_answer type: str
- **GEN-AMB-001** (ambiguous): expect_no_answer
- **GEN-AMB-002** (ambiguous): expect_no_answer
- **GEN-AMB-003** (ambiguous): expect_no_answer
- **GEN-AMB-004** (ambiguous): expect_no_answer
- **GEN-AMB-005** (ambiguous): expect_no_answer
- **GEN-AMB-006** (ambiguous): expect_no_answer
- **GEN-TRM-001** (term_mismatch): expect_no_answer
- **GEN-TRM-002** (term_mismatch): expect_no_answer
- **GEN-TRM-004** (term_mismatch): expect_no_answer
- **GEN-TRM-005** (term_mismatch): expect_no_answer
- **CO-NEG-005** (document): unformattable expected_answer type: str
- **GEN-AMB-003-F** (document): unformattable expected_answer type: list
- **GEN-DSC-001** (discovery): expect_no_answer
- **GEN-DSC-002** (discovery): expect_no_answer
- **GEN-DSC-003** (discovery): expect_no_answer
- **GEN-DSC-004** (discovery): expect_no_answer
- **GEN-DSC-005** (discovery): expect_no_answer
- **GEN-DSC-006** (discovery): expect_no_answer
- **GEN-DSC-007** (discovery): expect_no_answer
- **GEN-DSC-008** (discovery): expect_no_answer
- **GEN-DSC-009** (discovery): expect_no_answer
- **GEN-DSC-010** (discovery): expect_no_answer
- **GEN-DSC-011** (discovery): expect_no_answer
- **GEN-DSC-012** (discovery): expect_no_answer
- **GEN-DSC-013** (discovery): expect_no_answer
- **GEN-DSC-001-M** (discovery): expect_no_answer
- **GEN-DSC-006-M** (discovery): expect_no_answer
- **GEN-DSC-008-M** (discovery): expect_no_answer
- **GEN-DSC-007-K** (discovery): expect_no_answer
- **GEN-DSC-011-K** (discovery): expect_no_answer
