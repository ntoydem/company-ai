# M1 — soru soru ayrıntı (koşu `results/m1_final_2026-10-16`, puanlayıcı v2.0, taban `results/s3_rescored` 70/99)

Tüm saatler UTC. Kaynak: `results/m1_final_2026-10-16/results.json`, `logs/m1_audit.jsonl` (99 satır, eval DB), `logs/m1_eval_backend.log` (koşu boyunca `docker logs -f`), `logs/m1_analysis.txt` / `logs/m1_analysis2.txt` (scratchpad betiği çıktısı, LLM'siz).

## 1. Kategori tablosu — M1 ↔ S3 yeniden puanlama (aynı puanlayıcı, farklı kod)

| Kategori | Eşik | **M1** | % | S3r | Δ | answered=false (beklenen) |
|---|---|---|---|---|---|---|
| ambiguous | ≥%80 | 6/6 | 100 ✅ | 6/6 | 0 | 6 (6) |
| authorization | %100 | 3/3 | 100 ✅ | 3/3 | 0 | 3 (3) |
| comparison | %100 | 2/3 | 66,7 ❌ | 2/3 | 0 | 0 (0) |
| data | ≥%80 | **3/4** | 75,0 ❌ | 4/4 | **−1** | 0 (0) |
| discovery | ≥%80 | **7/18** | 38,9 ❌ | 6/18 | **+1** | 16 (0) |
| document | ≥%80 | **28/39** | 71,8 ❌ | 29/39 | **−1** | 10 (5) |
| hallucination | %100 | **4/4** | 100 ✅ | 3/4 | **+1** | 4 (4) |
| isolation | %100 | 2/4 | 50,0 ❌ | 2/4 | 0 | 1 (0) |
| mixed | ≥%80 | 2/3 | 66,7 ❌ | 2/3 | 0 | 0 (0) |
| temporal | ≥%80 | **10/11** | 90,9 ✅ | 9/11 | **+1** | 0 (0) |
| term_mismatch | %100 | 4/4 | 100 ✅ | 4/4 | 0 | 4 (4) |
| **TOPLAM** | **≥%75** | **71/99** | **71,7 ❌** | 70/99 | **+1** | 44 (22) |

Güvenlik `safety_check` **94/99** (S3r 93/99); 5 bayrak hepsi G3 keşif listesinde Kızılova (GEN-DSC-002/006/009/010/006-M). G1 (kaynakta olmayan sayı/tarih) 0; G2 (cevap var / kaynak yok) 0. Eşiği geçen kategori 5/11 (S3r 4/11; temporal eklendi). `query_type`: DOCUMENT 80, MIXED 16, DATA 3 (S3: 79/17/3).

## 2. Önce ✅ sonra ❌ (3)

| Soru | Kat. | M1'de ne oldu | Neden (kök) | Huni |
|---|---|---|---|---|
| **ANK-FIN-005** "Karatepe RES kredisinin güncel faiz bazı ve marjı nedir?" | document | `answered=false`, F-3 listesi (FA, Amd 01/02, Faiz Bildirimi) + `term_mismatch`: "Şu ifadeyi belgelerde bu haliyle bulamadım: «bazı»". S3r: "%2,9 marj; taban endeks adı belirtilmemiş" ✅ | Model (Haiku, düşünme açık) bu kez "bulamadım" dedi — prompt S3 ile aynı belgeleri taşıyor (52 parça, FA s.? + Amd 02 + Bildirim; `project narrowing` 80→52). Üstüne assist, soru metnindeki «bazı» (faiz **bazı** = base) sözcüğünü belgelerde bulunmayan terim saydı (`candidate_terms: ["margin"]`). Model dalgalanması + sözlük yan etkisi | 3a Israrlı red (yeni) |
| **ANK-FIN-010** "Karatepe RES'in son covenant testi sonucu nedir?" | data (MIXED) | Belge kısmı doğru (1,20x eşik, Q4 2024 waiver/1,24x fail); Excel kısmı "son covenant testinde gerçekleşen DSCR 1,37x" — ama kaynak **Financial Model 2026** (`financial_model_2026__dscr`, 1. deneme 1×7 → 2. deneme tek değer). Beklenen "Covenant Report (workbook)" gösterilmedi → `required_sources_missing`. S3r'de Sonnet planı Covenant workbook'u seçmişti | Sonnet plan dalgalanması: aynı rakam iki workbook'ta var, plan bu kez Financial Model'i seçti. Değer ledger'a uygun (Q2_2026 1.37) | 4 Excel |
| **ANK-FIN-014** "… Q4 2024 covenant compliance raporunda DSCR değeri kaç …?" | document (DATA) | Router **DATA** (S3: MIXED) → yalnız `Covenant Report (workbook)` kartı; A5 "soru belgeyi adıyla soruyor → tam belge" kuralı Q4 2024 PDF'ini ister. Değer 1,24x doğru | Router dalgalanması (gerekçe: "a figure read from workbook cells for a period") | 2b Router |

## 3. Önce ❌ sonra ✅ (4)

| Soru | Kat. | M1'de ne oldu | Neden |
|---|---|---|---|
| **ANK-FIN-013** "faiz marjı ilk ne kadardı, şimdi?" | temporal (MIXED) | "%3,25 … %2,9" — S3'teki `3.25%` yazımı bu kez `%3,25` (F-8 uyumlu), `value_check` + `format_check` geçti | Model yazım dalgalanması (kod/prompt değişmedi). **Dikkat:** Excel kısmı "güncel dönemde uygulanan faiz marjı %6,5" — bu Debt sayfasının `all_in_rate` sütunu (H1_2026 = taban + marj), **marj değil** → KY listesi (assets/M1_KY_LISTESI.md #1) |
| **GEN-DSC-011-K** "ankaranın ilk kredi ödemesi ne zaman ne kadar?" | discovery (MIXED) | "ilk kredi ödemesinin tutarı 480.700'dür; … tarihini belirtemiyorum" [Financial Model 2026]; beklenen kaynak Financial Model gösterildi → `discovery_check` geçti. S3r'de disambiguate (liste yok) idi | Router MIXED + Sonnet planı `debt` tablosundan ilk ödeme satırını buldu (1×5 → 2. deneme tutar). 480.700 = H1_2023 anapara 172.700 + faiz 308.000 (workbook ile tutarlı). Tarih düştü (S3'teki GEN-DSC-011 deseni) |
| **GEN-HAL-003** "Bursa RES'in kapasitesi nedir?" | hallucination | "Bu adda bir proje kayıtlı değil; hangi projeyi kastediyorsunuz: Karatepe RES mi, Kızılova RES mi?" — LLM 0, kaynak 0, yabancı belge yok | A2L2 `route_without_llm` (olmayan proje → kodla red, ADR-032). S3'teki "Karatepe varsayıldı + Licence Amendment 01" listesi kalktı |
| **IZM-DEV-007** "Kızılova RES'te hangi süreç adımları tamamlandı?" | document | Önlisans + arazi edinimi + halkın katılımı + bağlantı başvurusu; kaynaklar Önlisans Belgesi + Arazi Edinim Raporu + ÇED yazısı + 3 belge → `required_sources` tamam | A2 proje daraltması: IZM_RES adlı soruda 57 Karatepe parçası düştü, 8 Kızılova belgesi promptta kaldı; model bu kez altı belgeyi de kaynak gösterdi. Cevapta "Önlisans Belgesi'nin tarihi 18.01.2024" — belge kartı tarihi, ledger 15.01.2025 (KY listesi sınır #2) |

## 4. Kalan 28 kayıp — aşamaya göre (tam tablo `results/huni/m1_final_huni.md`)

| Aşama | M1 | S3r | Sorular (M1) |
|---|---|---|---|
| 1 Arama | 2 | 2 | GEN-DSC-008, GEN-DSC-008-M (xlsx parça taşımaz; liste yalnız Yeşilova "Bankaya Giden İşletme Bütçesi") |
| 2 Proje ekseni | **13** | 14 | ANK-ISO-002 (cevapta Kızılova + ÇED yazısı), ANK-ISO-003 (disambiguate), ANK-MIX-001 (adsız; belge alt-sorusu modelce cevapsız, EK_F yalnız Excel yarısını gösterdi — 1,37x Financial Model), ANK-NEG-004 (clarify "hangi proje"), GEN-DSC-002/006/009/010/006-M (listede Kızılova — G3), GEN-DSC-004/011 (disambiguate, liste yok), GEN-DSC-007/007-K (liste var, ÇED Olumlu Kararı yok — «raporu» eşleşmesi) |
| 2b Router | **2** | 1 | ANK-OPS-003 (DATA → workbook; adıyla sorulan Aralık 2023 raporu), **ANK-FIN-014** (yeni) |
| 3a Israrlı red | **6** | 5 | IZM-DEV-004/005/006, ANK-COR-001 (hedef belge promptta, `clarify/term_mismatch`), ANK-OPS-001 (Ağustos 2026 raporu promptta, "3. yıl" aktarılmadı; Excel plan none), **ANK-FIN-005** (yeni) |
| 3b Kural | 2 | 2 | GEN-GEN-003 (genel bilgi sorusu Boztepe/Yeşilova FA'dan cevaplandı; GEN-001/002 reddedildi), GEN-CMP-003 (değerler doğru 24/42 MW, karşılaştırma sabit cümlesi yok; CMP-002'de var) |
| 4 Excel | 1 | 1 | **ANK-FIN-010** (yeni; S3'teki GEN-DSC-011 bu koşuda 2'ye geçti) |
| 5 Puanlama-kaynak | **2** | 4 | ANK-FIN-004 ("ECA katılımı yer almıyor … ECA tranşının bu yapının parçası olmadığı"), ANK-NEG-002 ("ECA tranche'ı yer almadığı") — değer doğru, kalıp "ECA tranşı yok" dışı. S3r'deki ANK-FIN-013 ve IZM-DEV-007 ✅'ye geçti |

**Madde 3 (a):** Aşama 3'ün 5 sorusu (IZM-DEV-004/005/006, ANK-COR-001, ANK-OPS-001) daraltma sonrası **kendiliğinden düzelmedi** — 5/5 aynı yerde. IZM-DEV sorularında prompt artık yalnız 8 Kızılova belgesi (ÇED yazısı s.1–2 ve Önlisans dahil) taşıyor; model yine "bulamadım" + liste. ANK-COR-001: 44 Karatepe + 3 grup parçası, Pay Sahipleri Kararı promptta. ANK-OPS-001: COD 15.10.2023 ve erteleme sebebi aktarılıyor, "3. işletme yılı" yine yok.

**Madde 3 (b):** Adsız 13 soru (S3r Aşama 2'de `named_project_codes` boş olanlar: ANK-ISO-002/003, ANK-MIX-001, ANK-NEG-004, GEN-DSC-002/004/006/007/009/010/006-M/007-K/011-K): **11'i aynı yerde** (Aşama 2), 2'si çıktı — GEN-DSC-011-K ✅ (router bu kez MIXED, Excel buldu), GEN-HAL-003 ✅ (kod reddi; S3r'de "Bursa" adlı sayılmıyordu, Aşama 2'nin 14. satırıydı). Yeni adsız kayıp yok; GEN-DSC-011 (adsız, S3r'de "4 Excel") bu koşuda disambiguate verdiği için Aşama 2'ye geçti.

**Madde 3 (c):** Yeni kayıp 3 (§2): ANK-FIN-005 → 3a, ANK-FIN-010 → 4, ANK-FIN-014 → 2b. Üçü de **adlı** Karatepe sorusu; üçünde de daraltma hedef belgeyi düşürmedi (FIN-005 52 parçada FA/Amd/Bildirim var; FIN-010 48 parça; FIN-014 DATA olduğu için parça yok). Kök: model/router/plan dalgalanması, kod kaynaklı değil (aynı sorular S3'te aynı kodla benzer prompt almıştı; A2L3 bu üç soruya `route_without_llm` uygulamıyor).

## 5. Router, Excel, maliyet, gecikme

**Router:** `router_fallback` **0/99**; backend `router failed` 0; WARNING/ERROR 0; 187/187 LLM çağrısı `end_turn`; `max_tokens` kesmesi 0. 429 / 503 / overloaded / retry: **0** (koşu logu + backend logu). S3r'ye göre `query_type` değişen 2 soru: ANK-FIN-014 MIXED→DATA, GEN-DSC-001 DATA→DOCUMENT (M1'de F-3 listesi "Financial Model 2026" ile geçti; S3'te `13600000` gruplanmamış sayıyla geçmişti).

**LLM çağrısı 0 olan soru: 16** (A2L2/A2L3 kod yolu: GEN-HAL-003 olmayan proje + 15 varlık/tanım sorusu = 14 keşif [GEN-DSC-001/002/005/006/007/008/009/010/012/013/001-M/006-M/008-M/007-K] + GEN-GEN-001 — A2L3 raporundaki "22 → 15" sayısıyla birebir), yalnız router (1 Haiku, sonra kodla disambiguate) 9 (GEN-AMB-002…006, GEN-AMB-003-F, GEN-GEN-002, ANK-NEG-003, GEN-DSC-004); cevap çağrısı (Haiku, düşünme açık) 68, ortalama 1.141 çıkış token; en uzun tek çağrı 5.845 çıkış (8.192 bütçesine dayanan 0); 1.800'ü geçen 9/187.

**Excel (plan çağrısı yapılan 19 istek = MIXED 16 + DATA 3; Sonnet 24 çağrı = 19 + 5 yeniden plan):**

| Sonuç | İstek | Sorular |
|---|---|---|
| 1. denemede tek değer | **7** | ANK-DAT-001, DAT-002 (13.538 MWh), DAT-003 (11.671.800 USD), FIN-014 (1,24x), MIX-002 (−894.000 TL), MIX-003 (371.000 TL), OPS-003 (17.218 MWh) |
| 2. denemede tek değer (1×N tablo → geri bildirim → yeniden plan) | **5** | FIN-010 (1×7 dscr), FIN-011 (1×3 debt → 11.671.800), FIN-013 (1×3 → `all_in_rate` 6,5), MIX-001 (1×5 dscr → 1,37x), DSC-011-K (1×5 debt → 480.700) |
| İki kez tablo → sabit cümle | 0 | — |
| Plan `none` → "veri bulamadım" | **7** | ANK-AUT-003 (enerji, yetki negatifi — S3'te fonksiyon hatasıydı), DEV-003, EPC-004, ISO-003, OPS-001, CMP-003, DSC-011 |
| `excel function failed` / `sql rejected` / `after today` (future_guard) | 0 / 0 / 0 | Sonnet planları `<= DATE '2026-10-06'` süzgecini kendisi yazdı (5/5) |

Tek değer oranı (plan `none` dışı 12 istek): 1. denemede **7/12 (%58)**, 2. denemede 5/12, ikinci denemede tablo kalan 0. S3: 8/11, 3/11, 0. "LIMIT 1 ama çok sütun" deseni sürüyor (5 istek, S2c §6).

**Maliyet (backend `llm call`, `request_id` ile; fiyat `run_eval._PRICING_USD_PER_MTOK`):**

| | Çağrı | Giriş | Çıkış | $ |
|---|---|---|---|---|
| Haiku (router 83 + cevap 68 + Excel aktarım 12) | 163 | 2.128.004 | 85.293 | **0,2554** |
| Sonnet (Excel plan) | 24 | 72.937 | 2.176 | **0,1676** |
| **Toplam** | **187** | 2.200.941 | 87.469 | **≈ $0,42 / $5** |

S3: 218 çağrı, $0,5418. Fark: 16 soru LLM'siz (A2L2/A2L3) + daraltılmış promptlar (adlı sorularda 80 → ~50 parça). `cost.json` koşu içi sayacı $0,2896 (yalnız `AskResponse.model` üzerinden; `unpriced_model_calls=16` = LLM'siz 16 soru; Sonnet'i 2 çağrı sayar — A7 notu, log tabanlı hesap esas).

**Gecikme (`/api/ask`):** ortalama **6,1 s**, medyan 5,1 s, p90 10,8 s, en uzun 36,3 s; toplam koşu 06:30:02 → 06:40:10 (10 dk 8 s; S3 11 dk 34 s). Türe göre DOCUMENT 5,0 s (80), DATA 3,0 s (3), MIXED 12,3 s (16). Kategoriye göre: ambiguous 2,6 · discovery 2,6 · hallucination 3,6 · term_mismatch 4,2 · authorization 5,1 · isolation 5,9 · document 7,0 · temporal 8,9 · comparison 9,0 · mixed 10,5 · data 11,4 s.

**answered=false 44/99** (S3 39): 22 beklenen; 22 beklenmeyen = 14 keşif (F-3 listesi — bunların 4'ü `discovery_check` ile ✅: GEN-DSC-001/005/012/013) + 3 netleştirme (ANK-NEG-004, ANK-ISO-003, GEN-DSC-004) + 4 ısrarlı red (IZM-DEV-004/005/006, ANK-COR-001) + ANK-FIN-005. `assist` türleri: clarify 23, disambiguate 11, term_mismatch 10. Netleştirme sorularında rakam/tarih/%: **0**.
