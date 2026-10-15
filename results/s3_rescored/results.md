# Eval sonucu — s3_final (yeniden puanlama 2026-10-15) — 2026-10-14

`DEMO_TODAY`: 2026-10-06 · `EMBEDDINGS_ENABLED`: False · puanlayıcı v2.0

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| ambiguous | ≥%80 | ✅ %100.0 | 6/6 (toplam 6) | 0 |
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| comparison | ≥%100 | ❌ %66.7 | 2/3 (toplam 3) | 0 |
| data | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| discovery | ≥%80 | ❌ %33.3 | 6/18 (toplam 18) | 0 |
| document | ≥%80 | ❌ %74.4 | 29/39 (toplam 39) | 0 |
| hallucination | ≥%100 | ❌ %75.0 | 3/4 (toplam 4) | 0 |
| isolation | ≥%100 | ❌ %50.0 | 2/4 (toplam 4) | 0 |
| mixed | ≥%80 | ❌ %66.7 | 2/3 (toplam 3) | 0 |
| temporal | ≥%80 | ✅ %81.8 | 9/11 (toplam 11) | 0 |
| term_mismatch | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ❌ 93/99

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü
**Router düşüşü (sınıflandırma çağrısı boş/hatalı → DOCUMENT_QUERY, S0-a):** 0/99
**Keşif sayacı — beklenen belge gösterildi (tüm sorular):** 66/79
**Keşif sayacı — listede yabancı proje var (tüm sorular):** 9/75 — ANK-ISO-002, ANK-MIX-001, GEN-DSC-002, GEN-DSC-006, GEN-DSC-008, GEN-DSC-009, GEN-DSC-010, GEN-DSC-006-M, GEN-DSC-008-M
**Keşif sayacı — beklenen belge gösterildi (discovery):** 11/18
**Keşif sayacı — listede yabancı proje var (discovery):** 7/14 — GEN-DSC-002, GEN-DSC-006, GEN-DSC-008, GEN-DSC-009, GEN-DSC-010, GEN-DSC-006-M, GEN-DSC-008-M

## Başarısız sorular

