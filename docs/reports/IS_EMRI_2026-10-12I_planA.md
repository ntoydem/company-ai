# İş Emri 2026-10-12I — Faz A: Salt okunur keşif ve plan

**Tarih:** 12.10.2026 17:50 UTC · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `decf862`) ·
**Ürün:** Ürün 1 · **Anayasa:** Ç-15/6 (geri alınamaz üretim ortamı işlemi), T-9 (önce plan) ·
**Durum:** Faz A tamamlandı, hiçbir şey değiştirilmedi, hiçbir container durdurulmadı — **ONAY bekliyor.**

Faz A'da yalnız `docker compose ls/ps`, `docker volume ls`, salt okunur `SELECT`/`\d` sorguları,
`ls/du/df`, `docker logs` ve repo dosyaları okundu. `.env` yalnız anahtar adları için grep'lendi;
hiçbir gizli değer ekrana basılmadı ve bu rapora yazılmadı.

---

## 1. Canlı ortam tespiti

| Öğe | Değer |
|---|---|
| Compose projesi | **`company-ai`** (tek canlı proje; `company-ai-eval` D-Adım 5'te kaldırılmıştı, `docker compose ls` yalnız `company-ai` gösteriyor: `running(4)`) |
| Compose dosyası | `/home/naci/company-ai/infra/docker-compose.yml`, `name: company-ai` |
| Makefile çağrısı | `docker compose --project-directory . -f infra/docker-compose.yml --env-file .env` (= `$COMPOSE` aşağıda) |
| Container'lar | `company-ai-postgres-1` (pgvector/pgvector:pg16-bookworm, Up 2 weeks, healthy) · `company-ai-backend-1` (Up 20 h, healthy) · `company-ai-ocr-worker-1` (Up 5 days, healthy) · `company-ai-caddy-1` (Up 9 days, `0.0.0.0:8080->80`) |
| Volume | **Adlandırılmış docker volume YOK** (`docker volume ls` boş). Tümü bind mount: `DATA_ROOT=./data` (`.env` satır 10) |
| Postgres verisi | `./data/postgres` → container `/var/lib/postgresql/data` (host kullanıcısı okuyamaz — postgres uid; yedeği `pg_dump` ile alınır) |
| Belge deposu | `./data/documents` → backend ve ocr-worker'da `/data/documents` (`$DATA_ROOT/documents/<uuid>/original.pdf`, `ocr.pdf`) |
| Diğer | `./data/excel` (4 KB, boş), `./data/app-data` (Caddy state, 12 KB), `./data/backups` (önceki yedekler: `2026-09-26/`, `2026-10-07/`) |
| DB | `POSTGRES_DB=company_ai`, `POSTGRES_USER=company_ai`, alembic head **0015**, boyut **15 MB** |
| Backend bind mount | `./backend:/app`, `./seed_data:/app/seed_data` → `seed-demo-documents` **çalışan dalın** manifestini okur |
| Ayarlar | `EMBEDDINGS_ENABLED=false` · `LLM_MODEL_CLASSIFY=LLM_MODEL_ANSWER=gemini-3.5-flash-lite` (OpenAI-uyumlu Gemini) · `ASSIST_MODE=false`, `EK_F_MODE=false` · `DEMO_TODAY=2026-10-06` · `company_settings.enabled_products={P1,P2,P3}` |

Dikkat: `./data/documents` altında **67.652 klasör / 5,3 GB** var ama DB yalnız 76 belgeye işaret ediyor
(76 klasör, toplam **13 MB**). Kalan ~67.500 klasör `make test`'in yan ürünü: testler `compose run backend`
ile aynı bind mount'u (`/data/documents`) kullanıyor (`backend/tests/test_config.py`: `app_data_dir == /data`),
07.10 yedeğinden bu yana 52.526 klasör eklenmiş. Zararsız ama yedek tar'ını büyütüyor (bkz. §4) ve
`reset_demo.sh` bunları da siler (bkz. §3). Düzeltme bu emrin kapsamında değil (Ç-16), yalnız not.

## 2. Canlı DB'nin mevcut durumu (salt okunur)

### Belge tabloları (yükleme ile değişecek)

| Tablo | Satır | Not |
|---|---|---|
| `documents` | **76** | 74 `external_ref`'li demo belge (70 eski kütüphane PDF'i + 4 xlsx; eski adlarla: "Ankara RES"/"İzmir RES") + **2 elle web'den yüklenmiş test belgesi** (`Test Belgesi — Onay Akışı Denemesi`, finans, 02.10; `fatura`, idari_isler, 06.10; ikisi de admin tarafından) |
| `document_pages` | 313 | |
| `document_chunks` | 312 | `embedding` dolu: 0 (embedding kapalı) |
| `ingestion_jobs` | 72 | hepsi `done` |
| `document_metadata_suggestions` | 76 | 66 `failed` (Gemini 429/503), 8 `pending`, 2 `applied` |
| `document_review_events` | 6 | yalnız 2 web test belgesine ait |
| Durum dağılımı | active 40, executed 27, superseded 4, draft 3, amended 2 | confidentiality: normal 71, board 5, **restricted 0** (eski kütüphanede yoktu) |
| Proje bağı | ANK_RES 49, IZM_RES 16, TEST_PRJ 1, NULL 10 | |
| En son ingestion | **07.10.2026 18:09 UTC** (tek belge: `fatura`) | asıl toplu yükleme 25.09.2026 20:22 UTC |

