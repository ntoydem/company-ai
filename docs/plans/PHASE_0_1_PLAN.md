# Plan — Phase 0.1: İskelet + ADR'ler

## Bağlam
Repo şu an yalnızca `CLAUDE.md`, `docs/` ve `README_NASIL_KULLANILIR.md` içeriyor; kod yok. Phase 0.1'in amacı Adım 0'ın temelini kurmak: repo düzeni, `docker-compose` (postgres + backend aktif), FastAPI iskeleti (`/health`, ayarlar, JSON log, Alembic, pytest), tek admin seed, `docs/ARCHITECTURE.md` (≥ 10 ADR) ve `docs/DOMAIN_MODEL.md` iskeleti. Kabul kriterleri (PHASES.md, kelimesi kelimesine):
1. `make up` → postgres + backend; `curl localhost:8000/health` → 200.
2. `make test` ≥ 1 test geçer; `make lint` yeşil; `alembic upgrade head` boş DB'de hatasız.
3. ARCHITECTURE.md ≥ 10 ADR; secret yok; `DATA_ROOT=./data` ile çalışır.

Ortam tespiti (VM): Docker 29.8.1 + Compose v5.5.1, Python 3.12.3 (host'ta pip/uv yok → her şey container'da çalışır), 4 vCPU, **15 GB RAM** (docs 6 GB diyor; plan yine 6 GB varsayımına göre, embed kapalı), 5432/8000/8080 portları boş, uid/gid 1000, git remote `origin` mevcut.

Doğrulanan üçüncü taraf gerçekleri:
- Gemini OpenAI-uyumlu base URL: `https://generativelanguage.googleapis.com/v1beta/openai/`; `reasoning_effort` (`minimal|low|medium|high`) destekleniyor. Stable modeller: `gemini-3.8-flash` (cevap), `gemini-3.5-flash-lite` (sınıflandırma).
- `pgvector/pgvector:pg16-bookworm` image tag'i mevcut (pgvector 0.8.x, PG16).

---

## 1. Oluşturulacak dizin ve dosyalar

