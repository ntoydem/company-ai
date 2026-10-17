# İş Emri 2026-10-17P2C — Aşama 1: taban (P2A) × P2B'nin tamamı, eval ortamında

**Tarih:** 17.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `f03f765`) · **Ürün 1**

**Dayanak:**
- Plan `docs/reports/IS_EMRI_2026-10-17P2C_PLAN.md` (`f03f765`).
- Naci onayı (17.10.2026):
  - S-1: ölçüm için tek satırlık log yaması, ürün koduna commit edilmez.
  - S-2: aşamalı.
  - S-3: canlıya istek yok.
- Aşama 1: BASE (`faedc84`) 8 tekrar + ALL (`da3dd08`) 5 tekrar, 12 soru, bütçe $3,00.

Aşama 2 (dört tek kol) bu emirde yok.

**Bu rapor sebep iddiası yapmaz.** Yalnız sayılar var. Örneklem küçük: 8'e karşı 5 tekrar.

## 1. Sonuç

**Canlıdaki düşüşün eval'de yeniden üretilip üretilmediği (a, b, g):**

| Soru | Canlı P2B (2 smoke koşusu) | Eval ALL (P2B) | Eval BASE (P2A) |
|---|---|---|---|
| g | 1/2 düştü | **2/5 düştü** | 0/8 düştü |
| a | 1/2 düştü | **1/5 düştü** | 0/8 düştü |
| b | 1/2 düştü | **0/5 düştü**; router DOCUMENT→MIXED **5/5** | 0/8 düştü; router DOCUMENT **8/8** |

- **Tabanda a, b, g:** 24 denemede 24 doğru, router dağılımı sabit (a, g MIXED 8/8, b DOCUMENT 8/8).
- **ALL'da a, b, g:** 15 denemede 12 doğru. Düşen 3'ün hepsi Karatepe Excel yarısı.
  - g ×2: Excel yarısı 15.240.080,45 verdi (beklenen 11.671.800).
  - a ×1: Excel "bulamadım" dedi.
- **b:** ALL'da değer 5/5 doğru, ama router kararı 5/5 değişti. Canlıda da b iki koşuda MIXED'e gitmişti.

**Başka projenin rakamı:** iki kolda da **0**. Kriterler: workbook projesi ≠ soru projesi; j/k/o/p/q/r'de 11.671.800 ya da 1,37.

**Ek bulgu, taban:** BASE'te **4 HTTP 500** (p 3/8, q 1/8). ALL'da 0. Ayrıntı §5.

**Maliyet:** **$1,0703** (bütçe $3,00): BASE $0,5689, ALL $0,5014. Yalnız eval'de, canlıya istek yok.

## 2. Ortam ve güvenlik kontrolleri

**Canlı parmak izi:**

| | Başta (15:15:14Z) | Sonda (15:47:13Z) |
|---|---|---|
| Canlı backend StartedAt | `2026-10-17T15:02:05.996Z` | **aynı** |
| Canlı HEAD | `f03f765` | **aynı** |
| `git status --short` (ana klasör) | `?? logs/` | `?? logs/`, `?? results/p2c/` |
| Canlı DB (SELECT): documents / chunks / audit_log / alembic | 113 / 461 / **1707** / 0016 | 113 / 461 / **1711** / 0016 |

**Canlı audit artışı (+4) bu ölçümden değil:**
- Bütün smoke istekleri eval IP'sine (`172.19.0.3:8000`) gitti. 152 eval audit satırı eval DB'de.
- Eval yanıtlarının `audit_log_id`'leri eval `audit.jsonl` ile eşleşiyor.
- Canlı +4 satırın hepsi `admin` kullanıcısından ve spec'te olmayan sorular: 15:21:36 "Kızıltepe'nin Çed belgesini göster", 15:21:55 "Kızılova", 15:22:30 "Kızılova'nın şirket yapısı nasıl", 15:40:26 "Bütün projelerimizi alt alta sırala". Spec'te admin kullanıcısı yok.
- Canlı değişmediği için dur koşulu tetiklenmedi.

