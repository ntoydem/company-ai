import type {
  Confidentiality,
  DocumentStatus,
  IngestionStatus,
  ProjectStage,
  SuggestionStatus,
  UserRole,
} from "../api/types";

/** "2023-06-01" (or an ISO datetime) → "01.06.2023"; string-based on purpose so a
 * date-only value never shifts by the browser's timezone. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [y, m, d] = iso.slice(0, 10).split("-");
  return y && m && d ? `${d}.${m}.${y}` : iso;
}

export const STATUS_LABELS: Record<DocumentStatus, string> = {
  draft: "Taslak",
  executed: "İmzalandı",
  amended: "Tadil edildi",
  superseded: "Yerini yenisi aldı",
  active: "Aktif",
};

export const CONFIDENTIALITY_LABELS: Record<Confidentiality, string> = {
  normal: "Normal",
  restricted: "Kısıtlı",
  board: "Yönetim kurulu",
};

export const INGESTION_LABELS: Record<IngestionStatus, string> = {
  uploaded: "Kuyrukta",
  ocr: "İşleniyor",
  ready: "Hazır",
  failed: "Hata",
};

export const STAGE_LABELS: Record<ProjectStage, string> = {
  development: "Geliştirme",
  construction: "İnşaat",
  operation: "İşletme",
};

export const ROLE_LABELS: Record<UserRole, string> = {
  admin: "Yönetici",
  management: "Yönetim",
  employee: "Çalışan",
};

export const SUGGESTION_STATUS_LABELS: Record<SuggestionStatus, string> = {
  pending: "Bekliyor",
  applied: "Uygulandı",
  rejected: "Reddedildi",
  failed: "Hata",
};

export const SUGGESTION_FIELD_LABELS: Record<string, string> = {
  department: "Departman",
  subdepartment: "Alt departman",
  project_code: "Proje",
  document_type: "Belge türü",
  counterparty: "Muhatap",
  document_date: "Belge tarihi",
  status: "Durum",
  confidentiality: "Gizlilik",
  tags: "Etiketler",
};

export const SUGGESTION_FIELD_ORDER = [
  "department",
  "subdepartment",
  "project_code",
  "document_type",
  "counterparty",
  "document_date",
  "status",
  "confidentiality",
  "tags",
] as const;

/** Upload/apply forms offer these only; `superseded`/`active` are system-managed. */
export const SELECTABLE_STATUSES: DocumentStatus[] = ["draft", "executed", "amended"];
export const CONFIDENTIALITY_VALUES: Confidentiality[] = ["normal", "restricted", "board"];
export const STAGE_VALUES: ProjectStage[] = ["development", "construction", "operation"];
export const ROLE_VALUES: UserRole[] = ["admin", "management", "employee"];