```
.gitignore                      .env, data/, __pycache__, .venv, .pytest_cache, .mypy_cache, .ruff_cache,
                                seed_data/documents/, seed_data/excel/, seed_data/evaluation/results/, node_modules, dist
.gitattributes                  * text=auto eol=lf; *.sh eol=lf; pdf/xlsx/png/jpg binary
Makefile                        (bölüm 4)
README.md                       Türkçe: kurulum, make hedefleri, .env, DATA_ROOT, bilinen sınırlar (Phase 0.1 hali)
infra/docker-compose.yml        (bölüm 3)
infra/.env.example              tüm değişkenler açıklamalı; gerçek secret yok
infra/Caddyfile                 yer tutucu: :80 → /api/* backend:8000 (Phase 3.3'te frontend eklenir)
infra/postgres/init/01_init.sql CREATE DATABASE company_ai_test; her iki DB'de CREATE EXTENSION vector
infra/ocr-worker/Dockerfile     yer tutucu (python:3.12-slim, "placeholder" çıktısı; ocrmypdf Phase 0.2'de)
ocr-worker/README.md            tek satır: Phase 0.2'de dolacak
scripts/wait_for_services.sh    /health'i N saniye bekler (make up'ta ve smoke için)

backend/
  Dockerfile                    python:3.12-slim, uv ile bağımlılık kurulumu, non-root `app` kullanıcısı
  entrypoint.sh                 pg hazır bekle → alembic upgrade head → seed-admin (idempotent) → uvicorn
  pyproject.toml                deps: fastapi, uvicorn[standard], pydantic-settings, sqlalchemy>=2, psycopg[binary],
                                alembic, argon2-cffi, python-json-logger YOK (stdlib formatter); dev: pytest, httpx,
                                ruff, mypy; ruff+mypy ayarları burada. uv.lock commit edilir.
  alembic.ini, alembic/env.py, alembic/versions/0001_init.py   (vector extension + users tablosu)
  app/__init__.py               __version__
  app/main.py                   create_app(): lifespan, middleware, router kayıt, exception handler
  app/core/config.py            Settings (pydantic-settings): DATABASE_URL, APP_DATA_DIR, LOG_LEVEL, DEMO_TODAY,
                                ADMIN_USERNAME/ADMIN_PASSWORD, EMBEDDINGS_ENABLED, LLM_* (henüz kullanılmaz, opsiyonel)
  app/core/logging.py           stdlib logging + JSON formatter (ts, level, logger, msg, request_id, extra)
  app/core/request_id.py        middleware: X-Request-ID üret/aktar, contextvar, response header
  app/core/errors.py            HTTP/500 handler: kullanıcıya Türkçe mesaj + request_id; stack trace yalnızca logda
  app/core/db.py                engine, SessionLocal, get_session dependency
  app/models/base.py            DeclarativeBase, TimestampMixin (timestamptz, UTC)
  app/models/user.py            users: id uuid, username uniq, password_hash, display_name, role enum
                                (admin|management|employee), is_active, auth_provider='local', external_id null
  app/schemas/health.py         HealthResponse
  app/schemas/auth.py           AuthorizationScope (department, project_id — hepsi opsiyonel)
  app/api/router.py, app/api/health.py     GET /health → {status, version, db:"ok"}; DB'ye ulaşamazsa 503
  app/services/security.py      hash_password / verify_password (argon2-cffi)
  app/services/authorization.py allowed_document_ids(user, scope, document_ids_provider) -> set[UUID]  (Adım 0 stub)
  app/services/admin_seed.py    ensure_admin_user(session, settings): yoksa oluştur; varsa dokunma (şifre değiştirmez)
  app/repositories/user_repo.py get_by_username / create
  app/cli.py                    `python -m app.cli seed-admin`
  tests/conftest.py             test DB (company_ai_test): session başında alembic upgrade head, her test sonrası truncate
  tests/test_health.py          200 + body + X-Request-ID header; DB kapalıyken 503 (engine mock)
  tests/test_config.py          DATA_DIR/DATA_ROOT ve zorunlu ayarlar
  tests/test_logging.py         log satırı geçerli JSON, request_id içerir, şifre alanı maskelenir
  tests/test_authorization.py   stub tüm id'leri döndürür; boş sağlayıcı → boş küme; imza sözleşmesi
  tests/test_admin_seed.py      ilk çağrı oluşturur, ikinci çağrı değiştirmez; hash argon2; düz şifre DB'de yok
  tests/test_migrations.py      boş DB'de upgrade head → downgrade base → upgrade head hatasız

docs/ARCHITECTURE.md            (bölüm 2)
docs/DOMAIN_MODEL.md            rakamsız iskelet (aşağıda)
docs/reports/PHASE_0_1_REPORT.md phase sonunda, TEMPLATE.md'ye göre
docs/PHASES.md                  durum tablosu güncellenir
```
`frontend/`, `seed_data/` ve diğer script'ler bu phase'de **oluşturulmaz** (ilgili phase'lerde gelir; boş `.gitkeep` klasörü eklemiyorum).

**`docs/DOMAIN_MODEL.md` iskeleti (rakam yok):** varlıklar ve ilişkiler — User, Department (ağaç), UserDepartment, Project, Document (zorunlu / temporal / sistem alanları, SPEC_02 §2), DocumentPage, DocumentChunk, IngestionJob, DocumentMetadataSuggestion, AuditLog; enum'lar (role, confidentiality, status, ingestion_status, stage); versiyon zinciri (`supersedes/superseded_by`) ve belge ilişki grafı (SPEC_02 §12); iki demo proje tanımı (aşama ve "hangi alanlar boş" düzeyinde); "hangi phase'de hangi tablo gelir" tablosu.

---

## 2. `docs/ARCHITECTURE.md` — ADR listesi (her biri ≤ 15 satır: bağlam, karar, sonuç)

| # | Başlık | Karar (tek cümle) |
|---|---|---|
| ADR-001 | Topoloji ve deployment | Tek Ubuntu VM'de tek Docker Compose projesi; postgres + backend varsayılan, ocr-worker (0.2'de varsayılan), caddy (`web` profili, 3.3), embed (`full` profili); veri `DATA_ROOT` bind mount; host'a yalnızca `.env`'deki portlar açılır. |
| ADR-002 | Backend katmanları ve veri erişimi | FastAPI + Pydantic v2; api → services → repositories → models katmanları; **senkron** SQLAlchemy 2.x + psycopg3 (async yok: basitlik, Alembic/DuckDB uyumu); Alembic tek migration zinciri; `pydantic-settings` ile `.env`. |
| ADR-003 | Kimlik doğrulama | JWT httpOnly+SameSite cookie 8 saat, refresh yok; Argon2id; tek `local` sağlayıcı, `auth_provider/external_id` SSO için rezerve; admin kullanıcı `.env` şifresiyle idempotent seed edilir. |
| ADR-004 | Yetki modeli ve `allowed_document_ids` sözleşmesi | Tek fonksiyon `allowed_document_ids(user, scope, ...) -> set[UUID]`: saf, deterministik, DB'deki belge kümesinin alt kümesini döndürür; belge listesi / indirme / retrieval / `/api/ask` bu kümeyle **başlar**; Adım 0'da "tüm belgeler", Adım 1.2'de rol+departman+gizlilik kuralları; bypass eden kod yolu yasak, test ile kanıtlanır (boş küme → boş sonuç). |
| ADR-005 | `DocumentStore` arayüzü | `store(document_id, filename, stream) -> StoredFile`, `get_file(document_id, kind: original|ocr) -> Path`, `get_text(document_id) -> str`; tek implementasyon `LocalFileSystemStore` (`$APP_DATA_DIR/documents/<uuid>/original.<ext>`, `ocr.pdf`); metadata'nın tek kaynağı Postgres. |
| ADR-006 | Ingestion hattı ve `ingestion_jobs` kuyruğu | Kuyruk Postgres tablosudur (`status queued|running|done|failed`, `attempts`, `error`, `locked_at`); worker `SELECT … FOR UPDATE SKIP LOCKED` ile poll eder, 3 deneme, sonra `failed` + Türkçe sebep; Redis yok. |
| ADR-007 | Retrieval | Postgres FTS (`turkish` + `simple` tsvector) + metadata filtreleri varsayılan; `EMBEDDINGS_ENABLED=true` iken pgvector hibrit; bayrak kapalıyken sistem tam çalışır ve testler geçer. |
| ADR-008 | Sayfa bazlı kaynak | `document_pages` sayfa metnini tutar; chunk'lar sayfa sınırını aşmaz ve `page_number` NOT NULL; kaynak kartı belge+sayfa+tarih+versiyon+proje gösterir. |
| ADR-009 | LLM istemcisi | `LLMClient` protokolü; `OpenAICompatibleClient` (Gemini, `base_url`) varsayılan, `AnthropicClient` opsiyonel; `LLM_MODEL_CLASSIFY` / `LLM_MODEL_ANSWER` ayrı; her çağrıda token sayımı loglanır; `reasoning_effort` düşük. |
| ADR-010 | Soru yönlendirici | `DOCUMENT_QUERY | DATA_QUERY | MIXED_QUERY | GENERAL_QUERY`; MIXED = iki alt sorgu + birleştirme; GENERAL'de şirket verisi kullanılmaz ve belirtilir. |
| ADR-011 | Excel motoru sınırları | Inspection openpyxl, hesap DuckDB (read-only, in-memory, `enable_external_access=false`), dönüşüm Polars; LLM yalnızca whitelist SELECT + predefined fonksiyon parametreleri; `.xlsm` macro asla; `CalculationEngine` arayüzü, tek impl `CachedValueEngine`. |
| ADR-012 | Temporal model | `document_date`, `effective_date`, `version`, `supersedes/superseded_by`; "güncel" = zincirin son halkası (`DEMO_TODAY`'e göre), "ilk/tarihsel" = ilgili eski belge; eski ≠ yanlış. |
| ADR-013 | Synthetic truth modeli | Tüm demo rakam/tarih/isim `seed_data/master/*.yaml` ledger'dan; her değer `USER_FACT|AI_ASSUMPTION`; generator kodu backend'e import edilmez; mod A (production) ve mod B (generator) ayrı. |
| ADR-014 | "Yorum yok" kuralı (V0) | Sistem bulur/okur/aktarır; görüş, projeksiyon, sebep uydurma yok; standart "bilgi bulamadım" ve "belgelerde sebep belirtilmemiş" metinleri sabit. |
| ADR-015 | Güvenlik sınırları | Yetki yalnızca server-side; secrets yalnızca `.env`; MIME doğrulama; LLM'in yazdığı kod çalıştırılmaz; kullanıcıya stack trace yok; Postgres/ocr/embed portları host'a kapalı; CORS yalnızca Caddy origin; login rate limit. |
| ADR-016 | Audit log ≠ kurumsal hafıza | `audit_log` yalnızca admin görür, 90 gün, retrieval'da kullanılmaz; şifre/key/JWT loglanmaz. |
| ADR-017 | Yapısal loglama ve hata yönetimi | stdlib logging + JSON formatter (stdout), her logda `request_id` (middleware + contextvar); hata cevabı Türkçe + `request_id`; secret alanları maskelenir. |
| ADR-018 | Yapılandırma ve ortam | Tek `.env` (repo kökü), `DATA_ROOT` host tarafı (compose), `APP_DATA_DIR=/data` container tarafı; tüm host portları env'den; compose dosyası dev ve prod'da aynı; host'a özel yol yok. |
| ADR-019 | Test ve kalite | pytest + ayrı `company_ai_test` DB (migration ile kurulur), her endpoint ≥ 1 test; `ruff` + `mypy` (strict, `app/`); phase kapanış ritüeli (test → docs → migration → rapor → PHASES → tag). |

---

## 3. `infra/docker-compose.yml`

Makefile compose'u `docker compose --project-directory . -f infra/docker-compose.yml --env-file .env` ile çağırır → göreli yollar ve `DATA_ROOT=./data` repo köküne göre çözülür. Proje adı `company-ai`.

| Servis | Durum | İçerik |
|---|---|---|
| `postgres` | **aktif** | `pgvector/pgvector:pg16-bookworm`; env `POSTGRES_DB=company_ai`, user/pass `.env`; volume `${DATA_ROOT}/postgres:/var/lib/postgresql/data`, `./infra/postgres/init:/docker-entrypoint-initdb.d:ro`; healthcheck `pg_isready`; **host portu yok** |
| `backend` | **aktif** | `build: ./backend`; `env_file: .env` + `DATABASE_URL=postgresql+psycopg://…@postgres:5432/company_ai`, `APP_DATA_DIR=/data`; volumes `${DATA_ROOT}/documents:/data/documents`, `${DATA_ROOT}/excel:/data/excel`, `${DATA_ROOT}/app-data:/data/app-data`, `./backend:/app` (kaynak bind mount; dev'de yeniden build gerekmez, prod'da da zararsız); `ports: ${BACKEND_PORT:-8000}:8000`; `depends_on: postgres: condition: service_healthy`; healthcheck `/health` |
| `ocr-worker` | yer tutucu, `profiles: [ocr]` | `build: context ./ocr-worker, dockerfile ../infra/ocr-worker/Dockerfile`; aynı `DATABASE_URL`, `documents` volume; Phase 0.2'de profil kaldırılıp varsayılana alınır |
| `caddy` | yer tutucu, `profiles: [web]` | `caddy:2-alpine`; `ports: ${CADDY_PORT:-8080}:80`; `./infra/Caddyfile` ro; Phase 3.3'te frontend eklenir |
| `embed` | yer tutucu, `profiles: [full]` | `ghcr.io/huggingface/text-embeddings-inference:cpu-latest`, `--model-id BAAI/bge-m3`; model cache `${DATA_ROOT}/app-data/models`; host portu yok; Phase 3.4'te doğrulanır |

`make up` dirs'i önceden `mkdir -p` yapar (bind mount root ownership sorununu önlemek için); backend container non-root `app` (uid 1000 build-arg `APP_UID`, `.env`'den; varsayılan 1000).

