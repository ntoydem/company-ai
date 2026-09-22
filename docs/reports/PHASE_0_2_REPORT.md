# Phase 0.2 Raporu — Belge hattı

**Tarih:** 22.09.2026  **Model:** Claude Sonnet 5  **Tag:** phase-0-2  **Commit:** (aşağıda düzeltilecek, `git rev-list -n1 phase-0-2`)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | Dijital PDF upload → `ready`; `document_pages` sayfa sayısı = PDF sayfa sayısı. | ✅ | `ocr-worker/tests/test_pipeline.py::test_digital_pdf_becomes_ready_with_matching_page_count`. Ayrıca canlı stack'te gerçek `seed_data/t0/facility_agreement.pdf` (8 sayfa) ve `amendment_01.pdf` (6 sayfa) upload edildi; `GET /api/documents/{id}/status` → `{"ingestion_status":"ready","page_count":8}` ve `...":6}` — ikisi de eşleşti. |
| 2 | Görüntü PDF upload → ocrmypdf çalışır → `ready`; metin okunabilir ("DSCR" bulunur). | ✅ | `ocr-worker/tests/test_pipeline.py::test_scanned_pdf_ocr_produces_readable_text`. Canlı stack'te `facility_agreement_scanned.pdf` (metin katmanı yok, 200 DPI JPEG rasterize) upload edildi → `ready`, `page_count=8`; `document_pages` içeriği psql ile doğrulandı — 8 sayfanın hepsinde doğru başlıklar OCR'landı (`"5. Financial Covenants ... The Borrower shall ensure ..."` vb.). |
| 3 | Bozuk dosya → `failed` + `ingestion_error` dolu; `.exe` → 415. | ✅ | `ocr-worker/tests/test_pipeline.py::test_corrupt_pdf_fails_after_three_attempts` (3 deneme, `attempts==3`, `status=='failed'`). `backend/tests/test_documents.py::test_upload_exe_rejected_with_415`. Canlı stack'te de doğrulandı: `.exe` → `415`; bozuk `%PDF-` başlıklı ama içi gerçek olmayan dosya upload edildi → ~10 sn sonra `{"ingestion_status":"failed","ingestion_error":"Belge işlenirken bir hata oluştu."}`. |
| 4 | FTS: "DSCR covenant" → iki belgeden chunk döner, her chunk'ta `page_number` dolu. | ✅ | `backend/tests/test_retrieval.py::test_fts_finds_dscr_covenant_in_both_documents`. Canlı stack'te gerçek 3 belge (Facility, Amendment 01, taranmış Facility) üzerinde doğrudan `websearch_to_tsquery('turkish'/'simple', 'DSCR covenant')` SQL'i çalıştırıldı: **her üç belgeden** eşleşen chunk döndü (kriter "iki belgeden" istiyor, üçüncüsü aynı içeriğin taranmış kopyası — fazlasıyla karşılanıyor), tüm satırlarda `page_number` dolu. |
| 5 | Retrieval `allowed_document_ids()` üzerinden geçer (test: fonksiyon boş küme döndürünce sonuç boş). | ✅ | `backend/tests/test_retrieval.py::test_empty_allowed_ids_yields_empty_retrieval` (pasif kullanıcı → `allowed_document_ids` boş küme → `retrieve()` erken `[]` döner, chunk sorgusu hiç çalışmaz). |

