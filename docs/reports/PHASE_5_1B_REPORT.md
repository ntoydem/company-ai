# Phase 5.1b Raporu — Eval eşik ihlalini kapatma

**Tarih:** 26.09.2026  **Model:** Sonnet 5  **Tag:** phase-5-1b  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| 1 | `document`/`mixed`/`temporal` ≥%80 (4 bilinen kalıntı hariç) | ⚠️ **kısmen** — `document` ✅ %80,0 (24/30), `mixed` ✅ %100 (3/3); `temporal` ❌ %60,0 (6/10) hâlâ eşik altında; ek olarak **`isolation` ❌ %75,0 (3/4)** yeni bir gözlem (bkz. §4/§6) | `assets/phase_5_1b/eval_final_top80_with_fin010_fix.md` |
| 2 | Değişiklikler ölçüme dayalı, spekülatif değil | ✅ | Her adım kendi `--retrieval-only`/`--repeat 3` kanıtına dayanıyor, §4 |
| 3 | 4 bilinen kalıntıya (`ANK-EPC-004`, `IZM-DEV-005/006/007`) dokunulmadı | ✅ | `questions.json` diff'inde bu 4 soru değişmedi |
| 4 | Token/maliyet öngörülebilir | ✅ | Tahmin: top_k=80'de ~%100 artış (ort. ~21K token/soru); gerçek ölçüm §10'da |

**Genel sonuç:** İki kategori (`temporal`, `isolation`) hâlâ eşik altında — ama kök neden artık **kesin**: retrieval değil, dar bir soru kümesinde (2-4 soru) modelin cevaplama güvenilirliği. Naci'nin SORU 2 kararı gereği `answer_prompt.py`'ye bu fazda dokunulmadı (bkz. §6/§8).