---

## 4. Makefile hedefleri

| Hedef | Yaptığı |
|---|---|
| `up` | dirs oluştur → `compose up -d --build` (postgres, backend) → `scripts/wait_for_services.sh` |
| `up-full` | `--profile full` ile (embed dahil; 16 GB) |
| `down` / `ps` / `logs` | compose karşılıkları (`logs` follow, `SVC=` ile filtre) |
| `build` | `compose build` |
| `test` | `compose run --rm -e DATABASE_URL=<test db> backend pytest -q` (postgres'i otomatik başlatır) |
| `lint` | `compose run --rm backend sh -c "ruff check . && ruff format --check . && mypy app"` |
| `format` | `ruff format` + `ruff check --fix` |
| `migrate` | `alembic upgrade head` (container içinde) |
| `migration NAME=…` | `alembic revision --autogenerate -m` |
| `seed-admin` | `python -m app.cli seed-admin` |
| `psql` / `shell` | `compose exec postgres psql …` / backend'de `bash` |
| `seed`, `reset-demo`, `eval`, `backup`, `restore` | rezerve: "Henüz uygulanmadı (Phase 3.1 / 4.1 / 5.3)" mesajı verip çıkış 1 |
| `clean` | `down -v` **değil**; yalnızca container + image; veri silme yok (veri silme elle) |

---

## 5. Kendi aldığım küçük teknik kararlar (raporda da listelenecek)
- Bağımlılık yönetimi: `pyproject.toml` + `uv.lock`, image içinde `uv sync --frozen`. Host'ta Python bağımlılığı yok.
- Senkron SQLAlchemy + psycopg3 (ADR-002).
- JSON log için ek kütüphane yok (stdlib formatter).
- `/health` DB'yi `SELECT 1` ile yoklar; başarısızsa 503 (kabul kriteri 200 için DB ayakta olmalı; `make up` bunu garanti eder).
- Zaman: DB'de `timestamptz` UTC; UI/gösterim `Europe/Istanbul`, `DD.MM.YYYY` (Phase 3.3'te).
- `DEMO_TODAY=2026-09-15` `.env`'de (ISO; UI'da DD.MM.YYYY). Bu phase'de yalnızca ayar olarak okunur.
- `.env.example` ileri phase değişkenlerini de (JWT_SECRET, LLM_*, EMBEDDINGS_ENABLED, CADDY_PORT, BACKUP_SECONDARY_PATH) "(Phase x.y)" notuyla listeler; Settings'te opsiyonel tutulur; LLM varsayılanları: `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`, `LLM_MODEL_CLASSIFY=gemini-3.5-flash-lite`, `LLM_MODEL_ANSWER=gemini-3.8-flash`.
- Admin seed idempotent ve şifreyi **güncellemez** (mevcut kullanıcıya dokunmaz; şifre değişimi Phase 5.2 admin panel).
- Rapor şablonundaki "Model: Opus/Sonnet" alanına "Fable 5.1" yazılacak.

