# Company AI V0

Kurumsal doküman + Excel + AI bilgi platformu. Şirket bilgisinin **kaynağını, erişim yetkisini, tarihini,
versiyonunu ve ilişkilerini** koruyarak AI tarafından güvenilir kullanılmasını sağlar. Basit bir chatbot değildir.

Bu README Phase 0.1 (iskelet) durumunu anlatır; her phase sonunda güncellenir. Plan ve kabul kriterleri:
`docs/PHASES.md`. Mimari kararlar: `docs/ARCHITECTURE.md`. Alan modeli: `docs/DOMAIN_MODEL.md`.

## Gereksinimler (VM)
- Ubuntu 24.04, Docker Engine + Compose plugin (v2+), `make`, `curl`, `git`.
- Host'ta Python/Node gerekmez; test ve lint dahil her şey container içinde çalışır.
- RAM: temel servisler (postgres, backend, ocr-worker, caddy) 6 GB'a sığar; `embed` servisi (`make up-full`) 16 GB ister.

## Kurulum
```bash
git clone <repo> company-ai && cd company-ai
cp infra/.env.example .env      # şifreleri değiştir (POSTGRES_PASSWORD, ADMIN_PASSWORD, JWT_SECRET)
make up                         # postgres + backend build & start, /health bekler
curl localhost:8000/health      # {"status":"ok","version":"0.1.0","database":"ok"}
```
İlk açılışta backend container'ı sırayla: veritabanını bekler → `alembic upgrade head` → admin kullanıcısını
oluşturur (`ADMIN_USERNAME` / `ADMIN_PASSWORD`; kullanıcı varsa dokunmaz) → API'yi başlatır.

Veri kökü `.env` içindeki `DATA_ROOT` altındadır (dev: `./data`, prod: `/srv/company-ai`):
`postgres/ documents/ excel/ app-data/ backups/`. Container'ları silmek veri kaybettirmez.

## Make hedefleri
| Hedef | Açıklama |
|---|---|
| `make up` / `make down` | Servisleri başlat / durdur (veri kalır) |
| `make up-full` | `embed` dahil (profile `full`, 16 GB) |
| `make ps`, `make logs SVC=backend` | Durum ve loglar |
| `make test` | pytest — **önce `make up` gerekir**: test DB (`company_ai_test`) compose içindeki Postgres'tedir |
| `make lint` / `make format` | ruff + mypy / otomatik biçimlendirme |
| `make migrate`, `make migration NAME=...` | Alembic upgrade / yeni migration |
| `make seed-admin` | Admin kullanıcısını oluştur (yoksa) |
| `make psql`, `make shell` | Postgres'e psql / backend container'ında bash |
| `make seed`, `make reset-demo`, `make eval`, `make backup`, `make restore` | Sonraki phase'lerde (şimdilik "henüz uygulanmadı") |

Postgres portu host'a açılmaz; `make psql` kullanın. Backend `BACKEND_PORT` (varsayılan 8000) üzerinden
Caddy gelene kadar (Phase 3.3) doğrudan erişilebilir.

## Repo düzeni
```
backend/      FastAPI (app/api, app/services, app/repositories, app/models, app/schemas, app/core), tests/, alembic/
ocr-worker/   OCR worker (Phase 0.2)
infra/        docker-compose.yml, Caddyfile, .env.example, postgres/init, ocr-worker/Dockerfile
scripts/      wait_for_services.sh (+ ileride seed/backup/restore/eval)
docs/         SPEC_0x, PHASES.md, ARCHITECTURE.md (ADR), DOMAIN_MODEL.md, plans/, reports/, prompts/
```

## Bilinen sınırlar (V0)
- Yalnızca LAN, düz HTTP; HTTPS/Tailscale V0 sonrası.
- Embedding opsiyonel (`EMBEDDINGS_ENABLED=false` varsayılan); sistem yalnızca full-text + metadata ile çalışır.
- Consume klasörü, Word/e-posta ingest, SSO yok.
- Phase 0.1'de yalnızca `/health` ve admin kullanıcısı vardır; belge hattı Phase 0.2, soru-cevap Phase 0.3.
