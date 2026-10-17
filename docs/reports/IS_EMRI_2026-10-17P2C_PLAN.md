# İş Emri 2026-10-17P2C_PLAN — P2B ayrıştırma ölçüsü: PLAN (koşu yok, kod yok)

**Tarih:** 17.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `737b30a`) · **Ürün 1** · **Durum: yalnız plan, onay bekleniyor**

**Dayanak:**
- `docs/reports/IS_EMRI_2026-10-17P2B_CANLI.md`: P2B canlıda smoke 8/9 ve 7/9 verdi (g, a, b; hepsi Karatepe). Geri alındı (`faedc84`).
- `docs/reports/IS_EMRI_2026-10-17P2B.md`: P2B'nin içeriği.

Bu dosyada kod, prompt, ayar, soru seti ve canlı servis değişmedi. LLM çağrısı yapılmadı.

**Not:** Emir metni 8. maddede ("örneğin cümleyi …") kesik geldi. §8'i bağlamdan yazdım. Eksik bir istek varsa söyle, eklerim.

**Amaç:** P2B'deki dört parçadan hangisinin (ya da hiçbirinin, yani model dalgalanmasının) a, b, g kaymasını yaptığını ölçerek ayırmak. Kod düzeltilmeyecek.

---

## 1. Kollar

Taban, `faedc84` (P2A koduyla birebir aynı; `git diff 23e2828 faedc84 -- backend` boş). P2B kodu `da3dd08` içinde 5 dosyada 3 yerde değişiklik var. Bunlar dört yamaya bölünür:

