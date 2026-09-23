# Company AI V0

Kurumsal doküman + Excel + AI bilgi platformu. Şirket bilgisinin **kaynağını, erişim yetkisini, tarihini,
versiyonunu ve ilişkilerini** koruyarak AI tarafından güvenilir kullanılmasını sağlar. Basit bir chatbot değildir.

Bu README Phase 1.2 (departman, rol, proje, yetki) durumunu anlatır; her phase sonunda güncellenir. Plan ve kabul kriterleri:
`docs/PHASES.md`. Mimari kararlar: `docs/ARCHITECTURE.md`. Alan modeli: `docs/DOMAIN_MODEL.md`.

## Gereksinimler (VM)
- Ubuntu 24.04, Docker Engine + Compose plugin (v2+), `make`, `curl`, `git`.
- Host'ta Python/Node gerekmez; test ve lint dahil her şey container içinde çalışır.
- RAM: temel servisler (postgres, backend, ocr-worker, caddy) 6 GB'a sığar; `embed` servisi (`make up-full`) 16 GB ister.

## Kurulum
```bash
git clone <repo> company-ai && cd company-ai
cp infra/.env.example .env      # şifreleri değiştir (POSTGRES_PASSWORD, ADMIN_PASSWORD, JWT_SECRET, DEMO_USER_PASSWORD)
make up                         # postgres + backend build & start, /health bekler
curl localhost:8000/health      # {"status":"ok","version":"0.1.0","database":"ok"}
```
İlk açılışta backend container'ı sırayla: veritabanını bekler → `alembic upgrade head` → admin kullanıcısını
oluşturur (`ADMIN_USERNAME` / `ADMIN_PASSWORD`; kullanıcı varsa dokunmaz) → demo kullanıcılarını, demo
departmanlarını (+ üyeliklerini) ve demo projelerini oluşturur (`DEMO_USER_PASSWORD`, aşağıdaki tablo; var
olanlara dokunmaz) → API'yi başlatır. `ocr-worker` aynı anda ayağa kalkar ve `ingestion_jobs` kuyruğunu 2
saniyede bir yoklar.

Veri kökü `.env` içindeki `DATA_ROOT` altındadır (dev: `./data`, prod: `/srv/company-ai`):
`postgres/ documents/ excel/ app-data/ backups/`. Container'ları silmek veri kaybettirmez.

## Giriş yapma (Phase 1.1)
JWT, httpOnly cookie'de (`access_token`, 8 saat, `samesite=lax`; V0'da `secure=false` — LAN, düz HTTP).
```bash
curl -i -X POST http://localhost:8000/api/auth/login \
  -H 'content-type: application/json' -d '{"username":"admin","password":"<ADMIN_PASSWORD>"}' \
  -c cookies.txt
curl -b cookies.txt http://localhost:8000/api/auth/me
# {"id":"...","username":"admin","display_name":"Yönetici","role":"admin"}
curl -i -X POST http://localhost:8000/api/auth/logout -b cookies.txt
```
Yanlış şifre, bilinmeyen kullanıcı adı ve devre dışı hesap aynı `401` mesajını döner (kullanıcı adı sızdırılmaz).
Başarısız denemeler sınırlıdır: kullanıcı adı başına 5 / 15 dk, IP başına 20 / 15 dk — aşılınca `429`.

Demo hesapları — hepsi tek `DEMO_USER_PASSWORD` şifresini paylaşır; erişim departman üyeliğinden gelir, rolden
değil (`yonetim`/`admin` üyelikten bağımsız her şeyi görür):

| Kullanıcı adı | Rol | Departman üyeliği |
|---|---|---|
| `admin` | `admin` (ayrı `ADMIN_PASSWORD`) | — (her şeyi görür) |
| `yonetim` | `management` | — (üyelikten bağımsız her şeyi görür) |
| `finans` | `employee` | `finans`, `mali_isler` |
| `hukuk` | `employee` | `hukuk` |
| `enerji` | `employee` | `enerji_grubu` (Geliştirme/EPC-İnşaat/Bakım dahil) |

## Departman, rol, proje, yetki (Phase 1.2)
`allowed_document_ids()` gerçek kuralları uygular (SPEC_02 §5): `employee` yalnızca üye olduğu departman(lar)ın
`normal` belgelerini görür; `management` tüm departmanları ve tüm gizlilik seviyelerini (`normal`/`restricted`/
`board`) görür; `admin` her şeyi görür. Yetki her zaman belgenin `department` alanından gelir, projesinden değil.
Belge listesi, indirme (`GET /api/documents/{id}/download`) ve `/api/ask` — hepsi bu fonksiyondan geçer;
yetkisiz erişimde indirme `403`, liste ve `/api/ask` sessizce dışarıda bırakır ("bilgi bulamadım").

