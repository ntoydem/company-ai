# Phase 0.3 Raporu — LLM + soru-cevap + sayfa kaynaklı cevap (T0)

**Tarih:** 22.09.2026  **Model:** Claude Fable 5.1  **Tag:** phase-0-3  **Commit:** `git rev-list -n1 phase-0-3`

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | "Ankara RES'in güncel minimum DSCR covenant'ı nedir?" → 1,20x + Amendment 01 + sayfa numarası. | ✅ | `tests/live/test_t0_live.py::test_current_dscr_is_amendment` (gerçek Gemini, geçti). Canlı stack'te (`upload.sh` ile zincirli 2 belge, curl `POST /api/ask`): **"Ankara RES'in güncel minimum DSCR covenant'ı 1,20x'tir [K1], [K2]. Bu değer Amendment 01 ile önceki 1,25x seviyesinden değiştirilmiştir [K1], [K4], [K5]."** — kaynaklar: K1 **Amendment 01 sayfa 3** (15.03.2025, v1, executed, GÜNCEL), K2 Amendment 01 sayfa 1, K4 Facility Agreement sayfa 6, K5 Facility Agreement sayfa 1. `tokens_in=2425, tokens_out=60`. |
| 2 | "İlk DSCR covenant neydi?" → 1,25x + EXECUTED + sayfa; iki cevap farklı. | ✅ | `::test_initial_dscr_is_executed_and_differs` (geçti; ilk cümlede 1,25 var, 1,20 yok; iki cevap farklı). Canlı stack: **"İlk DSCR covenantı 1,25x seviyesindeydi [K3], [K4]. Bu değer Amendment 01 ile önceki 1,25x seviyesinden değiştirilmiştir [K1]."** — K3 **Facility Agreement sayfa 6** (01.06.2023, v1, **executed**, güncel değil, "Amendment 01 tarafından değiştirilmiş"), K4 Facility Agreement sayfa 1, K1 Amendment 01 sayfa 3 (GÜNCEL). |
| 3 | "İzmir RES'in COD tarihi nedir?" → "bilgi bulamadım". | ✅ | `::test_izmir_cod_no_answer` (geçti). Canlı stack: **"Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım."**, `answered=false`, `sources=[]`, **`retrieved_document_ids` 2 belge** (Ankara chunk'ları prompt'a girdi — bkz. §7 ilk madde), `tokens_in=1838`. Retrieval'ın boş olduğu yol ayrıca offline: `tests/test_ask.py::test_no_chunks_means_no_llm_call_and_zero_tokens` (LLM çağrısı yok, 0 token). |
| 4 | Prompt'a giden chunk'lar test ile yakalanır; `allowed_document_ids` dışı hiçbir chunk yok. | ✅ | `tests/test_ask.py::test_prompt_contains_only_allowed_chunks` — 3 belge (2 finance, 1 legal `SENTINEL-GIZLI-HUKUK-METNI`), `department=finance` scope'u **gerçek** `SqlDocumentIdsProvider` üzerinden; `FakeLLMClient` prompt'u yakalar: finance metinleri var, sentinel yok; kontrol çağrısında (scope'suz) sentinel var → dışlama yetki kapısından geliyor. Ek: `::test_prompt_respects_gate_subset` (kapı alt küme döndürünce yalnızca o), `::test_empty_gate_means_no_llm_call` (boş küme → LLM hiç çağrılmaz). |
| 5 | Cevaplar Türkçe, kaynak İngilizce olsa da; token sayıları loglanmış. | ✅ | Türkçe: canlı testlerde `_assert_turkish` (Türkçe karakter var, İngilizce işlev kelimesi yok) geçti; yukarıdaki üç cevap Türkçe, belgeler tamamen İngilizce. Token: `tests/test_llm_client.py::test_request_shape_and_usage_parsed` (`llm call` kaydında `tokens_in/out`), `tests/test_ask.py::test_ask_completed_log_carries_token_counts`; canlı log satırı: `{"logger": "app.services.llm.openai_compatible", "message": "llm call", "model": "gemini-3.5-flash", "tokens_in": 2425, "tokens_out": 60, "tokens_reasoning": null, "latency_ms": 40012, "finish_reason": "stop", "prompt_chars": 8165}`. |

## 2. Yapılanlar
- **LLM istemcisi** `app/services/llm/`: `LLMClient` Protocol + `LLMRequest/LLMResponse` (`base.py`), `OpenAICompatibleClient` (`openai` 3.17 SDK + `base_url`, `max_completion_tokens`, `temperature=0`, `reasoning_effort`, `max_retries=1`; vendor istisnaları `LLMAuthError/RateLimit/Timeout/Unavailable/Response` hiyerarşisine çevrilir; her çağrıda `llm call` log kaydı), `factory.py` (`LLM_PROVIDER`; key yoksa `LLMNotConfiguredError`, `anthropic` ertelendi). API: `LLMError` → 503 "Yapay zeka servisi geçici olarak kullanılamıyor." / "…yapılandırılmamış." (`core/errors.py`), sağlayıcı detayı yalnızca log'da. Yeni ayar `LLM_REASONING_EFFORT=low`.
- **`POST /api/ask`** (`api/ask.py`, `services/ask.py`, `schemas/ask.py`): authorize → `build_search_query` → `retrieve()` → zincir yükleme (`document_repo.load_with_chains`, her adımda izinli id kümesiyle) → `evaluate_version_chains` (`DEMO_TODAY`) → prompt → LLM → `[K#]` atıf parse → `SourceCard` (belge, **sayfa**, tarih, yürürlük, versiyon, durum, `is_current`, önceki/sonraki belge adı). Retrieval boşsa LLM çağrılmadan sabit "bilgi bulamadım"; modelin bu cümleyi içeren cevabı kanonikleştirilir. Cevapta `retrieved_document_ids`, `model`, `tokens_in/out`, sabit `notice` (yorum yok).
- **Sorgu kurma** `services/search_query.py` (ADR-020): kesme eki temizleme, Türkçe soru-kelimesi stoplist'i, `OR` birleştirme; `search_fts` sıralaması `ts_rank` → `ts_rank_cd`. Plan §T1 tespiti test olarak kayıt altında (`test_verbatim_question_finds_nothing_but_built_query_does`).
- **Versiyon zinciri** `services/version_chain.py` (ADR-021): `is_current` (bugün yürürlükte olan son halka, gizli ardılı yoksa), `is_initial`, `in_force`, görünmeyen (izinsiz) halka için yalnızca "var" bilgisi. Prompt'ta `Zincir: GÜNCEL / İLK HALKA (güncel değil) — "X" belgesini değiştirir` başlıkları; güncel belgeler önce.
- **Prompt** `services/answer_prompt.py`: 8 kural (kural 2 sabit cümle, kural 3 proje izolasyonu, kural 5 güncel/ilk, kural 6 yorum yok / "belgelerde sebep belirtilmemiş", Türkçe, DD.MM.YYYY, `BUGÜN=DEMO_TODAY`). Gözden geçirme kopyası `docs/prompts/ANSWER_SYSTEM_PROMPT.md` (`make prompt-doc`; `make lint` eşitliği `python -m app.cli print-answer-prompt` ile diff'ler).
- **Upload'a zincir alanları**: `effective_date`, `version (≥1)`, `supersedes_document_id` (opsiyonel); hedef izinli değilse 404, zaten değiştirilmişse 409 "Belge zaten başka bir belge tarafından güncellenmiş."; hedefin `superseded_by_document_id`'si aynı transaction'da yazılır, `status` değişmez. Migration yok (kolonlar 0002'de vardı).
- **Test arayüzü** `GET /ask` → `app/static/ask.html` (tek dosya, framework yok, örnek soru linkleri, kaynak kartları + GÜNCEL rozeti, model/token/request_id). `seed_data/t0/upload.sh` (curl+sed): PDF yoksa üretir, Facility → Amendment 01'i zincirli yükler, `ready` bekler.
- **Testler**: offline 82 backend (`FakeLLMClient`, httpx2 `MockTransport`, gerçek T0 PDF sayfaları `tests/t0_fixtures.py` ile DB'ye) + canlı 3 (`tests/live/`, `-m live_llm`, `make test-llm [MODEL=…]`; `LLM_LIVE_TESTS=1` yoksa skip). `pyproject`: `addopts -m 'not live_llm'`.
- **Yan düzeltmeler**: `alembic/env.py` `fileConfig(..., disable_existing_loggers=False)` (testte migration çalışınca tüm `app.*` logger'ları sessizce kapanıyordu — `llm call`/`ask completed` kayıtları kaybolmuştu); log maskeleme: `token` yalnızca tam segment olarak maskelenir (`tokens_in/out` okunur kalır, `llm_token` hâlâ maskeli — ADR-017 notu).

## 3. Değişen dosyalar
`git diff --stat phase-0-2..phase-0-3`: 43 dosya, +2474/−14 (`uv.lock` hariç 42 dosya, +2372).
```
Makefile, README.md, infra/.env.example, docs/ARCHITECTURE.md (ADR-009/017 notu, ADR-020, ADR-021),
docs/plans/PHASE_0_3_PLAN.md*, docs/prompts/ANSWER_SYSTEM_PROMPT.md*, seed_data/t0/upload.sh*
backend/: pyproject.toml (+openai), uv.lock, alembic/env.py
backend/app/: api/{ask*,ask_page*,deps,documents,router}.py, cli.py, core/{config,errors,logging}.py,
              repositories/{document_chunk_repo,document_repo}.py, schemas/ask*.py,
              services/{answer_prompt*,ask*,search_query*,version_chain*}.py, services/llm/{__init__,base,factory,openai_compatible}*.py,
              static/ask.html*
backend/tests/: fakes*.py, t0_fixtures*.py, live/test_t0_live*.py, test_{answer_prompt,ask,ask_page,llm_client,search_query,version_chain}*.py,
                test_documents.py, test_logging.py
```
(`*` = yeni)

## 4. Testler
- `make test`: backend **82/82** (3 canlı test deselect, ~20 s) → `assert-pipeline-schema` ✓ → ocr-worker **9/9** (~5,5 s). Toplam offline 91/91, atlanan 0.
- `make test-llm MODEL=gemini-3.5-flash`: **3/3** geçti (kriter 1–2 tek koşuda; kriter 3 ilk koşuda sağlayıcı 503'ü yedi, tek başına tekrar koşuda geçti; toplam ≈ 4 + 1,5 dk — ücretsiz katman için 13 s aralık + 503'te 65 s bekleme).
- `make lint`: backend ruff+format+mypy strict (47 dosya) ✓, ocr-worker ✓, prompt dokümanı diff ✓.
- Uyarı: Starlette TestClient deprecation (0.1'den beri, kütüphane kaynaklı).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| FTS sorgusu OR semantiği + `ts_rank_cd` (ADR-020) | Mevcut AND sorgusu 3 T0 sorusunda 0 chunk döndürüyordu (plan §T1); `ts_rank` ile kapak sayfası (kısa, terim yoğun) 5. madde sayfasını geçiyordu | Phase 0.2 testleri aynen geçiyor; İzmir sorusunda Ankara chunk'ları retrieval'a girer (bkz. §7) |
| `AnthropicClient` ertelendi (SORU 3 cevabı) | Test edilemez, ihtiyaç yok | `LLM_PROVIDER=anthropic` → 503 "yapılandırılmamış" |
| Canlı LLM testleri `make test` dışında (SORU 4) | Ağ/anahtar/oran sınırı | `make test` prod klonunda anahtarsız yeşil |
| Dev DB sıfırlama: volume silme yerine `TRUNCATE documents CASCADE` | `rm -rf data/postgres` komutu oturum izin katmanınca reddedildi; SQL truncate aynı sonucu verir, dosya sistemi silinmedi | `data/documents/` altında 0.2'den kalan 4 yetim klasör duruyor (zararsız; Phase 3.1 reset script'i temizler) |
| Canlı doğrulama `gemini-3.5-flash` ile | `.env`'deki `gemini-3.8-flash` bu oturumda ücretsiz katmanda sürekli 503 "high demand" + 429 (5 istek/dk) verdi; `.env` değiştirilmedi, `docker compose run -e LLM_MODEL_ANSWER=… -p 8001:8000` ile geçici ikinci backend kullanıldı | Rapordaki cevaplar 3.5-flash'a ait; 3.8-flash ile aynı akış, anahtar/endpoint doğrulandı (flash-lite ile de OK) |
| Düz metin + `[K#]` (JSON mode değil) | Basit parse, Türkçe kaçış sorunu yok | Etiketsiz olgu cümlesi riski → `warning` log; Phase 4.1 "citations" |
| `sources` = yalnızca atıf yapılanlar; `retrieved_document_ids` ayrı | Kullanıcı yalnızca gerçekten kullanılan kaynağı görür; eval/audit retrieval kümesini ister | Aynı belge+sayfa tek kart |
| Soru metni (ilk 200 karakter) `ask completed` log kaydında | T0 hata ayıklama; audit tablosu 3.4'te | Şifre/anahtar bu kayda giremez (alan listesi sabit) |
| `GET /ask` sayfası Phase 3.3'te de kalır (geliştirici sayfası) | Caddy `/`'yi alınca dışarıdan görünmez | — |
| `alembic/env.py` `disable_existing_loggers=False` | Test oturumunda `app.*` logger'ları kapanıyordu | Prod'da etkisiz (entrypoint ayrı süreçte migrate eder) |

## 6. Açık sorular (Naci cevaplamalı)
- Yok. Plandaki 6 SORU onayla cevaplandı ve uygulandı (1: upload alanları, status değişmez; 2: izolasyon prompt kuralıyla; 3: Anthropic ertelendi; 4: `make test-llm` ayrı; 5: dev DB sıfırlandı — truncate ile, bkz. §5; 6: `LLM_REASONING_EFFORT` env).

## 7. Riskler / sonraki phase için notlar
- **Kriter 3 (İzmir) LLM disiplinine dayanıyor — açıkça vurgulanır:** OR-retrieval, "İzmir RES'in COD tarihi nedir?" için `RES` terimi üzerinden **Ankara chunk'larını** prompt'a sokar (`retrieved_document_ids` = 2 Ankara belgesi, `tokens_in=1838`). "Bilgi bulamadım" cevabı, boş retrieval'dan değil, modelin kural 2 ve 3'e uymasından gelir. Testler bunu gizlemez: `test_izmir_question_returns_ankara_chunks_only` retrieval'ın dolu olduğunu, canlı test ise modelin reddettiğini kanıtlar. **Phase 4.1 notu (PHASES.md'ye eklendi):** eval'in `isolation` kategorisi bu senaryoyu — alakasız proje chunk'ları retrieval'a girdiğinde LLM'in çıkarım yapmaması — kapsamalı; yapısal `project_id` filtresi Phase 1.2'de gelince `expected_project`/`forbidden_sources` ile ikinci bir savunma hattı olur.
- Gemini ücretsiz katman: `gemini-3.8-flash` 5 istek/dk ve yoğunlukta 503; eval runner (4.1) bekleme/retry ile çalışmalı, `MODEL=` override'ı `make eval`'a da taşınmalı. Gecikme 12–46 s/çağrı (free tier).
- Cevap kalitesi gözlemi: "ilk" sorusunda model değişimi "önceki 1,25x seviyesinden değiştirilmiştir" diye yazdı, yeni değeri (1,20x) cümleye koymadı; canlı testte aynı soruya "1,20x seviyesine değiştirilmiştir" dedi. Prompt kural 5 şablonu Phase 3.2'de eval verisiyle sıkılaştırılabilir.
- Kapak sayfaları (`Sayfa 1`) meta tablosu içerdiği için sık atıf alıyor; doğru ama "ilgili section" bilgisi (SPEC_02 §10) henüz yok — Phase 3.2/3.3.
- Zincir tamamlama yok: retrieval yalnızca eski belgeyi bulursa güncel belgenin içeriği prompt'a girmez (yalnızca adı). T0'da OR sorgusu ikisini de buluyor; Phase 3.2 "güncel" sorularında ardıl belgenin chunk'larını otomatik eklemeyi değerlendirmeli.
- `retrieval_top_k=20` ile prompt 5–8 k karakter (≈1,6–2,4 k token); 15 belgede (3.1) büyür — maliyet için `top_k` düşürme/yeniden sıralama 3.4'te (hibrit) ele alınır.
- `AnthropicClient` ve `LLM_PROVIDER=anthropic` Phase 4.3 karar noktasına ertelendi.

## 8. Doğruladığım üçüncü taraf davranışları
- Gemini OpenAI-uyumlu endpoint (resmi doküman, 22.09.2026): `base_url .../v1beta/openai/`; `reasoning_effort` (`minimal|low|medium|high`) kabul ediliyor; `usage.prompt_tokens/completion_tokens` dolu, `completion_tokens_details.reasoning_tokens` **gelmiyor** (`tokens_reasoning=null`); `model` alanı istenen adla dönüyor. Model listesi: `gemini-3.8-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite` Stable.
- `openai` SDK **3.17.0**: `OpenAI(api_key, base_url, timeout, max_retries, http_client)`; `http_client` artık **`httpx2.Client`** (paket `httpx2` 2.13, `httpx` 0.28 yanında); `chat.completions.create(max_completion_tokens=…, reasoning_effort=…, temperature=…)`; istisnalar `AuthenticationError/PermissionDeniedError/RateLimitError/APITimeoutError/APIConnectionError/APIStatusError`. `httpx2.MockTransport` ile SDK uçtan uca test edildi (`Authorization: Bearer`, URL `…/chat/completions`).
- Gemini ücretsiz katman: `generate_content_free_tier_requests limit: 5` (dakika, model başına) → 429 "Please retry in Ns"; ayrıca model saturasyonunda 503 `UNAVAILABLE "high demand"`.
- Postgres: `websearch_to_tsquery('turkish', 'a OR b')` OR'u tanır; `turkish` config `nedir → 'ne'`, `İzmir → 'izmir'`, `Ankara → 'ankar'`; `ts_rank_cd` OR sorgusunda çok-terimli kesiti kapak sayfasının üstüne çıkarır (canlı: Amendment s.3 0,60 > Facility s.6 0,40 > kapaklar 0,30).
- Python `str.casefold()/lower()`: `"I" → "i"` (Türkçe `ı` değil) — `turkish_lower()` yardımcısı eklendi (`is_no_answer`, stoplist eşleşmesi).
- Alembic `fileConfig()` varsayılan `disable_existing_loggers=True` — mevcut tüm logger'ları kapatır.

## 9. Kaynak kullanımı
- `docker stats` (boşta): backend ≈ 83 MiB, ocr-worker ≈ 57 MiB, postgres ≈ 54 MiB; toplam ≈ 194 MiB / 16 GB.
- LLM: canlı testler + canlı stack + probe'lar ≈ 12 başarılı çağrı; T0 üç sorusu toplam `tokens_in` 5.840, `tokens_out` 129 (gemini-3.5-flash, ücretsiz katman, maliyet 0).