### Korunacak tablolar (yükleme dokunmaz — Faz B sonunda aynı sayılar doğrulanır)

| Tablo | Satır | İçerik |
|---|---|---|
| `users` | **6** | admin (admin), yonetim (management), finans_mudur (department_manager), finans, hukuk, enerji (employee); hepsi `auth_provider=local`, aktif. **Tansu kullanıcısı yok.** |
| `departments` | 12 | 6 üst (enerji_grubu, finans, hukuk, idari_isler, ik, mali_isler) + 6 alt |
| `user_departments` | 4 | |
| `projects` | **3** | ANK_RES "**Ankara RES**", IZM_RES "**İzmir RES**", TEST_PRJ "Test Project" — bkz. §6 risk R1 |
| `project_departments` | 6 | |
| `folders` | 6 | üst departman kök klasörleri (B-26) |
| `folder_grants` / `folder_grant_events` | 0 / 4 | |
| `company_settings` | 1 | `{P1,P2,P3}` |
| `tag_catalog` / `document_type_guide` | 21 / 10 | |
| `audit_log` | 1.362 | son 24 saat: 124 satır (11.10 20:00–21:00 UTC, demo kullanıcılar enerji/finans/hukuk/yonetim — eval koşusu deseni; 12.10 05:25 UTC admin 1 soru). `documents_retrieved` uuid[] **FK'sız** → truncate sonrası eski ID'ler kalır, zararsız. |
| `admin_events` | 1 | |

