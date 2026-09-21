# Phase 0.1 Raporu — İskelet + ADR'ler

**Tarih:** 21.09.2026  **Model:** Claude Fable 5.1  **Tag:** phase-0-1  **Commit:** 0df3cc0 (`git rev-list -n1 phase-0-1`)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | `make up` → postgres + backend; `curl localhost:8000/health` → 200. | ✅ | Temiz kurulum (`make down` → `data/postgres` silindi → `make up`): 32 s'de hazır; `curl -i localhost:8000/health` → `HTTP/1.1 200 OK`, `{"status":"ok","version":"0.1.0","database":"ok"}`, `x-request-id` header'ı var. `docker compose ps`: postgres (healthy), backend (healthy). |
| 2 | `make test` ≥ 1 test geçer; `make lint` yeşil; `alembic upgrade head` boş DB'de hatasız. | ✅ | `make test` → `21 passed in 0.62s`. `make lint` → ruff "All checks passed", "34 files already formatted", mypy "Success: no issues found in 24 source files". Boş DB: entrypoint logu `Running upgrade -> 0001, init: pgvector extension and users table`; ayrıca `tests/test_migrations.py::test_downgrade_to_empty_then_upgrade_head` (base'e in, head'e çık, `users` + `vector` extension doğrulanır). |
| 3 | ARCHITECTURE.md ≥ 10 ADR; secret yok; `DATA_ROOT=./data` ile çalışır. | ✅ | `grep -c '^## ADR-' docs/ARCHITECTURE.md` → 19 (en uzunu 8 satır). Secret taraması (`AIza…`, `sk-…`, private key kalıpları) → yok; `.env` git-ignore'da (`git check-ignore .env`); `.env.example` yalnızca `change-me-*` değerleri içerir. `.env`'de `DATA_ROOT=./data`; `data/{postgres,documents,excel,app-data,backups}` oluştu ve kullanıldı. |