## 2. Yapılanlar
- **Tablolar** (`backend/alembic/versions/0002_documents_pipeline.py`, tek migration): `documents` (SPEC_02 §2'nin 3 grubu tam; `department`/`subdepartment`/`project_id`/`ai_suggestion_id` FK'siz — henüz var olmayan tablolara işaret ediyor), `document_pages`, `document_chunks` (iki ayrı **generated** tsvector kolonu — `tsv_turkish`/`tsv_simple`, her biri GIN index'li — ve nullable `pgvector` `embedding(1024)`), `ingestion_jobs`. 5 yeni Postgres enum tipi. `downgrade()` tam ayna; `tests/test_migrations.py` roundtrip'i güncellendi (head artık `0002`).
- **`DocumentStore`** (`app/services/document_store.py`, ADR-005): `LocalFileSystemStore`, `$APP_DATA_DIR/documents/<uuid>/{original.<ext>, ocr.pdf, text.txt}`. `get_text()` DB'ye değil `text.txt` sidecar'a bakıyor (ocr-worker yazıyor) — arayüz saf dosya-sistemi kalıyor.
- **Upload + listing** (`app/api/documents.py`): `POST /api/documents/upload` (multipart; elle yazılmış 3-imza magic-byte kontrolü — pdf/png/jpg; `.exe` vb. → 415; boyut sınırı → 413), `GET /api/documents`, `GET /api/documents/{id}/status`. Hepsi `allowed_document_ids()` üzerinden geçiyor (`SqlDocumentIdsProvider`, SQL seviyesinde department/project_id filtresi). Geçici `get_current_user` stub'ı (`app/api/deps.py`) — her zaman seed admin, Phase 1.1'de JWT dependency ile değişecek.
- **Retrieval** (`app/services/retrieval.py`, `app/repositories/document_chunk_repo.py`): `retrieve(session, user, question, filters)` → önce `allowed_document_ids` (boş küme → erken `[]`), sonra `websearch_to_tsquery('turkish'|'simple', ...)` ile iki kolonu `OR`'layan FTS, `ts_rank` `GREATEST`'i ile sıralı.
- **`ocr-worker`** — tamamen bağımsız Python projesi (`ocr-worker/pyproject.toml`+`uv.lock`, `backend/app`'i import etmez, şemayı `MetaData().reflect()` ile okur): poll loop (2 sn), `SELECT ... FOR UPDATE SKIP LOCKED`, `ocrmypdf --language tur+eng --skip-text --rotate-pages --deskew`, PyMuPDF sayfa metni + png/jpg→PDF dönüşümü, `chunk_page_text` (800 kelime/100 overlap, sayfa sınırı yapısal olarak korunur), 3 deneme sonrası `failed`, 10 dk'dan eski `running` işler otomatik `queued`'a alınıyor (bu fazın kendi eklediği güvenlik ağı). `infra/ocr-worker/Dockerfile` artık gerçek (ocrmypdf 17.12.1, tesseract 5.5.0 + `tur`/`eng`, ghostscript, qpdf); placeholder kaldırıldı, varsayılan serviste (`profiles` yok).
- **`seed_data/t0/`**: `generate.py` + Jinja2/WeasyPrint şablonu (`templates/document.html`, DEMO filigranı, sayfa altı "DEMO — sentetik test belgesi"). Facility Agreement EXECUTED (DSCR 1,25x, tenor 12 yıl, 8 sayfa) ve Amendment 01 (DSCR 1,20x, tenor 14 yıl, 6 sayfa); Facility'nin taranmış kopyası PyMuPDF ile rasterize + JPEG sıkıştırma (ilk denemede sıkıştırmasız ~93 MB çıktı, düzeltildi → ~1,5 MB). Üretilen PDF'ler git'e girmiyor (`seed_data/t0/*.pdf` gitignore, "generated, not committed" kuralına uyumlu).
- **Makefile/compose**: `ocr-worker` varsayılan serviste, `TEST_DATABASE_URL` var, kaynağı `./ocr-worker:/worker` bind mount (backend'deki gibi). `make test`: backend pytest → `python -m app.cli assert-pipeline-schema` (yeni CLI komutu, göç gerçekten uygulanmış mı diye sert kontrol) → ocr-worker pytest, sırayla; ara adım başarısız olursa Make zinciri durur (`test_cli.py` bu komutun başarı/başarısızlık davranışını ayrıca birim test ediyor). `make lint`/`make format` artık ocr-worker'ı da kapsıyor. `infra/.env.example`'a `MAX_UPLOAD_SIZE_MB=50` eklendi.
- `docs/PHASES.md` satır 4: "6 GB VM yeter" → "16 GB VM yeter" (talimatla, CLAUDE.md'deki gerçek VM boyutuyla artık tutarlı).

## 3. Değişen dosyalar
`git diff --stat a8dec93..HEAD` (plan commit'inden bu yana; kısaltılmış, `.claude/settings.json` ve önceki phase'e ait commit'ler hariç): 55 dosya, +3488/−24 (`uv.lock` × 2 hariç ≈ 2.600 satır).
```
Makefile, README.md, .gitignore, docs/PHASES.md
infra/: docker-compose.yml, .env.example, ocr-worker/Dockerfile
backend/: Dockerfile, pyproject.toml, uv.lock, alembic/versions/0002_documents_pipeline.py
backend/app/: cli.py, core/config.py, api/{router,deps*,documents*}.py,
              models/{__init__,document*,document_page*,document_chunk*,ingestion_job*}.py,
              repositories/{document_repo*,document_chunk_repo*}.py,
              schemas/{document*,retrieval*}.py, services/{document_store*,retrieval*}.py
backend/tests/: conftest.py, test_migrations.py, + 6 yeni test dosyası (documents, retrieval,
                document_repo, document_store, cli — hepsi *)
ocr-worker/*: pyproject.toml, uv.lock, worker/ (11 modül), tests/ (4 dosya), README.md — hepsi *
seed_data/t0/: generate.py, templates/document.html — *
```
(`*` = bu fazda yeni)

## 4. Testler
- Backend: 38/38 geçti (~9,5 sn). ocr-worker: 9/9 geçti (~5,5 sn; gerçek `ocrmypdf`/`tesseract` binary'leri ile, mock yok). Toplam 47/47, atlanan 0.
- Ara doğrulama: `assert-pipeline-schema` — göç uygulanmadan ocr-worker testlerinin çalışmayacağını kanıtlıyor (`test_cli.py::test_assert_pipeline_schema_fails_when_a_table_is_missing` bunun başarısızlık yolunu da test ediyor).
- `make lint`: backend (`ruff check` + `ruff format --check` + `mypy --strict`, 36 dosya) ve ocr-worker (`ruff check` + `ruff format --check`, 17 dosya) — ikisi de yeşil.
- Uyarılar: Starlette httpx TestClient deprecation (0.1'den beri, kütüphane kaynaklı); ocr-worker'da `SAWarning: Did not recognize type 'vector'` (beklenen — `pgvector` Python paketi bilerek eklenmedi, worker `embedding` kolonuna hiç dokunmuyor, reflect sessizce opaque tip olarak görüyor, hata değil).
- Ayrıca canlı stack (`make up`) üzerinde uçtan uca manuel doğrulama: 3 gerçek belge upload edildi (Facility, Amendment 01, taranmış Facility), hepsi `ready` oldu, FTS sorgusu gerçek verilerde çalıştı, `.exe` ve bozuk dosya senaryoları canlıda da doğrulandı (bkz. §1).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| `ocr-worker` tamamen bağımsız proje (kendi pyproject/uv.lock/Dockerfile/testler), `MetaData().reflect()` ile şema okuyor | ADR-006'nın "tek ekstra container" gerekçesi; backend image'ı ocrmypdf/tesseract ile şişmesin (ADR-004'ün belirttiği RAM bütçesi) | `make test`/`make lint` iki ayrı `docker compose run`; şema drift'i sessiz değil, `AttributeError`/`KeyError` ile patlar |
| `get_current_user` her zaman seed admin'i döndüren stub (`app/api/deps.py`) | Phase 1.1'e kadar gerçek login yok; `allowed_document_ids`'in kendi Step-0 stub felsefesiyle tutarlı | Phase 1.1'de JWT-cookie dependency ile değişecek, endpoint imzaları aynı kalır |
| `DocumentStore.get_text()` DB değil `text.txt` sidecar okuyor | ADR-005'in arayüzü saf dosya-sistemi; Session almadan `get_text()` çalışsın diye ocr-worker ek bir dosya yazıyor | Bir dosya daha diskte; arayüz sözleşmesi bozulmadı |
| MIME doğrulama: elle 3-imza kontrolü (`python-magic` yok) | Sadece pdf/png/jpg destekleniyor; `libmagic1` sistem bağımlılığı gereksiz | Format listesi büyürse `python-magic`'e geçiş gerekebilir |
| png/jpg→PDF: PyMuPDF (`img2pdf` yok) | PyMuPDF zaten hard dependency; ekstra kütüphane eklenmedi | Gerçek OCR testinde ("DSCR" bulunması) sorun çıkmadı; kalite farkı gerekirse `img2pdf`'e geçiş tek satır |
| Chunking: kelime sayımı (`tiktoken` yok) | Hiçbir kabul kriteri kesin token sayısı istemiyor; Gemini'nin gerçek tokenizer'ı zaten farklı olurdu | Türkçe metinde gerçek token sayısı "800 kelime"den biraz yüksek çıkabilir — zararsız |
| `running` iş kurtarma: `locked_at` 10 dk'dan eskiyse `queued`'a al | ADR-006 çöken worker senaryosunu tanımlamıyor; kabul kriterleri de gerektirmiyor, ama basit bir güvenlik ağı ucuz | Sabit 10 dk (config yapılmadı — erken configurability istenmiyor) |
| **`department`/`project_id` filtresi yalnızca repo-seviyesi birim testle kanıtlandı** (`test_document_repo.py`), gerçek kullanıcı-departman ilişkisiyle **değil** | `departments`/`user_departments` tabloları ve `allowed_document_ids`'in gerçek kuralları Phase 1.2'de geliyor; 0.2'de sadece düz sütunlar var | **Phase 1.2'nin kendi test suite'i, "bu kullanıcı yalnızca kendi departmanını görür" senaryosunu gerçek verilerle uçtan uca kanıtlamalı — 0.2 bunu kanıtlamıyor, yalnızca SQL filtresinin doğru çalıştığını kanıtlıyor** |
| `seed_data/t0/*.pdf` git'e girmiyor (gitignore) | Mevcut "generated demo data, built not committed" kuralıyla tutarlı (`seed_data/documents/` vb. zaten aynı kuralda) | Her klonda `docker compose run --rm backend python seed_data/t0/generate.py` gerekiyor |
| Taranmış PDF üretiminde JPEG sıkıştırma (kalite 85) | İlk deneme sıkıştırmasız pixmap gömdü, tek belge ~93 MB çıktı (413'e takıldı); gerçek bir tarayıcının çıktısına da daha yakın | — |

## 6. Açık sorular (Naci cevaplamalı)
- Yok. Plandaki 2 SORU (ocr-worker'ın bağımsız proje olması, `get_current_user` admin-stub'ı) plan onayı sırasında cevaplandı ve uygulandı.
- Not (soru değil, bkz. §5 son satırdan bir önceki): department/project_id filtresi 0.2'de yalnızca birim testle kanıtlandı; gerçek entegrasyon kanıtı Phase 1.2'nin işi.

## 7. Riskler / sonraki phase için notlar
- **WeasyPrint yalnızca `seed_data/t0/generate.py` içindir, runtime'da kullanılmaz** — ama backend image'ı tek (dev=prod), yani native kütüphaneleri (`libpango`, `libgdk-pixbuf` vb.) şu an prod image'ında da var. Phase 5.4'te (temiz kurulum) bu image boyutu/saldırı yüzeyi büyütmesinin kabul edilebilir olup olmadığı değerlendirilmeli — gerekirse WeasyPrint'i ayrı bir "generator" image'ına taşımak bir seçenek (Phase 3.1'in tam `seed_data/generator/`'ı da aynı ihtiyacı duyacak).
- `documents.department`/`project_id`/`ai_suggestion_id` FK'siz kolonlar: Phase 1.2 (`departments`/`projects`) ve Phase 3.2 (`document_metadata_suggestions`) migration'ları FK eklemeli.
- `ocr-worker`'ın kendi image'ı ilk build'de büyük (tesseract dil paketleri) — ~7 sn cache'li, ilk build daha uzun (apt indirme dahil).
- `GET /api/documents` sayfalama yok (V0 ölçeğinde gereksiz); belge sayısı arttıkça (Phase 3.1'de 15, Phase 5.1'de ~70) eklenmesi gerekebilir.
- Phase 0.3 (`/api/ask`) bu fazın `retrieve()`'ini doğrudan kullanacak; `seed_data/t0/`'daki gerçek DSCR 1,25x/1,20x zinciri Phase 0.3'ün T0 kabul kriterleri (1,20x → Amendment 01, 1,25x → EXECUTED) için hazır.

## 8. Doğruladığım üçüncü taraf davranışları
- `ocrmypdf --language tur+eng --skip-text --rotate-pages --deskew`: gerçek çalıştırıldı (subprocess), dijital PDF'de metin korunuyor, taranmış (metin katmansız) sayfada gerçek tesseract OCR çalışıp "DSCR" metnini doğru okuyor (`OCR text: 'DEMO Facility Agreement DSCR covenant 1.25x'`).
- Debian bookworm apt paket adları (`tesseract-ocr`, `tesseract-ocr-tur`, `tesseract-ocr-eng`, `ghostscript`, `qpdf`) — `packages.debian.org` üzerinden doğrulandı, hepsi kuruldu ve `tesseract --list-langs` → `eng`, `tur`, `osd` gösterdi.
- Postgres generated column: `GENERATED ALWAYS AS (to_tsvector(<config>, text)) STORED` — `sa.Computed(..., persisted=True)` ile hem model hem migration'da doğru DDL üretti; INSERT'te SQLAlchemy bu kolonları otomatik dışarıda bırakıyor (hata yok).
- `MetaData().reflect(only=[...])`: bilinmeyen bir Postgres tipi (`vector`) olan bir kolonu hata vermeden, sessizce (yalnızca `SAWarning` ile) reflect ediyor — `pgvector` Python paketi worker'a eklenmedi, ihtiyaç yok.
- PyMuPDF: `import fitz` artık `DeprecationWarning` veriyor (sürüm 1.28.2), `import pymupdf` doğru yol — hem backend hem ocr-worker bunu kullanıyor.
- `pixmap.tobytes("jpeg", ...)` ile `insert_image(..., stream=...)`: ham `pixmap=` parametresi sıkıştırmasız gömüyor (A4 @ 200 DPI × 8 sayfa ≈ 93 MB); JPEG'e çevirip `stream=` ile vermek gerçekçi boyut veriyor (~1,5 MB).
- `docker compose run` bir servisin kaynak dizini bind-mount edilmemişse, container içinde `ruff format`/`--fix` çalıştırmak değişiklikleri **host'a yazmaz** (image'a build-time'da `COPY` edilmiş dosyalar üzerinde çalışır) — ocr-worker'a `./ocr-worker:/worker` mount'u eklenerek backend'deki dev-döngüsüyle tutarlı hale getirildi.

## 9. Kaynak kullanımı
- `docker stats` (boşta, `make up` sonrası): backend ≈ 64 MiB, ocr-worker ≈ 58 MiB, postgres ≈ 32 MiB; toplam ≈ 154 MiB. VM: 16 GB (bkz. PHASES.md satır 4 düzeltmesi).
- LLM çağrısı yok (0 token) — Phase 0.3'te başlıyor.
