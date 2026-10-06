# ocr-worker

Standalone ingestion pipeline worker (ADR-006): polls the Postgres `ingestion_jobs` table
and turns an uploaded PDF/PNG/JPG into OCR'd text, page rows, and search chunks.

It is a separate Python project from `backend/` — no shared code, no shared Docker image.
It never imports `backend/app`; instead it reflects the schema at startup from the live
database (`worker/db.py`), so backend's Alembic migrations remain the single source of
truth for table shape (ADR-002).

## Layout

```
worker/
  config.py        # env vars: DATABASE_URL, APP_DATA_DIR, POLL_INTERVAL_S, STALE_JOB_MINUTES
  logging_config.py # structured JSON logging (standalone, mirrors backend's shape)
  db.py             # engine + MetaData().reflect() of documents/document_pages/document_chunks/ingestion_jobs
  storage.py        # `$APP_DATA_DIR/documents/<uuid>/{original.<ext>, ocr.pdf, text.txt}` path helpers
  image_to_pdf.py   # png/jpg -> single-page PDF (PyMuPDF)
  ocr.py            # ocrmypdf subprocess wrapper
  extract.py        # per-page text extraction (PyMuPDF)
  errors.py         # failure classification: no_text / encrypted / corrupt / unknown (Not 7)
  chunking.py       # chunk_page_text(): ~800 words, 100-word overlap, page-bounded
  pipeline.py        # lock_next_job / process_one_job / handle_failure / stale-job requeue
  main.py             # poll loop entrypoint (`python -m worker.main`)
```

## Pipeline

`upload → documents(ingestion_status=uploaded) + ingestion_jobs(queued)` (written by the
backend) → worker locks the job (`SELECT ... FOR UPDATE SKIP LOCKED`) → png/jpg converted
to PDF first → `ocrmypdf --language tur+eng --skip-text --rotate-pages --deskew` →
`documents.ingestion_status=ocr` → per-page text via PyMuPDF → `document_pages` rows +
`text.txt` sidecar → `chunking.chunk_page_text()` per page → `document_chunks` rows
(`tsv_turkish`/`tsv_simple` are Postgres-generated, `embedding` stays NULL until Phase 3.4)
→ `documents.ingestion_status=ready`, `ingestion_jobs.status=done`.

On failure (Tansu Not 7, ADR-028): the exception is classified in `worker/errors.py` into a
closed code — `encrypted` (ocrmypdf exit code 8), `corrupt` (PyMuPDF cannot open the file /
format violation in the image), `no_text` (OCR finished, every page blank — previously this
became `ready` with zero chunks), `unknown` (everything else, including ocrmypdf exit code 2,
which is ambiguous). The code is written to `ingestion_jobs.error` and
`documents.ingestion_error`; the raw exception goes to the structured log only, and the
backend maps the code to the Turkish line the user sees. `unknown` is retried up to 3
attempts (`ingestion_jobs.attempts`); the other codes are deterministic and fail at once.
A `running` job whose `locked_at` is stale (default: >10 minutes, crash recovery — this
worker's own addition, not specified by ADR-006) is requeued automatically.

## Running

Via the parent repo's `docker compose` / `Makefile` — not run standalone. Local development:

```
cd ocr-worker
uv sync
DATABASE_URL=postgresql+psycopg://... APP_DATA_DIR=./tmp-data uv run python -m worker.main
```

## Tests

`tests/test_chunking.py` and `tests/test_image_to_pdf.py` are pure/local (no DB, no
ocrmypdf binary needed). `tests/test_pipeline.py` needs a live `*_test` Postgres database
and the real `ocrmypdf`/`tesseract` binaries — it runs inside the container, driven by the
parent Makefile's `test` target: `docker compose run --rm -T ocr-worker sh -c
'export DATABASE_URL="$TEST_DATABASE_URL"; pytest -q'`.
