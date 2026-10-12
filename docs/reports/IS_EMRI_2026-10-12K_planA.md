# İş Emri 2026-10-12K — Haiku geçişi + belirsiz soruda netleştirici soru — FAZ A (salt okunur keşif ve plan)

**Tarih:** 12.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `1f3b6f7`) · **Ürün:** Ürün 1 ·
**Dayanak:** AI-BalBal PR #23 §1 (Tansu, model kararı: Haiku + Haiku; belirsiz soruda netleştirici soru) ve PR #24 §4/4 (sıra) ·
**Anayasa:** Ç-15/8 (sistem promptu / davranış kuralı → önce plan, T-9), Ç-15/6 (üretim `.env` + restart → önce plan), Ç-11(b) (sağlayıcı/Haiku geçişi PR #23 ile Kayıtlı Kanalda onaylı), Ç-16 (kapsam).
**Durum:** ✅ FAZ A bitti — **Tansu onayı bekliyor.** Bu fazda rapor dışında hiçbir dosya değişmedi, hiçbir container durmadı/yeniden başlamadı, `.env` yalnız okundu (aşağıda yalnız anahtar ADLARI ve model adları var, gizli değer yok).

Bu fazda yapılan tek "çalıştırma": backend container'ı içinde LLM'siz, audit yazmayan, salt okunur bir Python kuru koşusu (§3.3; `classify_project_axis`'in 12 soruda ne diyeceği). Canlı süreç ve DB değişmedi.

---

## 0. Özet (karar verecek kişi için)

1. **Kod hazır:** `LLM_PROVIDER=anthropic` + `AnthropicClient` canlı kodda var, 13 birim testi var, D Adım'da 99+99 soruda hatasız koştu. Geçiş yalnız `.env` + `make restart-backend` (≈ 12 s kesinti, J ölçümü).
2. **Maliyet (Haiku 5.5, koddaki sabit $0,10/$0,50 per MTok):** ≈ **$0,004/soru** (D ölçümü: 99 soru $0,40). Sonnet fallback ≈ $0,077/soru (99 soru $7,5). Metadata-öneri döngüsü restart sonrası **yeniden tetiklenmez** (0 aday) → $0.
3. **Netleştirici soru bugün canlıda YOK:** bayraklar kapalı, model belirsiz soruya "proje bazında" sıralayarak cevap veriyor (D'de Haiku 6 belirsiz sorunun 5'ini cevapladı; GEN-AMB-001'de yanlış "vade 14 yıl"). Davranış iki yerde kararlaşıyor: (i) `EK_F_MODE` açıkken kod (`classify_project_axis`, yalnız **proje** ekseni), (ii) bayrak açıkken prompt (kural 11: cevap veremeyince tek SORU:). Hiçbiri "belirsizse cevaplama, sor" demiyor.
4. **Kuru koşu bulgusu (yeni, §3.3):** 113 belgeli canlı DB'de `classify_project_axis` **GEN-AMB-001'de ateşlenmiyor** (`dominant ANK_RES`) — Tansu'nun hedef aldığı soru proje değil **belge** ekseninde belirsiz. Yalnız bayrak açmak bu soruyu çözmez; prompt kuralı (kural 12) gerekir. Ayrıca negatif kontrol GEN-AMB-003-F'de (finans, cevap beklenir) proje ekseni **yanlış pozitif** veriyor (`ANK_RES` vs `YSV_RES`, Yeşilova belgeleri 12.10'da eklendi).
5. **Öneri:** `.env`: provider=anthropic, classify=answer=`claude-haiku-5-5`, **`EK_F_MODE=true`** (netleştirici sorunun kullanıcıya görünmesinin tek yolu; AI-BalBal `assist` bloğunu çizmiyor) + **kural 12** (07.10'da ölçülmüş metin, AYNEN, yalnız `SYSTEM_PROMPT_ASSIST`'e). Kapsam: 1 Python sabiti + 1 liste satırı + prompt dokümanı + 1 test.
6. **Tansu kararı gereken 6 soru** §6'da (en önemlileri: kural 12 metni; eval'da `expect_assist=clarify` ↔ kodun `disambiguate` üretmesi; GEN-AMB-003-F ve ANK-NEG-003 beklentileri yeni kütüphanede).

---

## 1. Model / sağlayıcı envanteri

### 1.1 `.env` LLM anahtarları (adlar) ve hangi kod yolu okuyor

Canlı `.env` ve çalışan container ortamı (`docker exec … env | cut -d= -f1`) aynı adları taşıyor. Değerler yalnız gizli olmayanlar için:

| Anahtar (`.env`) | Canlı değer | `Settings` alanı (`backend/app/core/config.py`) | Okuyan kod yolu |
|---|---|---|---|
| `LLM_PROVIDER` | `openai_compatible` | `llm_provider` (L48) | `services/llm/factory.py::build_llm_client` — tek istemci, `main.py` lifespan + `api/deps` |
| `LLM_BASE_URL` | Gemini OpenAI-uyumlu uç | `llm_base_url` (L49) | yalnız `OpenAICompatibleClient` |
| `LLM_API_KEY` | (dolu, gizli) | `llm_api_key` (L50) | yalnız `OpenAICompatibleClient` |
| `PROSE_ANTHROPIC_API_KEY` | (dolu, gizli) | `anthropic_api_key` (alias, L61–63) | yalnız `AnthropicClient` (factory L17–20). **`ANTHROPIC_API_KEY` adı `.env`'de var ama değeri BOŞ ve app tarafından hiç okunmaz** (bilinçli, config.py yorumu L57–60) |
| `LLM_MODEL_CLASSIFY` | `gemini-3.5-flash-lite` | `llm_model_classify` (L51) | **3 çağrı yolu:** (1) router `services/router.py` L140 (json_object, 300 token); (2) Excel **plan** `services/excel_ask.py` L266 (json_object, 400 token); (3) metadata önerisi `services/metadata_suggestion.py` L226 (json_object, `LLM_MAX_OUTPUT_TOKENS`) |
| `LLM_MODEL_ANSWER` | `gemini-3.5-flash-lite` | `llm_model_answer` (L52) | **2 çağrı yolu:** (1) belge cevabı `services/ask.py` L233; (2) Excel **yorum/cümleleme** `services/excel_ask.py` L375 (sonuç bloğunu Türkçe cümleye çevirir; ADR-011 rakam şablonu kodda) |
| `LLM_TIMEOUT_S` | 60 | `llm_timeout_s` | her iki istemci |
| `LLM_MAX_OUTPUT_TOKENS` | (dolu) | `llm_max_output_tokens` (varsayılan 2048) | belge cevabı, Excel yorum, metadata |
| `LLM_REASONING_EFFORT` | `.env`'de YOK → varsayılan `low` | `llm_reasoning_effort` | Gemini'de `reasoning_effort`; **Anthropic istemcisi bunu iletmez** (düz, thinking'siz çağrı — `anthropic_client.py` docstring) |
| `ANTHROPIC_MAX_RETRIES` | `.env`'de YOK → varsayılan 2 | `anthropic_max_retries` (L64) | `AnthropicClient` (SDK'nın kendi 429/5xx geri çekilmesi) |
| `PROSE_MODEL` | `gemini-3.5-flash` | — (app okumaz) | yalnız `seed_data/generator` `make prose` |
| `EVAL_BUDGET_USD` | `.env`'de YOK, `.env.example`'da YOK | — | yalnız `scripts/run_eval.py` (`--budget-usd` ya da koşu anında env) |
| `ASSIST_MODE` / `EK_F_MODE` | `false` / `false` | `assist_mode_enabled` / `ek_f_enabled` | §2 |
| `DEMO_TODAY` | `2026-10-06` | `demo_today` | `services/temporal.today()` (ADR-026) |

**Tek `LLMClient` örneği** süreç başında kurulur (`main.py` L108–113, `build_llm_client(settings)`); ayarlar yalnız süreç başında okunur → her `.env` değişikliği `make restart-backend` ister. Ayrı "Excel plan modeli" / "metadata modeli" anahtarı **yok**; ikisi de `LLM_MODEL_CLASSIFY`'ı paylaşır (SPEC_01/ADR-009 kararı). Yeni anahtar eklemek Ç-16 dışıdır; önerilmiyor.

### 1.2 Anthropic istemcisi hazır mı?

| Kalem | Durum | Kaynak |
|---|---|---|
| Modül | `backend/app/services/llm/anthropic_client.py` (154 satır): `messages.create(model, max_tokens, system, messages=[user])`; `json_object` isteğinde sistem promptuna "tek JSON, code fence yok" cümlesi eklenir ve ``` fence'i soyulur; `temperature`/`reasoning_effort` iletilmez; hata eşlemesi `openai_compatible.py` ile birebir (401/403→`LLMAuthError`, 429→`LLMRateLimitError`, timeout→`LLMTimeoutError`, 503/529/5xx/bağlantı→`LLMUnavailableError`) | İş Emri 2026-10-11-C Adım 3 |
| Fabrika | `factory.py`: `LLM_PROVIDER=anthropic` + `PROSE_ANTHROPIC_API_KEY` boşsa `LLMNotConfiguredError` → `main.py` metadata döngüsünü "LLM not configured" ile kapatır, `/api/ask` 503 | |
| SDK | `anthropic 1.13.0` (pyproject `anthropic>=1.13,<2`), container'da kurulu; `openai 3.17.0` | `docker exec … python -c "import anthropic"` |
| Testler | `backend/tests/test_anthropic_client.py` **13 test**: istek şekli + usage; JSON suffix + fence soyma; 401/403/429/5xx → LLMError eşlemesi (parametrize); timeout; bağlantı hatası; boş cevap; fabrika (anahtar var/yok/boş); env alias = `PROSE_ANTHROPIC_API_KEY`; 429 ve 529 gövdesinin anahtarsız güvenli loglanması; `_safe_error_summary` bilinmeyen alan/gövde yok. Son tam koşu: backend **685 passed**, worker 18 (H raporu) | |
| 429 davranışı | SDK `max_retries=2` (üstel geri çekilme) → hâlâ 429 ise `LLMRateLimitError` → API **HTTP 503** sabit Türkçe mesaj (README/ADR-009); uyarı logu `llm rate limited (429)` yalnız `type`/`message` alanları (anahtar/header asla değil). Hesap limiti (11-C Adım 1 ölçümü, kod yorumu): **1000 istek/dk, 2.400.000 token/dk** — ek pacing gerekmez. Kredi bakiyesi bu oturumda **kontrol edilmedi** (API çağrısı yapılmadı) → Faz B öncesi Naci konsoldan bakar | `anthropic_client.py` L77–80 |
| Bütçe sayacı | **App içinde yok:** `audit_log.cost_estimate` V0'da bilinçli `NULL` (`audit_writer.py` L67: "no invented per-model pricing"). **Eval'da var:** `scripts/run_eval.py::CostTracker` (`_PRICING_USD_PER_MTOK` L71–77: `claude-haiku-5-5` (0,10; 0,50), `claude-sonnet-5-5` (2,0; 10,0), gemini 0) — `EVAL_BUDGET_USD`/`--budget-usd` aşılınca koşu DURUR; 5 test (`test_run_eval_cost_tracker.py`) | |
| D Adım ortamı | Ayrı compose projesi `company-ai-eval` (kendi postgres/backend, `./data-eval`, `infra/.env.eval`); `env_file: .env` sabit olduğundan backend **`compose run -d --use-aliases -e LLM_PROVIDER=anthropic -e LLM_MODEL_CLASSIFY=claude-haiku-5-5 -e LLM_MODEL_ANSWER=claude-haiku-5-5|claude-sonnet-5-5`** ile açıkça başlatıldı; `ASSIST_MODE`/`EK_F_MODE` kapalı (results.json'da `assist_check: skipped`); `--min-interval-s 2`; `EVAL_BUDGET_USD=10`; 109 belge. Sonuç D-5: C2 ❌ (abstention %66,7 < %71,4; `document` 5 kayıp), C3 ❌ (`document` 4 kayıp); PR #23 §2 ile (d) kriteri **kalktı**, D sonucu aynen kalır | `IS_EMRI_2026-10-11D_adim4/5.md` |

**Doğrulanmış fiyat kaynağı:** `scripts/run_eval.py` L66–67 ("https://claude.com/pricing, 11.10.2026 doğrulandı — Haiku 5.5 $0.10/$0.50, Sonnet 5.5 $2/$10 (≤100K bağlam)"). Bu oturumda web'e çıkılmadı; fiyat **yeniden doğrulanmadı**, koddaki sabit esas alındı. `claude-haiku-5-5` model adı gerçek (audit_log'da API'nin döndürdüğü `model` alanı bu).

### 1.3 Maliyet tahmini

Canlı `audit_log` (1.376 satır, 110 hatalı, 24.09–12.10). **Son 50 hatasız `/api/ask`:** ortalama **31.237 giriş / 321 çıkış** token (router + cevap toplamı; `tokens_in` zaten her iki çağrıyı toplar — `ask_router.py` L307). Karışım: 35 satır `claude-sonnet-5-5` (11.10, İş Emri C'nin 40-soruluk C3 koşusu canlı DB'de), 15 satır `gemini-3.5-flash-lite` (12.10 I/J duman testleri). Tokenizer farkı gerçek: aynı 99 soru için Gemini 21.875 / Claude 35.368 giriş (D sonuç dosyaları) ≈ **1,6×**. Bu yüzden Haiku tahmini için Claude-tokenli D ölçümü daha güvenilir.

| Senaryo | Giriş/çıkış (ortalama) | Hesap (Haiku $0,10 / $0,50 per MTok) | Toplam |
|---|---|---|---|
| Son 50 canlı çağrı, Haiku fiyatıyla (karışık tokenizer, alt sınır) | 31.237 / 321 | 31.237×0,10 + 321×0,50 = 3.124 + 161 µ$ | **≈ $0,0033/çağrı → 50 çağrı ≈ $0,16** |
| **Haiku/Haiku, 99 soru** (D C2 ölçümü, 98 hatasız) | 35.368 / 1.060 | 3.537 + 530 µ$ = $0,00407/soru | **≈ $0,40** (D'de ölçülen: $0,3986) |
| Fallback Haiku router + Sonnet answer, 99 soru (D C3) | 35.369 / 597 | 70.738 + 5.970 µ$ = $0,0767/soru | **≈ $7,59** (D'de ölçülen: $7,5172) |
| Canlı tek duman seti (6 soru, §4) | ~35k / ~1k | | **< $0,03** |
| Metadata-öneri döngüsü, restart sonrası | — | aday = `ingestion_status=ready AND ai_suggestion_id IS NULL` (`document_repo.list_ids_pending_suggestion`) → canlıda **0/113** (113 belgenin hepsinde `ai_suggestion_id` dolu: 86 pending, 27 failed; failed olanlar otomatik yeniden denenmez, `POST …/suggest-metadata` yalnız pending/applied değilse yeniden çağırır) | **$0 — yeniden tetiklenmez** |
| Metadata-öneri, hipotetik 113 belge tam yeniden sınıflandırma (yalnız bilgi) | ilk 3 sayfa ort. **1.833 karakter** (106 sayfalı belge; max 3.116) + sistem promptu (rehber dahil) ≈ 1.500–2.000 giriş; JSON çıkış ≈ 300–500 | 113 × (2.000×0,10 + 500×0,50) µ$ ≈ 113 × $0,00045 | **≈ $0,05 (tahmin; sayfa karakterinden türetildi, ölçüm değil)** |

Not: PR #23 §1/4'teki "~44 bin input token" rakamı bu oturumda doğrulanamadı; audit/D ölçümü ≈ 35 bin (Claude tokenizer, `RETRIEVAL_TOP_K=80`). Prompt caching istemcide **kullanılmıyor** (`cache_control` yok); sistem promptu ≈ 1,5k token sabit, 80 parça soruya göre değişir → bağlam daraltma/caching ölçümü PR #23 §1/4, bu emrin dışında.

### 1.4 Önerilen ayar

| Anahtar | Öneri | Gerekçe |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` | PR #23 §1 (Ç-11(b) onayı) |
| `LLM_MODEL_CLASSIFY` (router **+ Excel plan + metadata**) | `claude-haiku-5-5` | Tansu kararı; D'de Haiku router 0 istek hatası, JSON suffix+fence soyma çalıştı; ayrı anahtar yok (Ç-16). Excel plan tarafında Haiku'nun ürettiği SQL ölçülmedi (§5 risk) |
| `LLM_MODEL_ANSWER` (belge cevabı **+ Excel yorum**) | `claude-haiku-5-5` | Tansu kararı. Excel yorum adımı ADR-011 şablonuyla korunur (motor rakamı metinde yoksa şablon basılır, `excel_ask.py` L383–389) |
| Fallback (önceden kararlı) | `LLM_MODEL_ANSWER=claude-sonnet-5-5` | yalnız bu anahtar değişir + restart; D C3 ≈ 19× maliyet |
| `ANTHROPIC_MAX_RETRIES` | `.env`'e yazılmaz (varsayılan 2) | değişiklik gerekmiyor |
| `LLM_API_KEY`, `LLM_BASE_URL` | **dokunulmaz** | Gemini'ye geri dönüş yolu (PR #23 §1/5) |
| `EK_F_MODE` | `true` (§2–3) | netleştirici sorunun kullanıcıya görünmesi için zorunlu |
| `ASSIST_MODE` | `false` kalır | `EK_F_MODE` assist hesaplarını zaten açar; ikisi birden gereksiz (§2.3) |

---

## 2. Bayraklar

### 2.1 `ASSIST_MODE` (ADR-027) ve `EK_F_MODE` (ADR-030) — açıkken tam olarak ne değişir

`Settings.assist_computations = assist_mode_enabled or ek_f_enabled` (`config.py` L83–87). Aşağıda "A" = yalnız ASSIST_MODE, "E" = EK_F_MODE (A'nın hesaplarını kapsar).

| Etki | A | E | Kod |
|---|---|---|---|
| Cevap promptu `SYSTEM_PROMPT_ASSIST` (kural 7 + dolgu yasağı, kural 8 "Süre:" aynen kopyala, **kural 11** tek `SORU:` satırı) | ✓ | ✓ | `answer_prompt.py` L88–119, `ask.py` L231 |
| Modelin `SORU:` satırı ayrılır, kodla doğrulanır (≤200 kr, tek cümle, `?`, rakam/tarih/para/% yok, yetkisiz belge adı yok, soruyu tekrar etmiyor) | ✓ | ✓ | `assist.py::split_question_line`, `validate_question` L603–632 |
| Sıfır parça yolunda LLM'siz assist (eşleşmeyen terimler, aday terimler, "elimde şunlar var" ≤5) | ✓ | ✓ (≤7, proje gruplu, kota 4+3) | `ask.py` L168–185, `assist.py::build_zero_chunk_assist` |
| Model "yeterli bilgi bulamadım" dediğinde `build_insufficient_assist` | ✓ | ✓ | `ask.py` L262–278 |
| **Kullanıcıya giden `answer` metni** | **değişmez** (sabit cümle; yardım yalnız `AskResponse.assist` JSON'unda) | **F-5 kalıbı** (`render_no_data`: "«x» ifadesini … olarak anladım." + "Bu konuda kesin bilgi bulamadım." + proje gruplu liste + "İsterseniz açayım." + yükleme cümlesi + **son satır soru**) | `assist.py::render_no_data` L883–931 |
| **Proje ekseni sınıflandırması** (`classify_project_axis` → `disambiguate` ise LLM hiç çağrılmaz, cevap tek sabit soru "Hangi projeyi kastediyorsunuz: A mi, B mi?") | ✗ | ✓ | `ask.py` L197–216; `assist.py` L352–418 |
| Ç-2 `previous_question` prompt'a bağlam satırı | ✗ | ✓ | `answer_prompt.py` L227–229 |
| F-8 biçim kapısı (`polish_answer`: ISO tarih → GG.AA.YYYY, `1,234,567.89` → `1.234.567,89`; Excel hücreleri birimli biçim) | ✗ | ✓ | `ask.py` L305–308, `ask_router.py` L239–241, `excel_ask.py` L361 |
| MIXED'de yalnız Excel cevaplıysa belge tarafının "Veri Yok"u gizlenir | ✗ | ✓ | `ask_router.py::merge_mixed_answer` |
| Not 7 bekleyen belge durumları A/B/C (LLM'siz, cevaptan sonra) | ✓ | ✓ | `ask_router.py` L209–231, `pending_documents.py` |
| Audit `assist` JSON (ne gösterildi + düşürülme sebebi) | ✓ | ✓ | `audit_writer.py`, `assist_json` |
| Eval `expect_assist` kontrolü aktif olur (`assist_check`) | ✓ | ✓ | `scripts/eval_lib.py` L551–560 |

**AI-BalBal arayüzü `assist` bloğunu çizmiyor** (`frontend-balbal/src` altında "assist" geçmiyor; ADR-027 "ayrı PR" notu hâlâ açık). Sonuç: yalnız `ASSIST_MODE` açılırsa kullanıcı **hiçbir fark görmez** (sabit cümle); netleştirici soru ancak `EK_F_MODE` ile `answer` metninin içinde görünür.

### 2.2 Test kapsamı

| Dosya | Test | Kapsam |
|---|---|---|
| `test_assist.py` | 11 | ADR-027: bayrak kapalı bayt-aynı, SORU: ayrıştırma/doğrulama, G3 (yetkisiz belge listelenmez) |
| `test_assist_ekf.py` | 19 | ADR-030: F-5 kalıbı, F-3 kota/gruplar, Ç-3 anladım satırı, Ç-2, F-8, MIXED, bayrak kapalı bayt-aynı |
| `test_assist_discovery.py` | 12 | keşif/varlık soruları, H Adım 1–2 kalıpları |
| `test_pending_documents.py` | 11 | Not 7 A/B/C/D |
| `test_config.py` | 8 | env adlarının (`ASSIST_MODE`, `EK_F_MODE`, `DEMO_MODE`) gerçekten okunması |
| `test_answer_prompt.py` | 7 | prompt varyantları, kural 7 EK-F cümlesi yalnız assist promptunda |
| `test_ask.py` / `test_ask_router.py` / `test_router.py` | 17 / 16 / 5 | yollar, DATA→DOCUMENT düşüş, audit |
| `make lint` | — | `docs/prompts/*.md` ↔ Python sabiti birebir (`print-answer-prompt-assist` diff) |

**Proje ekseni için canlı (LLM'li) ölçüm:** Adım 4 (09.10) dev setinde ayarlandı ve **76 belgeli** kütüphanede ölçüldü; **113 belgeli yeni kütüphanede hiç ölçülmedi** (§3.3 kuru koşusu bu boşluğun ilk kanıtı).

### 2.3 Canlıda ikisini birden açmanın riski

Teknik olarak zararsız: `assist_computations` OR'dur, `render_no_data` yalnız `ek_f_enabled`'a bakar; iki bayrak da açıkken davranış = yalnız `EK_F_MODE` ile aynı. Risk **karışıklık**: `ASSIST_MODE=true` tek başına "açık ama görünmez" bir durum üretir, rollback/raporda iki bayrağın hangisinin etkili olduğu belirsizleşir. Öneri: yalnız `EK_F_MODE=true`, `ASSIST_MODE=false` (ADR-030 kararıyla uyumlu: "ASSIST_MODE eski sunum").

### 2.4 `docs/anayasa/ek-f.md` ↔ kod uyumu — farklar

| Ek-F | Kod | Fark |
|---|---|---|
| F-4 "Cevap, hangi proje/belge/döneme ait olduğuna göre değişiyorsa … **tek** netleştirici soru; bu soruyla birlikte içerik sıralamaz" | yalnız `kind=disambiguate` (proje ekseni) soru-tek çıktı verir; `clarify`/`term_mismatch` türünde F-5 **liste + soru** birlikte gelir | **Belge/dönem ekseninde belirsizlik tespiti yok**; liste-soru birlikteliği F-4'e aykırı (yalnız clarify türünde) |
| F-4 "Eşleşme zayıfsa bulduklarını listeler ve tek soruyla teyit eder: '… mı kastettiniz?'" | `term_mismatch_template`: "Şu ifadeyi belgelerde bu haliyle bulamadım: «x». Ne demek istediğinizi açar mısınız?"; `CLARIFY_TEMPLATE`: "Hangi belge, proje veya konu hakkında olduğunu belirtebilir misiniz?" | Kalıp cümle farklı ("… mı kastettiniz?" yok); kalıplar Ek-F'ye göre "biçim örneği", sabit değil — fark küçük |
| F-5 kalıbı | `render_no_data` birebir sırayla uygular (anladım → verdict → liste → "İsterseniz açayım." → yükleme cümlesi yalnız liste boşken → soru) | ✓ uyumlu. "… olarak anladım" yalnız sözlükte etiketi olan terimler için yazılır; diğer sorularda anlama satırı yok (Ç-7.1/1 kısmi) |
| F-6 Çelişkili Veri kalıbı ("Kaynaklar farklı söylüyor … Hangisinin geçerli olduğunu teyit edebilir misiniz?") | **yok**; kural 9 "hepsini ayrı etiketle yaz, birini seçme" (kalıp cümlesiz, teyit sorusuz); Ç-7 "Çelişkili Veri" durum etiketi `warnings.kind`'da yok | Uygulanmamış |
| F-7 İş dışı soru kalıbı ("Bu konu şirket kayıtlarının dışında kalıyor…") | **yok**; GENERAL_QUERY 30.09'da kaldırıldı → iş dışı soru "yeterli bilgi bulamadım"/F-5 kalıbına düşer | Uygulanmamış |
| F-3 "Birden fazla projeyle ilgili soruda her proje **ayrı başlık** altında" | kural 10: her proje **ayrı cümle**; kural 7 başlık/madde işareti yasaklar | Çelişki (başlık ↔ cümle) |
| F-2 "Siz" hitabı, kullanıcının terimini tercih et | prompt'ta yalnız dolgu yasağı; "siz" talimatı yok; terim tercihi yalnız Ç-3 anladım satırı | Kısmi |
| F-8 biçim (tarih, tutar, oran, çarpan) | `tr_format.polish_answer` tarih + İngilizce binlik; tutar/oran kural 7 "kaynaktaki biçimde" | Kısmi (bilinçli, ADR-030 "kod yalnız tarih ve binlik") |
| F-9 durum etiketi atlanmaz | `warnings[].kind` + `NO_DATA_VERDICT` | ✓ |

Bu farklar bu iş emrinin kapsamı **dışında** (Ç-16); yalnız listelendi.

---

## 3. Netleştirici soru davranışı

### 3.1 Mevcut durum

**Canlı (iki bayrak kapalı):** `SYSTEM_PROMPT` (kural 1–10) → model ya cevaplar ya sabit cümleyi yazar. Netleştirici soru mekanizması **hiç yok**; `classify_project_axis` çalışmaz (`ask.py` L198 `if settings.ek_f_enabled`). Router (`router.py`) belirsizlik kararı vermez; yalnız DOCUMENT/DATA/MIXED seçer (MIXED'in "sözleşme eşiği mi gerçekleşen mi" belirsizliği ayrı ve kalır).

**D Adım ölçümü (bayraklar kapalı, 109 belge), `ambiguous` 6 soru:**

| Soru | C1 Gemini | C2 Haiku/Haiku | C3 Haiku/Sonnet | Beklenen |
|---|---|---|---|---|
| GEN-AMB-001 "Sözleşmenin vadesi ne zaman doluyor?" (yonetim) | sabit cümle ✓ | **cevapladı**: "Sorunuzda hangi sözleşmenin kastedildiği belirtilmediği için vade bilgileri proje bazında aktarılmıştır. Boztepe … 10 yıl [K15] …" ✗ | sabit cümle ✓ | clarify |
| GEN-AMB-002 "Raporda belirtilen DSCR değeri kaç?" (finans) | cevapladı ✗ | cevapladı ("hangi rapor belirtilmediği için … ayrı ayrı yazıyorum") ✗ | cevapladı ✗ | clarify |
| GEN-AMB-003 "Son tadil neyi değiştirdi?" (yonetim) | cevapladı ✗ | cevapladı ✗ | cevapladı ✗ | clarify |
| GEN-AMB-004 "Lisans ne zaman alındı?" (enerji) | cevapladı ✗ | cevapladı ✗ | cevapladı ✗ | clarify |
| GEN-AMB-005 "Toplantıda ne karar alındı?" (yonetim) | cevapladı ✗ | sabit cümle ✓ | sabit cümle ✓ | clarify |
| GEN-AMB-006 "Hukuki inceleme notunda ne tespit edildi?" (hukuk) | cevapladı ✗ | cevapladı ("Soruda hangi projenin notu kastedildiği belirtilmemiş … her biri ayrı") ✗ | cevapladı ✗ | disambiguate |
| **"vade 14 yıl" örneği** | İş Emri C Adım 1 (40 soru, 76 belge): C2 Haiku GEN-AMB-001'e "sözleşme vadesi 14 yıl … [K51]" — kendinden emin, yanlış (kütüphanede o sırada 12→14 yıl zinciri vardı; yeni kütüphanede Karatepe 13 yıl, Boztepe 10 yıl) | | | |

Okuma: Haiku belirsizliği **fark ediyor ve açıkça yazıyor**, ama kural 10 refleksiyle (projeleri ayrı cümlelerde ver) **sıralayarak cevaplıyor**. Promptta "belirsizse sorma, sor" diyen kural yok; kural 11 bile yalnız bayrak açıkken ve yalnız "cevap veremediğinde" soru izni verir.

**Karar nerede veriliyor (bayrak açıkken):** (1) kod, LLM'den önce — `classify_project_axis` yalnız **proje** ekseni (`ask.py` L197–216; sıfır parça yolunda `build_zero_chunk_assist` içinde); (2) prompt — kural 11, modelin inisiyatifine bağlı; (3) assist değil, router değil.

**Tarihçe (bu oturumda doğrulandı):** Tansu'nun 07.10 kararı (a) "belirsiz soruda kısa netleştirme sorusu, sıralama yok" için `feat/belirsizlik` dalında **kural 12** yazıldı ve ölçüldü (Gemini flash-lite, 5 soru × 3: A 8/15, A2 revize **10/15** netleştirme, G1–G3 15/15; AMB-003 0/3, AMB-004 1/3), sonra aynı dalda LLM'siz belge/proje ekseni dedektörü (`ambiguity.py`, kuru koşu 5/5, 0 yanlış pozitif, 76 belge) yazıldı ve kural 12 "ölçülmemiş ikinci mekanizma" diye daldan çıkarıldı. **Dal `main`'e/bu dala alınmadı** (`git merge-base`: ancestor değil). Mevcut daldaki proje ekseni (Adım 4, 09.10) ayrı ve daha dar bir uygulama.

### 3.2 Ç-7.1 sırasıyla karşılaştırma

| Ç-7.1 adımı | Bayraklar kapalı (canlı) | `EK_F_MODE` açık |
|---|---|---|
| 1. Anlama kontrolü (nasıl anladığını yaz; belirsizse netleştirici soru) | **yok** | kısmi: "«x» ifadesini … olarak anladım" yalnız sözlük terimlerinde; soru yalnız proje ekseninde (kod) ya da modelin kural 11 inisiyatifinde |
| 2. Durum bildirimi | sabit cümle + `warnings.kind` | `NO_DATA_VERDICT` + `warnings.kind` ✓ |
| 3. Yardım teklifi (yetki içi belgeler, göster, yüklenirse cevaplarım) | **yok** | ✓ F-5 listesi, "İsterseniz açayım", yükleme cümlesi |
| 4. Açık uç (soru/seçenekle biter) | **yok** | ✓ son satır soru |

Eksik olan tam olarak Ç-7.1/1'in ikinci yarısı: **"soru belirsizse netleştirici soru sorar"** — sıra "önce anlama, sonra Veri Yok" der; bugün model belirsiz soruyu "anlaşılmış" sayıp cevaplıyor.

### 3.3 Kuru koşu — `classify_project_axis` 113 belgeli canlı DB'de ne der (LLM'siz, audit'siz, salt okunur)

Backend container'ında `retrieve()` + `available_from_chunks` + `classify_project_axis` + `downgrade_existence_disambiguate`, canlı eşiklerle (0,5 / 0,75), `department=None` (eval payload'ı da `department` göndermiyor):

| Soru | Kullanıcı | Parça/belge | Proje dağılımı | Karar | Beklenen (eval) |
|---|---|---|---|---|---|
| GEN-AMB-001 Sözleşmenin vadesi ne zaman doluyor? | yonetim | 80/33 | ANK 24, IZM 6, BOZ 1, YSV 1, şirket 1 | **dominant ANK_RES → LLM çağrılır** | clarify ✗ (kod yakalamaz) |
| GEN-AMB-002 Raporda belirtilen DSCR değeri kaç? | finans | 24/11 | ANK 6, YSV 3, BOZ 2 | disambiguate (ANK, YSV) | clarify (tür farkı §3.5) |
| GEN-AMB-003 Son tadil neyi değiştirdi? | yonetim | 28/15 | ANK 8, IZM 5, YSV 1, şirket 1 | disambiguate (ANK, IZM) | clarify |
| GEN-AMB-004 Lisans ne zaman alındı? | enerji | 20/15 | ANK 9, IZM 6 | disambiguate (ANK, IZM) | clarify |
| GEN-AMB-005 Toplantıda ne karar alındı? | yonetim | 55/38 | ANK 14, IZM 11, şirket 7, BOZ 4, … | disambiguate (ANK, IZM) | clarify |
| GEN-AMB-006 Hukuki inceleme notunda ne tespit edildi? | hukuk | 17/7 | IZM 4, ANK 3 | disambiguate (ANK, IZM) | disambiguate ✓ |
| **GEN-AMB-003-F** Son tadil neyi değiştirdi? (negatif kontrol) | finans | 10/3 | ANK 2, YSV 1 | **disambiguate (ANK, YSV) — YANLIŞ POZİTİF** | cevap ✗ |
| ANK-NEG-003 Kredi sözleşmesinin vadesi kaç yıl? | finans | 80/28 | ANK 14, YSV 6, BOZ 4, IZM 4 | none → LLM | cevap (14/13 yıl) |
| ANK-NEG-004 Üretim lisansı ne zaman alındı? | enerji | 80/34 | ANK 26, IZM 8 | dominant ANK → LLM | cevap 15.06.2020 |
| Duman (a) Karatepe RES … fiilen kullandırılan tutar | finans | 80/32 | named ANK | named → LLM (router DATA'ya da gönderebilir) | cevap |
| Duman (b) Amendment ne demek biliyor musun? | finans | 9/2 | ANK 2 | none → LLM | liste + soru (H Adım 2) |
| Duman (c) Boztepe RES imar planı davası … | enerji | 80/33 | named BOZ (belge yok) | named → LLM | yetki negatifi |

Üç sonuç: (1) Tansu'nun "`classify_project_axis` disambiguate dediğinde cevap üretilmesin" ilkesi kodda **zaten var**, ama **GEN-AMB-001'i yakalamıyor** (belge ekseni: hangi sözleşme). (2) Yeni kütüphane (Yeşilova/Boztepe belgeleri) proje eksenini finans kullanıcısında **GEN-AMB-003-F'de yanlış pozitife** itiyor — bayrak açılırsa bu negatif kontrol düşer (bu emirden bağımsız, Adım 4 eşiklerinin 113 belgede ölçülmemiş olmasının sonucu). (3) ANK-NEG-003'te finans artık 4 projenin kredi sözleşmesini görüyor; "Kredi sözleşmesinin vadesi kaç yıl?" yeni kütüphanede gerçekten belirsiz (D'de Haiku ve Sonnet "Boztepe 10 yıl, Karatepe 13 yıl" diye sıraladı) → kural 12 ile soru sorulursa eval beklentisi (cevap) düşer.

### 3.4 ÖNERİLEN DEĞİŞİKLİK (en küçük kapsam)

**İki katman, ikisi de Tansu onayına bağlı:**

**(K-a) Kod değişikliği YOK, yalnız bayrak:** `EK_F_MODE=true`. Etkisi §2.1 tablosu; proje ekseni belirsizliği LLM'siz, kullanıcıya tek soru. Tansu'nun PR #23 §1/2 cümlesinin birebir karşılığı.

**(K-b) Prompt: kural 12, yalnız `SYSTEM_PROMPT_ASSIST`'e, 07.10'da ölçülmüş A2 metni AYNEN** (`git show e23ad5d~1:backend/app/services/answer_prompt.py`). Bayrak kapalı `SYSTEM_PROMPT` bayt-aynı kalır; `docs/prompts/ANSWER_SYSTEM_PROMPT.md` değişmez.

```diff
--- a/backend/app/services/answer_prompt.py
+++ b/backend/app/services/answer_prompt.py
@@ -107,7 +107,27 @@ _RULE_11_ASSIST = (
 _RULE_7_EKF = (
     _RULES[6] + ' Selamlama, "memnuniyetle", "harika soru" gibi dolgu ifadeleri, ünlem '
     "ve emoji kullanma; doğrudan konuya gir."
 )
-_RULES_ASSIST = [*_RULES[:6], _RULE_7_EKF, _RULE_8_ASSIST, *_RULES[8:], _RULE_11_ASSIST]
+# İş Emri 2026-10-12K (Tansu PR #23 §1/2, 07.10.2026 karar (a)): an ambiguous question asks,
+# it does not enumerate. Text = the measured A2 revision of 07.10.2026 (BELIRSIZLIK_REPORT §2,
+# commit 406251e/e23ad5d~1), verbatim. Assist prompt only; `SYSTEM_PROMPT` stays byte-identical.
+_RULE_12_ASSIST = (
+    "12. Soru hangi belgeyi, projeyi ya da raporu kastettiğini söylemiyorsa ve kaynaklar "
+    "birbirinden FARKLI belgelere, projelere ya da rapor dönemlerine ait farklı değerler "
+    "içeriyorsa, bunlardan birini seçme ve hepsini sıralama: 2. kuraldaki cümleyi yaz ve "
+    "11. kurala göre tek bir SORU: satırıyla hangisinin kastedildiğini sor. Birden fazla "
+    "aday olduğunu fark ettiysen bunu açıklayıp adayları listeleme; yalnızca sabit cümle ve "
+    "SORU: satırı. Kaynakların farklı projelere ait olması, soru projeleri adıyla saymıyorsa, "
+    "belirsizliktir ve soru sorulur. Bu kural şu durumlarda UYGULANMAZ: (a) aynı belgenin "
+    "sürüm zinciri (Zincir: satırı aynı belge ailesini gösteriyorsa) belirsizlik değildir — "
+    '5. kural geçerlidir ve "güncel", "ilk", "son", "orijinal" gibi kelimeler o zincir içinde '
+    "kapsamı belirler; kaynaklarda birden fazla ayrı belge ailesi (örneğin farklı türde iki "
+    'tadil zinciri) varsa "son" tek başına kapsam vermez ve soru sorulur; (b) soru proje adı, '
+    'belge adı veya dönem veriyorsa; (c) kullanıcı "tüm", "hepsi", "listele" gibi bir '
+    "ifadeyle hepsini istiyorsa; (d) soru 10. kuraldaki gibi birden fazla projeyi ADIYLA "
+    "sayıyorsa. 9. kural (aynı terimin farklı tanımları) bu kuraldan etkilenmez."
+)
+_RULES_ASSIST = [*_RULES[:6], _RULE_7_EKF, _RULE_8_ASSIST, *_RULES[8:], _RULE_11_ASSIST, _RULE_12_ASSIST]
 SYSTEM_PROMPT_ASSIST = _PREAMBLE + "\n".join(_RULES_ASSIST)
```

Kullanıcının göreceği metin (kural 12 tetiklenince, `EK_F_MODE` ile): model "Mevcut şirket kaynaklarında … bulamadım.\nSORU: Hangi sözleşmeyi kastediyorsunuz?" yazar → kod `SORU:` satırını ayırır, doğrular (rakam/tarih yok, yetkisiz belge adı yok) → `render_no_data`: "Bu konuda kesin bilgi bulamadım. Elimde konuyla ilgili şunlar var: Karatepe RES: …; … İsterseniz açayım. Hangi sözleşmeyi kastediyorsunuz?" (liste + soru; F-4 "içerik sıralamaz" ile gerilim → SORU 3).

Kapsamdaki dosyalar (K-b): `backend/app/services/answer_prompt.py` (yukarıdaki diff), `docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md` (`make prompt-doc` ile yeniden üretilir; başlık cümlesi "11 yenidir" → "11–12 yenidir", Makefile L126), `backend/tests/test_answer_prompt.py` (+1 test: `test_rule_12_asks_one_question_on_ambiguity_only_in_the_assist_prompt`, e23ad5d~1'deki metin aynen; `"\n12. " not in SYSTEM_PROMPT` iddiası dahil), `docs/ARCHITECTURE.md` ADR-027 altına bir tarihli madde. Başka dosya yok.

**Kural 12 ne zaman tetiklenir / tetiklenmez (kriter, metinden):**
- Tetiklenir: soru belge/proje/rapor adı vermiyor **ve** kaynaklar farklı belgelere/projelere/rapor dönemlerine ait **farklı değerler** taşıyor (AMB-001 hangi sözleşme; AMB-002 hangi rapor/dönem; AMB-005 hangi toplantı; proje adı sayılmadan iki projenin değeri).
- Tetiklenmez: (a) aynı belge ailesinin sürüm zinciri (TEMPORAL TRUTH, kural 5 geçerli); (b) proje/belge adı ya da dönem verilmiş; (c) "tüm/hepsi/listele"; (d) birden fazla proje ADIYLA (kural 10, Ü-3). **Yetki negatifi** ("Boztepe … davası", enerji): kaynaklarda Boztepe yok → kural 2/3 sabit cümle; kural 12'nin ön şartı (farklı değerler) yok → soru üretilmez; üretse bile `validate_question` yetkisiz başlık adını düşürür, `available` listesi `allowed` dışına çıkamaz (G3, `test_metadata_never_lists_a_document_outside_allowed`). **"Veri Yok"** (sıfır parça): LLM hiç çağrılmaz (ADR-021) → kural 12 devrede değil; F-5 kalıbı değişmez. Yani Ü-10/G3 ve ADR-014 sabit-cümle kuralı gevşemez: kural 12 yalnız "cevap" ↔ "sabit cümle + soru" seçimini değiştirir, yeni metin üretmez.

**Neden kodla belge-ekseni dedektörü (feat/belirsizlik `ambiguity.py`) değil:** ölçülmüş (kuru koşu 5/5) ama 76 belgede ayarlandı, dalı bu dala göre 22 dosya/1.469 satır geride (`tr_format.py` yok vb.), birleştirme büyük kapsam; held-out 10 soru o dalda. Tansu "genel kural şeklinde" dedi → prompt kuralı daha yakın. Seçenek olarak SORU 1'de.

### 3.5 Değerlendirme — `docs/plans/ADIM_D_KRITERLERI.md` (+ PR #23 §2 ile (d) kalktı)

`scripts/eval_lib.py::score_question`: `passed = answered_ok ∧ sources_ok ∧ value_check≠fail ∧ phrase_ok ∧ safety≠fail ∧ assist_check≠fail ∧ discovery≠fail`; `answered_ok = answered == ¬expect_no_answer`; `assist_check`: `expect_assist` varsa ve yanıt `assist` taşıyorsa **`kind` birebir eşit** olmalı, bayrak kapalıysa `skipped`.

- Netleştirici soru `ambiguous` kategorisinde "doğru" sayılır ⇔ `answered=false` **ve** (bayrak açıkken) `assist.kind == expect_assist` **ve** G1 (soruda rakam/tarih/para yok) ✓. Kriter (b) abstention: `expect_no_answer` sorularda `answered_ok` oranı — netleştirici soru burada **artı**. Kriter (a): güvenlik kategorilerine dokunmaz (clarify oralarda beklenmez).
- **Kriter sorunu 1 (Tansu kararı):** GEN-AMB-002/003/004/005 `expect_assist: "clarify"`; `EK_F_MODE` açıkken kod `kind="disambiguate"` üretiyor (§3.3) → `assist_check=fail` → `passed=false`, davranış istenen olduğu hâlde. Seçenekler: `expect_assist`'i `clarify|disambiguate` kabul edecek şekilde `eval_lib.assist_check`'i genişletmek (kod, 1 satır) ya da `questions.json`'da bu 4 sorunun beklentisini `disambiguate` yapmak. Ayrı kriter maddesi; D tabanı (bayraklar kapalı, `skipped`) ile karşılaştırmada `assist_check` D'de ölçülmemişti → karşılaştırma `answered_ok`/`passed` üzerinden.
- **Kriter sorunu 2:** GEN-AMB-003-F (negatif kontrol, `document`, cevap beklenir) proje ekseninde yanlış pozitif (§3.3) → `EK_F_MODE` ile düşer; ANK-NEG-003 kural 12 ile düşebilir. (d) kalktığı için red sebebi değil; PR #23 §2 gereği "tek belgeye/konuya yoğunlaşan kayıp" başlığıyla ayrı bulgu. Beklentiyi yeni kütüphaneye göre güncelleme kararı Tansu'nun.
- Tabanla karşılaştırılabilirlik: D tabanı Gemini, 109 belge, bayraklar kapalı, `demo_today` 2026-10-06. 99-soru yeniden ölçüm (PR #24 §4/5) **bu emrin dışında**, ayrı iş emri; ölçüm aynı ortam deseniyle (`company-ai-eval`, `compose run -e …`) ve `EK_F_MODE` açık/kapalı iki koşu olarak planlanmalı (bayrağın etkisi modelden ayrılsın).

---

## 4. Faz B uygulama planı (komut komut; Tansu + Naci onayından sonra)

Ön koşullar: Tansu'nun PR #23 (Kayıtlı Kanal) yorumunda §6 cevapları; Naci "Onaylandı, uygula"; Anthropic konsolunda kredi/limit kontrolü (Naci); `git status` temiz; `make test` başka bir yerde koşmuyor (bind mount).

```bash
# B/0 — ön kayıt (salt okunur)
git rev-parse HEAD; docker inspect -f '{{.State.StartedAt}}' company-ai-backend-1
docker exec company-ai-postgres-1 psql -U company_ai -d company_ai -At -c \
  "SELECT (SELECT count(*) FROM documents),(SELECT count(*) FROM users),(SELECT count(*) FROM audit_log);"

# B/1 — .env yedeği (REPO DIŞINA, 0600; logs/ untracked ama repo içinde — kullanılmaz)
install -m 600 .env "$HOME/.env.bak.2026-10-12K"

# B/2 — .env (yalnız bu anahtarlar; değerler burada yazılmaz, model adları hariç)
#   LLM_PROVIDER=anthropic
#   LLM_MODEL_CLASSIFY=claude-haiku-5-5
#   LLM_MODEL_ANSWER=claude-haiku-5-5
#   EK_F_MODE=true
#   (dokunulmaz: LLM_API_KEY, LLM_BASE_URL, PROSE_ANTHROPIC_API_KEY, ASSIST_MODE=false, DEMO_TODAY)
sed -i.tmp -E 's/^LLM_PROVIDER=.*/LLM_PROVIDER=anthropic/; s/^LLM_MODEL_CLASSIFY=.*/LLM_MODEL_CLASSIFY=claude-haiku-5-5/; s/^LLM_MODEL_ANSWER=.*/LLM_MODEL_ANSWER=claude-haiku-5-5/; s/^EK_F_MODE=.*/EK_F_MODE=true/' .env && rm .env.tmp
grep -E '^(LLM_PROVIDER|LLM_MODEL_CLASSIFY|LLM_MODEL_ANSWER|EK_F_MODE|ASSIST_MODE)=' .env   # yalnız bu 5 satır ekrana

# B/3 — kural 12 (K-b onaylandıysa): answer_prompt.py diff (§3.4) + test + ADR-027 maddesi
make prompt-doc                      # docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md yeniden üretilir (12 dahil)
make test ARGS="-k 'answer_prompt or assist or ask or router or anthropic or config'"
make lint                            # ruff + mypy + prompt dokümanı eşitliği
make test                            # tam koşu (~15 dk) — yeşil olmadan restart YOK (Çalışma biçimi 6)
git add -A backend/app/services/answer_prompt.py backend/tests/test_answer_prompt.py docs/prompts/ANSWER_SYSTEM_PROMPT_ASSIST.md docs/ARCHITECTURE.md
git commit -m "feat: rule 12 in the assist prompt — an ambiguous question asks, it does not enumerate (İş Emri 2026-10-12K, PR #23 §1)"

# B/4 — restart (≈ 12 s kesinti; yalnız backend; postgres/ocr-worker/caddy dokunulmaz)
make restart-backend
docker compose --project-directory . -f infra/docker-compose.yml --env-file .env exec -T backend python -c \
 "from app.core.config import get_settings as g; s=g(); print(s.llm_provider, s.llm_model_classify, s.llm_model_answer, s.ek_f_enabled, s.assist_mode_enabled)"
# beklenen: anthropic claude-haiku-5-5 claude-haiku-5-5 True False
docker logs --since "$(date -u -d '-2 min' +%FT%TZ)" company-ai-backend-1 | grep -E 'startup|metadata suggestion' | head
# beklenen: "startup version=…", "metadata suggestion background scan disabled" YOK (anahtar var) ve aday 0 → LLM çağrısı yok

# B/5 — duman testi (I/J kalıbı: Caddy http://localhost:8080, şifre .env'den, cookie login, ham cevap logs/is_emri_K_*.json; şifre/anahtar hiçbir çıktıya yazılmaz)
# (a) finans   "Karatepe RES kredisinde fiilen kullandırılan toplam tutar nedir?"
# (b) yonetim  "Sözleşmenin vadesi ne zaman doluyor?"                         (GEN-AMB-001)
# (c) enerji   "Boztepe RES imar planı davasında yürütmeyi durdurma talebi ne oldu?"   (yetki negatifi)
# (d) finans   "Amendment ne demek biliyor musun?"                            (liste + soru)
# (e) finans   "Son tadil neyi değiştirdi?"                                    (GEN-AMB-003-F, negatif kontrol)
# (f) finans   "Kredi sözleşmesinin vadesi kaç yıl?"                           (ANK-NEG-003, negatif kontrol)
# her biri için: HTTP kodu, query_type, answered, answer (ilk 300 kr), sources/excel_sources, warnings.kind, assist.kind/question, tokens, audit id

# B/6 — DB sayıları (documents/users aynı; audit_log +6, model=claude-haiku-5-5, error NULL) → rapor docs/reports/IS_EMRI_2026-10-12K.md → commit → push → ~/bin/tg-notify.sh done "…"
```

**Kabul kriterleri (Faz B):**
1. `make test` 0 hata (B/3), `make lint` yeşil; `SYSTEM_PROMPT` (bayrak kapalı) bayt-aynı (test).
2. Restart sonrası `get_settings()` beklenen 5 değeri verir; kesinti ≤ 20 s; diğer container'lar dokunulmamış.
3. Duman: 6/6 **HTTP 200**, hiçbir yanıtta stack trace/500 yok, `audit_log` +6 satır `model=claude-haiku-5-5`.
   - (a) kaynak kartı var (belge ya da Excel); rakamın doğruluğu J §3a'nın ayrı iş emri konusu — **yalnız raporlanır**.
   - (b) `answered=false`; `answer` bir soruyla biter; soruda rakam/tarih/para/% yok (G1); `sources=[]`; listede yalnız yonetim'in görebildiği belgeler (G3). **Bu, Tansu'nun hedefi; sağlanmazsa K-b revizyonu değil, rapor + SORU** (prompt tek revizyon hakkı Tansu'da).
   - (c) `answered=false`, `sources=[]`, `retrieved_document_ids` ve `assist.available` içinde BOZ-LEG yok (G3).
   - (d) `answered=false`, tanım cümlesi yok (Ç-3), F-5 listesinde Facility Agreement Amendment 01/02, son satır soru.
   - (e)/(f) sonuç **raporlanır** (cevap beklenir; §3.3 yanlış pozitif / kural 12 etkisi): G1–G3 ihlali yoksa kabul engeli değil, "tek konuya yoğunlaşan kayıp" bulgusu.
4. Gizlilik: şifre/anahtar hiçbir log/rapor/JSON'da yok.

**Geri dönüş (her an, ≈ 12 s):** `install -m 600 "$HOME/.env.bak.2026-10-12K" .env && make restart-backend` → Gemini + bayraklar kapalı. Kural 12 kodda kalsa bile bayrak kapalıyken **etkisizdir** (`SYSTEM_PROMPT` değişmedi); istenirse `git revert <B/3 commit>`.

---

## 5. Riskler

| # | Risk | Etki | Önlem / not |
|---|---|---|---|
| R1 | Anthropic kredi/limit (bakiye bu oturumda bakılmadı) | 429 → kullanıcıya 503; SDK 2 deneme | Faz B öncesi konsol kontrolü; limit 1000 istek/dk ölçülü; rollback 12 s |
| R2 | Haiku kalite: D'de abstention %66,7 (<C1 %71,4), `document` 5 kayıp (ÇED belgesi kümesi); uzun cevap (ort. **1.060 çıkış** token vs Sonnet 597) ve **markdown sızıntısı** (`**Kızılova RES…**`, "- " maddeler; kural 7'ye aykırı; `polish_answer` markdown soymaz) | F-2/F-3'e aykırı görünüm; maliyet çıkış tarafında 2× | Yeniden ölçümde ayrı başlık; markdown temizliği ayrı öneri (Ç-16) |
| R3 | Excel yolu Haiku ile: plan modeli Haiku'nun SQL'i hiç ölçülmedi (D'de `data` 1/4 vs Gemini 1/1, farklı payda); J §3a (1×1 olmayan tablo → model yanlış satır) model-bağımsız mekanizma | yanlış rakam, kaynaklı ama yanlış okunmuş | ADR-011 şablonu 1×1 sonuçta korur; §3a ayrı iş emri; duman (a) raporlanır |
| R4 | `EK_F_MODE` 113 belgede ölçülmemiş: GEN-AMB-003-F yanlış pozitif (§3.3), eşikler 76 belgede kilitli | negatif kontrol kaybı | Rapor + Tansu kararı (SORU 4); eşik oynatılmaz |
| R5 | Kural 12 Haiku ile ölçülmedi (A2 10/15 Gemini); Haiku kural 10 refleksi güçlü (D: "proje bazında aktarılmıştır") | GEN-AMB-001 yine cevaplanabilir | Duman (b) kabul kriteri; başarısızsa K-b revizyonu Tansu'ya |
| R6 | Cache/prompt uzunluğu: caching yok, ≈ 35k giriş/soru, kural 12 + Ek-F ile sistem promptu +~600 token | maliyet +%2 | PR #23 §1/4 ayrı ölçüm |
| R7 | `DEMO_TODAY=2026-10-06` (.env) ≠ CLAUDE.md 15.09.2026; D tabanı da 2026-10-06 ile koştu | karşılaştırılabilirlik | **Değiştirilmez** (bu emirde) |
| R8 | Ölçüm karşılaştırılabilirliği: D tabanı Gemini + bayrak kapalı + 109 belge; yeni ölçüm Haiku + `EK_F_MODE` + 113 belge → iki değişken aynı anda | hangi etki kimin, ayrışmaz | 99-soru emrinde Haiku/bayrak-kapalı ve Haiku/bayrak-açık iki koşu; `assist_check` D'de `skipped` |
| R9 | Bind mount: `make test` ile restart aynı anda yapılmaz; dal değiştirilmez | bozuk süreç | B/3 → B/4 sırası |
| R10 | Metadata döngüsü: restart sonrası aday 0 → Haiku'ya çağrı yok; **yeni belge yüklenirse** Haiku classify ile otomatik sınıflandırma (JSON suffix yolu) | küçük maliyet, bilinmeyen kalite | kapsam dışı; not |

---

## 6. SORU (Tansu / Naci kararı; cevaplar onayla birlikte)

1. **Kural 12 (K-b) uygulanacak mı, yoksa yalnız bayrak (K-a) mı?** Kuru koşu: K-a tek başına GEN-AMB-001'i (Tansu'nun hedefi) çözmüyor. Alternatif: `feat/belirsizlik` belge-ekseni dedektörünü taşımak (kod, büyük kapsam, 76 belgede ayarlı). Öneri: K-a + K-b.
2. **Kural 12 metni:** 07.10 A2 metni AYNEN mi (ölçülmüş, uzun), yoksa Tansu kısaltmak ister mi? (Prompt metni Ç-15/8 — Tansu'nun; bu planda AYNEN yazıldı.)
3. **F-4 "içerik sıralamaz" ↔ F-5 liste:** kural 12 netleştirmesinde kullanıcıya liste + soru mu (bugünkü `render_no_data`), yoksa proje ekseni gibi **yalnız soru** mu? İkincisi 1 satırlık kod (`render_no_data`'da `kind=clarify ∧ model sorusu` için liste atlanır) ama davranış kararı.
4. **GEN-AMB-003-F ve ANK-NEG-003 beklentileri** 113 belgeli kütüphanede (finans artık 4 projenin kredi belgesini görüyor): cevap mı, netleştirme mi beklenmeli?
5. **Eval `expect_assist`:** `clarify` beklenen 4 soruda kodun `disambiguate` üretmesi "doğru" sayılsın mı (`assist_check` genişletme ya da `questions.json` güncelleme)?
6. **Faz B sırası:** kural 12 commit'i restart'tan **önce** (tek restart) mi, yoksa önce yalnız Haiku + bayrak, duman, sonra kural 12 + ikinci restart mı (etkileri ayırır, +12 s kesinti)? Öneri: tek restart, duman (b) ile kontrol.

---

## [ANAYASA KONTROLÜ]
- **Anayasa versiyonu:** v2.1 · **Okunan modüller:** Çekirdek (Ç-7, Ç-11, Ç-15, Ç-16, Ç-17), 01 Ürün (Ü-3, Ü-10), 02 Teknik (T-9), Ek-F.
- **Ürün etiketi:** Ürün 1 (doküman + plan; bu fazda davranış değişikliği yok).
- **Ç-15/8:** Sistem promptu değişikliği (kural 12) **uygulanmadı**, metni AYNEN planda; Tansu onayı bekliyor. **Ç-15/6:** `.env`/restart uygulanmadı, komutlar planda.
- **Ç-11(b):** Sağlayıcı geçişi PR #23 ile onaylı; bu plan uygulamayı tarif eder, yetki genişletmez.
- **Ç-16 (kapsam):** Değişen tek dosya bu rapor. Container durmadı; `.env` yalnız okundu; gizli değer yazılmadı (yalnız anahtar adları, dolu/boş bilgisi ve model adları). Kuru koşu LLM'siz, audit yazmayan SELECT'lerden ibaret. Kapsam dışı bulgular (Ek-F F-6/F-7, markdown sızıntısı, J §3a, bağlam daraltma) yalnız **öneri/not** olarak yazıldı.
- **G3:** `allowed_document_ids`'e dokunulmadı; plandaki hiçbir adım yetki katmanını değiştirmiyor.
- **Gizlilik (T-14):** API anahtarı, şifre, JWT hiçbir çıktıda yok.
- **Kendi başına verilen kararlar:** maliyet hesabında D ölçümünün (Claude tokenizer) esas alınması; metadata maliyetinin sayfa karakterinden *tahmin* olarak türetilmesi; kuru koşunun yapılması (salt okunur). Diğer her karar §6'da soruya bırakıldı.
