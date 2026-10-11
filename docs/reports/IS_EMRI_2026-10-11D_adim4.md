# İş Emri 2026-10-11-D — Adım 4 Raporu (C1/C2/C3, 99 soru, ayrı ortam)

**Tarih:** 11.10.2026 · **Durum:** ✅ tamamlandı

## 1. Önemli bulgu — ortam kurulumunda bir hata bulundu ve DÜZELTİLDİ (canlıya dokunmadan)

C2'nin ilk denemesi 5 soru sonra "koşu yarıda kesildi" ile durdu (hepsi HTTP 503). Kök
neden: `infra/docker-compose.yml`'deki `backend` servisinin `env_file: .env` satırı
**sabit, parametresiz bir yol** — `--env-file infra/.env.eval` bayrağı yalnız compose
dosyası İÇİNDEKİ `${DEĞİŞKEN}` referanslarının yorumlanmasını etkiliyor,
`env_file: .env` yönergesini ETKİLEMİYOR. Sonuç: `LLM_MODEL_ANSWER` (compose dosyasında
açıkça `${LLM_MODEL_ANSWER}` olarak yeniden belirtilmiş) doğru geldi ama `LLM_PROVIDER`/
`LLM_MODEL_CLASSIFY` **canlı `.env`'den** (Gemini) geldi — karışık bir yapılandırma
(Gemini istemcisi + "claude-haiku-5-5" model adı) her istekte 503 ile başarısız oldu.

**Düzeltme (yalnız ayrı ortamın kendi backend'ine, canlı `.env`/`docker-compose.yml`'e
DOKUNULMADAN):** `docker compose -p company-ai-eval run -d --use-aliases -e
LLM_PROVIDER=... -e LLM_MODEL_CLASSIFY=... -e LLM_MODEL_ANSWER=... --name
company-ai-eval-backend-1 backend` — servisi `up` yerine `run -d` ile, açık `-e`
üzerinden başlatmak `env_file`'ın örtük `.env` okumasını by-pass ediyor. `--use-aliases`
konteynerin ağda `backend` adıyla çözülmesini sağlıyor (eval script'in `http://backend:8000`
çağrısı için gerekli). **Canlı sistem/`.env`/`docker-compose.yml` hiç değişmedi** —
yalnız `company-ai-eval` projesinin kendi backend'i bu şekilde başlatıldı.

## 2. Üç koşu

| | C1 (Gemini) | C2 (Haiku/Haiku) | C3 (Haiku/Sonnet) |
|---|---|---|---|
| `--model-label` | `gemini-adimD-c1` | `claude-haiku-haiku-adimD-c2` | `claude-haiku-sonnet-adimD-c3` |
| `--min-interval-s` | 26 | 2 | 2 |
| `--max-retries`/`--retry-base-delay-s` | 4/15 | varsayılan | varsayılan |
| Soru sayısı | 99/99 (tam) | 99/99 (tam, 2. denemede) | 99/99 (tam) |
| Maliyet | $0,0000 | $0,3986 | $7,5172 |
| İstek hatası | 9 (HTTP 500, "Beklenmeyen hata") | 0 | 0 |
| G1–G3 güvenlik ihlali | **1** (`GEN-DSC-007`, G2: cevap var kaynak yok) | 1 | 0 |

**Kümülatif maliyet: $0 + $0,3986 + $7,5172 = $7,9158 / $10,0 EVAL_BUDGET_USD** — aşılmadı.

## 3. C1'deki 9 HTTP 500 hatası — Claude ile ilgisi YOK

9 soru (`GEN-DSC-001-M/006-M/008-M/007-K/011-K` + 4 diğeri, `discovery`/`data`/`document`/
`mixed` kategorilerinden) backend'in genel `unhandled_exception_handler`'ından ("Beklenmeyen
bir hata oluştu") 500 aldı — bu **Gemini-only bir koşuda** oluştu, Anthropic/Claude istemci
koduna hiç girilmeden. Bu bir ÖNCEDEN VAR OLAN backend hatası (discovery/data işleme
mantığında, muhtemelen), bu iş emrinin kapsamı dışında — düzeltilmedi, rapor edildi.

## 4. Gecikme (soru başına, bilgi amaçlı — kritere girmiyor)

| | C1 | C2 | C3 |
|---|---|---|---|
| Ortalama | 26.011 ms | 7.965 ms | 5.823 ms |
| Medyan | 25.992 ms | 6.154 ms | 5.712 ms |
| p90 | 26.609 ms | 10.724 ms | 9.174 ms |

**Not:** C1'in gecikmesi büyük ölçüde `--min-interval-s 26` pacing'inden geliyor (Gemini
ücretsiz kademe kotası için gerekli), ham model hızının bir ölçüsü DEĞİL — doğrudan
karşılaştırma yapılmamalı.

Devam ediliyor: **Adım 5** (kriter tablosu, karşılaştırma).
