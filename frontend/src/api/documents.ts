import { useQuery } from "@tanstack/react-query";

import { ApiError, getJson, postForm, postJson, queryString } from "./client";
import type {
  DocumentDetail,
  DocumentListItem,
  DocumentStatusResponse,
  DocumentUploadResponse,
  MetadataSuggestion,
  MetadataSuggestionApply,
} from "./types";

export interface DocumentScope {
  department?: string;
  project_id?: string;
}

export const documentsKey = (scope: DocumentScope) =>
  ["documents", scope.department ?? null, scope.project_id ?? null] as const;

export function useDocuments(scope: DocumentScope) {
  return useQuery({
    queryKey: documentsKey(scope),
    queryFn: () =>
      getJson<DocumentListItem[]>(
        `/api/documents${queryString({ department: scope.department, project_id: scope.project_id })}`,
      ),
  });
}

export function useDocument(id: string | null) {
  return useQuery({
    queryKey: ["document", id],
    queryFn: () => getJson<DocumentDetail>(`/api/documents/${id as string}`),
    enabled: id !== null,
  });
}

export function uploadDocument(form: FormData): Promise<DocumentUploadResponse> {
  return postForm<DocumentUploadResponse>("/api/documents/upload", form);
}

const POLL_MS = 3000;

/** Polls every 3 s until the OCR pipeline reports `ready` or `failed`. */
export function useDocumentStatus(id: string | null) {
  return useQuery({
    queryKey: ["document-status", id],
    queryFn: () => getJson<DocumentStatusResponse>(`/api/documents/${id as string}/status`),
    enabled: id !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.ingestion_status;
      return status === "ready" || status === "failed" ? false : POLL_MS;
    },
  });
}

async function fetchSuggestion(id: string): Promise<MetadataSuggestion | null> {
  try {
    return await getJson<MetadataSuggestion>(`/api/documents/${id}/metadata-suggestion`);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}

const SUGGESTION_MAX_POLLS = 30; // ≈ 90 s; the background scan runs every 15 s (Phase 3.2)

/** `poll`: keep asking while there is no suggestion yet (right after an upload). */
export function useSuggestion(id: string | null, poll: boolean) {
  return useQuery({
    queryKey: ["suggestion", id],
    queryFn: () => fetchSuggestion(id as string),
    enabled: id !== null,
    refetchInterval: (query) =>
      poll && query.state.data === null && query.state.dataUpdateCount < SUGGESTION_MAX_POLLS
        ? POLL_MS
        : false,
  });
}

export function triggerSuggestion(id: string): Promise<MetadataSuggestion> {
  return postJson<MetadataSuggestion>(`/api/documents/${id}/suggest-metadata`);
}

export function applySuggestion(
  id: string,
  body: MetadataSuggestionApply,
): Promise<DocumentListItem> {
  return postJson<DocumentListItem>(`/api/documents/${id}/metadata-suggestion/apply`, body);
}

export function rejectSuggestion(id: string): Promise<MetadataSuggestion> {
  return postJson<MetadataSuggestion>(`/api/documents/${id}/metadata-suggestion/reject`);
}

export const downloadUrl = (id: string) => `/api/documents/${id}/download`;
