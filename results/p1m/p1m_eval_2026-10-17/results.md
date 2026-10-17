# Eval sonucu — p1m_eval — 2026-10-17

`DEMO_TODAY`: 2026-10-06 · `EMBEDDINGS_ENABLED`: False · puanlayıcı v2.2

## Kategori bazlı sonuç

| Kategori | Eşik | Sonuç | Geçen/Değerlendirilen | Hata |
|---|---|---|---|---|
| ambiguous | ≥%80 | ✅ %100.0 | 9/9 (toplam 9) | 0 |
| authorization | ≥%100 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| comparison | ≥%100 | ❌ %66.7 | 2/3 (toplam 3) | 0 |
| data | ≥%80 | ❌ %75.0 | 3/4 (toplam 4) | 0 |
| discovery | ≥%80 | ❌ %31.2 | 5/16 (toplam 16) | 0 |
| document | ≥%80 | ❌ %71.8 | 28/39 (toplam 39) | 0 |
| hallucination | ≥%100 | ✅ %100.0 | 4/4 (toplam 4) | 0 |
| isolation | ≥%100 | ❌ %75.0 | 3/4 (toplam 4) | 0 |
| mixed | ≥%80 | ✅ %100.0 | 3/3 (toplam 3) | 0 |
| temporal | ≥%80 | ❌ %72.7 | 8/11 (toplam 11) | 0 |
| term_mismatch | ≥%80 | ✅ %100.0 | 4/4 (toplam 4) | 0 |

**Güvenlik değişmezleri G1–G3 (ADR-027, %100 zorunlu):** ❌ 93/100

**Genel sonuç:** ❌ en az bir kategori eşiği altında ya da bir güvenlik değişmezi düştü
**Router düşüşü (sınıflandırma çağrısı boş/hatalı → DOCUMENT_QUERY, S0-a):** 0/100
**Keşif sayacı — beklenen belge gösterildi (tüm sorular):** 62/78
**Keşif sayacı — listede yabancı proje var (tüm sorular):** 8/71 — ANK-ISO-002, GEN-DSC-002, GEN-DSC-006, GEN-DSC-008, GEN-DSC-009, GEN-DSC-010, GEN-DSC-006-M, GEN-DSC-008-M
**Keşif sayacı — beklenen belge gösterildi (discovery):** 10/16
**Keşif sayacı — listede yabancı proje var (discovery):** 7/12 — GEN-DSC-002, GEN-DSC-006, GEN-DSC-008, GEN-DSC-009, GEN-DSC-010, GEN-DSC-006-M, GEN-DSC-008-M
**Liste kapsamı (opt-in `expected_items`, V21 R6):** 0/0 öğe (0 ölçülebilir soru)
**Sabit 'bulamadım' cümlesiyle geçen soru (answer_policy: either dahil):** 17/72 geçen — GEN-HAL-001, GEN-HAL-002, GEN-HAL-003, GEN-HAL-004, ANK-AUT-001, ANK-AUT-002, ANK-AUT-003, GEN-GEN-001, GEN-TRM-001, GEN-TRM-002, GEN-TRM-004, GEN-TRM-005, GEN-DSC-001, GEN-DSC-005, GEN-DSC-012, GEN-DSC-013, GEN-DSC-001-M

## Başarısız sorular

