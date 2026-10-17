# Eval sonucu — n1_final (yeniden puanlama 2026-10-17) — 2026-10-16

`DEMO_TODAY`: 2026-10-06 · `EMBEDDINGS_ENABLED`: False · puanlayıcı v2.2

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| ambiguous | ≥%80 | ✅ %87.5 | 7/8 (toplam 8) | 0 |
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| comparison | ≥%100 | ❌ %33.3 | 1/3 (toplam 3) | 0 |
| data | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| discovery | ≥%80 | ❌ %31.2 | 5/16 (toplam 16) | 0 |
| document | ≥%80 | ❌ %66.7 | 26/39 (toplam 39) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| isolation | ≥%100 | ❌ %75.0 | 3/4 (toplam 4) | 0 |
| mixed | ≥%80 | ❌ %66.7 | 2/3 (toplam 3) | 0 |
| temporal | ≥%80 | ✅ %81.8 | 9/11 (toplam 11) | 0 |
| term_mismatch | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ❌ 92/99

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü
**Router düşüşü (sınıflandırma çağrısı boş/hatalı → DOCUMENT_QUERY, S0-a):** 0/99
**Keşif sayacı — beklenen belge gösterildi (tüm sorular):** 61/78
**Keşif sayacı — listede yabancı proje var (tüm sorular):** 8/71 — ANK-ISO-002, GEN-DSC-002, GEN-DSC-006, GEN-DSC-008, GEN-DSC-009, GEN-DSC-010, GEN-DSC-006-M, GEN-DSC-008-M
**Keşif sayacı — beklenen belge gösterildi (discovery):** 10/16
**Keşif sayacı — listede yabancı proje var (discovery):** 7/12 — GEN-DSC-002, GEN-DSC-006, GEN-DSC-008, GEN-DSC-009, GEN-DSC-010, GEN-DSC-006-M, GEN-DSC-008-M
**Liste kapsamı (opt-in `expected_items`, V21 R6):** 0/0 öğe (0 ölçülebilir soru)
**Sabit 'bulamadım' cümlesiyle geçen soru (answer_policy: either dahil):** 17/68 geçen — GEN-HAL-001, GEN-HAL-002, GEN-HAL-003, GEN-HAL-004, ANK-AUT-001, ANK-AUT-002, ANK-AUT-003, GEN-GEN-001, GEN-TRM-001, GEN-TRM-002, GEN-TRM-004, GEN-TRM-005, GEN-DSC-001, GEN-DSC-005, GEN-DSC-012, GEN-DSC-013, GEN-DSC-001-M

## Başarısız sorular