```bash
curl http://localhost:8000/api/departments -b cookies.txt   # ağaç: id, name, slug, parent_id
curl http://localhost:8000/api/projects -b cookies.txt      # ANK_RES, IZM_RES (herkes okuyabilir)

# Admin: yeni proje (yalnızca admin; diğerleri 403)
curl -i -X POST http://localhost:8000/api/projects -b admin_cookies.txt \
  -H 'content-type: application/json' \
  -d '{"name":"Yeni Proje","code":"YENI_PRJ","stage":"development","department_ids":["<departman-uuid>"]}'
curl -i -X PATCH http://localhost:8000/api/projects/<id> -b admin_cookies.txt \
  -H 'content-type: application/json' -d '{"is_active": false}'
```

Departmanların CRUD ucu yok (V0'da yalnızca seed); admin'in proje formunda departman seçebilmesi için
`GET /api/departments` salt-okunur. Ankara RES ve İzmir RES `enerji_grubu`, `finans` ve `hukuk`
departmanlarına bağlı (`mali_isler`/`idari_isler` şirket geneli, proje-spesifik değil) — bu bağlantı yalnızca
organizasyonel/filtreleme amaçlıdır, belge yetkisini etkilemez.

## Belge yükleme (Phase 0.2)
Tüm `/api/documents/*` ve `/api/ask` istekleri artık giriş yapılmış olmayı gerektirir (yukarıdaki `cookies.txt`).
```bash
curl -X POST http://localhost:8000/api/documents/upload -b cookies.txt \
  -F "file=@sözleşme.pdf;type=application/pdf" \
  -F "title=Facility Agreement" -F "document_type=facility_agreement" \
  -F "document_date=2023-06-01" -F "counterparty=PQR Bank" -F "status=executed"
# {"id":"...","ingestion_status":"uploaded"} — birkaç saniye içinde "ready" olur:
curl -b cookies.txt http://localhost:8000/api/documents/<id>/status
curl -b cookies.txt http://localhost:8000/api/documents   # yetkili (Adım 0'da: tüm) belgeler
```
Kabul edilen türler: pdf/png/jpg (MIME imzasıyla doğrulanır, `.xlsx/.xlsm/.csv` Phase 4.2). Taranmış (görüntü)
PDF'ler `ocr-worker`'da `ocrmypdf` (tur+eng) ile OCR'lanır; sayfa metni ve ~800 kelimelik chunk'lar
(`document_pages`/`document_chunks`) full-text search (`turkish` + `simple`) için hazırlanır. Test fixture'ları
(`seed_data/t0/`) `docker compose run --rm backend python seed_data/t0/generate.py` ile üretilir.

## Soru sorma (Phase 0.3)
`LLM_API_KEY` `.env`'de dolu olmalı (varsayılan Gemini, OpenAI-uyumlu endpoint; model adları `LLM_MODEL_ANSWER` /
`LLM_MODEL_CLASSIFY`, thinking bütçesi `LLM_REASONING_EFFORT=low`). Anahtar yoksa yalnızca `/api/ask` 503 döner
("Yapay zeka servisi yapılandırılmamış."), belge hattı çalışmaya devam eder.
```bash
# T0 test belgelerini versiyon zinciriyle yükle (Facility Agreement → Amendment 01):
bash seed_data/t0/upload.sh
curl -s -X POST localhost:8000/api/ask -b cookies.txt -H 'content-type: application/json' \
  -d '{"question": "Ankara RES'\''in güncel minimum DSCR covenant'\''ı nedir?"}'
# {"answer":"... 1,20x'tir [K1] ...","answered":true,"sources":[{"ref":"K1","title":"Amendment 01","page_number":3,
#   "document_date":"2025-03-15","version":1,"status":"executed","is_current":true,...}],"model":"...","tokens_in":..}
```
Tek sayfalık test arayüzü: `http://<vm-ip>:8000/ask` (Caddy ve build gerektirmez). Cevaplar Türkçe'dir, her olgu
cümlesi `[K#]` etiketiyle bir belge+sayfaya bağlanır; kaynak yoksa sabit "…yeterli bilgi bulamadım." cevabı döner ve
LLM hiç çağrılmaz. "Güncel" / "ilk" ayrımı `supersedes` zinciri ve `DEMO_TODAY` ile kodda hesaplanır (ADR-021).
Yüklemede zincir kurmak için `effective_date`, `version`, `supersedes_document_id` form alanları opsiyoneldir.
Sistem promptu `backend/app/services/answer_prompt.py`'dedir; kopyası `docs/prompts/ANSWER_SYSTEM_PROMPT.md`
(`make prompt-doc` ile yenilenir, `make lint` eşitliği denetler).

Canlı LLM testleri `make test`'in dışındadır: `make test-llm` (ücretsiz katman 5 istek/dk — testler kendini yavaşlatır;
model saturasyonunda `make test-llm MODEL=gemini-3.5-flash`).

