// Hand-written mirrors of backend/app/schemas/*.py — keep in step with the API.

export type UserRole = "admin" | "management" | "employee";

export interface CurrentUser {
  id: string;
  username: string;
  display_name: string;
  role: UserRole;
  department_slugs: string[];
}

export interface Department {
  id: string;
  name: string;
  slug: string;
  parent_id: string | null;
}

export type ProjectStage = "development" | "construction" | "operation";

export interface Project {
  id: string;
  name: string;
  code: string;
  stage: ProjectStage;
  is_active: boolean;
  department_ids: string[];
}

export interface ProjectCreate {
  name: string;
  code: string;
  stage: ProjectStage;
  department_ids: string[];
}

export interface ProjectUpdate {
  name?: string;
  stage?: ProjectStage;
  is_active?: boolean;
  department_ids?: string[];
}

export type DocumentStatus = "draft" | "executed" | "amended" | "superseded" | "active";
export type Confidentiality = "normal" | "restricted" | "board";
export type IngestionStatus = "uploaded" | "ocr" | "ready" | "failed";

export interface DocumentListItem {
  id: string;
  title: string;
  document_type: string;
  counterparty: string;
  document_date: string;
  status: DocumentStatus;
  ingestion_status: IngestionStatus;
  department: string | null;
  subdepartment: string | null;
  project_id: string | null;
  confidentiality: Confidentiality;
  external_ref: string | null;
  created_at: string;
}

export interface DocumentDetail extends DocumentListItem {
  tags: string[];
  effective_date: string | null;
  expiration_date: string | null;
  version: number;
  supersedes_document_id: string | null;
  superseded_by_document_id: string | null;
  related_document_ids: string[];
  ingestion_error: string | null;
  page_count: number | null;
}

export interface DocumentUploadResponse {
  id: string;
  ingestion_status: IngestionStatus;
}

export interface DocumentStatusResponse {
  id: string;
  ingestion_status: IngestionStatus;
  ingestion_error: string | null;
  page_count: number | null;
}

export type SuggestionStatus = "pending" | "applied" | "rejected" | "failed";

export interface SuggestionField {
  value: string | string[] | null;
  confidence: number;
}

export interface MetadataSuggestion {
  id: string;
  document_id: string;
  model: string;
  status: SuggestionStatus;
  fields: Record<string, SuggestionField>;
  error: string | null;
  applied_at: string | null;
  applied_by_id: string | null;
}

export interface MetadataSuggestionApply {
  department?: string | null;
  subdepartment?: string | null;
  project_code?: string | null;
  document_type?: string;
  counterparty?: string;
  document_date?: string;
  status?: DocumentStatus;
  confidentiality?: Confidentiality;
  tags?: string[];
}

export interface AskRequest {
  question: string;
  department?: string;
  project_id?: string;
}

export interface SourceCard {
  ref: string;
  document_id: string;
  title: string;
  page_number: number;
  document_date: string;
  effective_date: string | null;
  version: number;
  status: DocumentStatus;
  is_current: boolean;
  supersedes_title: string | null;
  superseded_by_title: string | null;
}

// ADR-010 (Phase 4.3).
export type QueryType = "DOCUMENT_QUERY" | "DATA_QUERY" | "MIXED_QUERY" | "GENERAL_QUERY";

/** One cited workbook range (SPEC_04 §5): file + sheet + range, no page. */
export interface ExcelSourceCard {
  document_id: string | null;
  file: string;
  sheet: string;
  range: string;
  label: string;
}

export interface AskResponse {
  answer: string;
  answered: boolean;
  sources: SourceCard[];
  retrieved_document_ids: string[];
  model: string | null;
  tokens_in: number;
  tokens_out: number;
  notice: string;
  query_type: QueryType;
  excel_sources: ExcelSourceCard[];
}
