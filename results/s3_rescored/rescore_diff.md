# Yeniden puanlama — s3_final (2026-10-14) → puanlayıcı v2.0

**Önce 59/99 → sonra 70/99** (LLM çağrısı yok; aynı ham cevaplar).

## Kategori tablosu (önce → sonra)

| Kategori | Eşik | Önce | Sonra | Eşik |
|---|---|---|---|---|
| ambiguous | ≥%80 | 1/6 | 6/6 | ✅ |
| authorization | ≥%100 | 3/3 | 3/3 | ✅ |
| comparison | ≥%100 | 2/3 | 2/3 | ❌ |
| data | ≥%80 | 4/4 | 4/4 | ✅ |
| discovery | ≥%80 | 5/18 | 6/18 | ❌ |
| document | ≥%80 | 26/39 | 29/39 | ❌ |
| hallucination | ≥%100 | 2/4 | 3/4 | ❌ |
| isolation | ≥%100 | 1/4 | 2/4 | ❌ |
| mixed | ≥%80 | 2/3 | 2/3 | ❌ |
| temporal | ≥%80 | 9/11 | 9/11 | ✅ |
| term_mismatch | ≥%80 | 4/4 | 4/4 | ✅ |
| **TOPLAM** | ≥%75 | **59/99** | **70/99** | ❌ |

Güvenlik G1–G3: önce 80/99 → sonra 93/99

## Değişen sorular (hangi madde)

| Soru | Kategori | Önce | Sonra | Madde | Not |
|---|---|---|---|---|---|
| GEN-HAL-004 | hallucination | ❌ | ✅ | A4 |  |
| ANK-ISO-003 | isolation | ❌ | ❌ | A1 | answered=False, beklenen True; kaynak kümede değil (küme ['Facility Agreement', 'Facility Agreement Amendment 02']); beklenen değer metinde yok |
| IZM-ISO-004 | isolation | ❌ | ✅ | A4, B |  |
| GEN-GEN-002 | document | ❌ | ✅ | A1 |  |
| GEN-CMP-003 | comparison | ❌ | ❌ | A5 | ifade: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] |
| GEN-AMB-002 | ambiguous | ❌ | ✅ | A1 |  |
| GEN-AMB-003 | ambiguous | ❌ | ✅ | A1 |  |
| GEN-AMB-004 | ambiguous | ❌ | ✅ | A1 |  |
| GEN-AMB-005 | ambiguous | ❌ | ✅ | A1 |  |
| GEN-AMB-006 | ambiguous | ❌ | ✅ | A1 |  |
| ANK-NEG-003 | document | ❌ | ✅ | A1, A3 |  |
| GEN-AMB-003-F | document | ❌ | ✅ | A1 |  |
| GEN-DSC-004 | discovery | ❌ | ❌ | A1 | discovery: beklenen belge gösterilmedi (hiç belge yok) |
| GEN-DSC-001-M | discovery | ❌ | ✅ | A2 |  |
| GEN-DSC-006-M | discovery | ❌ | ❌ | A2 | güvenlik: G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-011-K | discovery | ❌ | ❌ | A1 | discovery: beklenen belge gösterilmedi (hiç belge yok) |