## 2. Yapılanlar
- Repo düzeni: `.gitignore`, `.gitattributes` (LF), `Makefile`, `README.md` (Türkçe), `infra/`, `backend/`, `ocr-worker/` (yer tutucu), `scripts/`.
- `infra/docker-compose.yml`: `postgres` (pgvector/pgvector:pg16-bookworm, host portu yok, init script ile `company_ai_test` DB + `vector` extension) ve `backend` aktif; `ocr-worker` (`ocr` profili), `caddy` (`web` profili), `embed` (`full` profili) yer tutucu. Tüm veri `${DATA_ROOT}` bind mount; tüm host portları `.env`'den.
- `infra/.env.example`: tüm değişkenler açıklamalı, ileri phase'ler işaretli; Gemini varsayılanları resmi dokümandan (`gemini-3.5-flash-lite`, `gemini-3.8-flash`).
- Backend (FastAPI 0.141, SQLAlchemy 2.0.54 sync + psycopg 3, Alembic 1.20, pydantic-settings 2.15, argon2-cffi): `GET /health` (DB yoklaması, ulaşılamazsa 503), `X-Request-ID` middleware, stdout JSON log (secret maskeleme), Türkçe hata cevapları (stack trace yok), `Settings`, `users` tablosu + `0001` migration (pgvector extension dahil), idempotent admin seed (`python -m app.cli seed-admin`), `wait-for-db` komutu, entrypoint (bekle → migrate → seed → serve; argüman verilirse onu çalıştırır).
- `allowed_document_ids(user, scope, document_ids_provider) -> set[UUID]` sözleşmesi + `DocumentIdsProvider` protokolü + `AuthorizationScope` şeması; Adım 0 stub'ı (aktif kullanıcı → sağlayıcının tüm id'leri; pasif kullanıcı / boş sağlayıcı → boş küme).
- Testler (21): health (200/503/request-id), hata yönetimi, config, JSON log + maskeleme, authorization sözleşmesi, admin seed idempotensi (şifre asla güncellenmez), migration up/down.
- `docs/ARCHITECTURE.md`: 19 ADR (`DocumentStore` ADR-005 ve `allowed_document_ids` ADR-004 ayrı; ADR-005'te "Paperless Adım 3'te DocumentStore arkasına alınabilir" notu). `docs/DOMAIN_MODEL.md` rakamsız iskelet.
- `CLAUDE.md`: dev VM RAM satırı 16 GB olarak düzeltildi (Naci'nin cevabı 3).

## 3. Değişen dosyalar
`git diff --stat dd27059..phase-0-1` (kısaltılmış): 55 dosya, +2601/−1 (uv.lock hariç ≈ 1.900 satır).
```
Makefile, README.md, .gitignore, .gitattributes, CLAUDE.md (1 satır)
infra/: docker-compose.yml, .env.example, Caddyfile, postgres/init/01_init.sql, ocr-worker/Dockerfile
backend/: Dockerfile, entrypoint.sh, pyproject.toml, uv.lock, alembic.ini, alembic/{env.py,script.py.mako,versions/0001_init_users.py}
backend/app/: main.py, cli.py, core/{config,db,logging,request_id,errors}.py, api/{router,health}.py,
              models/{base,user}.py, schemas/{health,authorization}.py, repositories/user_repo.py,
              services/{authorization,admin_seed,security}.py
backend/tests/: conftest.py + 7 test dosyası
docs/: ARCHITECTURE.md, DOMAIN_MODEL.md, plans/PHASE_0_1_PLAN.md, reports/PHASE_0_1_REPORT.md
ocr-worker/README.md, scripts/wait_for_services.sh
```

## 4. Testler
- Toplam: 21, geçen: 21, atlanan: 0, süre 0,62 s (container içinde, `company_ai_test` DB).
- `make lint`: ruff check + ruff format --check + mypy --strict (`app/`) yeşil.
- Uyarılar: Starlette'in httpx TestClient deprecation uyarısı (kütüphane kaynaklı, kodumuzda değil).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Senkron SQLAlchemy + psycopg3 (async yok) | Basitlik; Alembic/DuckDB senkron; LAN ölçeği | ADR-002; ileride async gerekirse yalnızca `core/db.py` + repository'ler değişir |
| Bağımlılıklar `pyproject.toml` + `uv.lock`, image içinde `uv sync --frozen`; dev grubu (pytest/ruff/mypy) image'da | Host'ta Python yok; `make test`/`make lint` container'da | Image ~+60 MB; prod'da da aynı image (V0 için kabul) |
| JSON log için ek kütüphane yok (stdlib formatter) | "framework soup" istenmiyor | `app/core/logging.py` 66 satır |
| Backend kaynağı `./backend:/app` bind mount | Dev'de her değişiklikte rebuild gerekmesin; prod'da zararsız (klon aynı kaynağı içerir) | Dockerfile yine kaynağı kopyalar (standalone build çalışır) |
| `/health` DB'ye `SELECT 1` atar; başarısızsa 503 + `database: unavailable` | "200 dönüyor ama DB yok" durumunu gizlememek | compose healthcheck bunu kullanır |
| Admin seed mevcut kullanıcıya hiç dokunmaz (şifre güncellemez) | `.env` şifresi değişince sessiz reset olmasın | Şifre değişimi Phase 5.2 admin panel |
| `AuthorizationScope` Pydantic modeli (`department`, `project_id`, ikisi de opsiyonel), frozen | Sözleşmenin bir parçası; `/api/ask` ve belge listesi aynı tipi kullanacak | 0.2/1.2'de değişmez |
| Pasif kullanıcı → boş küme, stub'da bile | Güvenli varsayılan | Test ile sabitlendi |
| `users.role` PG native enum `user_role` | Tek yerden doğrulama | Yeni rol = migration |
| `TEST_DATABASE_URL` compose'da tanımlı; `make test` bunu `DATABASE_URL` olarak verir; conftest DB adı `_test` ile bitmiyorsa reddeder | Gerçek DB'nin truncate edilmesini engellemek | — |
| `.env.example` ileri phase değişkenlerini de listeler; `Settings` bunları opsiyonel okur | SPEC_01 §5 "tüm değişkenler" | 0.3/1.1'de zorunlu hale gelir |
| Rapor şablonundaki "Model: Opus/Sonnet" alanına Fable 5.1 yazıldı | Kullanılan model bu | — |

## 6. Açık sorular (Naci cevaplamalı)
- Yok. Plan'daki 5 SORU cevaplandı ve uygulandı (users 0.1'de; allowed_document_ids imza+protokol; 16 GB; Postgres portu kapalı; backend 8000 Caddy'ye kadar açık).
- Not (soru değil): `docs/PHASES.md` 4. satırdaki "6 GB VM yeter" ifadesine dokunmadım; CLAUDE.md düzeltildi. İstersen bir sonraki phase'de PHASES.md'de de güncellerim.

## 7. Riskler / sonraki phase için notlar
- Phase 0.2: `ocr-worker` profili kaldırılıp varsayılan servise alınacak; `infra/ocr-worker/Dockerfile` ocrmypdf + tesseract `tur+eng` ile dolacak (image büyük, ilk build uzun sürebilir).
- `DocumentIdsProvider` 0.2'de `DocumentRepository`'ye bağlanır; `list_document_ids(scope)` SQL seviyesinde filtrelemeli (ADR-007).
- `documents` tablosu 0.2'de `department`, `project_id`, `confidentiality` alanlarını varsayılan değerlerle içermeli (CLAUDE.md).
- İlk `make up`'ta build süresi (image indirme dahil) ~2–3 dk; sonrakiler ~30 s.
- Starlette httpx TestClient deprecation: Starlette bir sonraki major'da `httpx2` isteyebilir; şimdilik sorun yok.

## 8. Doğruladığım üçüncü taraf davranışları
- Gemini OpenAI-uyumlu endpoint (`ai.google.dev/gemini-api/docs/openai`): base URL `https://generativelanguage.googleapis.com/v1beta/openai/`; `reasoning_effort` (`minimal|low|medium|high`) destekleniyor. Model listesi (`…/docs/models`): stable `gemini-3.8-flash`, `gemini-3.5-flash-lite`.
- `pgvector/pgvector` Docker Hub: `pg16-bookworm` tag'i mevcut (pgvector 0.8.x); container'da `CREATE EXTENSION vector` sorunsuz.
- Docker Compose v5.5.1: `env_file` ve göreli volume yolları `--project-directory` ile repo köküne göre çözülüyor (doğrulandı: `./data/...` mount'ları oluştu).
- Python `logging`: `extra` içinde `created` gibi rezerve LogRecord alanları `KeyError` verir (ilk `make up`'ta yaşandı, düzeltildi: `was_created`).
- `docker compose run backend <cmd>`: komut ENTRYPOINT'e argüman olarak gider; entrypoint `exec "$@"` desteklemeli (düzeltildi).

## 9. Kaynak kullanımı
- `docker stats` (boşta): backend ≈ 62 MiB, postgres ≈ 27 MiB; toplam < 100 MiB. VM: 16 GB.
- LLM çağrısı yok (0 token).
