# ARCHITECTURE — Architecture Decision Records

Short, numbered decisions with rationale. Not a design narrative. Add a new ADR when a new
architectural decision is taken; supersede (do not silently edit) an ADR when a decision changes.
Status values: `accepted` | `superseded by ADR-xxx`. Phase column = when the decision becomes code.

## ADR-001 — Topology: one VM, one Compose project
**Status:** accepted · **Phase:** 0.1
- One Ubuntu 24.04 VM on Proxmox, one `docker compose` project (`infra/docker-compose.yml`), same file for dev and prod; only `.env` differs.
- Default services: `postgres` (pgvector/pgvector:pg16) and `backend`. `ocr-worker` joins the default set in Phase 0.2.
- Profiles: `web` → `caddy` (Phase 3.3); `full` → `embed` bge-m3 (Phase 3.4). `make up` never starts profiled services.
- Persistent data lives under `DATA_ROOT` as bind mounts (`postgres/ documents/ excel/ app-data/ backups/`); containers are disposable.
- Host exposure: only ports listed in `.env`. Postgres, ocr-worker and embed are reachable solely on the compose network.
- Why: minimal moving parts, restorable from `git clone` + `.env` + `make up`; no Kubernetes, no external queue.

## ADR-002 — Backend layering and data access
**Status:** accepted · **Phase:** 0.1
- Python 3.12, FastAPI, Pydantic v2. Layers: `app/api` (HTTP only) → `app/services` (rules) → `app/repositories` (queries) → `app/models` (ORM). Schemas in `app/schemas`.
- **Synchronous** SQLAlchemy 2.x with psycopg 3. Rationale: simpler code and tests, Alembic and DuckDB are sync, request volume is LAN-scale; FastAPI runs sync endpoints in a threadpool.
- One Alembic migration chain (`backend/alembic/versions`), applied by the container entrypoint at startup (`alembic upgrade head`).
- Settings via `pydantic-settings` from environment variables only; no config files in code.
- Dependencies pinned with `uv.lock`; everything (tests, lint) runs inside the backend image, the host needs only Docker + make.

## ADR-003 — Authentication
**Status:** accepted · **Phase:** 0.1 (users table, admin seed) · 1.1 (login endpoints)
- JWT in an httpOnly + SameSite cookie, 8-hour lifetime, no refresh token; logout = cookie clear.
- Passwords hashed with Argon2id (`argon2-cffi`); plaintext never stored or logged.
- `users` carries `auth_provider` (`local` only in V0) and `external_id` so SSO/Entra ID can be added later without schema change. No SSO in V0.
- Initial admin is created idempotently at startup from `ADMIN_USERNAME` / `ADMIN_PASSWORD`; an existing user is never modified by the seed.
- Login rate limiting (Phase 1.1) protects the single password endpoint.
- **Phase 1.1 concretization:** JWT via `PyJWT` (HS256, `JWT_SECRET`), cookie name `access_token` (`path=/`, `samesite=lax`, `secure=false` in V0 plain-HTTP LAN, ADR-015). The token's `sub` (user id) and `role` claim are non-authoritative — `get_current_user` re-fetches the `User` row on every request and trusts only the DB's `role`/`is_active`, since there is no refresh/revocation mechanism. Wrong username, wrong password and a disabled account return an identical 401 (no username enumeration). Login rate limit: in-memory, 5 failed attempts/15 min per username and 20/15 min per client IP (no Redis in this stack; single `uvicorn` process makes this sufficient for V0; resets on restart). Demo users `yonetim`/`finans`/`hukuk`/`enerji` are seeded the same idempotent way as admin, sharing one `DEMO_USER_PASSWORD` — they carry only a `role` until Phase 1.2 adds department membership.
- **Phase 3.3 concretization:** the UI never reads the JWT (httpOnly); its only notion of "logged in" is `GET /api/auth/me` (200 → user, 401 → login screen), and any later 401 drops the session client-side. `/me` (and `/login`) now also return `department_slugs` — the user's direct memberships — so the home screen can hide cards of departments the employee cannot see; this is convenience only, ADR-004's server-side gate is unchanged.

