# Yeniden puanlama — m1_final (2026-10-16) → puanlayıcı v2.1

**Önce 71/99 → sonra 70/99** (LLM çağrısı yok; aynı ham cevaplar).

## Kategori tablosu (önce → sonra)

| Kategori | Eşik | Önce | Sonra | Eşik |
|---|---|---|---|---|
| ambiguous | ≥%80 | 6/6 | 7/8 | ✅ |
| authorization | ≥%100 | 3/3 | 3/3 | ✅ |
| comparison | ≥%100 | 2/3 | 2/3 | ❌ |
| data | ≥%80 | 3/4 | 3/4 | ❌ |
| discovery | ≥%80 | 7/18 | 6/16 | ❌ |
| document | ≥%80 | 28/39 | 27/39 | ❌ |
| hallucination | ≥%100 | 4/4 | 4/4 | ✅ |
| isolation | ≥%100 | 2/4 | 3/4 | ❌ |
| mixed | ≥%80 | 2/3 | 2/3 | ❌ |
| temporal | ≥%80 | 10/11 | 9/11 | ✅ |
| term_mismatch | ≥%80 | 4/4 | 4/4 | ✅ |
| **TOPLAM** | ≥%75 | **71/99** | **70/99** | ❌ |

Güvenlik G1–G3: önce 94/99 → sonra 92/99

## Değişen sorular (hangi madde)

| Soru | Kategori | Önce | Sonra | Madde | Not |
|---|---|---|---|---|---|
| ANK-FIN-011 | document | ✅ | ❌ | R2 | biçim (V21 R2): yüzde biçimi |
| ANK-FIN-013 | temporal | ✅ | ❌ | R1 | çelişen rakam: %6.5 (beklenen: ['2.9', '3.25']) |
| ANK-ISO-002 | isolation | ❌ | ✅ | A4 |  |
| ANK-MIX-001 | mixed | ❌ | ❌ | A3, B | answered=True, beklenen False; ifade: eksik ifade: ['Boztepe', 'Karatepe', 'Yeşilova'] |
| ANK-FIN-015 | document | ✅ | ✅ | R9 |  |
| ANK-OPS-002 | document | ✅ | ✅ | R9 |  |
| GEN-DSC-003 | ambiguous | ✅ | ❌ | B | answered=True, beklenen False |
| GEN-DSC-004 | ambiguous | ❌ | ✅ | B |  |
| GEN-DSC-008 | discovery | ❌ | ❌ | R7 | güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) |
| GEN-DSC-008-M | discovery | ❌ | ❌ | R7 | güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) |

Madde başına etkilenen soru: A3 (expect_no_answer + expect_assist → değer kontrolü atlanır): 1, A4 (yasak kaynak belge kimliğiyle (tür eşleşmesi kalktı)): 1, B (questions.json v13 (IZM-ISO-004 / GEN-HAL-004)): 3, R1 (V21 — çelişen rakam (kavram-sınırlı)): 1, R2 (V21 — F-8 biçim hatası artık düşürür): 1, R7 (V21 — G3 tüm projeler): 2, R9 (V21 — ledger biçimlendirici genişledi): 2

## Hâlâ kalan kayıplar (huni girdisi)