| Kol | İçerik (`git diff 23e2828 da3dd08`'den) | Dosya / parça |
|---|---|---|
| **BASE** | Taban, P2A. Değişiklik yok | — |
| **R** | (1) ROUTER: Excel tanımına "loan repayment schedules …", DATA_QUERY'ye "a value read from a repayment schedule row …", 1 örnek | `router.py` (tek parça) |
| **P** | (2) PLAN cümlesi: "Use the current version of a workbook; …" | `excel_ask.py` 1. parça (`PLAN_SYSTEM_PROMPT`) |
| **K** | (3) Katalog satırı: `project`, `status`, `superseded by` (`_workbook_line`) | `excel_ask.py` 2. parça (`_catalogue`) |
| **C** | (4) Başlık satırı + önsöz/alt not `_info` + tarih biçimi | `calc.py` (tamamı) + `excel_ask.py` 3. parça (`_sql_value` tarih dalı) |
| **ALL** | P2B'nin tamamı | `da3dd08` olduğu gibi |

**Kendi kararım:** `_sql_value` tarih dalı C koluna konur. Bu dala yalnız C'nin ürettiği tipli tarihlerle ulaşılır. C olmadan tarih zaten metin olarak gelir. C'yi bu dal olmadan koşmak, P2B'de olmayan bir 500 yolu açardı.

**Yamaların üretimi** (kod yazmadan, yalnız git):
```bash
mkdir -p results/p2c/patches
git diff 23e2828 da3dd08 -- backend/app/services/router.py          > results/p2c/patches/R.patch
git diff 23e2828 da3dd08 -- backend/app/excel/calc.py               > results/p2c/patches/C_calc.patch
git diff 23e2828 da3dd08 -- backend/app/services/excel_ask.py       > /tmp/…/excel_ask.full.patch
# excel_ask.full.patch üç parça (@@) içerir. Parçalar ayrı dosyalara bölünür:
#   1. parça → P.patch, 2. parça → K.patch, 3. parça → C_sqlvalue.patch
# Bölme `filterdiff --hunks=N` (patchutils) varsa onunla, yoksa dosya başlığı + ilgili @@ bloğu
# elle kopyalanarak yapılır. Her yama `git apply --check` ile tek başına tabana uygulanabilmeli.
```
`docs/prompts/*` kopyaları ve testler kollara konmaz. Çalışan kodu etkilemezler.

**Kolların doğrulanması:**
- Her kol için `git -C <kol> diff --stat` yalnız beklenen dosyaları göstermeli.
- R + P + K + C birlikte uygulanmış geçici bir ağaç, `da3dd08` ile backend kodunda **birebir aynı** olmalı (`git diff --no-index` boş). Bu, bölmenin eksiksiz olduğunu kanıtlar.
- Her kol için parmak izi (container içinde `grep -c`):

| Parmak izi | BASE | R | P | K | C | ALL |
|---|---|---|---|---|---|---|
| `"repayment schedule row"` in `router.py` | 0 | 1 | 0 | 0 | 0 | 1 |
| `"use a superseded one"` in `excel_ask.py` | 0 | 0 | 1 | 0 | 0 | 1 |
| `"def _workbook_line"` in `excel_ask.py` | 0 | 0 | 0 | 1 | 0 | 1 |
| `"def split_footer"` in `calc.py` | 0 | 0 | 0 | 0 | 1 | 1 |

## 2. Güvenlik: canlı klasör ve canlı container'lar dokunulmaz

**Risk:** Canlı backend `~/company-ai/backend`'i bind mount ile okuyor. Ana klasörde `git checkout` yapılırsa canlı kod değişir; bir sonraki yeniden başlatmada canlıya girer (bkz. memory notu "branch switch = live code").

**Kurallar:**
1. **Ana klasörde `git checkout`, `git switch`, `git apply`, `git stash` yapılmaz.** Ana klasörde yalnız `git worktree add`/`remove` (çalışma ağacına dokunmaz), `results/p2c/` altına yazma ve en sonda rapor commit'i olur.
2. Kollar ayrı worktree'lerde:
   ```bash
   A=../company-ai-arms
   git worktree add --detach $A/base faedc84
   git worktree add --detach $A/R    faedc84 && git -C $A/R apply ../../company-ai/results/p2c/patches/R.patch
   … P, K, C (C: C_calc.patch + C_sqlvalue.patch) …
   git worktree add --detach $A/all  da3dd08
   ```
3. **Bütün compose komutları tek bir değişkenle:**
   `EC="docker compose -p company-ai-eval --project-directory . -f infra/docker-compose.yml --env-file infra/.env.eval"`.
   `make` hiç kullanılmaz. `make … ENV_FILE=infra/.env.eval` compose adı `company-ai` olduğu için **canlıya** gider (D2 notu).
4. Eval backend her kol için yeniden yaratılır; yalnız `/app` kolun klasöründen bağlanır:
   ```bash
   docker rm -f company-ai-eval-backend-1 2>/dev/null
   $EC run -d --use-aliases --name company-ai-eval-backend-1 \
     -v $(realpath $A/<kol>)/backend:/app \
     -e LLM_PROVIDER=anthropic -e LLM_MODEL_CLASSIFY=claude-haiku-5-5 -e LLM_MODEL_ANSWER=claude-haiku-5-5 \
     -e LLM_MODEL_EXCEL_PLAN=claude-sonnet-5-5 -e ANTHROPIC_THINKING=false -e ANSWER_THINKING=true \
     -e ANSWER_THINKING_MAX_TOKENS=8192 -e EK_F_MODE=true -e ASSIST_MODE=false backend
   ```
   Bunlar D3/M1/P1M'deki `-e` bayraklarıdır (canlı ayar eşitliği). `-v …:/app` geçersiz kılmasının çalıştığı P2B ölçüsünde doğrulandı: "önce" koşusu eski sütun adlarını gördü.
5. **smoke_live her zaman açık hedefle** çağrılır: `--base-url http://<eval-backend-IP>:8000 --env infra/.env.eval`. Varsayılan `localhost:$CADDY_PORT` **canlı Caddy'dir**; sürücü betik, URL `8080` ya da `localhost` içerirse koşmadan çıkar.

**Doğrulama adımları** (her biri rapora yazılır):

| Ne zaman | Komut | Beklenen |
|---|---|---|
| Başta | `$EC config \| grep -E '^name:\|DATABASE_URL'` | `name: company-ai-eval`, `…/company_ai_eval` |
| Başta ve sonda | `docker inspect company-ai-backend-1 --format '{{.State.StartedAt}}'` | aynı (15:02:05Z) |
| Başta ve sonda | `git -C ~/company-ai rev-parse HEAD`, `git status --short` | aynı; yalnız `?? logs/` ve `results/p2c/` |
| Başta ve sonda | canlı `audit_log` sayısı (SELECT) | eval koşusu canlıya satır yazmaz. Artış olursa saatleri kontrol edilir (başka kullanıcı) |
| Her kolda | `docker inspect company-ai-eval-backend-1 --format '{{json .Mounts}}'` | `/app` kaynağı `…/company-ai-arms/<kol>/backend` |
| Her kolda | parmak izi tablosu (§1) | kolun satırı |
| Her kolda | `get_settings()` probu (M1 betiği) | canlıyla aynı; tek fark DB adı |
| Sonda | `docker rm -f company-ai-eval-backend-1 && $EC down`; `git worktree remove` ×6 | eval container'ı ve worktree kalmaz |

**Eval DB:** D2'den beri canlıyla aynı belge listesi (113). Kollar arasında DB değişmez; yalnız eval `audit_log`'a satır eklenir. Ölçüm öncesi belge sayısı ve 7 Excel dosyası kontrol edilir.

## 3. Sorular (12; `questions.json`'a eklenmez)

Ayrı spec dosyası: `results/p2c/spec.json`, smoke_live biçimi (`letter`, `user`, `question`, `expect`). Expectation'lar yalnız ilk bakış içindir. Asıl değerlendirme §4'teki analiz betiğindedir.

| # | Kaynak | Kullanıcı | Soru | Beklenen |
|---|---|---|---|---|
| a | smoke a | finans | Karatepe RES kredisinde fiilen kullandırılan toplam tutar nedir? | Excel yarısında 13.600.000 |
| b | smoke b | finans_mudur | Karatepe RES kredi sözleşmesine göre fiilen kullandırılan toplam kredi tutarı kaç USD? | 13.600.000 USD; router taban DOCUMENT |
| g | smoke g | finans | Karatepe için bankaya hâlâ ne kadar borcumuz var? | Excel yarısında 11.671.800 |
| j | P2A_CANLI | finans | Yeşilova RES'in kalan kredi borcu ne kadar? | 11.671.800 **geçmez** |
| k | P2A_CANLI | finans | Boztepe RES'in güncel DSCR değeri kaç? | 1,37 **geçmez** |
| l | P2A_CANLI | finans | Karatepe RES'in kalan kredi borcu ne kadar? | 11.671.800 geçer |
| m | yan etki | finans | Karatepe RES kredi sözleşmesinin vadesi kaç yıl? | DOCUMENT, 13 yıl |
| n | yan etki | finans | Kredi sözleşmesinde taksit sayısı kaç? | DOCUMENT (adsız: proje sorusu olabilir) |
| o | B-01 örnek 1 | finans | Yeşilova kredi ödeme planında 12. taksitin anapara tutarı nedir | 98.000 (Excel, Yeşilova 2026-09) |
| p | B-01 örnek 2 | finans | Yeşilova 2027'de hangi kredi ödemelerini yapacak? | Yalnız router kararı ölçülür (çok satır, 1×1 sınırı) |
| q | B-01 örnek 3 | finans | Yeşilova'nın bir sonraki kredi ödemesi ne zaman | 14.10.2026; anapara 98.000 varsa not edilir |
| r | P2B_CANLI | finans | Boztepe RES ödeme planında 12. taksitin anaparası ne kadar? | 178.571,43 (C'siz kollarda `178571.43` da doğru sayılır) |

**Tekrar sayısı (N):**
- BASE **8** (en az 5 şartı; taban dalgalanmasını ölçmek için fazladan 3).
- R, P, K, C, ALL: **5**'er.
- Toplam 8 + 5×5 = **33 geçiş × 12 soru = 396 `/api/ask`**.

**Sıra:** Kollar sırayla koşulur (BASE, R, P, K, C, ALL), ardından **BASE'in son 3 tekrarı en sona** konur. Böylece zaman içindeki sağlayıcı dalgalanması tabanda da görülür. Her geçiş 12 sorunun hepsidir; geçişler arası 2 sn.

## 4. Ölçülenler ve kayıt

**Soru × tekrar başına:**

| Ölçü | Kaynak |
|---|---|
| Router kararı (DOCUMENT/DATA/MIXED), `reason`, `document_question`, `data_question` | backend logu `question routed` (INFO; tam alanlar), `request_id` ile |
| Excel kaynağı (workbook, sayfa, aralık) | yanıt `excel_sources` |
| Değer doğru mu | yanıt `answer`: MIXED'de "Excel verisine göre" yarısı, DATA'da tamamı; beklenen değer F-8 biçimiyle |
| "Bulamadım" | Excel yarısı `NO_DATA_TEXT` / `NO_ANSWER_TEXT` |
| Başka projenin rakamı | yanıttaki `excel_sources` workbook'unun projesi ≠ sorudaki proje; ayrıca j/k için `11.671.800` / `1,37` geçiyor mu |
| Plan türü ve SQL | **sorun var, §9 S-1:** başarılı planlar bugün loglanmıyor. Yalnız başarısız/tekrar planlar loglanıyor (`excel sql result not scalar`, `… after today`, `excel function failed`) |
| LLM çağrıları, token, model | logdaki `llm call` satırları, `request_id` ile |

**Kayıt kaybolmasın diye** (P2B_CANLI'da log container yeniden yaratılınca gitti):
- Her kol için backend başlar başlamaz `docker logs -f company-ai-eval-backend-1 > results/p2c/<kol>/backend.log &`. Container silinmeden önce bu süreç biter ve dosya kapanır.
- Her geçişten sonra smoke_live'ın `logs/smoke_<damga>_<harf>.json` dosyaları `results/p2c/<kol>/rep<k>/` altına **taşınır**. Damga dakikalık; aynı dakikada iki geçiş üst üste yazardı. Bir geçiş ~3 dk sürdüğü için çakışma beklenmez, taşıma bunu garanti eder.
- Kol sonunda eval `audit_log`'un o kolun satırları dışa aktarılır (`row_to_json`, `timestamp >= kol başı`): `results/p2c/<kol>/audit.jsonl`.
- **Analiz betiği** `results/p2c/analyze_p2c.py` (onaydan sonra yazılır; ürün kodu değil): yanıt JSON + log + audit'i `request_id` ile birleştirir. Çıktılar `results/p2c/summary.md` (kol × soru tablosu) ve `results/p2c/rows.jsonl` (her satır bir istek).

## 5. Karar kuralı

Her soru `q` ve kol `A` için şunlar sayılır:
- `fail_A(q)`: §3 beklentisi tutmayan tekrar sayısı.
- `type_A(q)`: router kararı dağılımı (ör. DOCUMENT 4 / MIXED 1).

**Taban gürültüsü:** BASE'in 8 tekrarındaki `fail_BASE(q)` ve router dağılımı. Smoke a K2'de de bir kez düşmüştü; taban dalgalanıyor. Bu yüzden tek tek düşüşler sebep sayılmaz.

**"Zararlı sinyal" (kol A, soru q):** aşağıdakilerden biri.
1. **Başarı farkı:** BASE oranı ≤ 1/8 ve A'da ≥ 3/5 düşüş. Ya da genel olarak `fail_A/5 − fail_BASE/8 ≥ 0,5`.
2. **Router kayması:** BASE'te bir türün payı ≥ 7/8 iken A'da aynı tür ≤ 2/5 (ör. b: DOCUMENT 8/8 → 1/5).
3. **Başka projenin rakamı:** A'da bir kez bile olursa. Bu sinyal değil, **KY bulgusu**; ölçü sürer ama raporun başına yazılır.

**Kol sonucu:**
- **Zararlı:** a, b, g'den en az birinde sinyal var **ve** ALL kolunda da aynı yönde sinyal var.
- **Zararsız görünüyor:** hiçbir soruda sinyal yok.
- **Belirsiz:** diğer her durum.

**Doğrulama şartı:** ALL kolu canlıdaki düşüşü eval'de **yeniden üretmezse** (a, b, g'de sinyal yok), sonuç "eval canlıyı yeniden üretmedi" diye raporlanır. Bu durumda tek kollar için sebep iddiası yapılmaz.

**İstatistik çekincesi:**
- 5'e karşı 8 tekrar küçük bir örneklemdir. 0/8'e karşı 4/5 bile yalnız "güçlü işaret"tir. Fisher kesin testi p değeri bilgi olarak yazılır, ama "anlamlı" kelimesi kullanılmaz.
- Sonuç olduğu gibi raporlanır. Belirsiz kalan kollar için daha fazla tekrar ayrı onayla istenir (§9 S-2).

## 6. Maliyet tahmini

Birim maliyetler P1M/M1/D3'teki ölçülmüş çağrılardan (log tabanlı):
- Haiku çağrısı ortalama ≈ $0,0016. P1M: 142 çağrı $0,2334. Fiyat $0,10 / $0,50 per MTok.
- Sonnet plan çağrısı ≈ $0,0063–0,0070. P1M 18 çağrı $0,1131; M1 24 çağrı $0,1676. Fiyat $2 / $10 per MTok.

| Soru tipi | Çağrılar | Soru başına |
|---|---|---|
| DOCUMENT (router + cevap, thinking açık) | 2 Haiku | ≈ $0,003–0,004 |
| DATA | router + 1–2 Sonnet + 1 Haiku | ≈ $0,008–0,016 |
| MIXED | router + belge cevabı + 1–2 Sonnet + 1 Haiku | ≈ $0,011–0,019 |

**Bir geçiş (12 soru):** ~8–10 Excel'e giden (R ve ALL'da daha çok), 2–4 DOCUMENT.
- ≈ 9 × $0,014 + 3 × $0,0035 ≈ **$0,14**.
- Aralık **$0,08–0,22**.

**Toplam (33 geçiş, 396 istek):**
- Beklenen **≈ $4,5**.
- Aralık **$2,6–7,3**.
- Arka plandaki metadata sınıflama çağrıları (`request_id` boş) maliyete dahil edilmez, ayrıca yazılır.

**Bütçe önerisi:** **$8,00** sert sınır. smoke_live'da `--budget-usd` yok; sürücü betik her geçişten sonra `llm call` loglarından toplamı hesaplar (`run_eval._PRICING_USD_PER_MTOK`). Toplam $8'i geçerse kalan geçişleri koşmadan durur. Ayrıca **$6** eşiğinde durup Naci'ye haber verilir.

**Daha ucuz seçenek (§9 S-2):**
- A: yalnız a, b, g, l, m, n (6 soru) ile ≈ $2,2.
- B: önce yalnız ALL ve BASE (13 geçiş, ≈ $1,8). ALL düşüşü yeniden üretirse tek kollar koşulur.

**Onay:** Koşu bu plan ve bütçe Naci tarafından onaylanmadan **başlamaz**.

## 7. Süre ve ortam kurulumu

**Kurulum (≈ 15 dk):**
1. Önce-durum kaydı (§2 tablosu).
2. Yamalar, worktree'ler, parmak izi ve "R+P+K+C = da3dd08" kontrolü.
3. `$EC up -d --wait postgres`. ocr-worker açılmaz (bekleyen iş yok; D3/P1M ile aynı).
4. Spec dosyası ve `smoke_live --spec … --no-save` ile **kuru doğrulama**: yalnız `validate_spec`, istek yok. smoke_live'da kuru koşu bayrağı yoksa `python -c "from scripts.smoke_live import load_spec, validate_spec; …"` kullanılır.

**Koşu:**
- Geçiş başına ≈ 3 dk: MIXED/DATA 12–25 sn (canlı smoke süreleri), DOCUMENT 2–6 sn.
- 33 geçiş ≈ **100 dk**.
- Kol başına container değişimi ≈ 30 sn (7 kez, BASE iki parça).
- Toplam **≈ 2 saat**, analiz ve rapor ayrıca ≈ 30 dk.

**Kapanış:** `docker rm -f company-ai-eval-backend-1` (M1 notu: `down` bunu kaldırmaz), sonra `$EC down`, sonra `git worktree remove` ×6. Son-durum kaydı yapılır (§2).

## 8. Sonucun kullanımı

Emrin bu maddesi kesik geldi; bağlamdan yazıldı. Her seçenek **ayrı plan + Ç-15/8 onayı** ister. Canlıya almadan önce aynı spec ile yeniden ölçülür. Canlıya alma şartı smoke 9/9.

| Zararlı çıkan | Düzeltme seçenekleri |
|---|---|
| **R** (router cümlesi) | (a) Cümleyi daraltmak: DATA yalnız soru açıkça "taksit / ödeme planı / vade" söylerse; "kalan borç / bakiye / kullandırılan tutar" sorularını açıkça mevcut kurala bırakmak. Bir karşı örnek eklenir (proje adı yok, ör. "Bankaya kalan borcumuz ne kadar?" → mevcut tür). (b) Örneği çıkarıp yalnız tanım cümlesini bırakmak. (c) İpucunu kodla koşullu vermek: kullanıcının yetki kümesinde `Repayment Schedule` türünde workbook yoksa cümle prompta girmez. Bu, plan §10'daki dinamik katalog fikrinin küçük hâli; yetki sorgusu router'dan önce gelir. (d) Router'a hiç dokunmadan B-01'i yalnız C ile çözmek. Ödeme planı soruları DOCUMENT'a gitmeye devam eder; B-01 örnek 1 açık kalır. |
| **P** (PLAN cümlesi) | (a) Cümleyi kaldırıp eski sürümü **kodla** katalogdan çıkarmak: `status = superseded` workbook, soru o sürümün tarihini/adını anmıyorsa katalogda yok. Kural 5 kodla uygulanır. (b) Cümleyi yalnız katalogda `superseded` satırı varken eklemek. |
| **K** (katalog alanları) | (a) `project` alanını çıkarmak (daraltma zaten kodla yapılıyor). Yalnız `superseded` satırlarına `status` yazmak. (b) Alanları satır sonuna değil ayrı bir satıra taşımak. |
| **C** (başlık/alt not kodu) | Karatepe tabloları testle aynı olduğu için beklenmiyor. Çıkarsa: kuralı yalnız `Repayment Schedule` türüne uygulamak ya da eşiği/kesmeyi geri almak. Önce hangi tablonun değiştiği bulunur. |
| **Hiçbiri / belirsiz** | P2B model dalgalanması üstüne düşmüş olabilir. Seçenek: P2B'yi değiştirmeden, canlıya alma şartını "smoke 2 koşuda en az 17/18" gibi bir dalgalanma payıyla yeniden tanımlamak. Bu bir **ürün kararıdır** (Tansu/Naci), teknik değil. Ya da R'yi en dar hâline (a) çekmek. |

Ayrıca, sonuçtan bağımsız olarak, bu ölçünün kayıt düzeni (tam router logu + `request_id` birleştirme) sonraki canlıya almalarda da kullanılabilir. Bunu kalıcı hâle getirmek ayrı bir küçük iştir: router alanları audit'e eklenir, ama bu şema değişikliği (Ç-15/4) demektir.

## 9. Açık sorular

**S-1 (plan logu):** Başarılı Excel planları (SQL / fonksiyon) bugün hiçbir yerde loglanmıyor. Seçenekler:
- (a) **Yalnız ölçüm için**, altı kola da **aynı** tek satırlık INFO log yaması (`log.info("excel plan", extra={"plan": plan, "attempt": …})`). Canlıya girmez, commit edilmez, kolların farkını değiştirmez.
- (b) Yama yok. Plan yalnız başarısız/tekrar durumlarda ve `excel_sources` aralığından dolaylı okunur.

Önerim (a). "Kod yok" şartı ürün kodu içindir, ama bu da bir koddur; senin kararın.

**S-2 (kapsam/maliyet):** Tam plan (33 geçiş, ≈ $4,5, ≤ $8) mi, aşamalı mı? Aşamalı: önce BASE + ALL (≈ $1,8); ALL eval'de düşüşü üretirse dört tek kol. Önerim aşamalı. Aynı sonuca ulaşır; ALL üretmezse tek kollar zaten yorumlanamaz (§5 doğrulama şartı).

**S-3 (canlı smoke soruları):** Ölçüm canlıya istek atmaz. Canlı smoke, ölçümün parçası değildir; ölçüm sonunda canlıya dokunulmaz. Onaylıyor musun?

## 10. Riskler

| Risk | Önlem |
|---|---|
| Canlı koda dokunma | Ana klasörde checkout yok; worktree + `-v`; parmak izi ve Mounts kontrolü; başta/sonda canlı StartedAt ve HEAD (§2) |
| Canlıya istek gitmesi | smoke_live açık `--base-url` (eval IP:8000); sürücü `8080`/`localhost` görürse durur; canlı `audit_log` başta/sonda |
| Eval canlıyı yeniden üretmez | ALL kolu kontrolü; üretmezse sebep iddiası yok (§5) |
| Sağlayıcı dalgalanması zamanla değişir | BASE'in 3 tekrarı en sona |
| Log kaybı | `docker logs -f` dosyaya, container silinmeden önce kapatılır; smoke JSON'ları geçiş başına taşınır |
| Bütçe aşımı | geçiş başı maliyet hesabı, $6 uyarı, $8 durma |
| Yama bölme hatası | R+P+K+C birleşimi = `da3dd08` kontrolü; parmak izi tablosu |

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (+ ADT-4). Okunan: Çekirdek (Ç-9, Ç-15, Ç-16); P2B ve P2B_CANLI raporları;
  D3, M1, P1M ölçüm yöntemleri
Ürün etiketi      : Ürün 1 — T-11 (P2B'nin geri alınma sebebinin ölçülmesi; yeni yetenek yok)
Kritik Geliştirme Kararı : Yok — yalnız plan. Ölçüm LLM çağrısı içerir, maliyet §6; Naci onayı gerekir.
  Kollar canlıya alınmaz (Ç-15/6 yok). Prompt değişikliği canlıya girmez (Ç-15/8 yok; kollar P2B'nin
  onaylı metinleri). Şema yok (Ç-15/4 yok)
Gizli bilgi / yeni bağımlılık : Yok — .env/.env.eval değişmez; parolalar smoke_live içinde .env.eval'den;
  yeni paket yok (filterdiff yoksa elle bölme)
Kapsam dışı değişiklik : Yok — bu dosya dışında repo değişmedi; kod, prompt, soru seti, canlı servis,
  eval ortamı dokunulmadı; LLM çağrısı 0
Kendi başına verilen kararlar : (1) _sql_value tarih dalı C koluna (§1); (2) BASE N=8, diğerleri N=5 ve
  BASE'in 3 tekrarı sonda (§3); (3) 12 soru: emirdeki listeye B-01 örnek 2 yalnız router ölçüsü için
  eklendi, Boztepe 12. taksit P2B_CANLI'dan (§3); (4) karar eşikleri (§5); (5) $6 uyarı / $8 durma (§6);
  (6) §8 emir metni kesik geldiği için bağlamdan yazıldı; (7) S-1 log yaması önerisi — onaysız yapılmaz
```