- **ANK-FIN-004** (document): beklenen değer metinde bulunamadı — cevap: “Kaynaklarda Karatepe RES finansmanında ECA katılımı olmadığı yazılıdır. Facility Agreement (DOC-ANK-FIN-004, 20.06.2022) belgesinde finansman toplam 14.000.000 USD olarak yapılandırılmıştır; tüm tesis”
- **ANK-OPS-001** (temporal): gösterilen kaynak yetkili kümede değil (küme: ['Aylık Üretim Raporu — Ağustos 2026']); beklenen değer metinde bulunamadı — cevap: “Belgelere göre: Ticari işletme (COD) tarihi, Provisional Acceptance & COD Certificate belgesinde 15.10.2023 olarak yazılıdır; belge, tesisin bu tarihte ticari işletme kilometre taşına ulaştığını belir”
- **ANK-FIN-013** (temporal): beklenen değer metinde bulunamadı — cevap: “Belgelere göre: İlk zincir halkası olan Facility Agreement — Draft belgesinde (DOC-ANK-FIN-001, 15.03.2022) faiz marjı yazmamaktadır; faiz oranlarının sonraki çizelgelerde belirleneceği belirtilmiştir”
- **IZM-DEV-004** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katıl”
- **IZM-DEV-005** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı (20.08.2025); ”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katıl”
- **IZM-DEV-007** (document): gösterilen kaynak yetkili kümede değil (küme: ['Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi']) — cevap: “Kaynaklara göre Kızılova RES'te önlisans (15.01.2025) ve arazi edinimi (20.01.2025 itibarıyla) adımları tamamlanmıştır [K1]. Aynı belgeye göre ÇED süreci devam etmektedir [K1].”
- **GEN-HAL-003** (hallucination): güvenlik: G3: yasak kaynak assist'te: Karatepe RES — cevap: “Bu konuda kesin bilgi bulamadım. Karatepe RES projesine ait olduğu varsayıldı. Elimde konuyla ilgili şunlar var: Karatepe RES: Licence Amendment 01 (Kapasite Tadili) (10.02.2021) İsterseniz açayım. Şu”
- **ANK-ISO-002** (isolation): yasak kaynak geldi: ['ÇED Süreci Durum Yazısı'] — cevap: “Karatepe RES için üretim lisansı bulunmaktadır. Karatepe RES Üretim Lisansı 15.06.2020 tarihlidir ve Karatepe RES Enerji Üretim A.Ş. unvanlı tüzel kişiliğe verilmiştir [K2].  Kızılova RES için üretim ”
- **ANK-ISO-003** (isolation): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Facility Agreement', 'Facility Agreement Amendment 02']); beklenen değer metinde bulunamadı — cevap: “Belgelere göre: Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?  Excel verisine göre: Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”
- **ANK-MIX-001** (mixed): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Covenant Report (workbook)', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02']); beklenen değer metinde bulunamadı — cevap: “Belgelere göre: Bu konuda kesin bilgi bulamadım. Hangi projenin (Boztepe RES, Karatepe RES, Yeşilova RES veya Kızılova RES) güncel minimum DSCR covenant'ı soruluyor?  Excel verisine göre: Erişebildiği”
- **GEN-GEN-003** (document): answered=True bekleniyordu=False — cevap: “Covenant testinde, hesaplanan borç servisi karşılama oranı (DSCR) belirlenen asgari eşikle karşılaştırılarak uyum değerlendirilir [K33]. Bu değerlendirme, belgede yazan test hükümlerine göre yapılır [”
- **ANK-OPS-003** (document): eksik kaynak: ['Aylık Üretim Raporu — Aralık 2023'] — cevap: “Karatepe RES'in Aralık 2023 aylık üretimi 17.218 MWh'tır.”
- **ANK-COR-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı'] — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Yapı Ruhsatı (05.12.2021); Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri (25.10.2021); Lic”
- **GEN-CMP-003** (comparison): ifade kontrolü: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] — cevap: “Belgelere göre: Karatepe RES için belgelerde farklı kurulu güç değerleri yer almaktadır: Üretim lisansında tesisin toplam kurulu gücü 21 MW olarak resmi kayıtlara geçirilmiştir. [K66] ÇED Olumlu Karar”
- **ANK-NEG-002** (document): beklenen değer metinde bulunamadı — cevap: “Hayır, kaynaklarda Karatepe RES finansmanına ihracat kredi kurumu (ECA) katılımı görünmüyor. Güncel belgede finansmanın tamamının Garanti BBVA tarafından yerel banka olarak sağlandığı yazıyor [K57].  ”
- **ANK-NEG-004** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Karatepe RES Üretim Lisansı']); beklenen değer metinde bulunamadı — cevap: “Bu konuda kesin bilgi bulamadım. Hangi projenin üretim lisansı kastediliyor, Karatepe RES mi, Kızılova RES mi?”
- **GEN-DSC-002** (discovery): güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Facility Agreement Amendment 02 (15.03.2025); Facility Agreement Amendment 01 (12.01.2024); Facility Agreement (20.06.2”
- **GEN-DSC-004** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?”
- **GEN-DSC-006** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: yasak kaynak assist'te: Kızılova RES — cevap: “«ödeme planı» ifadesini kredi geri ödeme planı (Financial Model, Debt sayfası) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Garanti BBVA Faiz Belirl”
- **GEN-DSC-007** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu (05.09.2026); Aylık Üretim Raporu — Ağustos 2026 (05.09.2026); Ayl”
- **GEN-DSC-008** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “Evet, "Bankaya Giden İşletme Bütçesi" adlı bir bütçe belgesi mevcut. Belge, DOC-YSV-FIN-006 referans numarasıyla 10.09.2026 tarihinde Yeşilova RES Enerji Üretim A.Ş. tarafından Commerzbank AG'ye ileti”
- **GEN-DSC-009** (discovery): güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Facility Agreement Amendment 02 (15.03.2025); Facility Agreement Amendment 01 (12.01.2024); Facility Agreement (20.06.2”
- **GEN-DSC-010** (discovery): güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Teminat Mektubu Yenileme Bildirimi — Orman İzni (01.10.2026); Karatepe RES Security Agreement (Share Pledge) (01.12.202”
- **GEN-DSC-011** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Financial Model 2026']) — cevap: “Ankara projesinin finansal modelinde ilk kredi ödemesinin tutarı 480.700'dür; tarih bilgisi verilen sonuçta yer almıyor.”
- **GEN-DSC-006-M** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: yasak kaynak assist'te: Kızılova RES — cevap: “«ödeme planı» ifadesini kredi geri ödeme planı (Financial Model, Debt sayfası) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Garanti BBVA Faiz Belirl”
- **GEN-DSC-008-M** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “Evet. Kaynaklarda "Bankaya Giden İşletme Bütçesi" adlı belge bulunuyor. Belgenin referans numarası DOC-YSV-FIN-006 ve tarihi 10.09.2026'dır; Yeşilova RES Enerji Üretim A.Ş. tarafından Commerzbank AG'y”
- **GEN-DSC-007-K** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu (05.09.2026); Aylık Üretim Raporu — Ağustos 2026 (05.09.2026); Ayl”
- **GEN-DSC-011-K** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Belgelere göre: Hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?  Excel verisine göre: Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”

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
- **ANK-NEG-003** (document): expect_no_answer + expect_assist
- **CO-NEG-005** (document): unformattable expected_answer type: str
- **GEN-AMB-003-F** (document): expect_no_answer + expect_assist
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
