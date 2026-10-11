# İş Emri 2026-10-11-C — Adım 2 Raporu (backend'de Gemini kullanım yerleri)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — **DURMADAN Adım 3'e geçiliyor**

## 1. LLM (metin üretimi) — Gemini, `app/services/llm/openai_compatible.py`

| Yer | Fonksiyon | Model (ayar) | Çağrı sıklığı |
|---|---|---|---|
| Soru router'ı | `router.py::LLMRouter.route()` | `LLM_MODEL_CLASSIFY` (gemini-3.5-flash-lite) | Her `/api/ask` çağrısında **1 kez** (DOCUMENT/DATA/MIXED sınıflandırma). |
| Belge cevabı | `ask.py::answer_question()` | `LLM_MODEL_ANSWER` (gemini-3.8-flash) | DOCUMENT veya MIXED sorularında **1 kez**. |
| Excel plan | `excel_ask.py::answer_data_question()` (plan adımı) | `LLM_MODEL_CLASSIFY` | DATA veya MIXED sorularında **1 kez** (ne hesaplanacağını belirler). |
| Excel cevap yorumu | `excel_ask.py::answer_data_question()` (yorum adımı) | `LLM_MODEL_ANSWER` | DATA veya MIXED sorularında **1 kez** (DuckDB/Python sonucunu yorumlar — LLM matematik yapmaz). |
| Belge metadata önerisi | `metadata_suggestion.py::suggest_metadata()` | `LLM_MODEL_CLASSIFY` | **Arka plan taraması** — her `metadata_suggestion_poll_interval_s` (15 sn) bir batch (`metadata_suggestion_batch_size`=5 belge), yalnız öneri hiç yapılmamış `ready` belgeler için. |

**Bir soru başına toplam çağrı:** DOCUMENT 2 (router+answer) · DATA 3 (router+excel plan+excel yorum) ·
MIXED 4 (router+answer+excel plan+excel yorum) — `scripts/run_eval.py`'nin kendi yorumuyla
birebir tutarlı.

**İstemci:** `app/services/llm/factory.py::build_llm_client()` → `OpenAICompatibleClient`
(openai SDK + `base_url=LLM_BASE_URL`, varsayılan Gemini'nin OpenAI-uyumlu endpoint'i).
`LLM_PROVIDER` zaten bir `Literal["openai_compatible", "anthropic"]` alanı olarak VAR
(`app/core/config.py:48`) — `"anthropic"` dalı şu an `LLMNotConfiguredError` fırlatıyor
("Deferred (Phase 0.3 decision)"). Adım 3 bu dalı dolduracak.

## 2. Embedding — Gemini DEĞİL, değiştirilmiyor

`app/services/embedding_client.py::TEIEmbeddingClient` — Hugging Face **Text Embeddings
Inference** (bge-m3), `EMBEDDINGS_ENABLED=true` olduğunda ayrı `embed` servisine (compose
içi, Gemini'den tamamen bağımsız) bağlanır. **Gemini ile hiçbir ilgisi yok** — iş emrinin
"Embedding Gemini ise değiştirme" şartı bu nedenle **uygulanamaz** (önkoşulu gerçekleşmiyor);
Anthropic'in de zaten bir embedding API'si yok, bu yüzden bu alan hiçbir şekilde
Claude'a taşınmayacak/taşınamaz. Dev'de `EMBEDDINGS_ENABLED=false` varsayılan (CLAUDE.md).

## 3. OCR — LLM yok

`ocr-worker/worker` içinde Gemini/LLM/openai referansı **yok** — `ocrmypdf` + `PyMuPDF`
(CLAUDE.md'nin kendi kararı: OCR'da LLM kullanılmaz).

## 4. Diğer (seed_data/generator — backend DEĞİL, ADR-013 sınırı dışında, bilgi amaçlı)

`seed_data/generator/generate_prose.py` ZATEN dual-provider (Gemini varsayılan, `--provider
anthropic` ile Claude) — bu iş emrinden ÖNCE, ayrı bir görevde eklenmişti. Backend
(`app/`) bu modülü hiç import etmez (ADR-013) — bu iş emrinin "backend LLM'i taşıma"
kapsamına GİRMİYOR, yalnız bir ön emsal olarak not edildi (Adım 3'teki geri-çekilme/pacing
tasarımı `generate_prose.py::_call_anthropic_with_backoff`'tan esinlenecek).

## 5. Sonuç — Adım 3 için kapsam

Değiştirilecek/doldurulacak: `app/services/llm/factory.py` (anthropic dalı),
`app/core/config.py` (gerekirse yeni ayar alanları), yeni `app/services/llm/
anthropic_client.py`. **Hiçbir şey** `embedding_client.py`'ye veya `ocr-worker`'a
dokunmayacak.