Madde başına etkilenen soru: A1 (G2 — yalnız netleştirme sorusu sabit cümle istemez): 11, A2 (G3 görünürlük DB'den (finans_mudur)): 2, A3 (expect_no_answer + expect_assist → değer kontrolü atlanır): 1, A4 (yasak kaynak belge kimliğiyle (tür eşleşmesi kalktı)): 2, A5 (kaynak beklentisi: yetkili kaynak kümesi): 1, B (questions.json v13 (IZM-ISO-004 / GEN-HAL-004)): 1

## Hâlâ kalan kayıplar (huni girdisi)

| Soru | Kategori | Sebep |
|---|---|---|
| ANK-FIN-004 | document | beklenen değer metinde yok |
| ANK-OPS-001 | temporal | kaynak kümede değil (küme ['Aylık Üretim Raporu — Ağustos 2026']); beklenen değer metinde yok |
| ANK-FIN-013 | temporal | beklenen değer metinde yok |
| IZM-DEV-004 | document | answered=False, beklenen True; kaynak kümede değil (küme ['ÇED Süreci Durum Yazısı']) |
| IZM-DEV-005 | document | answered=False, beklenen True; kaynak kümede değil (küme ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']) |
| IZM-DEV-006 | document | answered=False, beklenen True; kaynak kümede değil (küme ['ÇED Süreci Durum Yazısı']) |
| IZM-DEV-007 | document | kaynak kümede değil (küme ['Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi']) |
| GEN-HAL-003 | hallucination | güvenlik: G3: yasak kaynak assist'te: Karatepe RES |
| ANK-ISO-002 | isolation | yasak kaynak ['ÇED Süreci Durum Yazısı'] |
| ANK-ISO-003 | isolation | answered=False, beklenen True; kaynak kümede değil (küme ['Facility Agreement', 'Facility Agreement Amendment 02']); beklenen değer metinde yok |
| ANK-MIX-001 | mixed | answered=False, beklenen True; kaynak kümede değil (küme ['Covenant Report (workbook)', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02']); beklenen değer metinde yok |
| GEN-GEN-003 | document | answered=True, beklenen False |
| ANK-OPS-003 | document | eksik kaynak ['Aylık Üretim Raporu — Aralık 2023'] |
| ANK-COR-001 | document | answered=False, beklenen True; eksik kaynak ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı'] |
| GEN-CMP-003 | comparison | ifade: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] |
| ANK-NEG-002 | document | beklenen değer metinde yok |
| ANK-NEG-004 | document | answered=False, beklenen True; kaynak kümede değil (küme ['Karatepe RES Üretim Lisansı']); beklenen değer metinde yok |
| GEN-DSC-002 | discovery | güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-004 | discovery | discovery: beklenen belge gösterilmedi (hiç belge yok) |
| GEN-DSC-006 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-007 | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) |
| GEN-DSC-008 | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) |
| GEN-DSC-009 | discovery | güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-010 | discovery | güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-011 | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Financial Model 2026']) |
| GEN-DSC-006-M | discovery | güvenlik: G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-008-M | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) |
| GEN-DSC-007-K | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) |
| GEN-DSC-011-K | discovery | discovery: beklenen belge gösterilmedi (hiç belge yok) |

## Yetkili kaynak kümesi — kontrolör onayına (A5)

Türetme: `required_sources` (tür → sorunun kendi projesinin canlı belgeleri) + ledger'da `key_facts` ile aynı yolu taşıyan belgeler; `draft` hiç, `superseded` yalnız canlı taşıyıcı yoksa; belgeyi adıyla soran soru ("… raporuna göre") tam belge şartında.

| Soru | Kural | Küme | Gösterilen | Not |
|---|---|---|---|---|
| ANK-FIN-005 | küme (type 'Facility Agreement' → ['Facility Agreement Amendment 02']; ankara_res.project.finance.interest.margin_pct.current.value: carriers ['Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi'] → kept ['Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi']) | ['Facility Agreement', 'Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi'] | ['Facility Agreement', 'Facility Agreement Amendment 02', 'Garanti BBVA Faiz Belirleme Bildirimi'] | ✅ |
| ANK-FIN-011 | küme (ankara_res.project.finance.outstanding_debt_as_of_demo_today.value: carriers ['Covenant Compliance Report Q2 2026'] → kept ['Covenant Compliance Report Q2 2026']) | ['Covenant Compliance Report Q2 2026'] | ['Covenant Compliance Report Q2 2026', 'Facility Agreement', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02', 'Financial Model 2026', 'Garanti BBVA Faiz Belirleme Bildirimi', 'Karatepe RES Drawdown Notice — Tranche 1'] | ✅ |
| ANK-FIN-014 | tam belge (question names the document) | ['Karatepe RES Covenant Compliance Report — Q4 2024'] | ['Covenant Report (workbook)', 'Karatepe RES Covenant Compliance Report — Q4 2024'] | ✅ |
| ANK-OPS-003 | tam belge (question names the document) | ['Aylık Üretim Raporu — Aralık 2023'] | ['Monthly Production 2026'] | ❌ eksik kaynak ['Aylık Üretim Raporu — Aralık 2023'] |
| IZM-DEV-007 | küme (izmir_res.project.development.permits_completed: carriers [] → kept []) | ['Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi'] | ['ÇED Süreci Durum Yazısı'] | ❌ kaynak kümede değil (küme ['Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi']) |