## ADR-004 — Authorization model and the `allowed_document_ids` contract
**Status:** accepted · **Phase:** 0.1 (contract) · 1.2 (rules)
- Exactly one gate: `app/services/authorization.py::allowed_document_ids(user, scope, document_ids_provider) -> set[UUID]`. The signature is frozen.
- Semantics: returns the ids `user` may see, restricted by `scope` (department / project). Scope only narrows. Result ⊆ provider output. Inactive user → ∅. Empty provider → ∅.
- Ordering rule for every question: AUTHORIZATION → allowed ids → retrieval → LLM. Listing, download, retrieval and `/api/ask` all start from this set; content outside it never reaches a prompt.
- Step 0: single admin, stub returns every existing document. Step 1.2: `employee` = `normal` docs of own departments; `management` = all departments, all confidentiality; `admin` = everything. Document permission derives from department, not project.
- Enforced server-side only; UI hiding is convenience, not security. Any code path bypassing the gate is a bug; tests assert "empty set → empty result".
- **Phase 1.2 implementation:** `DocumentIdsProvider` gained one method, `list_document_ids_for_departments(department_slugs, confidentiality_levels)` — `AuthorizationScope` itself did not change. `documents.department` stays a denormalized slug string with no FK (existing rows/tests predate the `departments` table); a misspelled or unknown slug fails safe — the document becomes invisible to everyone but admin, never exposed. `documents.project_id` gained an FK to `projects.id`. `departments`/`projects` are seed-only in V0 (no department CRUD); project CRUD is admin-only (`require_admin`, `app/api/deps.py`).

## ADR-005 — `DocumentStore` interface
**Status:** accepted · **Phase:** 0.2
- Files are stored behind a small interface: `store(document_id, filename, stream) -> StoredFile`, `get_file(document_id, kind: original | ocr) -> Path`, `get_text(document_id) -> str`.
- Single V0 implementation `LocalFileSystemStore`: `$APP_DATA_DIR/documents/<uuid>/original.<ext>` and `ocr.pdf`. Metadata has exactly one source of truth: Postgres. Filenames are never a source of metadata.
- No Paperless in V0. Paperless (or SharePoint/OneDrive later) can be placed behind `DocumentStore` in Step 3 if needed; this door is deliberately left open, but nothing in V0 depends on it.
- Rationale: swapping storage must not touch services, authorization or retrieval.

## ADR-006 — Ingestion pipeline and the `ingestion_jobs` queue
**Status:** accepted · **Phase:** 0.2 (pipeline) · 3.2 (metadata suggestion)
- Pipeline: upload → `documents(ingestion_status=uploaded)` + job row → `ocr-worker` (ocrmypdf `--language tur+eng --skip-text --rotate-pages --deskew`; png/jpg converted to PDF first) → page text with PyMuPDF → `document_pages` → chunking → `document_chunks` (+FTS, +vector when enabled) → `ready`.
- The queue is a Postgres table: `ingestion_jobs(status queued|running|done|failed, attempts, error, locked_at, ...)`; the worker polls with `SELECT … FOR UPDATE SKIP LOCKED`, max 3 attempts, then `failed` with a Turkish reason on the document.
- No Redis/Valkey/Celery: one extra container and one table are enough at this scale, and the queue is backed up with the database.
- LLM metadata suggestion (Phase 3.2) runs after `ready`; its failure never fails the upload.
- **Phase 4.2:** the Excel family (`xlsx`/`xlsm`/`csv`) bypasses this pipeline entirely — no job row, no OCR, no pages/chunks; the upload marks the document `ready` (sheet count as `page_count`). `ocr-worker` still defends itself: an Excel job, should one ever appear, is finished as `done` without calling ocrmypdf.
- **Phase 3.2 concretization:** `ingestion_jobs` stays OCR-only (no `job_type` column, YAGNI) — the metadata-suggestion queue is a plain SQL predicate (`ingestion_status=ready AND ai_suggestion_id IS NULL`), not a second job table. Two entry points share `app/services/metadata_suggestion.py::suggest_metadata()`: an admin-only `POST /api/documents/{id}/suggest-metadata` (idempotent while `pending`/`applied`; explicit retry after `failed`/`rejected`) and an in-process `asyncio` background scan (`app/main.py` lifespan, `metadata_suggestion_poll_interval_s`/`_batch_size`) that never starts against a `_test` database, so `make test` never calls the LLM through this path. `document_metadata_suggestions.document_id` is unique (one row per document, overwritten on retry — no suggestion history in V0). `documents.ai_suggestion_id` deliberately carries **no FK** to it: a real one would cycle with that table's own FK back to `documents.id` (SQLAlchemy cannot topologically sort the pair); it is kept in sync by the service only, used purely as an existence flag.