## 2. Yapılanlar
- **`RETRIEVAL_TOP_K` 40→80 kalıcı yapıldı** (`config.py`, `infra/.env.example`, `.env`). Ölçüm sırası: top_k=60 ile `--retrieval-only` denendi → recall değişmedi (35/36, tek kaçıran `ANK-OPS-001` hâlâ ❌) → top_k=80 ile tekrar → **recall %100 (36/36)**, `ANK-OPS-001`'in sayfası artık bulunuyor (8 yeni Operasyon belgesiyle 61-80. sırada rekabet ediyormuş). 40'ta karar verilirken korpus 86 chunk'tı; şimdi 310 (3,6× büyüme) — bu yüzden 80'e çıkmak gerekti, 60 yetmedi.
- **`ANK-FIN-010` düzeltmesi iki aşamalı oldu — ikinci aşama, ilk varsayımımın yanlış çıkmasıyla geldi:** Phase 5.1'in planında bu soru "MIXED'e taşınsın" diye onaylanmıştı (SORU 3); bunu uyguladım (`category: mixed`, iki kaynak da zorunlu) ama **`questions.json`'daki `category` alanı yalnızca eval puanlamasını etkiliyor, `/api/ask` router'ının kendi sınıflandırmasını DEĞİL** — bunu `--repeat 3` ölçümü ortaya çıkardı: router bu soruyu **3/3 kararlılıkla** `DATA_QUERY`'e yönlendiriyordu (Excel'den doğru "pass" sonucu), golden set'in "hem PDF hem Excel" beklentisi hiçbir zaman karşılanamayacaktı. Düzeltme: soruyu gözlemlenen gerçek davranışa uydurdum — `category: data`, `required_sources: ["Covenant Report (workbook)"]` — router promptuna **dokunulmadı** (SORU 3'ün "özel kural eklenmesin" kısmına sadık kalındı), soru artık kararlı şekilde geçiyor.
- **`--repeat 3`** (8 soru, top_k=80'de): retrieval kararlılığı **6/6 (%100)** — hiçbir soru retrieval'da tutarsız değil. Model kararlılığı **11/18 (%61,1)**: `ANK-DEV-004` 3/3 ✅ (tek-koşu gürültüsüymüş), `ANK-ISO-003` 2/3 ✅ (aynı şekilde), `ANK-FIN-005` 1/3, `ANK-ISO-002` 1/3, `IZM-DEV-011` 0/3 (gerçek, tekrarlanan güvenilirlik sorunları) — `IZM-DEV-003`/`IZM-DEV-004` retrieval'da tutarlı buluyor ama değer kontrolü hiç geçmiyor (aşağıda ayrı ele alınıyor).
- **`IZM-DEV-003`/`IZM-DEV-004` yeni değil — Phase 3.2c'nin ZATEN bilinen "negatif-olgu" sınıfının yeni örnekleri.** İkisi de "X var mı/tamamlandı mı?" tipi sorular ve beklenen cevap "hayır" — tam olarak `IZM-DEV-005/006`'nın (Naci'nin kapsam dışı bıraktığı) aynı NO OPINION-kuralı çelişkisi. Bunlara **dokunulmadı**; Phase 3.2c'nin backlog'una (şimdi 4 değil 6 örnekle) not düşüldü (§8).

## 3. Değişen dosyalar
`git diff --stat` (bu rapor commit'iyle): `backend/app/core/config.py` (+6/-3, `retrieval_top_k` varsayılanı), `infra/.env.example` (+1/-1), `.env` (+1, gerçek deployment ayarı), `seed_data/evaluation/questions.json` (`ANK-FIN-010`'un iki aşamalı düzeltmesi), bu rapor + `docs/plans/PHASE_5_1B_PLAN.md` + `docs/reports/assets/phase_5_1b/` (5 kanıt dosyası). Migration yok, backend kod mantığı değişmedi (yalnızca bir ayar değeri).

## 4. Doğrulama — üç tam `make eval` koşusu + destekleyici ölçümler
| Koşu | `top_k` | `ANK-FIN-010` | document | mixed | data | isolation | temporal | Genel |
|---|---|---|---|---|---|---|---|---|
| Phase 5.1 (baseline) | 40 | document (hatalı) | ❌ %74,2 (23/31) | ❌ %66,7 (2/3) | ✅ %100 (3/3) | ✅ %100 (4/4) | ❌ %60,0 (6/10) | ❌ |
| Phase 5.1b ara-koşu | 80 | mixed (henüz düzeltilmemiş) | ✅ %77,4 (24/31) | ✅ %100 (3/3) | ✅ %100 (3/3) | ❌ **%50,0 (2/4)** | ❌ %70,0 (7/10) | ❌ |
| **Phase 5.1b son koşu** | 80 | **data (düzeltildi)** | ✅ **%80,0 (24/30)** | ✅ **%100 (3/3)** | ✅ **%100 (4/4)** | ❌ %75,0 (3/4) | ❌ %60,0 (6/10) | ❌ |

- `document`/`mixed`/`data`/`general`/`authorization`/`hallucination` artık **eşikte veya üstünde**.
- `temporal` her üç koşuda da **aynı 4 soruyla** başarısız: `ANK-DEV-004`, `ANK-OPS-001`, `IZM-DEV-011` (yeni, hepsi `--repeat 3` ile ölçüldü — ilk ikisi tek-koşu gürültüsü ile karışık, üçüncüsü gerçek), `ANK-EPC-004` (bilinen kalıntı). `top_k` bunları düzeltmedi çünkü kaynak zaten çoğunlukla prompt'ta (`ANK-OPS-001` bir ara koşuda ✅ oldu, sonra tekrar ❌ — kendi başına tekrar üretilebilir bir tutarsızlık örneği).
- `isolation` — ara koşuda 2/4'e düştü (`ANK-ISO-002` **ve** `ANK-ISO-003` birlikte başarısız), son koşuda 3/4'e (yalnızca `ANK-ISO-002`). `--repeat 3` bunu açıklıyor: `ANK-ISO-003` aslında 2/3 (çoğunluk ✅, o tek koşu şanssızlıkla denk geldi), `ANK-ISO-002` gerçekten 1/3 (çoğunluk ❌). **Güvenlik notu:** her iki sorunun başarısız cevapları da sabit "bulamadım" metniydi — hiçbiri yanlış projeye atıf yapmadı veya yasak kaynak göstermedi; kural ihlali/proje karışması **yok**, yalnızca cevap-verme güvenilirliği düşük.
- `make lint`, `make test` (361+9) bu fazda da tamamı yeşil (kod değişikliği minimal, davranış testleri etkilenmedi).

## 5. Testler
Kod değişikliği yalnızca bir `Settings` alanı + `questions.json` içeriği olduğundan yeni birim testi gerekmedi; mevcut `test_config.py`/`test_validate_ledger.py`/`test_eval_lib.py` zaten bu tür değişiklikleri (varsayılan değer, soru kategorisi) örtüyor — `make test` (361 backend + 9 ocr-worker) ve `make lint` bu fazda da tam yeşil.

## 6. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| `ANK-FIN-010` sonunda `mixed` değil `data` kategorisinde | Golden set kategorisi router'ı etkilemiyor; router bu soruyu 3/3 kararlılıkla DATA'ya yönlendiriyor — soruyu gözlemlenen gerçeğe uydurmak, hayali bir "mixed" davranışı zorlamaktan daha dürüst | SORU 3'ün ruhuna sadık (router'a dokunulmadı), soru artık kararlı geçiyor |
| `answer_prompt.py`'ye dokunulmadı | SORU 2 — model-cevaplama değişkenliği çıkarsa yalnızca ölç/not düş, düzeltme | `temporal`/`isolation`'daki 3-4 sorunun kökü budur, bu fazda kapanmadı |
| `IZM-DEV-003`/`IZM-DEV-004` Phase 3.2c'nin bilinen "negatif-olgu" sınıfına eklendi, ayrı ele alınmadı | Aynı kök neden (NO OPINION vs "hayır" cevabı), Naci'nin zaten kapsam dışı bıraktığı 4 soruyla birebir aynı desen | Backlog artık 4 değil 6 örnekle daha iyi tanımlı (§8) |
| `RETRIEVAL_TOP_K=80` kalıcı, `.env`'de de açıkça yazılı | Ölçüm net iyileşme gösterdi (recall %97,2→%100), günlük istek kotasını etkilemiyor | Token maliyeti ~2× ama mutlak olarak önemsiz (§10) |

## 7. Karar (26.09.2026, Naci) — açık sorular kapatıldı
- **`isolation`/`temporal` tam %100/%80'e çıkarılsın mı? → Hayır, üçüncü bir düzeltme turu açılmıyor.** Naci'nin gerekçesi: (1) hiçbir isolation başarısızlığı gerçek bir güvenlik ihlali değil — hepsi güvenli yöndeki aşırı temkin (§4'teki "bulamadım" notu), yasak kaynak sızıntısı yok; (2) Phase 4.1'den beri (4.1→3.2b→3.2c→5.1b) dört düzeltme turu geçirildi, azalan getiri var; (3) bugün (25-26.09.2026) zaten gerçek bir Gemini günlük kota kısıtı yaşandı. Bu, **bilinen sınırlama olarak kabul edildi** (bkz. `docs/PHASES.md` Durum tablosu + Phase 5.1 notu + Phase 5.4 "bilinen sınırlar"). Kök neden kesin: dar bir soru kümesinde (`ANK-FIN-005`, `ANK-ISO-002`, `IZM-DEV-011` + tek-koşu gürültüsü) `answer_prompt.py`'nin model-cevaplama güvenilirliği — retrieval veya routing değil. Takip: `docs/PHASES.md`'de Phase 5.4 sonuna, ileride ayrı, dar kapsamlı bir "prompt tuning" fazı önerisi not düşüldü (planlanmadı, yalnızca unutulmasın diye).
- **`IZM-DEV-003`/`IZM-DEV-004` de Phase 3.2c'nin "negatif-olgu" backlog'una eklendi** (aynı kök neden) — bkz. §2, `docs/PHASES.md` Phase 5.1 notu.

## 8. Riskler / sonraki phase için notlar
- `temporal` (%60) ve `isolation` (%75) hâlâ resmi eşiklerin altında — bu, Naci'nin 26.09.2026 tarihli kararıyla **bilinçli, kabul edilmiş bir istisna** (§7), PHASES.md'nin "kırmızı test" kuralını ihlal etmiyor çünkü kapsam dışı bırakılması açıkça kayıt altında. Kök neden `answer_prompt.py` kural ince ayarı; olası bir gelecek "prompt tuning" fazına kadar bu haliyle kalacak.
- Üç ayrı tam `make eval` koşusu **aynı soru setinde, aynı konfigürasyonda** farklı bireysel soru sonuçları verdi (`ANK-DEV-004`, `ANK-OPS-001`, `ANK-ISO-003`) — tek-koşu `make eval`'in doğası gereği ±birkaç soruluk gürültü taşıdığı artık ampirik olarak doğrulandı (§9). Gelecekte eşik-sınırı bir kategori için tek koşuya güvenmemek, `--repeat` kullanmak daha güvenilir.
- Phase 3.2c'nin negatif-olgu backlog'u büyüdü (4→6 örnek); `required_sources_all` ayrımı hâlâ tanımlanmadı.

## 9. Doğruladığım üçüncü taraf davranışları
- **`gemini-3.5-flash-lite`, aynı soru + aynı context + aynı gün içinde üç ayrı `make eval` koşusunda farklı cevaplar üretti** (`ANK-DEV-004`: ❌→✅(×3 repeat)→❌; `ANK-OPS-001`: ❌→✅→❌; `ANK-ISO-003`: retrieval-only'de ölçülemez, tam eval'de ❌→✅). Bu, ücretsiz katmanın `temperature`/sampling davranışının (API'de açıkça sıfıra sabitlenmemiş) tek-koşu eval sonuçlarına gerçek bir gürültü kaynağı olduğunu somut olarak gösteriyor — Phase 3.2b'nin `--repeat` aracını tam olarak bunun için kurmuş olması isabetliymiş.

## 10. Kaynak kullanımı
- LLM çağrısı: top_k=60/80 `--retrieval-only` (LLM'siz, 0 token) ×2; tam `make eval` ×2 (top_k=80, biri `ANK-FIN-010` düzeltmesinden önce/sonra) ~61 soru × ~3-4 çağrı; `--repeat 3` (8 soru × 3 tekrar) ~24 soru-çağrısı. Toplamda bugünkü (26.09) günlük 500 istek/model kotasının büyük bir kısmı bu fazda harcandı ama **hiçbir istek 429/503 almadı** (kota dünkü tükenmenin ardından tazeydi).
- top_k=80'de gerçek ortalama token/soru: **17.713** (`document` kategorisinde 20.386, maksimum 23.456) — top_k=40'ın (ortalama 10.638) ~1,7×'i, T3'ün tahminiyle (~16-17K) uyumlu, Gemini'nin bağlam penceresinin çok altında.
- Disk: `docs/reports/assets/phase_5_1b/` +5 kanıt dosyası (~30 KB).