- **ANK-FIN-003** (document): gösterilen kaynak yetkili kümede değil (küme: ['Facility Agreement', 'Facility Agreement Amendment 02']) — cevap: “Karatepe RES'in toplam kullandırılan kredi tutarı 13.600.000 USD'dir ve tamamı yerli banka olarak Garanti BBVA tarafından sağlanmıştır [K30]. Aynı belgeye göre raporlama tarihindeki kalan bakiye 11.67”
- **ANK-FIN-005** (document): çelişen rakam: %3.25 (beklenen: ['2.9']) — cevap: “Güncel faiz marjı %2,9'dur ve taban endeks üzerine uygulanır [K1]. Kaynaklarda taban endeksin adı ya da güncel değeri yer almamaktadır.  Bu marj, Facility Agreement Amendment 02 ile önceki %3,25 seviy”
- **ANK-OPS-001** (temporal): gösterilen kaynak yetkili kümede değil (küme: ['Aylık Üretim Raporu — Ağustos 2026']); expected value text not found in answer — cevap: “Belgelere göre: Karatepe RES'in ticari işletmeye geçiş (COD) tarihi belgelerde 15.10.2023 olarak kaydedilmiştir; projenin ticari işletme kilometre taşına bu tarihte ulaştığı ve tesisin işletme fazına ”
- **ANK-FIN-011** (document): gösterilen kaynak yetkili kümede değil (küme: ['Covenant Compliance Report Q2 2026']); expected value text not found in answer — cevap: “Karatepe RES'in en son dönemine ait kalan kredi borç bakiyesi 11.671.800'dür.”
- **ANK-FIN-013** (temporal): gösterilen kaynak yetkili kümede değil (küme: ['Facility Agreement', 'Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi']); expected value text not found in answer — cevap: “Karatepe RES kredisinin en son dönemdeki faiz marjı 2.9'dur.”
- **IZM-DEV-003** (document): expected value text not found in answer — cevap: “Kaynaklara göre Kızılova RES için ÇED süreci henüz tamamlanmamış, devam etmektedir [K1]. ÇED Süreci Durum Yazısı'nda, onay süreçlerinin MNO Teknik Danışmanlık Ltd. nezdinde tamamlanması ve ardından ye”
- **IZM-DEV-004** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katıl”
- **IZM-DEV-005** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı (20.08.2025); ”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katıl”
- **ANK-ISO-003** (isolation): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Facility Agreement', 'Facility Agreement Amendment 02']); expected value text not found in answer — cevap: “Belgelere göre: Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?  Excel verisine göre: Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”
- **ANK-MIX-001** (mixed): ifade kontrolü: yasak ifade: ['Kızılova'] — cevap: “Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”
- **GEN-GEN-002** (document): either: netleştirici soru — kaynaklı cevap da sabit cümle de değil — cevap: “Hangi proje için sormak istiyorsunuz (Akyar GES, Boztepe RES, Demirci RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”
- **GEN-GEN-003** (document): either: netleştirici soru — kaynaklı cevap da sabit cümle de değil — cevap: “Hangi proje için sormak istiyorsunuz (Akyar GES, Boztepe RES, Demirci RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”
- **ANK-OPS-003** (document): eksik kaynak: ['Aylık Üretim Raporu — Aralık 2023'] — cevap: “Karatepe RES'in Aralık 2023 üretimi 17.218 MWh'tır.”
- **ANK-COR-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı'] — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Yapı Ruhsatı (05.12.2021); Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri (25.10.2021); Lic”
- **GEN-CMP-002** (comparison): expected value text not found in answer — cevap: “Projeler arası karşılaştırma bu üründe yapılmaz; değerler ayrı ayrı aşağıdadır.  Karatepe RES Üretim Lisansı'nın belge tarihi ve yürürlük tarihi 15.06.2020'dir [K22][K54].  Kızılova RES Önlisans Belge”
- **GEN-CMP-003** (comparison): ifade kontrolü: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] — cevap: “Belgelere göre: Karatepe RES'in güncel kurulu gücü 24 MW'tır [K24]. Bu değer Licence Amendment 01 (Kapasite Tadili) ile önceki 21 MW seviyesinden değiştirilmiştir [K69]. Önceki kayıtta tesisin toplam ”
- **ANK-NEG-002** (document): expected value text not found in answer — cevap: “Güncel Covenant Compliance Report Q2 2026 belgesinde, kullandırılan toplam tutarın (13.600.000 USD) tamamının Garanti BBVA tarafından yerel banka olarak sağlandığı yazıyor [K32].  Güncel olmayan (supe”
- **ANK-NEG-004** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Karatepe RES Üretim Lisansı']); expected value text not found in answer — cevap: “Hangi proje için sormak istiyorsunuz (Karatepe RES, Kızılova RES)?”
- **GEN-DSC-002** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Facility Agreement Amendment 02 (15.03.2025); Facility Agreement Amendment 01 (12.01.2024); Facility Agreement (20.06.2”
- **GEN-DSC-003** (ambiguous): ifade kontrolü: yasak ifade: ['Kızılova'] — cevap: “Hangi proje için sormak istiyorsunuz (Karatepe RES, Kızılova RES)?”
- **GEN-DSC-006** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES — cevap: “«ödeme planı» ifadesini kredi geri ödeme planı (Financial Model, Debt sayfası) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Garanti BBVA Faiz Belirl”
- **GEN-DSC-007** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu (05.09.2026); Aylık Üretim Raporu — Ağustos 2026 (05.09.2026); Ayl”
- **GEN-DSC-008** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “«bütçe» ifadesini bütçe / gerçekleşen (Budget) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Yeşilova RES: Bankaya Giden İşletme Bütçesi (10.09.2026) İsterseniz aç”
- **GEN-DSC-009** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Facility Agreement Amendment 02 (15.03.2025); Facility Agreement Amendment 01 (12.01.2024); Facility Agreement (20.06.2”
- **GEN-DSC-010** (discovery): güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: başka projenin belgesi önerildi: Yeşilova RES Annex F Raporu (2025); G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Teminat Mektubu Yenileme Bildirimi — Orman İzni (01.10.2026); Karatepe RES Security Agreement (Share Pledge) (01.12.202”
- **GEN-DSC-011** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Hangi proje için sormak istiyorsunuz (Akyar GES, Boztepe RES, Demirci RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”
- **GEN-DSC-006-M** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES — cevap: “«ödeme planı» ifadesini kredi geri ödeme planı (Financial Model, Debt sayfası) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Garanti BBVA Faiz Belirl”
- **GEN-DSC-008-M** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “«bütçe» ifadesini bütçe / gerçekleşen (Budget) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Yeşilova RES: Bankaya Giden İşletme Bütçesi (10.09.2026) İsterseniz aç”
- **GEN-DSC-007-K** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu (05.09.2026); Aylık Üretim Raporu — Ağustos 2026 (05.09.2026); Ayl”
- **GEN-DSC-011-K** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Hangi proje için sormak istiyorsunuz (Akyar GES, Boztepe RES, Demirci RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”

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
- **GEN-HAL-001** (hallucination): no_literal_expected_answer
- **GEN-HAL-002** (hallucination): no_literal_expected_answer
- **GEN-HAL-003** (hallucination): no_literal_expected_answer
- **GEN-HAL-004** (hallucination): no_literal_expected_answer
- **ANK-AUT-001** (authorization): no_literal_expected_answer
- **ANK-AUT-002** (authorization): no_literal_expected_answer
- **ANK-AUT-003** (authorization): no_literal_expected_answer
- **ANK-MIX-001** (mixed): expect_no_answer + expect_assist
- **ANK-MIX-002** (mixed): unformattable expected_answer type: dict
- **GEN-GEN-001** (document): no_literal_expected_answer
- **GEN-GEN-002** (document): no_literal_expected_answer
- **GEN-GEN-003** (document): no_literal_expected_answer
- **ANK-MIX-003** (mixed): unformattable expected_answer type: dict
- **GEN-AMB-001** (ambiguous): no_literal_expected_answer
- **GEN-AMB-002** (ambiguous): no_literal_expected_answer
- **GEN-AMB-003** (ambiguous): no_literal_expected_answer
- **GEN-AMB-004** (ambiguous): no_literal_expected_answer
- **GEN-AMB-005** (ambiguous): no_literal_expected_answer
- **GEN-AMB-006** (ambiguous): no_literal_expected_answer
- **GEN-TRM-001** (term_mismatch): no_literal_expected_answer
- **GEN-TRM-002** (term_mismatch): no_literal_expected_answer
- **GEN-TRM-004** (term_mismatch): no_literal_expected_answer
- **GEN-TRM-005** (term_mismatch): no_literal_expected_answer
- **ANK-NEG-003** (document): expect_no_answer + expect_assist
- **CO-NEG-005** (document): unformattable expected_answer type: str
- **GEN-AMB-003-F** (document): expect_no_answer + expect_assist
- **GEN-DSC-001** (discovery): no_literal_expected_answer
- **GEN-DSC-002** (discovery): no_literal_expected_answer
- **GEN-DSC-003** (ambiguous): no_literal_expected_answer
- **GEN-DSC-004** (ambiguous): no_literal_expected_answer
- **GEN-DSC-005** (discovery): no_literal_expected_answer
- **GEN-DSC-006** (discovery): no_literal_expected_answer
- **GEN-DSC-007** (discovery): no_literal_expected_answer
- **GEN-DSC-008** (discovery): no_literal_expected_answer
- **GEN-DSC-009** (discovery): no_literal_expected_answer
- **GEN-DSC-010** (discovery): no_literal_expected_answer
- **GEN-DSC-011** (discovery): no_literal_expected_answer
- **GEN-DSC-012** (discovery): no_literal_expected_answer
- **GEN-DSC-013** (discovery): no_literal_expected_answer
- **GEN-DSC-001-M** (discovery): no_literal_expected_answer
- **GEN-DSC-006-M** (discovery): no_literal_expected_answer
- **GEN-DSC-008-M** (discovery): no_literal_expected_answer
- **GEN-DSC-007-K** (discovery): no_literal_expected_answer
- **GEN-DSC-011-K** (discovery): no_literal_expected_answer