- **ANK-FIN-005** (document): biçim (F-8, V21 R2): yüzde biçimi — cevap: “Güncel marj %2,9'dur; bu oran Garanti BBVA Faiz Belirleme Bildirimi'nde (25.09.2026) teyit edilmektedir [K1]. Bu değer Facility Agreement Amendment 02 ile önceki 3,25% seviyesinden değiştirilmiştir [K”
- **ANK-FIN-007** (temporal): gösterilen kaynak yetkili kümede değil (küme: ['Facility Agreement', 'Facility Agreement Amendment 02']) — cevap: “İlk halka olan Facility Agreement — Draft (DOC-ANK-FIN-001, 15.03.2022) belgesinde minimum DSCR 1,25x olarak yazıyor: borrower, kredinin aktif yaşam döngüsü boyunca minimum debt service coverage ratio”
- **ANK-OPS-001** (temporal): gösterilen kaynak yetkili kümede değil (küme: ['Aylık Üretim Raporu — Ağustos 2026']); expected value text not found in answer — cevap: “Belgelere göre: Karatepe RES'in işletmeye alınma tarihi (COD) 15.10.2023'tür. Belgede, proje Karatepe RES Enerji Üretim A.Ş. tarafından geliştirilmiş ve bu tarihte ticari işletme aşamasına ulaşmıştır ”
- **ANK-FIN-010** (data): gösterilen kaynak yetkili kümede değil (küme: ['Covenant Report (workbook)']) — cevap: “Belgelere göre: Güncel belgeye göre covenant testindeki minimum borç servis karşılama oranı (DSCR) 1,20x'tir ve 15.03.2025 tarihinden itibaren geçerlidir [K28].  Bu değer Facility Agreement Amendment ”
- **ANK-FIN-013** (temporal): expected value text not found in answer; biçim (F-8, V21 R2): yüzde biçimi — cevap: “Belgelere göre: İlk belirlenen marj, Facility Agreement belgesinde (20.06.2022) "baseline index plus 3.25%" olarak yazılmıştır [K43].  Bu değer Facility Agreement Amendment 02 ile önceki 3.25% seviyes”
- **IZM-DEV-004** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katıl”
- **IZM-DEV-005** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı (20.08.2025); ”
- **IZM-DEV-006** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['ÇED Süreci Durum Yazısı']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Kızılova RES: ÇED Süreci Durum Yazısı (27.08.2026); Askeri Yasak Bölgeler Ön Görüş Talebi (01.09.2025); Kamu Duyurusu ve Halkın Katıl”
- **IZM-DEV-007** (document): gösterilen kaynak yetkili kümede değil (küme: ['Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi']) — cevap: “Kaynaklara göre tamamlanmış adımlar şunlardır: - Önlisans, 15.01.2025 tarihinde tamamlanmıştır [K1]. - Arazi edinimi, 20.01.2025 itibarıyla tamamlanmıştır [K1]. - Kamu duyurusu ve halkın katılımı topl”
- **ANK-ISO-003** (isolation): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Facility Agreement', 'Facility Agreement Amendment 02']); expected value text not found in answer — cevap: “Belgelere göre: Hangi projeyi kastediyorsunuz: Karatepe RES mi, Yeşilova RES mi?  Excel verisine göre: Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım.”
- **GEN-GEN-002** (document): either: netleştirici soru — kaynaklı cevap da sabit cümle de değil — cevap: “Hangi proje için sormak istiyorsunuz (Karatepe RES, Kızılova RES)?”
- **GEN-GEN-003** (document): either: netleştirici soru — kaynaklı cevap da sabit cümle de değil — cevap: “Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”
- **ANK-OPS-003** (document): eksik kaynak: ['Aylık Üretim Raporu — Aralık 2023'] — cevap: “Karatepe RES'in Aralık 2023 aylık üretimi 17.218 MWh'tır.”
- **ANK-COR-001** (document): answered=False bekleniyordu=True; eksik kaynak: ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı'] — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Yapı Ruhsatı (05.12.2021); Sözleşme Uyum Değerlendirmesi — EPC ve Finansman Sözleşmeleri (25.10.2021); Lic”
- **GEN-CMP-003** (comparison): ifade kontrolü: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] — cevap: “Belgelere göre: **Karatepe RES:** Belgelerde iki farklı değer geçmektedir. Üretim Lisansı'nda tesisin toplam kurulu gücü 21 MW olarak kaydedilmiştir [K66]. Geçici Kabul ve COD Sertifikası'nda tesisin ”
- **ANK-NEG-002** (document): expected value text not found in answer — cevap: “Kaynaklara göre Karatepe RES finansmanında ihracat kredi kurumu (ECA) katılımı yoktur. Tesisin tamamı Garanti BBVA tarafından yerel banka olarak sağlanmakta olup bu yapının parçası olarak ayrı bir ECA”
- **ANK-NEG-004** (document): answered=False bekleniyordu=True; gösterilen kaynak yetkili kümede değil (küme: ['Karatepe RES Üretim Lisansı']); expected value text not found in answer — cevap: “Hangi proje için sormak istiyorsunuz (Karatepe RES, Kızılova RES)?”
- **GEN-DSC-002** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Facility Agreement Amendment 02 (15.03.2025); Facility Agreement Amendment 01 (12.01.2024); Facility Agreement (20.06.2”
- **GEN-DSC-006** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES — cevap: “«ödeme planı» ifadesini kredi geri ödeme planı (Financial Model, Debt sayfası) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Garanti BBVA Faiz Belirl”
- **GEN-DSC-007** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu (05.09.2026); Aylık Üretim Raporu — Ağustos 2026 (05.09.2026); Ayl”
- **GEN-DSC-008** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “«bütçe» ifadesini bütçe / gerçekleşen (Budget) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Yeşilova RES: Bankaya Giden İşletme Bütçesi (10.09.2026) İsterseniz aç”
- **GEN-DSC-009** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Facility Agreement Amendment 02 (15.03.2025); Facility Agreement Amendment 01 (12.01.2024); Facility Agreement (20.06.2”
- **GEN-DSC-010** (discovery): güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: başka projenin belgesi önerildi: Yeşilova RES Annex F Raporu (2025); G3: yasak kaynak assist'te: Kızılova RES — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Teminat Mektubu Yenileme Bildirimi — Orman İzni (01.10.2026); Karatepe RES Security Agreement (Share Pledge) (01.12.202”
- **GEN-DSC-011** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”
- **GEN-DSC-006-M** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES — cevap: “«ödeme planı» ifadesini kredi geri ödeme planı (Financial Model, Debt sayfası) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Garanti BBVA Faiz Belirl”
- **GEN-DSC-008-M** (discovery): güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) — cevap: “«bütçe» ifadesini bütçe / gerçekleşen (Budget) olarak anladım. Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Yeşilova RES: Bankaya Giden İşletme Bütçesi (10.09.2026) İsterseniz aç”
- **GEN-DSC-007-K** (discovery): discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) — cevap: “Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu (05.09.2026); Aylık Üretim Raporu — Ağustos 2026 (05.09.2026); Ayl”
- **GEN-DSC-011-K** (discovery): discovery: beklenen belge gösterilmedi (hiç belge yok) — cevap: “Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Kızılova RES, Yeşilova RES)?”

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
- **GEN-DSC-003-F** (ambiguous): no_literal_expected_answer
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
