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
- **Phase 3.2 concretization:** `ingestion_jobs` stays OCR-only (no `job_type` column, YAGNI) — the metadata-suggestion queue is a plain SQL predicate (`ingestion_status=ready AND ai_suggestion_id IS NULL`), not a second job table. Two entry points share `app/services/metadata_suggestion.py::suggest_metadata()`: an admin-only `POST /api/documents/{id}/suggest-metadata` (idempotent while `pending`/`applied`; explicit retry after `failed`/`rejected`) and an in-process `asyncio` background scan (`app/main.py` lifespan, `metadata_suggestion_poll_interval_s`/`_batch_size`) that never starts against a `_test` database, so `make test` never calls the LLM through this path. `document_metadata_suggestions.document_id` is unique (one row per document, overwritten on retry — no suggestion history in V0). `documents.ai_suggestion_id` deliberately carries **no FK** to it: a real one would cycle with that table's own FK back to `documents.id` (SQLAlchemy cannot topologically sort the pair); it is kept in sync by the service only, used purely as an existence flag.

## ADR-007 — Retrieval: full-text + metadata first, embeddings behind a flag
**Status:** accepted · **Phase:** 0.2 (FTS) · 3.4 (hybrid)
- Default retrieval is Postgres FTS (`tsvector` with `turkish` and `simple` configurations) plus metadata filters (department, project, document_type, dates, status).
- `EMBEDDINGS_ENABLED=false` is the reference configuration: the whole system and test suite must pass without the `embed` service.
- With the flag on, bge-m3 vectors in `document_chunks.embedding` (pgvector) are combined with FTS (hybrid); the `embed` container runs only under `--profile full` (16 GB VM).
- Retrieval always receives the allowed-id set first (ADR-004) and filters at the SQL level, never after the fact.

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

## ADR-011 — Excel engine boundaries
**Status:** accepted · **Phase:** 4.2
- Inspection with openpyxl (`data_only=True` cached values, formulas, named ranges, hidden sheets); calculation with DuckDB (in-memory, read-only, `enable_external_access=false`, 10 s timeout, row limit); Polars for transformations.
- The LLM decides *what* to compute: either parameters of predefined functions (`dscr`, `outstanding_debt`, `budget_variance`, `capacity_factor`, `production`) or a single whitelisted `SELECT` (no `;`, known tables only, `LIMIT` added, `COPY/ATTACH/INSTALL/LOAD/PRAGMA` rejected). The final number never comes from the model.
- `.xlsm` macros are never executed. No LLM-written Python is executed.
- `CalculationEngine` interface with one implementation, `CachedValueEngine`; missing cached values produce a user message, not a server-side recalculation (LibreOffice recalc is a build step for demo files only).
- Every Excel answer cites `file + sheet + range`.

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

## ADR-021 — Answer pipeline: deterministic temporal evaluation, cited sources, no-LLM fallback
**Status:** accepted · **Phase:** 0.3
- Order per question (SPEC_02 §9): `allowed_document_ids` → `retrieve()` → load the `supersedes` chains of the retrieved documents (restricted to allowed ids at every hop) → `evaluate_version_chains()` → prompt → LLM → parse citations. Only chunk text from `retrieve()` ever enters the prompt.
- **Temporal truth is computed in code** (`app/services/version_chain.py`): `is_current` = last chain link in force on `DEMO_TODAY` (effective_date or document_date ≤ today, not expired, not superseded by a hidden document); `is_initial` = first link. The prompt carries these as `Zincir: GÜNCEL / İLK HALKA …` headers, current documents first; the model reads them, never derives them. Old values are relayed as historical, never as wrong (ADR-012).
- Sources are what the model cites: every source block is labelled `[K<n>]`; the answer must end factual sentences with labels; `parse_citations()` maps labels back to (document, page). Unknown labels are dropped and logged. Plain text + labels was chosen over JSON mode (simpler parsing, no escaping issues with Turkish text).
- No retrieved chunk → the fixed "bilgi bulamadım" answer is returned **without calling the LLM** (zero tokens). A model reply containing the no-answer sentence is canonicalised to the exact fixed string with `answered=false` and no sources (ADR-014).
- The response also carries `retrieved_document_ids` (for tests, the Phase 4.1 eval and the Phase 3.4 audit log) and a fixed notice that answers contain no interpretation.
- Version chains are created at upload time via optional `effective_date` / `version` / `supersedes_document_id` fields; the predecessor must be visible to the uploader and not already superseded (409); its `status` is not changed (Phase 3.2 owns status transitions).
- `GET /ask` serves a single-file HTML test page from the backend (no Caddy, no build); it stays as a developer page after the real frontend (Phase 3.3).
