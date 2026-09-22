# Phase 0.2 — Belge Hattı: Implementation Plan

## Context

Phase 0.1 (tamamlandı, `phase-0-1`) FastAPI iskeletini, `users` tablosunu, pydantic-settings config'i, structured logging'i, Alembic + pytest altyapısını ve `allowed_document_ids()` stub'ını (ADR-004, imzası dondurulmuş) kurdu. Phase 0.2 bunun üzerine "Adım 0 — T0 Çekirdek testi"nin belge tarafını inşa ediyor: upload → OCR → sayfa metni → chunk → FTS → yetki-filtreli retrieval, artı Phase 0.3'ün (`/api/ask`) üzerine kuracağı `seed_data/t0/` test belgeleri. Kabul kriterleri ve tüm ADR'ler `docs/PHASES.md`, `docs/SPEC_01/02`, `docs/ARCHITECTURE.md` (ADR-004/005/006/007/008) doğrudan okunarak doğrulandı; kod tarafında mevcut konvansiyonlar (`app/models/base.py`, `app/services/authorization.py`, `app/schemas/authorization.py`, `alembic/versions/0001_init_users.py`, `infra/docker-compose.yml`, `docs/PHASES.md`) verbatim okunarak teyit edildi.

İki mimari karar kullanıcıyla netleştirildi:
- **ocr-worker tamamen bağımsız bir Python projesi** olacak (kendi `pyproject.toml`/`uv.lock`/Dockerfile/tests; `backend/app`'i import etmez, Postgres şemasını `MetaData().reflect()` ile okur). Gerekçe: ADR-006'nın "tek ekstra container yeterli" mantığı ve CLAUDE.md'nin RAM bütçesi (backend image'ı hafif kalmalı, ocrmypdf+tesseract'ın ağırlığı izole edilmeli).
- **`GET /api/documents` ve `retrieve()` için "mevcut kullanıcı"**, Phase 1.1'deki gerçek login'e kadar seed edilmiş admin'e sabitlenen bir stub `get_current_user` dependency'sinden gelecek — `allowed_document_ids()`'in Step-0 stub felsefesiyle tutarlı, Phase 1.1'de JWT-cookie tabanlı gerçek dependency ile değiştirilecek.

---

## 1. Tablolar

### Enum'lar (raw `CREATE TYPE` + `postgresql.ENUM(..., create_type=False)`, `0001`'in deseni)
- `document_status`: `draft | executed | amended | superseded | active`
- `confidentiality_level`: `normal | restricted | board` (tip adı `confidentiality` kolon adıyla çakışmasın diye farklı)
- `document_source`: `web | consume`
- `ingestion_status`: `uploaded | ocr | ready | failed`
- `ingestion_job_status`: `queued | running | done | failed`

### `documents` (`backend/app/models/document.py`)
SPEC_02 §2'deki üç grup birebir: **Zorunlu** `title, department, subdepartment, project_id, document_type, counterparty, document_date, status, confidentiality, tags, source, created_at, updated_at`; **Temporal** `effective_date, expiration_date, version, revision, supersedes_document_id, superseded_by_document_id, related_document_ids`; **Sistem** `storage_path, ingestion_status, ingestion_error, uploaded_by, ai_suggestion_id, page_count`.

Karar verdiğim noktalar (küçük teknik detay, burada listeleniyor):
- `department`, `subdepartment`, `project_id` — **FK yok, düz nullable kolon** (`departments`/`projects` tabloları Phase 1.2'de gelecek; Phase 1.2 migration'ı FK'yi sonradan ekleyecek).
- `ai_suggestion_id` — nullable UUID, FK yok (`document_metadata_suggestions` Phase 3.2).
- `uploaded_by` → `uploaded_by_id`, FK `users.id ON DELETE SET NULL` (users zaten var, FK güvenli).
- `supersedes_document_id`/`superseded_by_document_id` → self-FK `documents.id ON DELETE SET NULL`.
- `related_document_ids` → `ARRAY(UUID)`, join table yok (V0 basitleştirmesi, API şekli aynı kalır, ileride join table'a geçilebilir).
- Index'ler: `ix_documents_department`, `ix_documents_project_id`, `ix_documents_status`, `ix_documents_ingestion_status`.

### `document_pages`
`id, document_id (FK CASCADE, indexed), page_number, text` + `TimestampMixin`. `UNIQUE(document_id, page_number)`.

### `document_chunks`
`id, document_id (FK CASCADE, indexed), chunk_index, page_number (NOT NULL — ADR-008), text, tsv_turkish, tsv_simple, embedding` + `TimestampMixin`. `UNIQUE(document_id, chunk_index)`.

**FTS tasarımı — iki ayrı generated kolon, tek birleşik değil:**
```sql
tsv_turkish tsvector GENERATED ALWAYS AS (to_tsvector('turkish', text)) STORED,
tsv_simple  tsvector GENERATED ALWAYS AS (to_tsvector('simple',  text)) STORED,
```
Her biri kendi GIN index'ine sahip. Gerekçe: `turkish` config Türkçe stemming uygular ve "DSCR"/"covenant" gibi İngilizce ödünç kelimeleri/kısaltmaları farklı token'layabilir; `simple` config stemming yapmadan güvenlik ağı sağlar. Sorgu her iki kolonu da `OR` ile arar (bkz. §5) — kabul kriteri 4'ün "DSCR covenant" testini garantiler. Tek birleşik `setweight` kolonu alternatifi, hangi config'in eşleştiğini belirsizleştirdiği ve indexleme avantajı sağlamadığı için elendi.

`embedding`: `Vector(1024)` (bge-m3 boyutu, Phase 3.4'te doğrulanacak), nullable, `EMBEDDINGS_ENABLED=false` iken hep NULL.

### `ingestion_jobs`
`id, document_id (FK CASCADE, indexed), status, attempts (default 0), error, locked_at` + `TimestampMixin`. `job_type` kolonu YOK (YAGNI — V0'da tek iş türü var). Composite index `(status, created_at)` — polling sorgusunu (`WHERE status='queued' ORDER BY created_at`) destekler.

### Migration
**Tek migration**, `0002_documents_pipeline.py` (`revision="0002"`, `down_revision="0001"`): 5 enum → `documents` → `document_pages` → `document_chunks` (generated tsvector kolonları + GIN index'ler) → `ingestion_jobs`, sırayla. Tek migration'da toplamanın gerekçesi: DOMAIN_MODEL §9 bu 4 tabloyu tek fazda (0.2) topluca listeliyor ve birlikte test ediliyorlar — `0001`'in "faz başına tek migration" emsaliyle tutarlı. `downgrade()` ters sırada tam ayna (index → tablo → enum), `tests/test_migrations.py`'nin `downgrade("base")` → `upgrade("head")` roundtrip'ini geçecek şekilde. `make migration NAME=...` ile iskelet alınsa bile generated tsvector kolonları ve enum/index şekli elle düzeltilecek (autogenerate bunları doğru üretmez).

`app/models/__init__.py`'a yeni modeller + enum'lar eklenir (test `_clean_tables` fixture'ının truncate edebilmesi için zorunlu).

**Not:** `documents.project_id`/`department` üzerine FK, Phase 1.2'nin migration'ı tarafından eklenecek — bu, o fazın kapsamı, burada sadece not düşülüyor.

---

## 2. ocr-worker

### Proje yapısı (bağımsız Python projesi — kullanıcı onaylı)
```
ocr-worker/
  pyproject.toml        # sqlalchemy, psycopg[binary], ocrmypdf, pymupdf; dev: pytest
  uv.lock
  worker/
    __init__.py
    config.py            # os.environ'dan DATABASE_URL, APP_DATA_DIR, POLL_INTERVAL_S — pydantic-settings değil, basit dataclass
    db.py                 # engine + MetaData().reflect(only=["documents","document_pages","document_chunks","ingestion_jobs"])
    storage.py             # original/ocr path yardımcıları (ADR-005 layout'unu ayna alır, kod paylaşımı yok)
    image_to_pdf.py         # png/jpg -> tek sayfalık PDF (PyMuPDF ile — bkz. karar aşağıda)
    ocr.py                   # subprocess: ocrmypdf --language tur+eng --skip-text --rotate-pages --deskew
    extract.py               # PyMuPDF sayfa metni çıkarma
    chunking.py               # chunk_page_text(text, size=800, overlap=100)
    pipeline.py                 # lock -> process -> commit/fail orkestrasyonu
    main.py                      # poll loop + heartbeat
  tests/
    conftest.py                  # TEST_DATABASE_URL engine fixture + truncate fixture
    test_pipeline.py
    test_chunking.py
    test_image_to_pdf.py
```

Şema senkronizasyonu `MetaData().reflect()` ile sağlanır (backend'in Alembic migration'ı tek doğruluk kaynağı); bir migration worker'ın beklediği kolonu değiştirirse reflect + assert sessizce değil, açıkça patlar.

### `infra/ocr-worker/Dockerfile` (mevcut placeholder'ın yerine)
Base `python:3.12-slim` (backend ile tutarlı). Sistem paketleri (ocrmypdf'in resmi kurulum dokümanına göre implementasyon sırasında doğrulanacak — CLAUDE.md'nin "olmayan API/parametre üretme" kuralı gereği, aşağıdaki liste ilk tahmindir, kesin değildir):
- `tesseract-ocr`, `tesseract-ocr-tur`, `tesseract-ocr-eng` (Türkçe+İngilizce dil paketleri)
- `ghostscript`, `qpdf` (ocrmypdf'in PDF/A dönüşümü ve onarımı için gerektirdiği araçlar)
- `unpaper` **eklenmiyor** — sadece `--clean` bayrağı kullanılırsa gerekir, ADR-006'nın bayrak listesinde (`--skip-text --rotate-pages --deskew`) yok.
- WeasyPrint'in gerektirdiği `libpango`/`libgdk-pixbuf` paketleri **worker'a gerekmiyor** (o backend'in seed script'i içindir, bkz. §6).
- `uv` ile `uv sync --frozen`, backend Dockerfile'ındaki non-root user deseniyle tutarlı.

**Karar: png/jpg → PDF dönüşümü için PyMuPDF kullanılacak, `img2pdf` eklenmeyecek.** PyMuPDF zaten sayfa metni çıkarma için hard dependency; ekstra kütüphane eklememek CLAUDE.md'nin "gereksiz bağımlılık ekleme" ilkesiyle uyumlu. Not: `img2pdf` görüntüyü yeniden sıkıştırmadan gömdüğü için teorik olarak biraz daha iyi OCR kalitesi verebilir; V0 ölçeğinde (6-10 sayfalık demo belgeler) bu farkın kabul kriteri 2'yi ("DSCR" okunabilir olması) etkilemesi beklenmiyor. Sorun çıkarsa (OCR testi "DSCR" bulamazsa) `img2pdf`'e geçiş tek satırlık bir değişiklik.

### Polling döngüsü (pseudocode)
```
loop forever:
    touch_heartbeat_file()
    job = lock_next_job(engine)   # SELECT ... WHERE status='queued' ORDER BY created_at
                                    # FOR UPDATE SKIP LOCKED LIMIT 1; sonra
                                    # UPDATE status='running', attempts=attempts+1, locked_at=now()
    if job is None:
        sleep(POLL_INTERVAL_S)  # default 2s
        continue
    try:
        process(job)             # bkz. aşağı
    except Exception as exc:
        handle_failure(job, exc)
```
`process(job)`: (1) `documents` satırını oku; (2) png/jpg ise `image_to_pdf` ile tek sayfalık PDF'e çevir, değilse orijinal PDF; (3) `ocrmypdf --language tur+eng --skip-text --rotate-pages --deskew <in> <out>` çalıştır (`subprocess.run(check=True, capture_output=True)`), `documents.ingestion_status='ocr'` ara-durum güncellemesi; (4) `fitz.open(ocr_path)` ile her sayfa → `document_pages` satırı; (5) `page_count` güncelle; (6) her sayfa metnini `chunk_page_text` ile chunk'la → `document_chunks` satırları (tsv kolonları Postgres tarafından otomatik hesaplanır, `embedding` NULL); (7) `documents.ingestion_status='ready'`, `ingestion_jobs.status='done'`; tek transaction'da commit (yarım yazılmış `document_pages`/`document_chunks` bırakmamak için).

`handle_failure`: Türkçe hata mesajı üret (örn. "Belge işlenirken bir hata oluştu."), `attempts >= 3` ise `ingestion_jobs.status='failed'` + `documents.ingestion_status='failed'` + `documents.ingestion_error=<mesaj>`; değilse `status='queued'` (yeniden dene). Tam hata detayı sadece structured log'a (`repr(exc)`), kullanıcıya asla stack trace gösterilmez.

**Çökme sonrası "running" job kurtarma:** ADR-006 bunu tanımlamıyor ve kabul kriterlerinin hiçbiri buna bağlı değil. Basit bir güvenlik ağı ekleniyor: polling döngüsü, `locked_at` üzerinden N dakikadan eski `running` işleri stale sayıp `queued`'a geri alır (N=10 dakika, sabit; ayrı bir config yapmıyoruz — CLAUDE.md'nin premature configurability karşıtlığı). Bu bir SORU değil, küçük bir sağlamlık eklemesi olarak uygulanıyor; raporda not edilecek.

### Liveness
HTTP health endpoint yok (worker bir web server değil). Docker `HEALTHCHECK`, her loop turunda dokunulan bir heartbeat dosyasının mtime'ını kontrol eder (`find /tmp/worker-heartbeat -mmin -1`).

### docker-compose.yml / Makefile değişiklikleri
- `ocr-worker` servisinden `profiles: ["ocr"]` kaldırılır (varsayılan serviste çalışır).
- `ocr-worker` environment'ına `TEST_DATABASE_URL` eklenir (backend ile aynı desende) — kendi test suite'i için.
- `Makefile`'ın `up:` hedefi `ocr-worker`'ı da açıkça listeler (mevcut hedef servisleri tek tek sayıyor).
- `Makefile`'ın `test:` hedefi, backend pytest'inden sonra `docker compose run --rm -T ocr-worker sh -c 'export DATABASE_URL="$$TEST_DATABASE_URL"; pytest -q'` ile ocr-worker'ın kendi test suite'ini de çalıştırır (migration backend'in sorumluluğunda kalır, worker testleri Alembic çalıştırmaz).
- `ocr-worker/README.md` (repo kökündeki boş placeholder) gerçek `worker/` paket yapısını anlatacak şekilde güncellenir — `infra/ocr-worker/Dockerfile` ile aynı yerin iki farklı placeholder'ı olması giderilir.

---

## 3. Upload endpoint + DocumentStore

### `DocumentStore` (`backend/app/services/document_store.py`, ADR-005)
```python
class DocumentStore(Protocol):
    def store(self, document_id: UUID, filename: str, stream: BinaryIO) -> StoredFile: ...
    def get_file(self, document_id: UUID, kind: Literal["original", "ocr"]) -> Path: ...
    def get_text(self, document_id: UUID) -> str: ...
```
`LocalFileSystemStore`: `store()` → `$APP_DATA_DIR/documents/<uuid>/original.<ext>` (uzantı, client'ın verdiği dosya adından değil, doğrulanmış MIME'dan türetilir). `get_file()` → `original.*` veya `ocr.pdf`.

**`get_text()` çözümü — sidecar text dosyası.** ADR-005'in arayüzü DB'ye değil dosya sistemine dayanıyor; sayfa metni ise Postgres'te (`document_pages`). Seçim: `DocumentStore` arayüzünü Session almadan saf dosya-sistemi tabanlı tutmak için, **ocr-worker pipeline'ının 4. adımı ek olarak `$APP_DATA_DIR/documents/<uuid>/text.txt` sidecar dosyasını da yazar** (sayfa metinlerinin sayfa numarası prefix'iyle birleşimi). `get_text()` bu dosyayı okur. Alternatif (Session parametresi eklemek) arayüzü "storage-only" olmaktan çıkarırdı; sidecar dosya ADR-005'in ruhuna daha sadık.

### `POST /api/documents/upload`
Multipart form. Zorunlu alanlar (SPEC_02 §2 "Zorunlu" listesinden, bu faz için anlamlı olanlar): `file`, `title`, `document_type`, `document_date`, `counterparty`. Opsiyonel: `status` (default `draft`), `tags`. `department`/`subdepartment`/`project_id`/`confidentiality` client'tan **kabul edilmez** — PHASES.md'nin "varsayılan değerle" ifadesi gereği hep `None`/`None`/`None`/`normal`. `source` sunucu tarafında hep `web`.

Doğrulama sırası:
1. `settings.max_upload_size_mb` sınırı (413) — kabul kriterlerinde yok ama makul bir koruma, SORU değil.
2. **Magic-byte kontrolü** — elle yazılmış 3 imza kontrolü (`%PDF-`, `\x89PNG\r\n\x1a\n`, `\xFF\xD8\xFF`), `python-magic`/`libmagic1` eklenmiyor (sadece 3 format destekleniyor, ekstra sistem bağımlılığı gereksiz). Eşleşmezse `HTTPException(415, "Desteklenmeyen dosya türü.")`.
3. `DocumentStore.store()` ile orijinal dosya yazılır.
4. Tek transaction'da `documents` (`ingestion_status=uploaded`) + `ingestion_jobs` (`status=queued`) satırları birlikte oluşturulur (`document_repo.create_with_job(...)`) — biri olmadan diğeri asla commit edilmez.

**Bozuk dosya senaryosu (kabul kriteri 3a)** burada yakalanmaz — geçerli `%PDF-` header'lı ama içi bozuk bir dosya magic-byte kontrolünü geçer, hatayı worker'ın `ocrmypdf`/PyMuPDF çağrısı üretir (§2'deki `handle_failure`).

### Kullanıcı stub'ı (kullanıcı onayladı)
`backend/app/api/deps.py` (yeni): `get_current_user` dependency, her zaman seed edilmiş admin kullanıcıyı döndürür (`settings.admin_username` ile). `allowed_document_ids`'in Step-0 stub'ıyla aynı felsefe; Phase 1.1'de JWT-cookie tabanlı gerçek dependency ile değiştirilecek — bu not raporda da geçecek.

`GET /api/documents` ve `GET /api/documents/{id}/status` bu dependency'yi kullanır; `GET /api/documents`, `allowed_document_ids()` → filtre → sayfalama sırasıyla çalışır (aynı yetki yolu, ADR-004).

---

## 4. Chunking + FTS

### Chunking (`ocr-worker/worker/chunking.py`)
`chunk_page_text(text, size=800, overlap=100)`: kelime sayısı sezgisi (yeni tokenizer bağımlılığı yok). Metni `\S+` ile kelimelere ayır; `len(words) <= 800` ise tek chunk; değilse `step = 700` kayan pencere (`[0:800], [700:1500], ...`), son pencere kısa kalabilir (birleştirilmez, YAGNI). Her çağrı tek bir sayfanın metnine uygulanır → chunk'lar hiçbir zaman sayfa sınırını geçmez (ADR-008, yapısal olarak garanti).

**Kelime-sayımı vs `tiktoken` kararı:** Yeni bağımlılık eklenmiyor. Gerekçe: (a) hiçbir kabul kriteri kesin token sayısı kontrol etmiyor, (b) `tiktoken` OpenAI'ye özel bir tokenizer — Gemini'nin gerçek tokenizer'ıyla zaten eşleşmeyecek, yani "kesinlik" yanıltıcı olurdu, (c) CLAUDE.md'nin gereksiz bağımlılık/premature abstraction karşıtlığı. Türkçe'nin sondan eklemeli yapısı nedeniyle gerçek token sayısı 800 kelimelik bir chunk için muhtemelen biraz daha yüksek çıkacak — kabul edilebilir, hiçbir kriteri etkilemiyor.

### FTS kolonları
Bkz. §1 — `tsv_turkish`/`tsv_simple`, her biri GIN index'li, generated (`STORED`) kolonlar.

---

## 5. `retrieve(user, question, filters)`

`backend/app/services/retrieval.py`:
```python
def retrieve(session: Session, user: User, question: str, filters: RetrievalFilters) -> list[RetrievedChunk]:
    scope = AuthorizationScope(department=filters.department, project_id=filters.project_id)
    provider = SqlDocumentIdsProvider(session)
    allowed = allowed_document_ids(user, scope, provider)
    if not allowed:
        return []  # kabul kriteri 5'i doğrudan kanıtlar
    return document_chunk_repo.search_fts(session, allowed_ids=allowed, query=question, top_k=settings.retrieval_top_k)
```
`SqlDocumentIdsProvider` (`document_repo.py`), `DocumentIdsProvider` Protocol'ünü uygular; `documents` tablosunu `scope.department`/`scope.project_id` üzerinden **SQL seviyesinde** filtreler (sadece dolu olan alanlar için WHERE eklenir — scope sadece daraltır, ADR-004). `GET /api/documents` da aynı provider + `allowed_document_ids`'i kullanır — tek yetki yolu.

FTS sorgusu (`websearch_to_tsquery` — kullanıcı arama kutusu için Postgres'in kendi önerdiği fonksiyon, `to_tsquery`'nin aksine bozuk noktalama/dengesiz tırnakta hata fırlatmaz, `plainto_tsquery` gibi terimleri AND'ler):
```sql
SELECT c.*, GREATEST(
    ts_rank(c.tsv_turkish, websearch_to_tsquery('turkish', :q)),
    ts_rank(c.tsv_simple,  websearch_to_tsquery('simple',  :q))
  ) AS rank
FROM document_chunks c
WHERE c.document_id = ANY(:allowed_ids)
  AND (c.tsv_turkish @@ websearch_to_tsquery('turkish', :q)
       OR c.tsv_simple @@ websearch_to_tsquery('simple', :q))
ORDER BY rank DESC LIMIT :top_k;
```
`retrieval_top_k: int = 20` yeni bir `# Phase 0.2` ayarı olarak `Settings`'e eklenir.

---

## 6. `seed_data/t0/` üretimi

Yeni script `seed_data/t0/generate.py` (repo kökünde `seed_data/` bu fazda ilk kez oluşturuluyor — Phase 2.1/3.1'in tam `master/`+`generator/` sistemiyle karıştırılmıyor, bu sadece hafif bir test fixture'ı). `docker compose run --rm backend python seed_data/t0/generate.py` ile çalıştırılır — bunun için `docker-compose.yml`'deki backend servisine `./seed_data:/app/seed_data` bind mount'ı eklenmesi gerekiyor (şu an sadece `./backend:/app` mount'lu).

Backend `pyproject.toml`'a eklenir: `weasyprint`, `pymupdf` (dev/generation amaçlı). `backend/Dockerfile`'a WeasyPrint'in native kütüphaneleri eklenir (`libpango-1.0-0`, `libpangocairo-1.0-0`, `libgdk-pixbuf-2.0-0`, `libffi-dev`, `shared-mime-info`, `fonts-dejavu-core` — kesin Debian bookworm paket adları implementasyon sırasında WeasyPrint'in resmi kurulum dokümanına göre doğrulanacak).

İçerik:
- İki HTML/Jinja2 şablonu → WeasyPrint → PDF, 6-10 sayfa: **Facility Agreement** (status `executed`, DSCR **1,25x**, tenor **12 yıl**) ve **Amendment 01** (DSCR **1,20x**, tenor **14 yıl**). Her ikisi de görünür "DEMO" filigranı taşır (CSS diagonal overlay), rakamlar/isimler açıkça placeholder (CLAUDE.md'nin ledger kuralı bu fazda muaf — henüz ledger yok, Phase 2.1'de gelecek).
- `facility_agreement.pdf` ve `amendment_01.pdf` olarak kaydedilir.
- Facility Agreement'ın **görüntü/taranmış kopyası** üretilir: `generate.py`, PyMuPDF ile dijital PDF'in her sayfasını PNG'ye rasterize eder (200 DPI), sonra metinsiz yeni bir PDF'e (`page.insert_image(...)`) gömer → `facility_agreement_scanned.pdf`. Bu, worker'ın tek-görüntü→PDF akışından farklı (çok sayfalı rasterize), ayrı bir yol, kod paylaşımı beklenmiyor.
- `generate.py` upload API'sini çağırmaz (runtime altyapısına bağımlılık yaratmamak için) — sadece 3 PDF dosyasını diske yazar. Testler (`TestClient.post(...)`) bu dosyaları okuyup yükler.

---

## 7. Test planı (kabul kriteri → test)

| # | Kriter | Test | Kanıt |
|---|---|---|---|
| 1 | Dijital PDF → `ready`; sayfa sayısı eşleşir | `ocr-worker/tests/test_pipeline.py::test_digital_pdf_becomes_ready_with_matching_page_count` | `documents.ingestion_status=='ready'` ve `count(document_pages) == fitz.open(path).page_count` |
| 2 | Görüntü PDF → ocrmypdf → `ready`, "DSCR" okunabilir | `ocr-worker/tests/test_pipeline.py::test_scanned_pdf_ocr_produces_readable_text` | `"DSCR" in " ".join(page texts)` |
| 3a | Bozuk dosya → `failed` + `ingestion_error` | `ocr-worker/tests/test_pipeline.py::test_corrupt_pdf_fails_after_retries` | 3 deneme sonrası `ingestion_jobs.status=='failed'`, `attempts==3`, `documents.ingestion_error` dolu |
| 3b | `.exe` → 415 | `backend/tests/test_documents.py::test_upload_exe_rejected_with_415` | `response.status_code == 415` |
| 4 | FTS "DSCR covenant" → iki belgeden, her chunk'ta `page_number` | `backend/tests/test_retrieval.py::test_fts_finds_dscr_covenant_in_both_documents` | İki `document_id` de sonuçta, hepsinde `page_number is not None` |
| 4b | Aynı, gerçek OCR ile uçtan uca | `ocr-worker/tests/test_pipeline.py::test_fts_after_full_pipeline_both_documents` | Gerçek pipeline sonrası aynı FTS sorgusu doğrudan test DB'ye karşı |
| 5 | Boş yetki kümesi → boş sonuç | `backend/tests/test_retrieval.py::test_empty_allowed_ids_yields_empty_retrieval` | `set()` döndüren bir provider ile `retrieve(...) == []` |

Destekleyici testler: `test_chunking.py` (800-kelime sınırı, 700-kelime overlap, sayfa sınırı asla geçilmiyor), `test_attempts_increment_and_requeue_before_third_failure`, `test_documents.py` (`upload_creates_document_and_job_row`, `upload_missing_required_field_422`, `list_only_allowed_ids`, `get_status_fields`, `get_status_404_outside_allowed_set`), `test_document_repo.py` (department/project_id filtresi SQL seviyesinde), `test_image_to_pdf.py` (PNG/JPG → PDF, OCR öncesi metin katmanı yok).

`docs/reports/PHASE_0_2_REPORT.md` (implementasyon sonrası, bu planın parçası değil) şunları içerecek: kesin kütüphane sürümleri (ocrmypdf/tesseract/pymupdf/weasyprint), 5 kriterin kanıtı, "ocr-worker ayrı deploy edilebilir birim" kararının `docs/ARCHITECTURE.md`'ye yeni bir ADR olarak eklenip eklenmeyeceği.

---

## 8. PHASES.md düzeltmesi

`docs/PHASES.md` satır 4: `Model: \`O\` = Opus, \`S\` = Sonnet. RAM: aksi yazılmadıkça 6 GB VM yeter.` → talimatınız gereği **"6 GB" → "16 GB"** olarak değiştirilecek.

Not (bilginize, engelleyici değil): `SPEC_01_urun_kapsam_altyapi.md §4` VM boyutunu zaten "4 vCPU, 6→16 GB, 100 GB NVMe" (aralık) olarak veriyor, ve `CLAUDE.md` "dev VM 16 GB; temel servisler (postgres, backend, ocr-worker, caddy) 6 GB'a sığar" diyor — yani fiziksel VM zaten 16 GB, sadece 0.2'nin servisleri 6 GB'a sığıyor. Talimatınızı olduğu gibi uyguluyorum (satırı "16 GB VM yeter" yapıyorum); bu, CLAUDE.md'deki gerçek VM boyutuyla (16 GB) uyumlu hale geliyor, sadece "hangi fazın ne kadar RAM'e ihtiyacı var" ayrımını PHASES.md satır 4 artık yapmıyor — o ayrım zaten CLAUDE.md ve Phase 3.4 satırında ("embedding için VM 16 GB") ayrıca var.

---

## Uygulama Sırası (implementasyon fazında)

1. Modeller + migration (`0002`) + `app/models/__init__.py`.
2. `document_repo.py`, `SqlDocumentIdsProvider`, `document_store.py`, `retrieval.py`.
3. `POST /api/documents/upload`, `GET /api/documents`, `GET /api/documents/{id}/status`, `deps.py::get_current_user`.
4. `ocr-worker/` yeni proje (pyproject, Dockerfile, `worker/` paketi, `tests/`).
5. `docker-compose.yml`/`Makefile` güncellemeleri (profil kaldırma, TEST_DATABASE_URL, seed_data mount, test hedefi).
6. `seed_data/t0/generate.py` + WeasyPrint bağımlılıkları (backend Dockerfile).
7. Testler (tablo §7'deki tümü) + `make lint` + `make test` yeşil.
8. `docs/PHASES.md` satır 4 düzeltmesi.
9. `docs/reports/PHASE_0_2_REPORT.md`, `docs/PHASES.md` durum tablosu güncellemesi, commit + `git tag phase-0-2`.

## Kritik Dosyalar
- `backend/app/models/document.py`, `backend/alembic/versions/0002_documents_pipeline.py`
- `backend/app/services/authorization.py` (değişmeyecek, sadece wiring) → `backend/app/repositories/document_repo.py`, `backend/app/services/retrieval.py`
- `ocr-worker/worker/pipeline.py` (kriter 1-3'ün kalbi)
- `infra/docker-compose.yml`, `infra/ocr-worker/Dockerfile`
- `seed_data/t0/generate.py`