**Kurallar:**
- **Ana klasörde `git checkout`/`switch`/`apply` yok.**
- Kollar ayrı worktree'lerde:
  - `/home/naci/company-ai-arms/base` = `faedc84` + log yaması
  - `/home/naci/company-ai-arms/all` = `da3dd08` + log yaması
  - İş sonunda ikisi de `git worktree remove` ile silindi.
- Bütün compose komutları açık `-p company-ai-eval` ile. `make` kullanılmadı.
  - `config`: `name: company-ai-eval`, `DATABASE_URL …/company_ai_eval`.
- Eval backend her kolda `results/p2c/start_arm.sh` ile yeniden yaratıldı (`-v <worktree>/backend:/app`, D3/P1M'deki `-e` bayrakları).
- Sürücü (`results/p2c/drive_p2c.py`) `--base-url http://172.19.0.3:8000 --env infra/.env.eval` ile çağırdı. URL `localhost`, `127.0.0.1` ya da `8080` içerseydi koşmadan çıkacaktı.

**Her kolda kontrol** (`results/p2c/check_arm.sh`, çıktı aşağıda):

| Kontrol | BASE (15:16 ve 15:40) | ALL (15:27) |
|---|---|---|
| `/app` kaynağı | `/home/naci/company-ai-arms/base/backend` | `/home/naci/company-ai-arms/all/backend` |
| `repayment schedule row` (router.py) | 0 | 2 (cümle + örneğin `reason`'u) |
| `use a superseded one` (excel_ask.py) | 0 | 1 |
| `def _workbook_line` | 0 | 1 |
| `def split_footer` (calc.py) | 0 | 1 |
| P2C log yaması | 1 | 1 |
| Ayarlar | anthropic · haiku-5-5 / haiku-5-5 · plan sonnet-5-5 · anthropic_thinking False · answer_thinking True/8192 · ek_f True · assist False · demo_today 2026-10-06 · db `company_ai_eval` | aynı |

**Eval DB:**
- Önce: documents 113, xlsx 7, audit_log 607, alembic 0016.
- Sonra: 113, 7, **759** (+152), 0016.
- 156 istekten 152'si audit'te. Eksik 4 = HTTP 500'ler (yakalanmayan hata audit yazmıyor).
- Belge ve ayar değişmedi. Ocr-worker açılmadı.

**Kapanış:** `docker rm -f company-ai-eval-backend-1`, `$EC down`. Eval container'ı kalmadı. Worktree'ler silindi.

**Log yaması** (`results/p2c/patches/plan_log.patch`): `excel_ask.request_plan` içinde planı `log.info("excel plan", …)` ile yazan tek satır (+ değişken). İki kola da aynı uygulandı. Ürün koduna commit edilmedi; ana klasörde yok.

## 3. Sıra ve zaman

| Kol | Tekrarlar | Zaman (UTC) | Geçiş başına | Smoke özeti |
|---|---|---|---|---|
| BASE | 1–5 | 15:16–15:27 | ~120 sn | 12, 12, 12, 12, 11/12 |
| ALL | 1–5 | 15:27–15:40 | ~145 sn | 12, 11, 12, 11, 11/12 |
| BASE | 6–8 | 15:40–15:47 | ~123 sn | 11, 11, 11/12 |

## 4. Kol × soru

Kaynak: `results/p2c/summary.md` (`analyze_p2c.py`). Ham satırlar `results/p2c/rows.jsonl`.

**Sütunlar:**
- **Doğru:** a/b/g/l'de beklenen değer smoke'taki gibi aranır (MIXED cevapta Excel yarısında, diğerlerinde tüm cevapta). m/o/q/r'de tüm cevapta aranır.
- **Excel'den doğru:** o/q/r için değer Excel yarısında ve Excel kaynağı var.
- Router "None" = HTTP 500 (yanıtta tür yok).

| Soru | Kol | N | Router | Excel kaynağı | Doğru | Excel'den doğru | Smoke geçti | Excel "bulamadım" | HTTP 500 | Başka proje (workbook / rakam) |
|---|---|---|---|---|---|---|---|---|---|---|
| a | base | 8 | MIX 8 | Financial_Model_2026 8 | 8/8 | — | 8/8 | 0/8 | 0 | 0 / 0 |
| a | all | 5 | MIX 5 | Financial_Model_2026 4 | 4/5 | — | 4/5 | 1/5 | 0 | 0 / 0 |
| b | base | 8 | DOC 8 | — | 8/8 | — | 8/8 | 0/8 | 0 | 0 / 0 |
| b | all | 5 | MIX 5 | Financial_Model_2026 5 | 5/5 | — | 5/5 | 0/5 | 0 | 0 / 0 |
| g | base | 8 | MIX 8 | Financial_Model_2026 8 | 8/8 | — | 8/8 | 0/8 | 0 | 0 / 0 |
| g | all | 5 | MIX 5 | Financial_Model_2026 5 | 3/5 | — | 3/5 | 0/5 | 0 | 0 / 0 |
| j | base | 8 | MIX 8 | — | — | — | 8/8 | 8/8 | 0 | 0 / 0 |
| j | all | 5 | MIX 5 | — | — | — | 5/5 | 5/5 | 0 | 0 / 0 |
| k | base | 8 | MIX 8 | — | — | — | 8/8 | 8/8 | 0 | 0 / 0 |
| k | all | 5 | MIX 5 | — | — | — | 5/5 | 5/5 | 0 | 0 / 0 |
| l | base | 8 | MIX 8 | Financial_Model_2026 8 | 8/8 | — | 8/8 | 0/8 | 0 | 0 / 0 |
| l | all | 5 | MIX 5 | Financial_Model_2026 5 | 5/5 | — | 5/5 | 0/5 | 0 | 0 / 0 |
| m | base | 8 | DOC 8 | — | 8/8 | — | 8/8 | 0/8 | 0 | 0 / 0 |
| m | all | 5 | DOC 5 | — | 5/5 | — | 5/5 | 0/5 | 0 | 0 / 0 |
| n | base | 8 | DOC 8 | — | — | — | 8/8 | 0/8 | 0 | 0 / 0 |
| n | all | 5 | DOC 5 | — | — | — | 5/5 | 0/5 | 0 | 0 / 0 |
| o | base | 8 | DOC 8 | — | 8/8 | 0/8 | 8/8 | 0/8 | 0 | 0 / 0 |
| o | all | 5 | DATA 5 | Yesilova_Repayment_Schedule_2026-09 5 | 5/5 | 5/5 | 5/5 | 0/5 | 0 | 0 / 0 |
| p | base | 8 | MIX 5, 500 3 | Yesilova_Repayment_Schedule_2026-09 4 | — | — | 5/8 | 5/8 | **3** | 0 / 0 |
| p | all | 5 | MIX 5 | Yesilova_Repayment_Schedule_2026-09 2 | — | — | 5/5 | 2/5 | 0 | 0 / 0 |
| q | base | 8 | MIX 7, 500 1 | Yesilova_Repayment_Schedule_2026-09 6 | 7/8 | 0/8 | 7/8 | 7/8 | **1** | 0 / 0 |
| q | all | 5 | DATA 4, MIX 1 | Yesilova_Repayment_Schedule_2026-09 5 | 5/5 | 5/5 | 5/5 | 0/5 | 0 | 0 / 0 |
| r | base | 8 | DOC 8 | — | 0/8 | 0/8 | 8/8 | 0/8 | 0 | 0 / 0 |
| r | all | 5 | DOC 5 | — | 0/5 | 0/5 | 5/5 | 0/5 | 0 | 0 / 0 |

**Notlar:**
- **j, k:** "Excel bulamadım" 8/8 ve 5/5. Bu, P2A'nın beklenen davranışı: Yeşilova/Boztepe borç ve DSCR workbook'u yok. Belge yarısı cevap veriyor.
- **o:** BASE'te router 8/8 DOCUMENT; 98.000 belge metninden geliyor (sözleşmedeki "her taksit 98.000 USD"). ALL'da router 5/5 DATA; değer Excel'den.
- **q:** BASE'te Excel yarısı 7/8 "bulamadım"; 14.10.2026 belge yarısından (banka bildirimi). ALL'da Excel'den 5/5.
- **r:** Boztepe 12. taksit iki kolda da 13/13 DOCUMENT'a gitti ve değer hiç verilmedi. ALL'daki router cümlesi bu soruyu DATA'ya çevirmedi.

## 5. Taban gürültüsü ve ek bulgular

**a, b, g, l, m, n, o, j, k (BASE):** 8 tekrarda router kararı ve değer **değişmedi** (her biri 8/8 aynı tür, 8/8 doğru).

**BASE'te HTTP 500 (4 istek):** hepsi Excel SQL çalışırken DuckDB `BinderException`:

| Saat | Soru | Hata (log) |
|---|---|---|
| 15:27:00 | p | `sum(VARCHAR)`: `SELECT SUM(col_c) AS principal_2027 … FROM yesilova_repayment_schedule_2026_09__schedule …` |
| 15:42:26 | p | `sum(VARCHAR)` |
| 15:44:42 | q | `Cannot compare values of type VARCHAR and type TIMESTAMP` |
| 15:46:27 | p | `sum(VARCHAR)` |

- `run_sql` bu istisnayı `ExcelError`'a çevirmiyor. Yalnız zaman aşımı yakalanıyor, bu yüzden yanıt 500 oluyor ve audit satırı yazılmıyor.
- Bu taban kodu (**şu an canlıda çalışan P2A**). Kod değiştirilmedi (emir).
- ALL'da aynı sorularda 500 yok. ALL'da sütunlar tipli (`vade` tarih, `anapara_usd` sayı).

**Ölçülmüş farklar (BASE → ALL; sebep iddiası değil):**

| | BASE | ALL |
|---|---|---|
| g: router `reason`'unda "repayment schedule" | 2/8 | 5/5 |
| g: `data_question`'da "ödeme planı" | 0/8 | 4/5 |
| g: "excel sql result not scalar" (yeniden plan) | 0/8 | 3/5 |
| l: router `reason`'unda "repayment schedule" | 0/8 | 5/5 |
| l: `data_question`'da "ödeme planı" | 0/8 | 5/5 |
| b: Excel plan çağrısı | 0 (DOCUMENT) | 5 |

**ALL'daki 3 düşüşün ham kaydı** (`rows.jsonl`):
- **g rep2:**
  - `data_question`: "Karatepe için ödeme planında henüz ödenmemiş (kalan) anapara ve faiz toplamı ne kadardır?"
  - 1. plan: `SELECT SUM(principal_usd) AS remaining_principal_usd, SUM(interest_usd) …, SUM(principal_usd) + SUM(interest_usd) … FROM financial_model_2026__debt WHERE end_date > DATE '2026-10-06'` (3 sütun, tek değer değil).
  - 2. plan: `SELECT SUM(principal_usd) + SUM(interest_usd) AS total_remaining_usd … WHERE end_date > DATE '2026-10-06'`.
  - Excel yarısı: "Karatepe için ödenmemiş anapara ve faiz toplamı 15.240.080,45'tir."
- **g rep5:** aynı biçim (`future_ok: true` ile), aynı sonuç 15.240.080,45.
- **a rep4:** planlayıcı cevabı ayrıştırılamadı (`{"kind": "none", "reason": "unparseable plan"}`). Excel yarısı "bulamadım".

15.240.080,45 Karatepe'nin kendi Debt sayfasından geliyor (proje doğru). Ölçü farklı: kalan anapara + faiz toplamı.

## 6. Plan §5 karar kuralına göre durum (yalnız sayılar)

| Kural | a | b | g |
|---|---|---|---|
| 1. Başarı farkı (BASE ≤ 1/8 ve ALL ≥ 3/5 düşüş) | 0/8 → 1/5: **eşik altı** | 0/8 → 0/5: yok | 0/8 → 2/5: **eşik altı** |
| 2. Router kayması (BASE ≥ 7/8 tek tür, ALL ≤ 2/5 aynı tür) | MIX 8/8 → 5/5: yok | DOC 8/8 → **0/5**: **var** | MIX 8/8 → 5/5: yok |
| 3. Başka projenin rakamı | 0 | 0 | 0 |

**Plan §5 doğrulama şartı:** "ALL, a/b/g'de sinyal üretmeli". b'de router kayması sinyali var. a ve g'de düşüş var ama eşik altında (1/5, 2/5). Yani eval canlıdaki tabloyu **kısmen** üretti: b kayması tam, a/g düşüşü daha seyrek.

Aşama 2'ye geçme kararı Naci'nin.

## 7. Dosyalar (`results/p2c/`, commit edildi)

| Dosya | İçerik |
|---|---|
| `spec.json` | 12 soru (smoke_live biçimi; `questions.json`'a girmedi) |
| `patches/plan_log.patch` | ölçüm log yaması (ürün koduna commit edilmedi) |
| `start_arm.sh`, `check_arm.sh`, `drive_p2c.py`, `analyze_p2c.py` | kurulum, kontrol, sürücü (bütçe/URL koruması), analiz |
| `eval_ip.txt` | eval backend IP'si |
| `base/backend.log`, `all/backend.log` | eval backend'in tam logu (`docker logs -f`, container silinmeden önce) |
| `base/rep1..8/`, `all/rep1..5/` | her geçişin `smoke_*_<harf>.json` yanıtları + `smoke_stdout.txt` |
| `audit.jsonl` | eval audit_log satırları (15:16Z sonrası, 152) |
| `rows.jsonl`, `summary.md` | analiz çıktısı |

## 8. Maliyet

| | Çağrı (request_id'li) | USD |
|---|---|---|
| BASE (8 geçiş) | — | 0,5689 |
| ALL (5 geçiş) | — | 0,5014 |
| **Toplam** | 478 (fiyatsız 0) | **1,0703** |

- Planda tahmin $1,8 idi (aralık daha yüksekti). Gerçek değer daha düşük.
- Arka plan (`request_id` boş) LLM çağrısı: 0.
- Bütçe $3,00, aşılmadı. Sürücü her geçişten önce "toplam + $0,25 > $3,00" kontrolü yaptı.

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (+ ADT-4). Okunan: Çekirdek (Ç-9, Ç-15, Ç-16); P2C planı; P2B, P2B_CANLI
Ürün etiketi      : Ürün 1 — T-11 (P2B'nin geri alınma sebebini ayırma ölçüsü; yeni yetenek yok)
Kritik Geliştirme Kararı : Yok. Ölçüm yalnız eval ortamında (Naci onayı 17.10.2026, plan f03f765;
  S-1/S-2/S-3 evet). Ç-15/6 yok (canlıya bir şey alınmadı, canlıya istek yok). Ç-15/8 yok (kollar
  onaylı P2B metinleri; prompt canlıya girmedi). Ç-15/4 yok (şema yok)
Gizli bilgi / yeni bağımlılık : Yok — .env/.env.eval değişmedi; parolalar smoke_live içinde .env.eval'den,
  yazdırılmadı; yeni paket yok
Kapsam dışı değişiklik : Yok — ürün kodu, prompt, soru seti, canlı servis ve eval DB içeriği dokunulmadı
  (eval DB'ye yalnız ölçümün kendi 152 audit satırı). Ölçüm log yaması yalnız worktree'lerde, dosya olarak
  results/p2c/patches/ altında. Ana klasörde git checkout yok. Git'te yalnız bu rapor + results/p2c/
Dur koşulları     : tetiklenmedi — canlı backend StartedAt ve HEAD aynı; eval container'ının /app'ı her
  kolda doğru worktree; bütçe aşılmadı
Kendi başına verilen kararlar :
  1. "Doğru" kuralı: a/b/g/l smoke'taki gibi Excel yarısı; m/o/q/r tüm cevap; o/q/r için ayrıca
     "Excel'den doğru" (§4)
  2. HTTP 500 satırları "smoke geçti" sayılmadı; router sütununda "500" diye ayrıldı
  3. Maliyet request_id'li bütün llm call satırlarından (500'lerin çağrıları dahil; audit'te olmadıkları
     için satır bazlı toplam $1,0308 daha düşük)
  4. BASE'teki 500'ler (canlı P2A kodunda run_sql BinderException) yalnız raporlandı; düzeltilmedi
  5. Eşik altı farklar "eşik altı" diye yazıldı; sebep iddiası yok
```
