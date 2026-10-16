# Yeniden puanlama — s3_final (yeniden puanlama 2026-10-15) (2026-10-14) → puanlayıcı v2.1

**Önce 70/99 → sonra 70/99** (LLM çağrısı yok; aynı ham cevaplar).

## Kategori tablosu (önce → sonra)

| Kategori | Eşik | Önce | Sonra | Eşik |
|---|---|---|---|---|
| ambiguous | ≥%80 | 6/6 | 6/6 | ✅ |
| authorization | ≥%100 | 3/3 | 3/3 | ✅ |
| comparison | ≥%100 | 2/3 | 2/3 | ❌ |
| data | ≥%80 | 4/4 | 4/4 | ✅ |
| discovery | ≥%80 | 6/18 | 5/18 | ❌ |
| document | ≥%80 | 29/39 | 29/39 | ❌ |
| hallucination | ≥%100 | 3/4 | 3/4 | ❌ |
| isolation | ≥%100 | 2/4 | 3/4 | ❌ |
| mixed | ≥%80 | 2/3 | 2/3 | ❌ |
| temporal | ≥%80 | 9/11 | 9/11 | ✅ |
| term_mismatch | ≥%80 | 4/4 | 4/4 | ✅ |
| **TOPLAM** | ≥%75 | **70/99** | **70/99** | ❌ |

Güvenlik G1–G3: önce 93/99 → sonra 92/99

## Değişen sorular (hangi madde)

| Soru | Kategori | Önce | Sonra | Madde | Not |
|---|---|---|---|---|---|
| ANK-FIN-013 | temporal | ❌ | ❌ | R2 | expected value text not found in answer; biçim (V21 R2): yüzde biçimi |
| ANK-ISO-002 | isolation | ❌ | ✅ | A4 |  |
| ANK-MIX-001 | mixed | ❌ | ❌ | R4, R7 | answered=False, beklenen True; kaynak kümede değil (küme ['Covenant Report (workbook)', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02']); expected value text not found in answer; güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Boztepe RES — Covenant Compliance Report Q3 2026; G3: başka projenin belgesi önerildi: Yeşilova RES Annex F Raporu (2025); MIXED tamlık (V21 R4): belge yarısı boş/sabit cümle |
| ANK-FIN-015 | document | ✅ | ✅ | R9 |  |
| ANK-OPS-002 | document | ✅ | ✅ | R9 |  |
| GEN-DSC-001 | discovery | ✅ | ❌ | R2 | biçim (V21 R2): gruplanmamış sayı |

Madde başına etkilenen soru: A4 (yasak kaynak belge kimliğiyle (tür eşleşmesi kalktı)): 1, R2 (V21 — F-8 biçim hatası artık düşürür): 2, R4 (V21 — MIXED tamlık (T-1)): 1, R7 (V21 — G3 tüm projeler): 1, R9 (V21 — ledger biçimlendirici genişledi): 2

## Hâlâ kalan kayıplar (huni girdisi)

| Soru | Kategori | Sebep |
|---|---|---|
| ANK-FIN-004 | document | expected value text not found in answer |
| ANK-OPS-001 | temporal | kaynak kümede değil (küme ['Aylık Üretim Raporu — Ağustos 2026']); expected value text not found in answer |
| ANK-FIN-013 | temporal | expected value text not found in answer; biçim (V21 R2): yüzde biçimi |
| IZM-DEV-004 | document | answered=False, beklenen True; kaynak kümede değil (küme ['ÇED Süreci Durum Yazısı']) |
| IZM-DEV-005 | document | answered=False, beklenen True; kaynak kümede değil (küme ['Kızılova RES Önlisans Belgesi', 'ÇED Süreci Durum Yazısı']) |
| IZM-DEV-006 | document | answered=False, beklenen True; kaynak kümede değil (küme ['ÇED Süreci Durum Yazısı']) |
| IZM-DEV-007 | document | kaynak kümede değil (küme ['Arazi Edinim Durum Raporu', 'Kızılova RES Önlisans Belgesi']) |
| GEN-HAL-003 | hallucination | güvenlik: G3: yasak kaynak assist'te: Karatepe RES |
| ANK-ISO-003 | isolation | answered=False, beklenen True; kaynak kümede değil (küme ['Facility Agreement', 'Facility Agreement Amendment 02']); expected value text not found in answer |
| ANK-MIX-001 | mixed | answered=False, beklenen True; kaynak kümede değil (küme ['Covenant Report (workbook)', 'Facility Agreement Amendment 01', 'Facility Agreement Amendment 02']); expected value text not found in answer; güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Boztepe RES — Covenant Compliance Report Q3 2026; G3: başka projenin belgesi önerildi: Yeşilova RES Annex F Raporu (2025); MIXED tamlık (V21 R4): belge yarısı boş/sabit cümle |
| GEN-GEN-003 | document | answered=True, beklenen False |
| ANK-OPS-003 | document | eksik kaynak ['Aylık Üretim Raporu — Aralık 2023'] |
| ANK-COR-001 | document | answered=False, beklenen True; eksik kaynak ['Pay Sahipleri Kararı — GHI Yatırım A.Ş. Ortaklık Onayı'] |
| GEN-CMP-003 | comparison | ifade: eksik ifade: ['Projeler arası karşılaştırma bu üründe yapılmaz'] |
| ANK-NEG-002 | document | expected value text not found in answer |
| ANK-NEG-004 | document | answered=False, beklenen True; kaynak kümede değil (küme ['Karatepe RES Üretim Lisansı']); expected value text not found in answer |
| GEN-DSC-001 | discovery | biçim (V21 R2): gruplanmamış sayı |
| GEN-DSC-002 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-004 | discovery | discovery: beklenen belge gösterilmedi (hiç belge yok) |
| GEN-DSC-006 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-007 | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Arazi Edinim Durum Raporu', 'Aylık Üretim Raporu — Aralık 2023', 'Aylık Üretim Raporu — Ağustos 2026', 'Aylık Üretim Raporu — Haziran 2025', 'Bakım Raporu — Temmuz 2024 (Türbin T-07 Arızası)', "Karatepe RES Independent Engineer's Completion Report", 'Karatepe RES Kullanılabilirlik Garantisi Uyum Raporu']) |
| GEN-DSC-008 | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Bankaya Giden İşletme Bütçesi']) |
| GEN-DSC-009 | discovery | güvenlik: G3: başka projenin belgesi önerildi: Boztepe RES Facility Agreement (2024-BZ); G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-010 | discovery | güvenlik: G3: başka projenin belgesi önerildi: EPC Avans Teminat Mektubu; G3: başka projenin belgesi önerildi: Yeşilova RES Annex F Raporu (2025); G3: yasak kaynak assist'te: Kızılova RES |
| GEN-DSC-011 | discovery | discovery: beklenen belge gösterilmedi (gösterilen: ['Financial Model 2026']) |
| GEN-DSC-006-M | discovery | güvenlik: G3: başka projenin belgesi önerildi: Anapara Geri Ödeme Planı (84 Taksit); G3: başka projenin belgesi önerildi: Ödeme Planı — Güncel; G3: başka projenin belgesi önerildi: Avans Faturası — ABC2026000000184; G3: başka projenin belgesi önerildi: Taksit #11 Banka Faiz Bildirimi; G3: başka projenin belgesi önerildi: Aylık Faiz Bildirimi — Ekim 2026 Taksidi; G3: yasak kaynak assist'te: Kızılova RES |
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