| Soru | Kategori | Sebep |
|---|---|---|
| ANK-FIN-004 | document | expected value text not found in answer |
| ANK-FIN-005 | document | answered=False, beklenen True; kaynak kümede değil (küme ['Facility Agreement', 'Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi']); expected value text not found in answer |
| ANK-OPS-001 | temporal | kaynak kümede değil (küme ['Aylık Üretim Raporu — Ağustos 2026']); expected value text not found in answer |
| ANK-FIN-010 | data | kaynak kümede değil (küme ['Covenant Report (workbook)']) |
| ANK-FIN-011 | document | biçim (V21 R2): yüzde biçimi |
| ANK-FIN-013 | temporal | çelişen rakam: %6.5 (beklenen: ['2.9', '3.25']) |
| IZM-DEV-004 | document | answered=False, beklenen True; kaynak kümede değil (küme ['ÇED Süreci Durum Yazısı']) |
| IZM-DEV-005 | document | answered=False, beklenen True; kaynak kümede değil (küme ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']) |
| IZM-DEV-006 | document | answered=False, beklenen True; kaynak kümede değil (küme ['ÇED Süreci Durum Yazısı']) |
| ANK-ISO-003 | isolation | answered=False, beklenen True; kaynak kümede değil (küme ['Facility Agreement', 'Facility Agreement Amendment 02']); expected value text not found in answer |
| ANK-MIX-001 | mixed | answered=True, beklenen False; ifade: eksik ifade: ['Boztepe', 'Karatepe', 'Yeşilova'] |
| GEN-GEN-003 | document | answered=True, beklenen False |
| ANK-FIN-014 | document | eksik kaynak ['Karatepe RES Covenant Compliance Report — Q4 2024'] |
| ANK-OPS-003 | document | eksik kaynak ['Aylık Üretim Raporu — Aralık 2023'] |
| ANK-COR-001 | document | answered=False, beklenen True; eksik kaynak ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı'] |
| GEN-CMP-003 | comparison | ifade: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] |
| ANK-NEG-002 | document | expected value text not found in answer |
| ANK-NEG-004 | document | answered=False, beklenen True; kaynak kümede değil (küme ['Karatepe RES Üretim Lisansı']); expected value text not found in answer |
| GEN-DSC-002 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-003 | ambiguous | answered=True, beklenen False |
| GEN-DSC-006 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-007 | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) |
| GEN-DSC-008 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) |
| GEN-DSC-009 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-010 | discovery | güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: başka projenin belgesi önerildi: Yeşilova RES Annex F Raporu (2025); G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-011 | discovery | discovery: beklenen belge gösterilmedi (hiç belge yok) |
| GEN-DSC-006-M | discovery | güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-008-M | discovery | güvenlik: G3: başka projenin belgesi önerildi: Bankaya Giden İşletme Bütçesi; discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) |
| GEN-DSC-007-K | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) |

## Yetkili kaynak kümesi — kontrolör onayına (A5)

Türetme: `required_sources` (tür → sorunun kendi projesinin canlı belgeleri) + ledger'da `key_facts` ile aynı yolu taşıyan belgeler; `draft` hiç, `superseded` yalnız canlı taşıyıcı yoksa; belgeyi adıyla soran soru ("… raporuna göre") tam belge şartında.

| Soru | Kural | Küme | Gösterilen | Not |
|---|---|---|---|---|
| ANK-FIN-005 | küme (type 'Facility Agreement' → ['Facility Agreement Amendment 02']; ankara_res.project.finance.interest.margin_pct.current.value: carriers ['Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi'] → kept ['Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi']) | ['Facility Agreement', 'Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi'] | [] | ❌ answered=False, beklenen True; kaynak kümede değil (küme ['Facility Agreement', 'Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi']); expected value text not found in answer |
| ANK-FIN-011 | küme (ankara_res.project.finance.outstanding_debt_as_of_demo_today.value: carriers ['Covenant Compliance Report Q2 2026'] → kept ['Covenant Compliance Report Q2 2026']) | ['Covenant Compliance Report Q2 2026'] | ['Covenant Compliance Report Q2 2026', 'Facility Agreement', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02', 'Financial Model 2026', 'Garanti BBVA Faiz Belirleme Bildirimi'] | ❌ biçim (V21 R2): yüzde biçimi |
| ANK-FIN-014 | tam belge (question names the document) | ['Karatepe RES Covenant Compliance Report — Q4 2024'] | ['Covenant Report (workbook)'] | ❌ eksik kaynak ['Karatepe RES Covenant Compliance Report — Q4 2024'] |
| ANK-OPS-003 | tam belge (question names the document) | ['Aylık Üretim Raporu — Aralık 2023'] | ['Monthly Production 2026'] | ❌ eksik kaynak ['Aylık Üretim Raporu — Aralık 2023'] |
| IZM-DEV-007 | küme (izmir_res.project.development.permits_completed: carriers [] → kept []) | ['Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi'] | ['Arazi Edinim Durum Raporu', 'Askeri Yasak Bölgeler Ön Görüş Talebi', 'Kamu Duyurusu ve Halkın Katılımı Toplantısı Tutanağı', 'Kızılova RES Bağlantı Görüşü Başvurusu', 'Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı'] | ✅ |
