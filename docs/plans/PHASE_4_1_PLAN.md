# Phase 4.1 — Eval runner (karne): Implementation Plan

## Bağlam ve tespitler

Phase 3.4 (`phase-3-4`) Adım 3'ü kapattı; Adım 4'ün ilk fazı `scripts/run_eval.py`'yi yazıyor:
`seed_data/evaluation/questions.json` (43 soru) → gerçek `/api/ask` çağrıları (`ask_as_user` ile giriş yapılmış) →
normalize edilmiş skor → `seed_data/evaluation/results/<model>_<date>/` altına markdown + JSON.

Okunanlar: `docs/PHASES.md` (Phase 4.1 + ön koşul notu), `docs/SPEC_05_synthetic_veri_ve_evaluation.md` §9-11,
kod: `backend/app/api/ask.py`, `backend/app/services/ask.py`, `backend/app/schemas/ask.py`,
`backend/app/api/auth.py`, `backend/app/services/demo_users_seed.py`, `seed_data/evaluation/questions.json`
(gerçek 43 soru, canlı yüklendi), `seed_data/generator/{facts.py,validate_ledger.py,ledger_schema.py}`,
`seed_data/documents/manifest.json` (15 belgenin gerçek `title`/`document_type`/`project_code`'ı), `Makefile`
(`eval`/`test-llm` hedefleri), `infra/docker-compose.yml` (backend servisinin `environment`/`volumes`/ağ takma adı).

### T1 — `questions.json` zaten Pydantic şemalı, elle parse gerekmiyor
`seed_data/generator/ledger_schema.py::QuestionSet`/`Question` (`extra="forbid"`, `ask_as_user: DemoUser`,
`category: QuestionCategory`) `validate_ledger.py`'de zaten kullanılıyor. `run_eval.py` aynı modeli import eder
(`ledger_fixtures.py`'nin test'lerde `seed_data.generator`'ı doğrudan import etme emsali — ADR-013 yalnızca
`app/`'i (üretim kodu) bağlar, script'i değil).

### T2 — `expected_answer` her zaman bir **ledger yolu**, düz metin değil
Gerçek veriyi çözdüm (43 sorunun tamamı canlı `resolve_path` ile): sonuçlar `date` (6), sayı/oran/para (11),
düz string/enum (5), `DOC-*` belge-id string'i (3, bir belgeyi "bu" diye işaret ediyor — literal metin değil),
liste (4, `facility_chain`/`pending_steps`/`permits_completed` gibi çok-değerli alanlar) ve `None` (3, "henüz
olmadı" tipi negatif gerçek — örn. `izmir_res.project.timeline.licence`) olmak üzere karışık. `expected_answer_
aliases` **43 sorunun 0'ında dolu** — SPEC_05 §9'daki `["1,20x", "1.2"]` örneği bu veri setinde hiç kullanılmamış.
Bu yüzden karşılaştırma normalizasyonunu runner'ın kendisi üretmek zorunda (bkz. §2).

### T3 — `facts.py::format_value` demo belgelere gömülen **gerçek** metin — yeniden icat etmiyorum
`seed_data/generator/facts.py`, ledger değerlerini demo PDF'lere basılan **aynı** biçimde üretiyor (`format_date`
→ `GG.AA.YYYY`, `_format_ratio` → `1,20x`, `_format_money` → `50.400.000 EUR`, `format_percent` → `%3,25` vb.);
`answer_prompt.py`'nin sistem promptu da LLM'e **birebir aynı** biçimi emrediyor ("tarihleri GG.AA.YYYY biçiminde
yaz", "(örneğin 1,20x)" — `backend/app/services/answer_prompt.py:49`). Yani cevap metninde beklenen sayı/tarih
formatı, kaynak belgede zaten o formatta yazılı — `run_eval.py` kendi formatlayıcısını yazmak yerine
`facts.format_value(field_name, value, "tr")`'ü çağırır; `field_name`, ledger yolundaki `_FIELD_KIND` anahtarlarından
biriyle **alt-string eşleşmesiyle** bulunur (örn. yol `...finance.outstanding_debt_as_of_demo_today.value` içinde
`outstanding_debt` anahtarı geçiyor → `money`). Bu yaklaşımı gerçek 43 soru üzerinde denedim: `date`/`number`/
`money`/`percent`/`ratio`/`ordinal` tiplerinin **tamamı** (17/17) doğru `field_name`'e eşleşip doğru biçimlendi.

### T4 — para birimi ledger'da kardeş alan (`currency`), `value` değil
`total_debt: {value: 50400000, currency: EUR, ...}` — `money` tipi için runner, `...value` son ekini atıp üst
düğümü (`{value, currency, ...}`) çözer, `_format_money(node["value"], "tr", node["currency"])` çağırır (sabit
`"EUR"` varsaymaz — ileride başka para birimi eklenirse kırılmaz).

### T5 — kaynak (required/forbidden) eşlemesi `validate_ledger.py`'nin kendi mantığıyla birebir aynı olmalı
`check_questions()` (`validate_ledger.py:670-687`) her `required_sources`/`forbidden_sources` girdisinin bir belge
**adı** (title) veya belge **tipi** (document_type) olabileceğini zaten doğruluyor (örn. `"Facility Agreement"`
üç ayrı belgenin tipi — base + 2 amendment). `run_eval.py` aynı ikili eşlemeyi, `AskResponse.sources[].title`'a
karşı çalıştırır: `seed_data/documents/manifest.json`'dan (yerelde okunur, ekstra API çağrısı gerekmez) bir kere
`title → document_type` ve `title → project_name` (proje kodu `ANK_RES`/`IZM_RES` → `"Ankara RES"`/`"İzmir RES"`
sabit eşlemesiyle) tablosu kurulur. `forbidden_sources` ayrıca proje **adı** da olabiliyor (`"İzmir RES"`,
`validate_ledger.py`'nin `project_names` kontrolüyle aynı) — üç seviyeli kontrol (title / type / project) hem
required hem forbidden için uygulanır.

### T6 — model karşılaştırması: `/api/ask` çağıran servis **kalıcı**, `test-llm`'in tek-seferlik container'ı değil
`make test-llm MODEL=...`, LLM istemcisini bir **tek-seferlik** `docker compose run` içinde kuruyor — env override
o container'a özel, çalışan `backend` servisini etkilemiyor. `run_eval.py` ise gerçek `POST http://backend:8000/api/
ask`'i çağırıyor (spec: "questions.json → /api/ask"), yani **kalıcı `backend` servisinin** o an hangi
`LLM_MODEL_ANSWER`'la ayağa kalktığı önemli. `docker-compose.yml`'de bugün `LLM_MODEL_ANSWER` yalnızca
`env_file: .env`'den geliyor, servisin `environment:` bloğunda `${...}` ile yeniden ifade edilmiyor — yani
`LLM_MODEL_ANSWER=X docker compose up -d backend` çalıştırmak **hiçbir şey değiştirmez** (compose, host'un shell
env'ini container'a otomatik geçirmez, yalnızca `.env` dosyasını veya `environment:`'ta açıkça `${VAR}` ile
referans edilen değişkenleri geçirir). **Küçük ama gerekli kod değişikliği:** `docker-compose.yml`'nin `backend`
servisine `environment:` altına `LLM_MODEL_ANSWER: ${LLM_MODEL_ANSWER}` eklenir (mevcut `DATABASE_URL` vb. ile
aynı desen) — böylece `make eval MODEL=gemini-3.5-flash`, Makefile'da `LLM_MODEL_ANSWER=$(MODEL) $(COMPOSE) up -d
backend` çalıştırınca compose, servisi **yeniden oluşturur** (env fark ettiği için) ve gerçek çalışan backend o
modeli kullanır. **Yan etki (SORU 2'de netleştiriliyor):** bu, `.env`'i değiştirmeden `backend` servisini kalıcı
olarak farklı bir modelle bırakır — bir sonraki `make up` veya başka bir `make eval MODEL=...` çağrısına kadar.

### T7 — `scripts/` bugün backend container'ına mount edilmiyor
`docker-compose.yml`'de `backend` yalnızca `./backend:/app` ve `./seed_data:/app/seed_data` mount ediyor;
`./scripts` yok. `scripts/run_eval.py`'nin `python scripts/run_eval.py` olarak container içinde çalışabilmesi
için `./scripts:/app/scripts` mount'u eklenir (mevcut `seed_data` deseniyle birebir aynı) — script değişikliğinde
image yeniden build gerekmez.

### T8 — Gemini ücretsiz katman: iki farklı hata modu, farklı tepki gerektiriyor
`.env`'de bugün `LLM_MODEL_ANSWER=gemini-3.5-flash-lite` (Phase 3.2/3.3/3.4 deneyiminden — `.env.example`'daki
`gemini-3.8-flash` yerine). `OpenAICompatibleClient` zaten SDK-seviyesinde `max_retries=1` ile 429/5xx'e karşı bir
tur kendi backoff'unu yapıyor (`openai_compatible.py:36`); yine de tükenirse `/api/ask` her zaman **503** döner
(`llm_exception_handler`, tüm `LLMError` alt sınıflarını 503'e eşliyor — rate-limit ile gerçek kesinti ayrımı HTTP
seviyesinde yok). İki senaryo ayrılmalı: (a) **dakikalık hız sınırı** (5 istek/dk, "high demand" 503) — kısa
bekleme + retry ile geçer; (b) **günlük kota tükenmesi** — retry işe yaramaz, sonsuz döngüye girmemeli. Runner bu
ikisini yanıt içeriğinden ayıramaz (backend, detayı loga yazıp kullanıcıya yalnızca sabit Türkçe mesaj döner) —
bu yüzden runner sabit sayıda deneme sonrası **pes eder ve soruyu `error` olarak işaretleyip devam eder**, sonsuz
retry döngüsü kurmaz (§3).

---

## 1. `scripts/run_eval.py` — mimari

```
load_questions(path) -> QuestionSet                    # ledger_schema.QuestionSet, doğrudan import
build_document_catalog(manifest_path) -> DocumentCatalog  # title→type, title→project (yerel dosyadan)
resolve_expected(question, raws) -> ExpectedValue | None  # T2/T3/T4; None = "değer kontrolü atlanıyor"
EvalSession(base_url, username, password)               # httpx.Client, tek login, cookie yeniden kullanılır
ask(session_by_user, question) -> AskOutcome             # POST /api/ask + hız sınırlama + retry (§3)
score(question, outcome, expected, catalog) -> QuestionResult
run(questions, sessions, catalog, raws) -> EvalReport    # tüm soruları sırayla işler, ilerleme stderr'e yazılır
write_report(report, out_dir)                            # results.json + results.md
```

`ask_as_user` yalnızca `"enerji"`/`"finans"` (43 sorunun tamamında — doğrulandı); her ikisi için de
`app.core.config.get_settings().demo_user_password` ile bir kez `/api/auth/login` yapılır, `httpx.Client` cookie'yi
saklar, sonraki tüm sorular aynı client'ı yeniden kullanır (43 kez login yok).

**HTTP hedefi:** `http://backend:8000` (compose ağı içi takma ad, Phase 3.3'ten beri backend'in tek erişim yolu;
Caddy/frontend'e bağımlı değil — `make up` her ikisini de içerir ama runner yalnızca `backend`+`postgres`
ayaktayken de çalışır).

## 2. Değer karşılaştırma — normalize edilmiş, katmanlı

Her sorunun `expected_answer`'ı çözülür (`resolve_path`) ve **Python tipine göre** sınıflandırılır:

| Tip | Örnek | Karşılaştırma |
|---|---|---|
| `date` | `2020-06-15` | `facts.format_date(v, "tr")` = `"15.06.2020"` alt-string kontrolü; ayrıca ISO `"2020-06-15"` de aday olarak eklenir (LLM sapıp ISO yazarsa da yakalansın diye, ama asıl beklenen TR biçimi) |
| `number` (money/ratio/percent/plain+birim, `_FIELD_KIND` alt-string eşleşmesiyle) | `1.2` → `dscr_covenant` | `facts.format_value(matched_key, v, "tr")` = `"1,20x"`; ek alias: nokta-ondalık biçim (`"1.20x"`) — LLM bazen İngilizce ondalık yazabilir, bu esneklik payı |
| `number`, eşleşmeyen alan | (gözlenmedi ama olabilir) | TR yerel biçimi (binlik nokta, ondalık virgül), birimsiz |
| `string`, `DOC-` ile başlamıyor | `"development"`, `"ongoing"`, `"pass"` | **küçük, elle hazırlanmış eşanlam tablosu** (§2.1) — tabloda yoksa değer kontrolü atlanır, yalnızca kaynak kontrolü geçerli sayılır |
| `string`, `DOC-` ile başlıyor | `"DOC-ANK-EPC-001"` | değer kontrolü **hep atlanır** — bu zaten `required_sources`'ın işi (o belgenin `title`'ı `required_sources`'ta ayrıca listeleniyor, T5 kontrolü asıl kanıt) |
| `list` / `dict` | `facility_chain`, `pending_steps` | değer kontrolü **atlanır** (bkz. SORU 1) |
| `None`, `expect_no_answer=False` | `izmir_res.project.timeline.licence` | "negatif gerçek" — değer kontrolü atlanır, yalnızca `answered=True` beklenir (LLM'in "hayır/henüz alınmadı" türü bir şey söylemesi bekleniyor ama literal metni önceden bilinemiyor) |

### 2.1 String eşanlam tablosu (implementasyonda gerçek belge metnine bakılarak dolduruluyor)
Şu an ledger'da görülen 5 string değer: `project.stage` (`development`/`construction`/`operation`),
`ced_status.value` (`ongoing`), `covenant_tests[-1].result` (`pass`/`fail`). Bunlar `facts.py`'nin token
biçimlendirme tablosunda yok (belge içi serbest metne düşüyorlar) — implementasyon sırasında üretilmiş gerçek
PDF'lerdeki karşılık gelen cümle bir kez okunup üç-dört karşılığı (TR + varsa EN, çünkü finans belgeleri EN)
elle eşlenir. Karşılığı bulunamayan/gelecekte eklenecek bir string alanı sessizce "atlandı" sayılır, asla
sessizce "geçti" sayılmaz.

## 3. Gemini ücretsiz katmana uyum

- **Hız sınırı:** her `/api/ask` çağrısından önce, son çağrıdan bu yana geçen süre `--min-interval-s`'den
  (varsayılan **13 sn** — 5 istek/dk'nın altında güvenli pay) azsa fark kadar uyunur. Tek `EvalSession` başına
  değil, **tüm oturumlar arasında paylaşılan** global bir "son istek zamanı" değişkeniyle (enerji+finans ardışık
  çalışıyor, ikisi birden paylaşımlı kotayı tüketiyor).
- **Retry:** bir çağrı 503 dönerse (rate limit veya geçici kesinti ayrımı yapılamıyor, T8), `--max-retries`
  (varsayılan 3) kez, artan bekleme ile (10 sn, 20 sn, 40 sn) tekrar denenir. Tüm denemeler tükenirse soru
  `error: "llm_unavailable_after_retries"` ile **hata** olarak işaretlenir (başarısız/`answered=False` değil —
  ayrı bir üçüncü durum: rapor bunu "puanlanamadı" diye ayrı sayar, %80/%100 paydasından **çıkarılır**, kaç
  sorunun bu şekilde atlandığı rapor özetinde açıkça yazılır).
- **Günlük kota tükenmesi:** ayrı bir sinyal yok (T8) — 5 ardışık soru üst üste retry-tükenmesiyle başarısız
  olursa (yapılandırılabilir eşik, varsayılan 5) runner **tüm koşuyu durdurur** ("günlük kota tükenmiş olabilir,
  bkz. Gemini konsolu" mesajıyla), kalan sorular için sahte `error` satırları üretip yanıltıcı bir "%X başarı"
  raporu basmaz — o ana kadarki kısmi sonuç yine de yazılır (`partial: true` bayrağıyla JSON'da işaretli).

## 4. Çıktı formatı

`seed_data/evaluation/results/<model>_<YYYY-MM-DD>/` (`.gitignore`'da zaten var, Phase 2.1'den beri):
- `results.json` — her soru için `{id, category, ask_as_user, answered, expected_answered, sources_ok,
  required_sources_missing, forbidden_sources_hit, value_check: "pass"|"fail"|"skipped", passed: bool, error:
  str|null, latency_ms, tokens_in, tokens_out, model}` + üstte `{model, date, demo_today, total, passed, skipped_
  errors, category_breakdown: {kategori: {total, passed, pct}}, project_breakdown, partial: bool}`.
- `results.md` — insan-okunur özet: üstte kategori bazlı tablo (kriter eşiğiyle karşılaştırmalı, ✅/❌), sonra
  başarısız/hata olan her sorunun tek satırlık nedeni (`beklenen X, sources eksik: [...]` / `value mismatch`
  / `llm error`), en altta bilinen sınırlama notu (T-FTS, §5) ve "değer kontrolü atlanan" soruların listesi
  (şeffaflık için — bunlar `passed` sayılmış olsa da hangi sorular olduğu görünür kalsın).

## 5. Ön koşul: FTS'in çoğul/kısaltma zayıflığı — üç seçenek değerlendirmesi

**(a) Golden question metnini değiştir** ("covenant" yerine belge diliyle birebir eşleşen kelime) — **reddedildi**:
SPEC_05 §9'un minimum soru listesi bu soruyu ("ilk DSCR covenant") birebir bu Türkçe/İngilizce karışık haliyle
istiyor; metni FTS'e uydurmak spec'in "gerçekçi doğal dil sorusu" amacını bozar ve testin ölçtüğü şeyi değiştirir
(retrieval sağlamlığını değil, soru yazarının FTS'i bilmesini ölçer hale gelir).

**(b) Prose'a "DSCR"/çoğul kelime anchor'ı ekle** — **reddedildi (bu faz için)**: `seed_data/generator/prose/
*.yaml` ve `facts.py` içeriğine dokunmak Adım 3'ün (belge üretimi) kapsamı; Phase 4.1 yalnızca bir test/ölçüm
aracı yazıyor, içerik üretmiyor. Ayrıca bu zaten Phase 3.2'nin raporunda bilinçli olarak ertelenmiş bir iş
(`docs/reports/PHASE_3_2_REPORT.md §7`) — 4.1 içinde sessizce "düzeltmek" o kararı atlamak olur.

**(c) Bilinen sınırlama olarak eval sonuçlarına not düş — SEÇİLDİ.** Gerekçe: PHASES.md'nin Phase 4.1 ön koşul
notu zaten bunu öneriyor; kök neden zaten teşhis edilmiş (retrieval katmanı, model hatası değil) ve **Phase 3.4
bunu bağımsız olarak çözmüş durumda** — `EMBEDDINGS_ENABLED=true` iken hibrit (FTS+vektör) retrieval, canlı
doğrulanmış şekilde tam bu soruyu buluyor (`docs/reports/PHASE_3_4_REPORT.md §7`). Runner bu ID'yi
(`ANK-FIN-007`, "İlk DSCR covenant neydi?") özel olarak işaretlemez ama **rapor şablonu**, `.env`'deki
`EMBEDDINGS_ENABLED` değerini okuyup başlığa yazar ("bu koşu embedding açık/kapalı çalıştı") — böylece
`false` iken bu sorunun düşmesi "bilinen sınırlama, bkz. Phase 3.4" diye rapor içinde otomatik bağlamlanır
(sabit bir dipnot, ID'ye özel hardcode değil — ileride başka sorular da aynı nedenle düşerse aynı not geçerli
kalır). `true` iken düşerse bu artık "bilinen sınırlama" değil, gerçek bir regresyon sayılır.

## 6. Model karşılaştırması

`make eval MODEL=gemini-3.5-flash` (varsayılan boş = `.env`'deki mevcut `LLM_MODEL_ANSWER`, bugün
`gemini-3.5-flash-lite`):
```makefile
eval: dirs
	$(if $(MODEL),LLM_MODEL_ANSWER=$(MODEL)) $(COMPOSE) up -d --build backend
	$(COMPOSE) run --rm -T backend python scripts/run_eval.py $(EVAL_ARGS)
```
(T6'nın `docker-compose.yml` değişikliğine bağımlı.) İki modelin karşılaştırması: `make eval MODEL=gemini-3.5-
flash-lite` ve `make eval MODEL=gemini-3.5-flash` art arda çalıştırılır — her biri kendi `results/<model>_<date>/`
klasörünü üretir (klasör adı, `--model-label` argümanı yerine **gerçek `AskResponse.model`** alanından — yani
sunucunun fiilen hangi modeli kullandığından — türetilir; Makefile'ın geçtiği `MODEL` ile fiilen çalışanın aynı
olduğunu bağımsızca doğrular). Karşılaştırma için üçüncü bir adım gerekmiyor — iki klasörü yan yana okumak
yeterli (SPEC_05/PHASES.md "iki model karşılaştırma dosyası" derken iki ayrı sonuç klasörünü kastediyor,
otomatik bir diff aracı istemiyor — SORU değil, spec metninden açık).

## 7. Kabul kriteri → kanıt

| Kriter (PHASES.md) | Kanıt |
|---|---|
| `make eval MODEL=…` çalışır | Canlı: `make eval` (varsayılan model) ve `make eval MODEL=gemini-3.5-flash` ikisi de 0 exit code, `results.json`/`results.md` üretir |
| isolation/hallucination/authorization %100 | Bu üç kategori yalnızca `answered==expect_no_answer` + kaynak kontrolüyle puanlanıyor (değer normalizasyonuna bağımlı değil, T5) — rapor kategori tablosunda ayrı satır; %100 değilse runner `exit 1` döner (CI/insan için net sinyal) |
| document/temporal ≥ %80 | Aynı tablo, ayrı eşik; altına düşerse rapor `docs/reports/PHASE_3_2_REPORT.md`'ye (metadata/temporal mantığı) dönülmesi gerektiğini metinde hatırlatır (PHASES.md'nin kendi notu) |
| iki model karşılaştırma dosyası | İki ayrı `results/<model>_<date>/` klasörü, ikisi de commit edilmez (`.gitignore`), rapor (`PHASE_4_1_REPORT.md`) ikisinin özet tablosunu yan yana gösterir |

---

## SORU (Naci cevaplamalı)

1. **Liste/sözlük/negatif-gerçek tipi `expected_answer`'lar için puanlama.** 32 document+temporal sorudan 7'si
   (4 liste — `facility_chain`/`pending_steps`/`permits_completed`; 1 sözlük — `ANK-FIN-013`'ün yolu
   `project.finance.tenor_years` `.initial`/`.current` belirtmeden bir sözlüğe düşüyor, muhtemelen questions.json'da
   eksik bir `.current.value`/`.initial.value` son eki; 2 negatif-gerçek — İzmir'in henüz olmamış lisans/inşaat
   tarihleri) otomatik metin karşılaştırmasıyla güvenilir şekilde doğrulanamıyor (§2). Önerim: bu 7 soru için
   **değer kontrolünü atla, yalnızca kaynak (required/forbidden sources) + `answered` kontrolünü uygula** — yani
   "atlandı" nötr sayılır (ne geçti ne kaldı, ama nihai `passed` hesabına kaynak+answered kontrolü üzerinden
   girer), rapor bu 7'yi açıkça listeler ki %80 eşiği "gerçekte doğrulanmamış" sorularla şişmiş görünmesin. Bunu
   onaylıyor musun, yoksa (a) bu 7 soru puana hiç girmesin (payda 32 değil 25 olsun) yoksa (b) manuel inceleme
   gerektirsin (otomatik olarak hep `fail` sayılsın, sen elle "aslında doğru" diye işaretleyene kadar) mi
   istersin? Ayrıca `ANK-FIN-013`'ün yol eksikliğini (`questions.json`'da `.current.value` veya `.initial.value`
   son eki yok) ayrı, küçük bir veri düzeltmesi olarak bu faz içinde mi düzelteyim (tek satır JSON değişikliği,
   ledger validator zaten `resolve_path`'in başarılı olduğunu doğruluyor — sözlük dönmesi validator'ı da
   kırmıyor çünkü sadece "path çözülüyor mu" kontrol ediyor, "leaf mi" kontrol etmiyor)?
2. **`make eval MODEL=...` çalışan `backend` servisini kalıcı olarak yeniden başlatıyor (T6).** Bu, `.env`'i
   değiştirmeden `docker-compose.yml`'e bir `environment: LLM_MODEL_ANSWER: ${LLM_MODEL_ANSWER}` satırı eklememi
   ve Makefile'ın `backend` servisini `MODEL` verildiğinde yeniden oluşturmasını (recreate) gerektiriyor — servis
   eval sonrası da o modelde kalır (bir sonraki `make up`'a veya başka bir `make eval MODEL=...`'e kadar). Dev
   VM'de tek kullanıcı olduğu için zararsız olmalı ama `test-llm`'in tek-seferlik container'ından farklı olarak
   **paylaşılan servisi** etkiliyor — onaylıyor musun, yoksa eval sonunda otomatik olarak `.env`'deki orijinal
   modele geri dönecek bir adım (`make eval` sonunda `docker compose up -d --build backend` .env'in kendi
   değeriyle tekrar) ekleyeyim mi?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- `run_eval.py`, `seed_data.generator.ledger_schema.QuestionSet` ve `seed_data.generator.facts` modüllerini
  doğrudan import eder (ADR-013 yalnızca `app/`'i bağlar; `ledger_fixtures.py` test emsali).
- HTTP hedefi `http://backend:8000` (compose ağı, Caddy'ye bağımlı değil).
- `ask_as_user` başına tek `EvalSession` (tek login, cookie yeniden kullanılır) — 43 kez login yok.
- Hız sınırı tüm oturumlar arasında paylaşılan global "son istek zamanı" (13 sn varsayılan aralık).
- 503'ler 3 kez artan gecikmeyle yeniden denenir; tükenirse soru "error" (puanlanamadı) sayılır, "başarısız"
  değil — payda dışı tutulur, sayısı raporda ayrı gösterilir.
- 5 ardışık retry-tükenmesi → günlük kota şüphesiyle koşu tamamen durur, o ana kadarki sonuç `partial: true` ile
  yazılır.
- Değer karşılaştırması `facts.py::format_value` + `_FIELD_KIND` alt-string eşleşmesini yeniden kullanır — yeni
  bir formatlayıcı icat edilmiyor (demo belgelere gömülen ve LLM'e emredilen biçimle birebir aynı, T3).
  `DOC-*` string'leri ve liste/sözlük/negatif-gerçek değerler için değer kontrolü atlanır (SORU 1).
  String enum'lar (`development`/`ongoing`/`pass` vb.) için küçük elle hazırlanmış eşanlam tablosu.
- Kaynak (required/forbidden) kontrolü `validate_ledger.py::check_questions`'la aynı üç seviyeli mantık (title /
  document_type / proje adı), `seed_data/documents/manifest.json`'dan yerel olarak kurulan bir katalogla.
- FTS'in çoğul/kısaltma zayıflığı: golden soru metni değiştirilmiyor, prose'a dokunulmuyor — rapor `EMBEDDINGS_
  ENABLED` durumunu başlığa yazan sabit bir dipnotla bağlamlıyor (§5).
- `docker-compose.yml`'e `backend.environment.LLM_MODEL_ANSWER: ${LLM_MODEL_ANSWER}` ve `backend.volumes`'a
  `./scripts:/app/scripts` eklenir (T6/T7) — ikisi de mevcut desenlerin (`DATABASE_URL`, `seed_data` mount'u)
  birebir tekrarı, yeni bir mimari desen değil.
- `results/<model>_<date>/` klasör adı, Makefile'ın geçtiği `MODEL` argümanından değil, `AskResponse.model`'in
  fiilen döndürdüğü değerden türetilir (gerçeği bağımsız doğrulamak için).

## Doküman değişiklikleri

- `docs/reports/PHASE_4_1_REPORT.md`, `docs/PHASES.md` durum satırı, `git tag phase-4-1`.
- `README.md`: "Eval (Phase 4.1)" bölümü — `make eval`, `make eval MODEL=...`, çıktı klasörünün nerede olduğu,
  hız sınırı/retry davranışı, bilinen FTS sınırlaması notu.
- `docs/ARCHITECTURE.md`: yeni ADR gerekmiyor (eval bir test aracı, mimari karar değil) — ADR-007'nin "embedding
  kapalıyken bilinen retrieval sınırlaması" notuna (Phase 3.4'te yazılan) tek cümlelik bir "Phase 4.1'de eval
  raporunda gözlemlendi" eki düşülebilir (küçük, karar değil).

## Uygulama sırası

1. `docker-compose.yml`: `backend.environment.LLM_MODEL_ANSWER` + `backend.volumes` (`./scripts`) eklemeleri.
2. `seed_data/documents/manifest.json` tabanlı `DocumentCatalog` (title→type, title→project) + birim testi
   (backend `tests/` altında değil — `scripts/` için ayrı, hafif bir test dosyası; konumu implementasyonda
   netleşir, küçük teknik detay).
3. `resolve_expected()` (§2) — ledger yolu çözme, tip sınıflandırma, `facts.format_value` entegrasyonu, string
   eşanlam tablosu; gerçek 43 soru üzerinde kuru-çalıştırma (LLM'siz) ile doğrulama.
4. `EvalSession` (login + cookie + hız sınırı + retry, §3).
5. `score()` + `run()` + `write_report()` (§4).
6. `scripts/run_eval.py`'nin CLI arayüzü (`argparse`: `--questions`, `--base-url`, `--min-interval-s`,
   `--max-retries`, `--out-dir`), `Makefile`'ın `eval` hedefi (§6).
7. Canlı koşu: `make eval` (varsayılan `gemini-3.5-flash-lite`) ve `make eval MODEL=gemini-3.5-flash` — ikisinin
   `results.md`'si karşılaştırılır, kabul kriterleri (%100/%80) doğrulanır.
8. `README.md` → rapor → `docs/PHASES.md` → commit + tag `phase-4-1` + push.

## Kritik dosyalar

- `scripts/run_eval.py` (yeni)
- `infra/docker-compose.yml` (backend `environment`/`volumes`)
- `Makefile` (`eval` hedefi)
- `seed_data/evaluation/questions.json` (yalnızca SORU 1'in `ANK-FIN-013` düzeltmesi onaylanırsa dokunulur)