## ADR-007 — Retrieval: full-text + metadata first, embeddings behind a flag
**Status:** accepted · **Phase:** 0.2 (FTS) · 3.4 (hybrid)
- Default retrieval is Postgres FTS (`tsvector` with `turkish` and `simple` configurations) plus metadata filters (department, project, document_type, dates, status).
- `EMBEDDINGS_ENABLED=false` is the reference configuration: the whole system and test suite must pass without the `embed` service.
- With the flag on, bge-m3 vectors in `document_chunks.embedding` (pgvector) are combined with FTS (hybrid); the `embed` container runs only under `--profile full` (16 GB VM).
- Retrieval always receives the allowed-id set first (ADR-004) and filters at the SQL level, never after the fact.
- **Phase 3.4 concretization:** `retrieve()` fuses FTS and vector results with Reciprocal Rank Fusion (k=60; rank position only, never raw scores — `ts_rank_cd` and cosine similarity live on incomparable scales). A dead/slow `embed` service degrades retrieval to FTS-only (`EmbeddingError` caught, warning logged) rather than failing `/api/ask` — live-verified by stopping the `embed` container mid-session and confirming a 200 response (SPEC_06 §8). A background loop (`app/main.py`, same pattern as Phase 3.2's metadata scan) backfills `document_chunks.embedding` in batches; `ocr-worker` stays unaware of `embed` entirely. No pgvector ANN index (ivfflat/hnsw) yet — at V0's chunk count (dozens–low hundreds) a plain `<=>` scan is fast enough; add one if Phase 5.1's dataset makes it necessary. **Measured RAM was ~10.5 GB for the `embed` container alone (`docker stats`), well above the ~3-4 GB estimated from bge-m3's published weight size — TEI's CPU runtime overhead (batch buffers, ONNX runtime, tokenization workers) is the difference.** Still fits the 16 GB dev VM (`free -h` showed ~4 GB available with everything else running) but leaves less headroom than planned; `docs/reports/PHASE_3_4_REPORT.md` has the full numbers.

- **Phase 3.2b concretization (hybrid diagnosis):** with both legs capped at `top_k`, RRF (k=60) can never rank a chunk found by one leg only above a chunk found by both (`1/61 < 2/(60+top_k)` for any `top_k < 62`), so a page only the vector leg finds was cut — that, not embed quality or latency (measured 40–190 ms, no fallback), is why Phase 4.1's embedding probe showed no gain. `retrieve()` now fetches each leg at `2×top_k` and cuts after fusion. On the 43-question golden set hybrid retrieval adds no measurable page recall over glossary-expanded FTS (both 100% on the 20 measurable questions), so `EMBEDDINGS_ENABLED=false` stays the reference configuration; the `retrieval explain` log line (per-leg timings and page lists) is the tool for revisiting this at Phase 5.1 scale.

## ADR-008 — Page-level sourcing
**Status:** accepted · **Phase:** 0.2
- `document_pages(document_id, page_number, text)` keeps page text; chunks never cross a page boundary and `document_chunks.page_number` is NOT NULL.
- Chunk size ≈ 800 tokens with 100 overlap inside a page.
- Every document-based answer cites document title, **page**, document date, version and project; the audit log stores the same citation.
- Rationale: auditability (rule 4) requires that a human can open the PDF at the cited page.

## ADR-009 — LLM client
**Status:** accepted · **Phase:** 0.3
- `LLMClient` protocol with `OpenAICompatibleClient` (openai SDK + `base_url`; default Gemini at `https://generativelanguage.googleapis.com/v1beta/openai/`) and optional `AnthropicClient`.
- Two model settings: `LLM_MODEL_CLASSIFY` (cheap, metadata suggestion / routing) and `LLM_MODEL_ANSWER`. Defaults from the official model list at the time of writing: `gemini-3.5-flash-lite`, `gemini-3.8-flash`.
- Thinking/reasoning kept low (`LLM_REASONING_EFFORT`, default `low`), output tokens capped; token counts in/out logged per call (`llm call` record) and, from Phase 3.4, written to the audit log. Gemini's OpenAI endpoint reports no separate reasoning-token count (`tokens_reasoning` stays null).
- The LLM receives only allowed chunks (ADR-004), never does arithmetic (ADR-011), and cannot execute code.
- No LangChain/LlamaIndex: prompts and retrieval are explicit and testable.
- Phase 0.3 decision: `AnthropicClient` is deferred; `LLM_PROVIDER=anthropic` raises a clear "not configured" error until the Phase 4.3 model decision point. Vendor errors are mapped to an `LLMError` hierarchy; the API answers 503 with a fixed Turkish message and never exposes provider detail.
- **Phase 3.2 concretization:** `LLMRequest` gained an optional `response_format: "text" | "json_object"` (default `"text"`, unchanged for `/api/ask`); `OpenAICompatibleClient` passes it through as the OpenAI-typed `ResponseFormatJSONObject` param, omitted (`openai.Omit()`) rather than sent for the default case. Metadata classification (`metadata_suggestion.py`) is the only caller that sets `"json_object"`.

## ADR-010 — Question router
**Status:** accepted · **Phase:** 4.3 (simple version in 0.3 answers DOCUMENT only)
- Query types: `DOCUMENT_QUERY | DATA_QUERY | MIXED_QUERY | GENERAL_QUERY`.
- MIXED = two sub-queries (document + Excel) merged without interpretation. Ambiguous "current DSCR?" → covenant (document) and actual (Excel), two source types.
- GENERAL uses no company data and says so in the answer.
- The router is a service with a fixed interface so future "Email AI" can be added without touching callers (SPEC_01 §8) — but only the two V0 branches exist.
- **Phase 4.3 concretization:** `app/services/router.py` — `Router` Protocol (`route(question) -> RoutedQuestion{query_type, document_question, data_question}`) with one implementation, `LLMRouter`: a single `LLM_MODEL_CLASSIFY` call, `response_format=json_object`, few-shot with the SPEC_04 §7 examples plus the explicit rule "ambiguous contractual-vs-realised value → MIXED with two self-contained sub-questions". DOCUMENT/DATA always run the *original* question (retrieval/planning unchanged by the router); only MIXED uses the rewritten sub-questions. Every failure (LLM error, malformed JSON, unknown type) degrades to `DOCUMENT_QUERY` — the safe direction: a wrongly-GENERAL answer would drop company sources. `app/services/ask_router.py::answer_routed_question` runs the pipelines **unchanged** (`ask.answer_question`, `excel_ask.answer_data_question`, both with `write_audit=False`) and merges MIXED deterministically under two fixed Turkish headings (`Belgelere göre:` / `Excel verisine göre:`) — no third LLM call, both branches always run, a branch that found nothing keeps its fixed "not found" text so the model never silently picks a side. GENERAL (`app/services/general_answer.py`): no `allowed_document_ids`, no retrieval, no workbook; the fixed notice is prepended by code; a reply that names a project (from the `projects` table) or contains a money amount is dropped for a fixed text (leak guard). `AskResponse` grew backwards-compatibly (`query_type`, `excel_sources`, type-specific `notice`); `sources` keeps meaning document pages. `POST /api/excel/ask` stays as the router-less DATA endpoint (SORU 5). **DATA miss falls through to documents:** when the Excel branch of a `DATA_QUERY` answers nothing (no visible workbook, plan `none`, unknown period), the original question runs through the document pipeline and the row/response carry `DOCUMENT_QUERY` — the first eval run showed the router tagging contract-stated amounts ("yerli banka kredisi ne kadar?") as DATA and dead-ending in "Excel'de bulamadım"; with the fall-through a mis-routed question costs one extra call and behaves exactly as before the router.

## ADR-011 — Excel engine boundaries
**Status:** accepted · **Phase:** 4.2
- Inspection with openpyxl (`data_only=True` cached values, formulas, named ranges, hidden sheets); calculation with DuckDB (in-memory, read-only, `enable_external_access=false`, 10 s timeout, row limit); Polars for transformations.
- The LLM decides *what* to compute: either parameters of predefined functions (`dscr`, `outstanding_debt`, `budget_variance`, `capacity_factor`, `production`) or a single whitelisted `SELECT` (no `;`, known tables only, `LIMIT` added, `COPY/ATTACH/INSTALL/LOAD/PRAGMA` rejected). The final number never comes from the model.
- `.xlsm` macros are never executed. No LLM-written Python is executed.
- `CalculationEngine` interface with one implementation, `CachedValueEngine`; missing cached values produce a user message, not a server-side recalculation (LibreOffice recalc is a build step for demo files only).
- Every Excel answer cites `file + sheet + range`.
- **Phase 4.2 concretization:** `backend/app/excel/` — `inspect.py` (openpyxl, two loads: `data_only=True` values / formulas; macro presence read from the zip member `xl/vbaProject.bin`, never from the extension, never loaded), `sql_guard.py` (pure whitelist: no `;`/comments, `SELECT`/`WITH` only, forbidden keyword and file-function token list, `FROM/JOIN` names must be known tables, `LIMIT` capped at `EXCEL_ROW_LIMIT`), `calc.py` (`CalculationEngine` Protocol + `CachedValueEngine`: visible sheets → Polars → DuckDB tables `<file>__<sheet>` with an `_row` column carrying the Excel row number, `enable_external_access=false`, `conn.interrupt()` after `EXCEL_QUERY_TIMEOUT_S`; a workbook with uncached formula cells raises `NeedsRecalculationError` → user message, no server-side recalc), `functions.py` (`dscr`, `outstanding_debt`, `budget_variance`, `capacity_factor`, `production` read named ranges — the contract with `generate_excel.py` — and cite the cell/range). Two LLM calls in `services/excel_ask.py`: a planning call (`LLM_MODEL_CLASSIFY`, JSON: function+params | one SELECT | none) over a catalogue of the workbooks the user may see (ADR-004 first), and a phrasing call (`LLM_MODEL_ANSWER`); if the phrased answer does not contain the engine's number verbatim, a template answer is returned — the final figure never comes from the model, measurably. Excel-family uploads (`xlsx`/`xlsm`/`csv`, sniffed from bytes) are `ready` at once, get no OCR job and no chunks (SPEC_04 §1); `documents.has_macros`/`file_name` (migration 0008). Demo workbooks: `seed_data/generator/generate_excel.py` (formulas only) → `recalc.sh` in the `libreoffice` tools container (LibreOffice Calc headless `--convert-to xlsx` writes cached values; ~3 s for four files, named ranges and the hidden `_meta` sheet survive the round-trip) → `validate_excel.py` W1-W5 in `make lint`; the four recalculated files are committed (`seed_data/excel/`, SORU 2) so the prod clone never needs LibreOffice. `/api/ask` stays DOCUMENT-only; `POST /api/excel/ask` is the DATA entry point until the router (Phase 4.3).

## ADR-012 — Temporal model: old ≠ wrong
**Status:** accepted · **Phase:** 3.2 (full) · 0.3 (DSCR chain)
- Fields: `document_date`, `effective_date`, `expiration_date`, `version`, `revision`, `supersedes_document_id`, `superseded_by_document_id`, `related_document_ids`, `status`.
- "Current" = last link of the `supersedes` chain effective on `DEMO_TODAY`; "initial/historical" = the specific earlier document. Both are correct answers to different questions; answers name the change ("changed by Amendment 01 from X").
- `DEMO_TODAY` (env, ISO date) replaces the wall clock for every "current / which operating year" computation.
- Timestamps stored as `timestamptz` (UTC); displayed in `Europe/Istanbul`, `DD.MM.YYYY`.
- **Phase 3.2 concretization:** `document_repo.mark_superseded()` now also transitions `older.status` to `superseded` (from `draft`/`executed`/`amended`; left untouched if already `superseded` or `active` — `active` is an operational, not lifecycle, state). The chain-evaluation code itself (`version_chain.py`/`answer_prompt.py`) needed no change — it was already general, not DSCR-specific, since Phase 0.3; this phase's own `test_current_tenor_vs_initial_facility_tenor_differ` (a non-DSCR field on the same real Facility chain) is the first automated proof of that generality. Licence → Licence Amendment 01 cannot exercise this mechanism at all: that pair is deliberately linked via `related_document_ids`, not `supersedes` (Phase 3.1), so it never carries a GÜNCEL/İLK HALKA distinction — a real gap between SPEC_02 §11's illustrative example and Phase 3.1's own document-relationship modelling, left for Phase 4.1/5.1 to reconcile (either re-model the pair as a chain, or drop the illustrative example).

## ADR-013 — Synthetic truth model
**Status:** accepted · **Phase:** 2.1, 3.1
- Every demo number, date and name comes from `seed_data/master/*.yaml` (truth ledger); each value tagged `USER_FACT` or `AI_ASSUMPTION`; nothing is approved until Naci marks it `USER_FACT`.
- `validate_ledger.py` checks coarse chronology, finance consistency, İzmir post-licence fields empty, currencies, name whitelist. Documents and workbooks are generated only after validation passes.
- Two AI modes are strictly separated: production Company AI never assumes; the generator (`seed_data/generator/`) fills gaps deliberately and is never imported by the backend.
- Demo entities are fictional and generic (ABC Enerji A.Ş., PQR Bank …); every document carries a DEMO/FICTIONAL banner.
- **Phase 2.1 concretization:** the ledger schema is a set of Pydantic v2 models (`seed_data/generator/ledger_schema.py`, `extra="forbid"`); every fact is a `{value, tag}` / `Money{value, currency, tag}` / `Event{date, doc, tag}` mapping or a tagged list record, identity keys stay untagged. `documents[].key_facts` and `questions.json`'s `expected_answer` hold **ledger paths** (`ledger:ankara_res.project…`), never repeated values. Departments are the DB slugs (`finans`, not `finance`). Operating year is anniversary-based. `questions.json` lives at `seed_data/evaluation/`. `make validate-ledger` (also part of `make lint`) must report 0 errors; Phase 3.1 additionally requires a separate "ledger onayı" commit in which Naci flips reviewed values to `USER_FACT`.
- **Phase 3.1 concretization:** the LLM never sees a fact. Prose is generated **once** (`make prose`) with only `[[token]]` placeholders — the LLM is told the available tokens and forbidden from writing any digit/date/currency/name itself; `generate_documents.py` (deterministic, no LLM) substitutes tokens from `facts.py` and renders via Jinja2/WeasyPrint. Prose is committed to git (`seed_data/generator/prose/*.yaml`, `tag: AI_ASSUMPTION`) so `make seed` on a prod clone needs no LLM/network call. `validate_documents.py` enforces this structurally (no 3+ digit run, no currency token, no un-whitelisted name in prose; banner/isolation/fact-presence checks on the rendered PDFs). `documents.external_ref` (migration `0004`) is the ledger-id seed idempotency key; `app/cli.py seed-demo-documents` reads only `seed_data/documents/manifest.json` (JSON), never the generator's Python.

## ADR-014 — "No opinion" rule (V0)
**Status:** accepted · **Phase:** 0.3
- The system finds, reads and relays. It produces no opinion, projection, recommendation or speculation.
- Fixed strings: no source → "Mevcut şirket kaynaklarında bu soruyu güvenilir şekilde cevaplamak için yeterli bilgi bulamadım."; "why?" without a stated reason in the documents → "belgelerde sebep belirtilmemiş".
- The answer UI states briefly that answers contain no interpretation.
- Rationale: trust is built on verifiable relay before any reasoning feature is considered.
- **Phase 3.2 concretization:** live testing surfaced a real ambiguity between this rule and rule 2 ("kaynaklar yetmiyorsa" → the no-source sentence) — a model asked "neden değiştirildi?" about a fact that *is* in the sources (only the cause isn't) sometimes fell back to the generic no-source sentence instead of "belgelerde sebep belirtilmemiş". `answer_prompt.py`'s rule 6 now explicitly says which sentence wins when the topic itself is present but its cause isn't; `backend/tests/live/test_ledger_live.py::test_why_question_without_stated_reason_returns_fixed_text` is the regression test (`make test-llm`).

## ADR-015 — Security boundaries
**Status:** accepted · **Phase:** 0.1 onward
- Authorization only server-side (ADR-004). Secrets only in `.env` (never in code, logs, fixtures); `.env` is git-ignored; `.env.example` holds obviously fake values.
- Upload: extension + MIME validation (`pdf xlsx xlsm csv png jpg`), size limit, stored under a server-generated UUID path. `.xlsm` macros never run.
- No execution of model-generated code; SQL whitelist (ADR-011). LLM prompts contain only allowed content.
- Users never see stack traces: generic Turkish message + `request_id`; details go to the JSON log (ADR-017).
- Network: LAN only, plain HTTP on Caddy `:8080` in V0; Postgres/ocr/embed ports closed to the host; CORS limited to the Caddy origin; login rate limit.

## ADR-016 — Audit log is not corporate memory
**Status:** accepted · **Phase:** 3.4
- `audit_log` records who asked what, when, with which scope, which documents/Excel ranges were used, the answer, model and token counts, `request_id`, errors.
- Visible only to admins; retained 90 days with a daily cleanup; never used by retrieval or prompts. One user's questions never influence another user's answers.
- Passwords, API keys and JWTs are never written to it.
- **Phase 3.4 concretization:** one row is written per `/api/ask` call from `app/services/ask.py::answer_question()` itself (not the API layer) — the zero-chunk "no answer" path, the LLM-answered path and the LLM-error path (`error` set, response still the existing 503, unchanged) all write a row; a broken audit write never breaks the answer already computed (same "never breaks the caller" pattern as Phase 3.2's metadata suggestion). Retention/cleanup: a background loop (6 h interval — a cheap idempotent `DELETE ... WHERE timestamp < cutoff` comfortably satisfies "daily") plus `python -m app.cli cleanup-audit-log` for a host cron or one-off run. Admin-only read API: `GET /api/audit-log` (filtered list, no `answer`/`sources`) and `GET /api/audit-log/{id}` (full record) — the UI on top is Phase 5.2. `cost_estimate` stays `NULL` in V0: no invented per-model pricing table.
- **Phase 4.2:** `POST /api/excel/ask` writes its own row (`query_type=DATA_QUERY`, `excel_files_used`, `sources` = file/sheet/range cards, `documents_retrieved` = the cited workbooks); a rejected SQL plan is logged with `error="sql rejected: …"`.
- **Phase 4.3:** one `/api/ask` call = one row, whatever the type (SORU 2): the single write path is `app/services/audit_writer.py::write_audit_row`, called by the router orchestrator (the sub-pipelines run with `write_audit=False`) or by each pipeline when it is the entry point itself. `query_type` is now the real router decision; `sources` JSONB cards carry `kind: "document" | "excel"` so a MIXED row's two source kinds stay distinguishable; `documents_retrieved` = retrieved document ids + cited workbook ids; `chunks_retrieved` from the document branch; `tokens_*` include the router call. An LLM failure inside any branch writes the row with `error` (and the router's type) before the 503 propagates. GENERAL rows have empty `documents_retrieved`/`sources`/`excel_files_used` — the measurable form of "no company data used".
- **Phase 3.2b concretization:** `chunks_retrieved` (JSONB, migration `0007`) records the `(document_id, page_number, rank)` of every chunk that reached the prompt — `documents_retrieved` alone could not tell a retrieval miss (right document, wrong page) from a model refusal, which is exactly the distinction Phase 4.1's failures needed. Still admin-only, still never read by retrieval or prompts.

## ADR-017 — Structured logging, request id, error handling
**Status:** accepted · **Phase:** 0.1
- Standard-library `logging` with a JSON formatter to stdout (no extra library): `ts` (UTC ISO), `level`, `logger`, `message`, `request_id`, plus caller `extra` fields.
- `X-Request-ID` middleware: accepts a well-formed client id or generates one, stores it in a context variable, returns it in the response header and in every error body.
- Keys containing `password`, `api_key`, `secret`, `authorization`, `cookie` are masked in log output regardless of caller; `token` is masked as a whole key segment (`llm_token`, `access_token`) so that LLM usage counters (`tokens_in`, `tokens_out`) stay readable (Phase 0.3).
- Unhandled exceptions → HTTP 500 with a fixed Turkish message; the traceback is logged once with path, method and request id.

## ADR-018 — Configuration and environments
**Status:** accepted · **Phase:** 0.1
- One `.env` at the repo root, template `infra/.env.example` documenting every variable, including those of later phases.
- Host side: `DATA_ROOT` (dev `./data`, prod `/srv/company-ai`) and all host ports (`BACKEND_PORT`, `CADDY_PORT`) are consumed only by compose. Container side: `APP_DATA_DIR=/data` with `documents/ excel/ app-data/` sub-mounts.
- The Makefile calls `docker compose --project-directory . -f infra/docker-compose.yml --env-file .env`, so relative paths resolve from the repo root on any host. No host-specific path exists in the repo.
- Backend port 8000 is exposed on the host until Caddy arrives (Phase 3.3); afterwards it is closed to the compose network.
- **Phase 3.3 concretization:** done — `backend.ports` removed from compose; `caddy` is part of the default `make up` (no profile) and is the only host-facing service (`CADDY_PORT`). The React bundle is built in a multi-stage `infra/caddy/Dockerfile` (node → `caddy:2-alpine`, `/srv`) and served with an SPA fallback (`try_files … /index.html`); `/api/*`, `/health` and `/ask` are reverse-proxied. The app uses relative URLs only; in `make dev-frontend` Vite's dev proxy plays Caddy's role, so the backend needs no CORS configuration in either mode. A `frontend` tooling service (`profiles: ["tools"]`) exists solely for `make lint` / `make dev-frontend`.

## ADR-019 — Testing and quality gates
**Status:** accepted · **Phase:** 0.1
- pytest runs inside the backend container against a dedicated `company_ai_test` database (created by the Postgres init script); a session fixture applies `alembic upgrade head` and refuses any database whose name does not end in `_test`.
- Every endpoint has at least one integration test; every service has unit tests with fakes (e.g. `DocumentIdsProvider`).
- `ruff` (lint + format) and `mypy --strict` on `app/` must be green before a phase closes; frontend adds `eslint` + `tsc` in Phase 3.3.
- **Phase 3.3 concretization:** `make lint` runs `eslint .` + `tsc --noEmit` (app and vite configs) in the `frontend` tooling container. No Playwright/UI test suite (CLAUDE.md: out of V0 scope) — UI acceptance criteria are verified by hand in a browser and documented with screenshots in the phase report; endpoint-level guarantees behind the UI (403/404, error bodies, `/me` memberships) stay covered by the backend's pytest suite.
- Phase closing ritual (CLAUDE.md): all tests green → docs/README updated → migration present → `docs/reports/PHASE_x_y_REPORT.md` → `docs/PHASES.md` status → commit + tag `phase-x-y`.

## ADR-020 — Search query construction: OR semantics for natural-language questions
**Status:** accepted · **Phase:** 0.3
- `websearch_to_tsquery` ANDs terms; a Turkish question ("Ankara RES'in güncel minimum DSCR covenant'ı nedir?") against English contracts therefore matched **zero** chunks (measured on the live DB before Phase 0.3).
- `app/services/search_query.py::build_search_query()` strips apostrophe suffixes (`RES'in → RES`), drops a small Turkish question-word/particle stoplist and duplicates, and joins the rest with `OR`. Lower-casing and stemming stay in Postgres (`turkish` / `simple`), consistent with indexing.
- Ranking uses `ts_rank_cd` (cover density): chunks where several distinct query terms occur together outrank cover pages that merely list the words. `search_fts()` and `retrieve()` keep their signatures; the repository never sees question text, only the built query.
- Consequence (deliberate): a question about a project with no documents (İzmir RES) still retrieves chunks of another project through shared terms ("RES"). Project isolation is then the LLM's rule-2/3 discipline (ADR-021) until the structural `project_id` filter arrives with the `projects` table (Phase 1.2). Phase 4.1's `isolation` eval category must cover exactly this scenario.
- Embeddings (ADR-007, Phase 3.4) will add semantic recall; this ADR governs the FTS leg only.
- **Phase 3.2b concretization:** Phase 4.1's eval showed the OR query's real failure mode is *cross-language*: a Turkish question ("finansman", "kredi") shares no lexeme with the English page that states the figure, so that page ties with ~27 others at the lowest matching rank and `LIMIT top_k` picked the winners by heap order — the same question could reach the LLM with a different page set on each call. Three fixes, all on the FTS leg: (1) `app/services/search_glossary.py` — a curated energy-project-finance glossary (Turkish stem → English document terms, and the reverse) ORed into the query by `build_search_query()`; not a list of the golden questions' words; (2) a deterministic tie-break `(rank DESC, document_id, chunk_index)` in `search_fts`/`search_vector`; (3) `retrieval_top_k` 20 → 40 (the corpus is one page per chunk, ~450 chars, so 40 chunks ≈ 10k tokens). Measured with the LLM-free `run_eval.py --retrieval-only` probe: page recall@20 18/20 → 20/20 with (1)+(2) alone.

## ADR-021 — Answer pipeline: deterministic temporal evaluation, cited sources, no-LLM fallback
**Status:** accepted · **Phase:** 0.3
- Order per question (SPEC_02 §9): `allowed_document_ids` → `retrieve()` → load the `supersedes` chains of the retrieved documents (restricted to allowed ids at every hop) → `evaluate_version_chains()` → prompt → LLM → parse citations. Only chunk text from `retrieve()` ever enters the prompt.
- **Temporal truth is computed in code** (`app/services/version_chain.py`): `is_current` = last chain link in force on `DEMO_TODAY` (effective_date or document_date ≤ today, not expired, not superseded by a hidden document); `is_initial` = first link. The prompt carries these as `Zincir: GÜNCEL / İLK HALKA …` headers, current documents first; the model reads them, never derives them. Old values are relayed as historical, never as wrong (ADR-012).
- Sources are what the model cites: every source block is labelled `[K<n>]`; the answer must end factual sentences with labels; `parse_citations()` maps labels back to (document, page). Unknown labels are dropped and logged. Plain text + labels was chosen over JSON mode (simpler parsing, no escaping issues with Turkish text).
- No retrieved chunk → the fixed "bilgi bulamadım" answer is returned **without calling the LLM** (zero tokens). A model reply containing the no-answer sentence is canonicalised to the exact fixed string with `answered=false` and no sources (ADR-014).
- The response also carries `retrieved_document_ids` (for tests, the Phase 4.1 eval and the Phase 3.4 audit log) and a fixed notice that answers contain no interpretation.
- Version chains are created at upload time via optional `effective_date` / `version` / `supersedes_document_id` fields; the predecessor must be visible to the uploader and not already superseded (409); its `status` is not changed (Phase 3.2 owns status transitions).
- `GET /ask` serves a single-file HTML test page from the backend (no Caddy, no build); it stays as a developer page after the real frontend (Phase 3.3).
- **Phase 4.3:** `POST /api/ask` now enters through the router (ADR-010) before this pipeline; the pipeline itself is unchanged and, for `DOCUMENT_QUERY`, receives the original question verbatim.