## 6. SORU: (spec'te bulamadıklarım — cevap gelene kadar varsayılanla ilerlerim)
1. **SORU:** `users` tablosu PHASES'te Phase 1.1'de listeleniyor ama 0.1 "tek admin kullanıcı seed" istiyor. Varsayılanım: 0.1'de `users` tablosunu Phase 1.1 alanlarıyla (`username, password_hash, display_name, role, is_active, auth_provider, external_id`) oluşturup admin'i seed etmek; 1.1'de yalnızca login/JWT endpoint'leri eklenir. Uygun mu?
2. **SORU:** `allowed_document_ids` 0.1'de `documents` tablosu olmadan tanımlanacak (tablo 0.2'de). Varsayılanım: fonksiyon belge id sağlayıcısını (repository) parametre alır, stub "sağlayıcının verdiği tüm id'ler"i döndürür; 0.2'de `DocumentRepository` bağlanır. Alternatif: `documents` tablosunun `id/department/project_id/confidentiality` iskeletini 0.1'de açmak. Hangisi?
3. **SORU:** VM'de 15 GB RAM görünüyor (docs 6 GB diyor). 6 GB varsayımıyla devam ediyorum, `embed` bu phase'de yine kapalı — doğru mu?
4. **SORU:** Postgres portu host'a açılmasın (SPEC_06 §6). Dev'de DBeaver vb. istersen `.env`'de opsiyonel `POSTGRES_HOST_PORT` yerine `make psql` yeterli mi? Varsayılan: port kapalı, `make psql`.
5. **SORU:** Backend 8000 portu Adım 0'da host'a açık (kabul kriteri `curl localhost:8000/health`). Caddy geldiğinde (3.3) kapatılsın mı? Şimdilik açık bırakıyorum.

---

## Doğrulama (phase sonunda, kabul kriterleri kelimesi kelimesine)
```
cp infra/.env.example .env && make up
curl -i localhost:8000/health                       # 200, JSON, X-Request-ID
make test                                           # ≥ 6 test yeşil
make lint                                           # ruff + mypy yeşil
make down && rm -rf data/postgres && make up        # boş DB'de alembic upgrade head hatasız (entrypoint logu)
grep -rn "sk-\|AIza\|password" --include=*.py --include=*.yml --include=*.example .  # gerçek secret yok
ls docs/ARCHITECTURE.md && grep -c '^## ADR-' docs/ARCHITECTURE.md   # ≥ 10
```
Sonra: README + docs güncel → `docs/reports/PHASE_0_1_REPORT.md` → `docs/PHASES.md` durum tablosu (0.1 tamamlandı, tag, rapor) → `git commit` + `git tag phase-0-1`.
