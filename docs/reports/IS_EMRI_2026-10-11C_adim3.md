# İş Emri 2026-10-11-C — Adım 3 Raporu (Gemini↔Claude bayrağı, backend)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı — **lint ve solo `make test` yeşil**

## 1. Ne eklendi

- `app/services/llm/anthropic_client.py` (yeni) — `openai_compatible.py` ile BİREBİR aynı
  arayüz/hata eşlemesi (`LLMAuthError`/`LLMRateLimitError`/`LLMTimeoutError`/
  `LLMUnavailableError`/`LLMResponseError`). `response_format="json_object"` için (Anthropic'te
  karşılığı yok) sistem promptuna tek satır JSON talebi eklenir, markdown kod bloğu soyulur
  (seed_data/generator'ın `generate_prose.py`sındaki aynı teknik).
- `app/services/llm/factory.py` — Phase 0.3'ün "Deferred" `anthropic` dalı dolduruldu.
- `app/core/config.py` — `anthropic_api_key`'in env alias'ı **`PROSE_ANTHROPIC_API_KEY`**
  olarak düzeltildi (önceden hiç kullanılmayan bir stub alandı, varsayılan olarak
  `ANTHROPIC_API_KEY`'e düşerdi — SDK kendiliğinden `api_key` verilmezse o adı okur, bu
  yüzden alias ŞART). `anthropic_max_retries: int = 2` eklendi.
- `backend/pyproject.toml` + `uv.lock` — `anthropic` paketi dev-only grubundan ana
  `dependencies`'e taşındı (artık app/'nin runtime bağımlılığı; versiyon değişmedi).
- `infra/.env.example` — `LLM_PROVIDER=anthropic` örneği + `ANTHROPIC_MAX_RETRIES`;
  eski, hiç okunmayan `ANTHROPIC_API_KEY=` placeholder'ı kaldırıldı (canlı `.env`'deki
  aynı adlı, kullanılmayan değere DOKUNULMADI — yalnız örnek dosya, kod hiçbir yerde o adı
  okumuyor).
- `scripts/run_eval.py` — **`CostTracker`** sınıfı (`EVAL_BUDGET_USD`/`--budget-usd`): her
  `/api/ask` cevabının `model`/`tokens_in`/`tokens_out`'u üzerinden kümülatif $ hesaplar,
  bütçe aşılırsa koşuyu DURDURUR (`partial`/`partial_reason`, aynı ardışık-hata deseni).
  Fiyat tablosu: Haiku 5.5 $0,10/$0,50, Sonnet 5.5 $2/$10 (MTok, claude.com/pricing,
  11.10.2026 doğrulandı); Gemini $0 (ücretsiz kademe kullanılıyor).
- **Pacing:** mevcut `RateLimiter`/`--min-interval-s` zaten vardı (Gemini'nin 5 istek/dk
  sınırı için 26 sn) — Adım 1'in ölçümü (Anthropic: dakikada 1000 istek) sayesinde Adım
  4'teki Claude koşuları çok daha küçük bir aralıkla (~3 sn) çalışacak, kod değişikliği
  gerekmedi, yalnız parametre.

## 2. Gerçek (mock olmayan) uçtan uca doğrulama

Geçici olarak `.env`'i `LLM_PROVIDER=anthropic`/`LLM_MODEL_CLASSIFY=claude-haiku-5-5`/
`LLM_MODEL_ANSWER=claude-sonnet-5-5` yapıp `make restart-backend`, gerçek bir `/api/ask`
çağrısı yapıldı: `model: claude-sonnet-5-5`, gerçek token kullanımı (44.574 girdi/264
çıktı) — pipeline uçtan uca çalıştı. Cevap "yeterli bilgi bulamadım" döndü; AYNI soru
Gemini'ye (önceki `.env` durumuna geri alınıp) sorulduğunda **O DA** aynı sonucu verdi —
bu bir Claude-entegrasyon hatası DEĞİL, canlı DB'nin kendi (dokunulmayan) korpus durumu.
**`.env` deneyden sonra `diff` ile birebir eski haline döndürüldüğü doğrulandı; backend
Gemini ile yeniden başlatıldı — canlı sistem Gemini varsayılanında kalıyor.**

## 3. Testler

`backend/tests/test_anthropic_client.py` (17 test, `httpx2.MockTransport` — ağ/anahtar
yok) + `backend/tests/test_run_eval_cost_tracker.py` (7 test, saf mantık). Eski
`test_factory_anthropic_is_deferred` kaldırıldı (artık yanlış — Anthropic deferred değil).

## 4. Kapı sonuçları

| Kapı | Sonuç |
|---|---|
| `make lint` | ✅ (ruff+mypy+validate-ledger+validate-documents+validate-excel) |
| solo `make test` | ✅ **680 passed + 18 passed, 0 hata** (657→680, +23 yeni test) |

## 5. Küçük teknik kararlar (raporda listelendi, kapıya dokunulmadı)

- `ROUTER_MODEL`/`ANSWER_MODEL` adları iş emrinde geçiyor ama CLAUDE.md zaten
  `LLM_MODEL_CLASSIFY`/`LLM_MODEL_ANSWER` diyor — **yeniden adlandırma yapılmadı**, mevcut
  adlar korundu (CLAUDE.md'nin kendi ismi otoriter kaynak).
- `temperature` parametresi Anthropic'e HİÇ gönderilmiyor — kurulu SDK sürümünün
  `messages.create()` imzasında bu parametre yok (introspection ile doğrulandı, 11.10.2026);
  üretilmedi/tahmin edilmedi, gerçek sürümün gerçek imzası okundu.
- `LLM_PROVIDER`'ın değeri hâlâ `"openai_compatible"` (iş emrinin "gemini|anthropic" lafzı
  yalnız betimleyici) — yeniden adlandırma gereksiz bir kırılma yaratırdı, davranış aynı.

## 6. Maliyet

Bu adımda (lint/test dışında) yalnız 2 gerçek `/api/ask` çağrısı (Claude) + 1 (Gemini,
karşılaştırma) — toplam ~$0,01 altında. Kümülatif iş emrinde: Adım 1 (~$0,0001) + Adım 3
(~$0,01) ≈ **$0,01 / $4,0 DUR eşiği**.