`documents`'a FK ile bağlı tablolar (CASCADE ile birlikte boşalacaklar): `document_pages`, `document_chunks`,
`ingestion_jobs`, `document_metadata_suggestions`, `document_review_events` (+ `documents`'ın kendi
supersedes/superseded_by self-FK'leri). Başka hiçbir tablo `documents`'a FK ile bağlı değil.

## 3. Yükleme yolu

### Resmi komutlar (repo)
- `make seed` → `scripts/seed_demo.sh`: ledger doğrula → `generate_documents` (prose'dan PDF, LLM yok) →
  `validate_documents` → seed-admin/users/departments/folders/projects → **`seed-demo-documents`** →
  `wait-for-documents --timeout 1800`.
- `make seed-demo-documents` → `python -m app.cli seed-demo-documents` (`seed_data/documents/manifest.json`
  + otomatik `seed_data/excel/manifest.json`) ve ardından `wait-for-documents --timeout 600`.
- `make reset-demo` → `scripts/reset_demo.sh`: `TRUNCATE documents CASCADE` + `rm -rf $DATA_ROOT/documents/*`.
  "Kullanıcı/departman/proje korunur" (script başlığı, Phase 3.1 SORU 2).

### Eval ortamında nasıl yüklendi (D Adım 2, 11.10.2026)
`COMPOSE_PROJECT_NAME=company-ai-eval ENV_FILE=infra/.env.eval bash scripts/seed_demo.sh` — **boş** bir DB'ye
(`./data-eval`, `company_ai_eval`). O gün 109 belge (102 PDF + 7 xlsx); bugünkü manifest **106 PDF + 7 xlsx = 113**
(`generated_at 2026-10-12T17:17:52Z`, İş Emri H'de üretildi; `seed_data/documents/` gitignore'da, yerelde mevcut:
130 PDF dosyası = 106 servis edilen + 9 `.digital.pdf` + eski kalıntılar; manifest 106 girdi; 97 `digital_pdf`, 9 `scanned_pdf`).

### Siler mi / üstüne yazar mı / ekler mi?
`ensure_demo_documents` (`backend/app/services/demo_documents_seed.py`) **create-if-missing, `external_ref` anahtarlı**:
- Var olan `external_ref` → **hiç dokunmaz** (başlık, dosya, metadata dahil; yalnız boşsa `parties` ekler). Zincir
  (`supersedes`/`related`) ikinci geçişte yeniden bağlanır.
- Olmayan `external_ref` → ekler (PDF için `ingestion_jobs` kuyruğuna koyar, xlsx'i doğrudan `ready` yaratır).
- **Sonuç:** Canlıdaki 74 ref'in tamamı yeni manifestte de var. Tek başına `seed-demo-documents` çalıştırılırsa
  yalnız **39 yeni belge eklenir, 74 eski belge ESKİ içerikle kalır** (ör. DOC-ANK-FIN-007 13,6M düzeltmesi,
  G Adım 3 dava dilekçesi davacı adları, F/G yeniden üretimleri canlıya yansımaz). "Yeni kütüphane"
  istendiği için **önce `reset_demo.sh` (TRUNCATE + dosya silme), sonra `seed-demo-documents`** gerekir.
- Kullanıcı/yetki tabloları: `reset_demo.sh` yalnız `documents` + CASCADE tablolarını siler; `seed-demo-documents`
  `users/departments/projects/folders/company_settings`'e **yazmaz** (yalnız okur: `uploaded_by=admin`,
  departman kök klasörü, `project_code → projects.code` eşlemesi).

### Önerilen Faz B yükleme komutları (sırayla, repo kökünde)
```bash
COMPOSE="docker compose --project-directory . -f infra/docker-compose.yml --env-file .env"
mkdir -p logs
TS=$(date +%Y%m%d-%H%M)            # yedekle aynı TS kullanılır

# 3a. Ön kontrol (salt okunur): manifest 106 girdi, dosyalar yerinde
python3 -c "import json,os; m=json.load(open('seed_data/documents/manifest.json'))['documents']; \
  missing=[d['file'] for d in m if not os.path.exists('seed_data/documents/'+d['file'])]; \
  print(len(m), 'eksik:', missing)"

# 3b. Eski kütüphaneyi sıfırla (documents + CASCADE; users/departments/projects/folders KORUNUR)
bash scripts/reset_demo.sh --yes 2>&1 | tee logs/is_emri_I_${TS}_reset.log
#   (rm -rf izin katmanınca reddedilirse eşdeğeri: $COMPOSE run --rm --user root --entrypoint sh \
#    -v "$PWD/data/documents:/docs" postgres -c 'rm -rf /docs/*'  — aynı sonuç, container içinden)

# 3c. (SORU 1 "evet" ise) proje satırları — §6 R1'deki SQL, ayrı dosya logs/is_emri_I_${TS}_projects.log

# 3d. Yeni kütüphaneyi yükle + OCR bitene kadar bekle (timeout 600 s; yetmezse wait-for-documents 1800 ile tekrar)
make seed-demo-documents 2>&1 | tee logs/is_emri_I_${TS}_seed.log
```

### Tetiklenen arka plan işleri ve süre
- **OCR (ocr-worker):** 106 PDF için 106 `ingestion_jobs`. Referans: 25.09'daki 69 belge/306 sayfa **80 saniyede**
  bitti (`document_pages.created_at` 20:22:06 → 20:23:26). Yeni kütüphanede 9 `scanned_pdf` (200 DPI raster,
  gerçek tesseract tur+eng) var → tahmin **3–6 dakika**, `wait-for-documents --timeout 600` yeterli olmalı.
- **Embedding:** `EMBEDDINGS_ENABLED=false`, `embed` servisi yok → **tetiklenmez**, `document_chunks.embedding` NULL kalır (beklenen).
- **metadata_suggestion döngüsü (backend lifespan, `app/main.py`):** her 15 s'de `ready` + `ai_suggestion_id IS NULL`
  olan ≤5 belgeyi `LLM_MODEL_CLASSIFY` (gemini-3.5-flash-lite) ile sınıflandırır. **Kapatılamaz** (backend restart
  gerekir — emirde yok). 113 belge → **≤113 Gemini çağrısı, ~6 dakika** (5/15 s). Başarısız çağrı `failed` olarak
  kaydedilir, tekrar denenmez (bugünkü canlıda 66/76 `failed`). Yükleme için **zorunlu değil**; sonradan admin
  `POST /api/documents/{id}/suggest-metadata` ile tek tek yeniden üretebilir.
- **Servis kesintisi:** YOK — hiçbir container durdurulmaz/yeniden başlatılmaz; `seed-demo-documents` ayrı
  `compose run` container'ında çalışır. TRUNCATE ile `ready` arasında (~5 dk) arayüz boş/eksik kütüphane gösterir.

## 4. Yedek ve geri dönüş planı

Yedek yeri: **`./data/backups/`** (= `$DATA_ROOT/backups`, repo `backup.sh`/`restore.sh` konvansiyonu, gitignore'da;
emirdeki "backups/" bu dizin olarak yorumlandı). Disk: `/` 96 GB, **54 GB boş** (%45 dolu). Beklenen yedek boyutu:
dump ~0,5–1 MB; `documents` tar'ı 5,3 GB ham → tahmini 1–3 GB sıkıştırılmış (67 k test klasörü yüzünden; canlı 76
belge yalnız 13 MB), süre 2–5 dk.

```bash
COMPOSE="docker compose --project-directory . -f infra/docker-compose.yml --env-file .env"
TS=$(date +%Y%m%d-%H%M); mkdir -p data/backups

# 4a. Postgres tam dump (custom format)
$COMPOSE exec -T postgres sh -c 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > data/backups/live_pre_I_${TS}.dump
ls -l data/backups/live_pre_I_${TS}.dump
$COMPOSE exec -T postgres pg_restore --list < data/backups/live_pre_I_${TS}.dump | grep -cE 'TABLE DATA'   # ≥ 20 bekleniyor
$COMPOSE exec -T postgres pg_restore --list < data/backups/live_pre_I_${TS}.dump | grep -E 'TABLE DATA public (documents|users) '

# 4b. ./data dosya yedeği (postgres/ hariç — host okuyamaz, dump kapsıyor)
tar czf data/backups/live_pre_I_${TS}_documents.tar.gz -C data documents excel
$COMPOSE run --rm --user root --entrypoint sh -v "$PWD/data/app-data:/app-data:ro" \
  -v "$PWD/data/backups:/backup" postgres -c "tar czf /backup/live_pre_I_${TS}_app-data.tar.gz -C / app-data"
tar tzf data/backups/live_pre_I_${TS}_documents.tar.gz | head -3   # okunabilirlik
ls -lh data/backups/live_pre_I_${TS}*
```

**GERİ DÖNÜŞ (yalnız gerekirse):**
```bash
# R1. Backend + worker'ı durdur (açık bağlantı kalmasın), postgres ve caddy çalışmaya devam eder
$COMPOSE stop backend ocr-worker
# R2. DB'yi dump'tan geri yükle (mevcut tabloları düşürüp yeniden yaratır)
$COMPOSE exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < data/backups/live_pre_I_${TS}.dump
# R3. Belge dosyalarını geri aç
$COMPOSE run --rm --user root --entrypoint sh -v "$PWD/data/documents:/docs" postgres -c 'rm -rf /docs/*'
tar xzf data/backups/live_pre_I_${TS}_documents.tar.gz -C data
# R4. Servisleri geri getir ve doğrula
$COMPOSE up -d backend ocr-worker && CADDY_PORT=8080 bash scripts/wait_for_services.sh 120
$COMPOSE exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select count(*) from documents"'   # 76
```
Alternatif tam yol: `bash scripts/restore.sh <dizin> --yes` (tüm servisleri `down` eder, postgres verisini siler
ve `postgres.dump/documents.tar.gz/excel.tar.gz/app-data.tar.gz` adlarını bekler — bu yüzden yukarıdaki hedefli
yol tercih edildi).

## 5. Kabul kontrolü planı (Faz B/3)

**5a. Sayılar (salt okunur SQL):**

| Kontrol | Beklenen |
|---|---|
| `select count(*) from documents` | **113** (106 PDF + 7 xlsx) |
| `… where external_ref is not null` | 113 (web belgesi yok) |
| `select ingestion_status, count(*) … group by 1` | `ready` 113, `failed` 0 |
| `select status, count(*) from ingestion_jobs group by 1` | `done` 106 |
| `select count(*) from document_pages` / `document_chunks` | > 0 (rapora yazılır) |
| `select confidentiality, count(*) …` | normal 90 (83 PDF + 7 xlsx), restricted 18, board 5 |
| `select count(*) from users` | **6, aynı kullanıcı adları/roller** |
| `departments / user_departments / folders / company_settings / tag_catalog / document_type_guide` | 12 / 4 / 6 / 1 ({P1,P2,P3}) / 21 / 10 — değişmemiş |
| `projects` | SORU 1'e göre 3 (değişmemiş) ya da 7 |
| `select count(*) from documents where folder_id is null` | 0 |
| `wait-for-documents` log satırı | `all ready, count: 113` |
| (isteğe bağlı, salt okunur) `make validate-ocr ARGS="--all"` | taranmış 9 belgenin OCR metni ↔ manifest `key_facts_used` |

**5b. `/api/ask` duman testi (Caddy üzerinden, `http://localhost:8080`, 3 çağrı, şifreler `.env`'den okunur, loga yazılmaz):**

| # | Kullanıcı | Soru | Beklenen |
|---|---|---|---|
| 1 | `finans` (employee, finans) | "Karatepe RES kredisinde fiilen kullandırılan toplam tutar nedir?" | cevaplı; **13.600.000 USD**; kaynak DOC-ANK-FIN-007 (İş Emri H Adım 3 düzeltmesi canlıya yansıdı) |
| 2 | `hukuk` (employee, hukuk) | "Yeşilova RES arazi tahsisi tazminat davasında davacı kimdir?" | cevaplı; **Hasan Çelik**; kaynak DOC-YSV-LEG-002 (yeni kütüphane + restricted hukuk belgesini hukuk çalışanı görür) |
| 3 | **`enerji`** (employee, enerji_grubu) — **yetki negatifi** | "Boztepe RES imar planı davasında yürütmeyi durdurma talebi ne oldu?" | `answered=false`, kaynak yok, cevapta "yeterli bilgi bulamadım" kalıbı; `sources` boş; DOC-BOZ-LEG-001..004 (hukuk/restricted) **hiç anılmaz** |

```bash
BASE=http://localhost:8080; J=$(mktemp)
curl -s -c $J -X POST $BASE/api/auth/login -H 'content-type: application/json' \
  -d "{\"username\":\"finans\",\"password\":\"$(grep -E '^DEMO_USER_PASSWORD=' .env | cut -d= -f2-)\"}" >/dev/null
curl -s -b $J -X POST $BASE/api/ask -H 'content-type: application/json' \
  -d '{"question":"Karatepe RES kredisinde fiilen kullandırılan toplam tutar nedir?"}' | python3 -m json.tool
# (aynı kalıp hukuk ve enerji için; çıktılar logs/is_emri_I_${TS}_ask_{1,2,3}.json — şifre dosyaya yazılmaz)
```
Her çağrı ayrıca `audit_log`'a düşer (G4 — rapora `select question, answered… order by timestamp desc limit 3`).
Gemini 429/503 verirse (ücretsiz kota, bkz. §6) yükleme **geçersiz olmaz**; duman testi kota açılınca tekrarlanır ve rapora not düşülür.

## 6. Riskler

| # | Risk | Değerlendirme |
|---|---|---|
| R1 | **Proje satırları eski/eksik.** Canlı `projects`: ANK_RES "Ankara RES", IZM_RES "İzmir RES", TEST_PRJ. Ledger/manifest: "Karatepe RES", "Kızılova RES" + **YSV_RES (11 belge+2 xlsx), BOZ_RES (8+1), AKY_GES (1), DMR_RES (1)**. `seed-demo-projects` yalnız ANK/IZM'yi yaratır ve var olanı değiştirmez. Etkisi: (a) 21 PDF + 3 xlsx `project_id=NULL` ile yüklenir; (b) `named_project_codes()` proje adını **DB'den** okur → "Karatepe RES'in…" sorusu ANK_RES'e daraltılmaz, "Yeşilova/Boztepe" hiç tanınmaz → Ü-3/G2 proje izolasyonu eval ortamındakinden (taze DB, yeni adlar) **farklı** davranır; eval sonuçları canlıyı temsil etmez. | **SORU 1** (aşağıda). Kod değişikliği değil, 6 satırlık SQL. |
| R2 | **2 web test belgesi + 6 review event + 2 applied suggestion** TRUNCATE ile silinir (dump'ta kalır). | **SORU 2.** `TEST_PRJ` proje satırı kalır (reset dokunmaz). |
| R3 | **Canlı kullanıcı:** Tansu web testi başlamadı; `users`'da Tansu yok; son 24 saatteki 124 audit satırı demo kullanıcılarla eval koşusu deseni (11.10 20–21 UTC) + admin 1 soru (12.10 05:25). Kesinti yok; ~5 dk boş kütüphane penceresi. | Düşük. Faz B sırasında `make test`/`make eval` **çalıştırılmamalı** (aynı `data/documents` ve backend). Dal değiştirilmemeli (bind mount). |
| R4 | **Gemini çağrısı/maliyet:** metadata_suggestion ≤113 classify çağrısı (kapatılamaz) + 3 `/api/ask` (~25 k giriş token/çağrı, 12.10 05:25 örneği). Ücretsiz katmanda **$0**; ücretli katman olsaydı flash-lite ile tahmini **< $0,10** toplam. Ücretsiz kota (500/gün/model, 429) aşılırsa suggestion satırları `failed` olur (yükleme etkilenmez), duman testi 503 döner → tekrar. | Orta (kota). Anthropic çağrısı **yok**. |
| R5 | **Yedek boyutu/süresi:** `documents` tar'ı 5,3 GB ham (67 k test klasörü). 54 GB boş disk yeter; 2–5 dk. | Düşük. |
| R6 | `rm -rf data/documents/*` izin katmanınca reddedilebilir (26.09'da yaşandı). | §3b'deki root-container eşdeğeri hazır. |
| R7 | `wait-for-documents --timeout 600` taranmış 9 belge yüzünden yetmezse komut 1 döner ama OCR devam eder. | `$COMPOSE run --rm -T backend python -m app.cli wait-for-documents --timeout 1800` ile beklemeye devam. |
| R8 | `logs/` dizini gitignore'da değil → untracked kalır; `.gitignore` değişikliği emirde yok. | Loglar commit edilmez, rapora yol yazılır. |

## SORU (onayla birlikte cevap bekliyor)

**SORU 1 — Proje satırları (R1):** Faz B/3c'de, `reset` sonrası ve `seed-demo-documents` öncesi aşağıdaki SQL
çalıştırılsın mı? Önerim: **EVET** (aksi hâlde yeni kütüphanenin 24 belgesi projesiz yüklenir ve "Karatepe/Kızılova/
Yeşilova/Boztepe" adları `/api/ask` proje tespitinde tanınmaz). Adlar ve `stage` değerleri ledger `project.name/stage`'den;
departman bağı ANK/IZM ile aynı (enerji_grubu, finans, hukuk — `demo_projects_seed.py`). GNS_GES belgesi olmadığı için eklenmiyor.
```sql
BEGIN;
UPDATE projects SET name='Karatepe RES' WHERE code='ANK_RES';
UPDATE projects SET name='Kızılova RES' WHERE code='IZM_RES';
INSERT INTO projects (id, code, name, stage, created_at, updated_at) VALUES
  (gen_random_uuid(),'YSV_RES','Yeşilova RES','operation',now(),now()),
  (gen_random_uuid(),'BOZ_RES','Boztepe RES','operation',now(),now()),
  (gen_random_uuid(),'AKY_GES','Akyar GES','development',now(),now()),
  (gen_random_uuid(),'DMR_RES','Demirci RES','development',now(),now());
INSERT INTO project_departments (project_id, department_id)
  SELECT p.id, d.id FROM projects p, departments d
  WHERE p.code IN ('YSV_RES','BOZ_RES','AKY_GES','DMR_RES') AND d.slug IN ('enerji_grubu','finans','hukuk');
COMMIT;
```
(Kolonlar Faz A'da `\d projects` / `\d project_departments` ile doğrulandı: `id, name, code, stage, is_active (default true), created_at, updated_at` / `project_id, department_id, created_at`; `stage` enum `project_stage` = development|construction|operation. Geri dönüşü dump.)
Alternatif: HAYIR → 3 proje aynen kalır, 24 belge `project_id=NULL`, rapora kayıt düşülür.

**SORU 2 — İki web test belgesi (R2):** `Test Belgesi — Onay Akışı Denemesi` ve `fatura` (admin'in elle yüklediği
denemeler) TRUNCATE ile silinsin mi? Önerim: **EVET** (demo kütüphanesinin parçası değil; dump'tan geri alınabilir).
`TEST_PRJ` proje satırına dokunulmaz.

**SORU 3 — Yedek konumu:** `./data/backups/live_pre_I_<TS>.dump` (+ `_documents.tar.gz`, `_app-data.tar.gz`)
uygun mu, yoksa repo kökünde ayrı `backups/` mı isteniyor?

## [ANAYASA KONTROLÜ] — Faz A
- **Ç-15/6:** Üretim ortamında hiçbir yazma yapılmadı; container durdurulmadı; `.env` düzenlenmedi.
- **T-9:** Plan uygulamadan önce yazıldı; Faz B yalnız "ONAY FAZ B" ile başlar.
- **Ç-16:** Kod değişikliği yok. Emirde yazmayan tek öneri (proje satırları SQL'i) **SORU** olarak soruldu, uygulanmadı.
- **G3 (yetki):** Duman testi #3 yetki negatifi içerir; yükleme `allowed_document_ids`'e dokunmaz.
- **Gizlilik:** Hiçbir anahtar/şifre okunmadı, yazılmadı; Faz B komutları şifreyi `.env`'den alır, loga yazmaz.
