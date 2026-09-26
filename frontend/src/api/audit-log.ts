import { useQuery } from "@tanstack/react-query";

import { getJson } from "./client";
import type { AuditLogDetail, AuditLogFilter, AuditLogListItem } from "./types";

function toQueryString(filter: AuditLogFilter): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(filter)) {
    if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  }
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}

export function auditLogKey(filter: AuditLogFilter) {
  return ["audit-log", filter] as const;
}

export function useAuditLog(filter: AuditLogFilter) {
  return useQuery({
    queryKey: auditLogKey(filter),
    queryFn: () => getJson<AuditLogListItem[]>(`/api/audit-log${toQueryString(filter)}`),
  });
}

export function useAuditLogDetail(id: string | null) {
  return useQuery({
    queryKey: ["audit-log-detail", id],
    queryFn: () => getJson<AuditLogDetail>(`/api/audit-log/${id as string}`),
    enabled: id !== null,
  });
}