## Truth ledger (Phase 2.1)
İki demo projenin **tüm** rakam, tarih ve isimleri tek yerde: `seed_data/master/` — `company.yaml` (kurgusal
taraflar, SPV'ler, isim whitelist'i), `ankara_res.yaml` (işletmedeki proje: lisans → finansman → inşaat → COD →
operasyon, Facility zinciri DRAFT→V01→V02→EXECUTED→AMD01→AMD02), `izmir_res.yaml` (development; lisans sonrası
alanlar tasarım gereği `null`), `fx_rates.yaml` (kurgusal sabit kurlar). Şema: `seed_data/generator/ledger_schema.py`
(Pydantic). Golden sorular: `seed_data/evaluation/questions.json` (cevaplar rakam değil, `ledger:` yol referansı).
```bash
make validate-ledger     # kronoloji, finans tutarlılığı, İzmir izolasyonu, para birimi, isim whitelist, soru kotaları
# ... 0 error(s), 0 warning(s)  +  tags: USER_FACT=… AI_ASSUMPTION=…
```
**Onay akışı (ADR-013):** her değer `tag: AI_ASSUMPTION` (Claude taslağı) ya da `tag: USER_FACT` (Naci/ortak onayı)
taşır. Taslak tamamen `AI_ASSUMPTION` ile teslim edilir; onaylanan değerin tag'i YAML'da `USER_FACT` yapılır (değer
değişiyorsa yeni değer + `USER_FACT`), `make validate-ledger` tekrar 0 hata vermelidir. **Adım 3 (Phase 3.1, belge
üretimi) ayrı bir "ledger onayı" commit'i olmadan başlamaz.** Durum: v1 ledger **23.09.2026'da onaylandı**
(269/269 `USER_FACT`, "ledger onayı" commit'i); ileride eklenen her yeni değer yine `AI_ASSUMPTION` ile girer ve aynı
akıştan geçer. Onay tablosu `docs/reports/PHASE_2_1_REPORT.md §10`. `make lint` de validator'ı çalıştırır; ledger'ı
bozan bir düzenleme lint'i kırar.

## Make hedefleri
| Hedef | Açıklama |
|---|---|
| `make up` / `make down` | Servisleri başlat / durdur (veri kalır) |
| `make up-full` | `embed` dahil (profile `full`, 16 GB) |
| `make ps`, `make logs SVC=backend` | Durum ve loglar |
| `make test` | pytest: backend → şema doğrulaması → ocr-worker, sırayla; test DB (`company_ai_test`) compose içindeki Postgres'tedir |
| `make lint` / `make format` | ruff + mypy / otomatik biçimlendirme |
| `make migrate`, `make migration NAME=...` | Alembic upgrade / yeni migration |
| `make seed-admin`, `make seed-demo-users`, `make seed-demo-departments`, `make seed-demo-projects` | Admin/demo kullanıcı/demo departman+üyelik/demo proje oluştur (yoksa) |
| `make psql`, `make shell` | Postgres'e psql / backend container'ında bash |
| `make seed`, `make reset-demo`, `make eval`, `make backup`, `make restore` | Sonraki phase'lerde (şimdilik "henüz uygulanmadı") |

Postgres portu host'a açılmaz; `make psql` kullanın. Backend `BACKEND_PORT` (varsayılan 8000) üzerinden
Caddy gelene kadar (Phase 3.3) doğrudan erişilebilir.

## Repo düzeni
```
backend/      FastAPI (app/api, app/services, app/repositories, app/models, app/schemas, app/core), tests/, alembic/
ocr-worker/   ocrmypdf + PyMuPDF ingestion worker; kendi pyproject/tests'i, backend/app'i import etmez
infra/        docker-compose.yml, Caddyfile, .env.example, postgres/init, ocr-worker/Dockerfile
scripts/      wait_for_services.sh (+ ileride seed/backup/restore/eval)
docs/         SPEC_0x, PHASES.md, ARCHITECTURE.md (ADR), DOMAIN_MODEL.md, plans/, reports/, prompts/
```

## Bilinen sınırlar (V0)
- Yalnızca LAN, düz HTTP; HTTPS/Tailscale V0 sonrası.
- Embedding opsiyonel (`EMBEDDINGS_ENABLED=false` varsayılan); sistem yalnızca full-text + metadata ile çalışır.
- Consume klasörü, Word/e-posta ingest, SSO yok.
- `/api/ask` yalnızca belge sorularını cevaplar (DOCUMENT); Excel/DATA ve MIXED sorgular Adım 4.
- Gemini ücretsiz katmanı: `gemini-3.8-flash` için 5 istek/dk; yoğunlukta "high demand" 503 dönebilir — `/api/ask`
  bunu Türkçe 503 mesajıyla iletir, sistem çalışmaya devam eder.
- `POST /api/documents/upload` hâlâ `department`/`project_id`/`confidentiality` almıyor (AI metadata önerisi
  Phase 3.2'de geliyor) — bu alanlar bugün yalnızca DB'ye doğrudan yazılarak (seed/test) doldurulabilir.
  `documents.department` bir FK değil, serbest slug string'idir; yanlış yazılmış bir slug güvenli yönde
  başarısız olur (belge admin dışında kimseye görünmez) ama sessizce — Phase 3.2'nin doğrulama alması gerekiyor
  (bkz. `docs/PHASES.md` Phase 3.2 notu).
- Departman CRUD ucu yok (V0'da yalnızca seed); proje-departman bağlantısı yalnızca organizasyonel/filtreleme
  amaçlıdır, belge yetkisi her zaman belgenin kendi `department` alanından gelir.
