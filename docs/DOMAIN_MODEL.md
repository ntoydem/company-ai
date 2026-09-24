# DOMAIN MODEL — Company AI V0 (skeleton, no figures)

Entities, relationships and enumerations of the platform. **No numbers, dates or amounts here**:
all demo figures live in `seed_data/master/*.yaml` (truth ledger, Phase 2.1). Column details per phase
are in the Alembic migrations; this file explains what the tables mean and how they relate.

## 1. Entity overview

```
User ──< UserDepartment >── Department (tree: parent_id)
User ──< Document (uploaded_by)
Department ──< Document (department, subdepartment)
Project ──< Document (project_id)          Project >──< Department (project_departments)
Document ──< DocumentPage ──< DocumentChunk
Document ──< IngestionJob
Document ──< DocumentMetadataSuggestion
Document ── supersedes / superseded_by ── Document      (version chain)
Document ──< related_document_ids >── Document          (relationship graph)
User ──< AuditLog
```

## 2. Entities

| Entity | Table | Purpose | Phase |
|---|---|---|---|
| User | `users` | Login identity: `username`, `password_hash` (Argon2id), `display_name`, `role`, `is_active`, `auth_provider` (`local`), `external_id` (SSO-ready, unused) | 0.1 |
| Department | `departments` | Organisation tree: Enerji Grubu (Geliştirme, EPC/İnşaat, Bakım), Finans, Hukuk, Mali İşler, İdari İşler | 1.2 |
| UserDepartment | `user_departments` | Membership; a user may belong to several departments | 1.2 |
| Project | `projects` | `name`, `code` (e.g. `ANK_RES`, `IZM_RES`), `stage`, `is_active`, linked departments. Not hard-coded; admin CRUD | 1.2 |
| Document | `documents` | Master metadata of one file (see §3). `department`, `project_id`, `confidentiality` exist from the first migration with defaults | 0.2 |
| DocumentPage | `document_pages` | `page_number`, `text` per page (PyMuPDF after OCR) | 0.2 |
| DocumentChunk | `document_chunks` | `chunk_index`, `page_number` (NOT NULL), `text`, `tsv` (FTS), `embedding` (pgvector, NULL unless enabled) | 0.2 |
| IngestionJob | `ingestion_jobs` | Postgres-backed work queue polled by `ocr-worker`: status, attempts, error, lock | 0.2 |
| DocumentMetadataSuggestion | `document_metadata_suggestions` | AI-proposed metadata with per-field confidence; applied only on user acceptance | 3.2 |
| AuditLog | `audit_log` | Who asked what, scope, sources used, model, tokens, request id; admin-only; 90 days | 3.4 |
| Excel workbook | *(no table in V0)* | Workbooks are Documents with `document_type` in the Excel family; sheets are loaded into DuckDB at query time | 4.2 |

## 3. Document metadata groups (SPEC_02 §2)

- **Mandatory:** `title, department, subdepartment, project_id, document_type, counterparty, document_date, status, confidentiality, tags, source (web|consume), created_at, updated_at`
- **Temporal:** `effective_date, expiration_date, version, revision, supersedes_document_id, superseded_by_document_id, related_document_ids`
- **System:** `storage_path, ingestion_status, ingestion_error, uploaded_by, ai_suggestion_id, page_count`
- Filenames are never a primary information source; metadata is.

## 4. Enumerations

| Enum | Values | Notes |
|---|---|---|
| `user_role` | `admin`, `management`, `employee` | permission tiers (SPEC_02 §5) |
| `confidentiality` | `normal`, `restricted`, `board` | `employee` sees only `normal` of own departments |
| `document_status` | `draft`, `executed`, `amended`, `superseded`, `active` | lifecycle of a document, not of the project. `superseded` is set automatically (`mark_superseded`, Phase 3.2) when another document's `supersedes_document_id` points at it; `active` is left alone (operational, not lifecycle) |
| `ingestion_status` | `uploaded`, `ocr`, `ready`, `failed` | pipeline state |
| `ingestion_job_status` | `queued`, `running`, `done`, `failed` | queue state |
| `project_stage` | `development`, `construction`, `operation` | |
| `query_type` | `DOCUMENT_QUERY`, `DATA_QUERY`, `MIXED_QUERY`, `GENERAL_QUERY` | router output; every `audit_log` row is `DOCUMENT_QUERY` until the router (ADR-010) lands in Phase 4.3 |
| `ledger_tag` | `USER_FACT`, `AI_ASSUMPTION` | truth ledger only, never in the app DB |

## 5. Authorization rules (summary; implementation in `allowed_document_ids`, ADR-004)

- `employee`: `normal` documents of the departments they belong to.
- `management`: every department, every confidentiality level.
- `admin`: everything plus administration.
- A project may span departments; a document's permission comes from its department, never from its project.
- Step 0 (single admin): the gate returns all documents. Step 1.2: the rules above.

## 6. Version chain and temporal truth

A document may supersede exactly one earlier document and be superseded by exactly one later one:
`DRAFT → V01 → V02 → EXECUTED → AMENDMENT 01 → AMENDMENT 02`. Content changes are real (values differ),
not just file names. "Current value" = last link effective on `DEMO_TODAY`; "initial value" = first
link. An old value is a correct answer to a historical question. Amendments state what they change.

## 7. Document relationship graph (SPEC_02 §12)

`Licence → Technical Report → EPC Contract → Financial Model → Facility Agreement → Board Resolution →
Insurance → Construction → Commissioning → COD → Operation`. Capacity, dates, SPV name, loan amount,
contract price and COD must be consistent across linked documents; links are stored in `related_document_ids`.

## 8. Demo projects (structure only; figures in the ledger)

| | Ankara RES | İzmir RES |
|---|---|---|
| Stage | operation (in its third operating year on `DEMO_TODAY`) | development |
| Lifecycle covered | licence → financing → financial close → construction → commissioning → COD → operation | pre-licence steps: pre-licence, land, EIA (ÇED) ongoing |
| Finance documents | full chain incl. amendments, covenant reports | none (no financing yet) |
| Post-licence fields | filled | `null` by design |
| Isolation rule | never receives İzmir EIA status | never receives Ankara capacity/financing/COD |

## 9. Table arrival by phase

| Phase | Tables |
|---|---|
| 0.1 | `users` (+ pgvector extension) |
| 0.2 | `documents`, `document_pages`, `document_chunks`, `ingestion_jobs` |
| 1.2 | `departments`, `user_departments`, `projects`, `project_departments` |
| 3.2 | `document_metadata_suggestions` |
| 3.4 | `audit_log` |
