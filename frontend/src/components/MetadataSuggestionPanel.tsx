import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { useDepartments } from "../api/departments";
import { applySuggestion, rejectSuggestion, triggerSuggestion, useSuggestion } from "../api/documents";
import { useProjects } from "../api/projects";
import type {
  Confidentiality,
  DocumentDetail,
  DocumentStatus,
  MetadataSuggestion,
  MetadataSuggestionApply,
  SuggestionField,
} from "../api/types";
import {
  CONFIDENTIALITY_LABELS,
  CONFIDENTIALITY_VALUES,
  SELECTABLE_STATUSES,
  STATUS_LABELS,
  SUGGESTION_FIELD_LABELS,
  SUGGESTION_FIELD_ORDER,
  SUGGESTION_STATUS_LABELS,
  formatDate,
} from "../lib/format";
import { S } from "../lib/strings";
import { ErrorBox } from "./ErrorBox";
import { Spinner } from "./Spinner";

type FieldName = (typeof SUGGESTION_FIELD_ORDER)[number];

function toInput(field: SuggestionField | undefined): string {
  const value = field?.value;
  if (value === null || value === undefined) return "";
  return Array.isArray(value) ? value.join(", ") : value;
}

/** Shows the AI suggestion for one document. Admin can edit each value, tick the fields
 * to write, then apply — only ticked fields go into the request body (SPEC_02 §4).
 * Everyone else sees it read-only (Phase 3.2 SORU 2). */
export function MetadataSuggestionPanel({
  documentId,
  poll,
  isAdmin,
  current,
}: {
  documentId: string;
  poll: boolean;
  isAdmin: boolean;
  current?: DocumentDetail;
}) {
  const queryClient = useQueryClient();
  const suggestion = useSuggestion(documentId, poll);
  const projects = useProjects();
  const departments = useDepartments();
  const [values, setValues] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [message, setMessage] = useState<string | null>(null);

  const data = suggestion.data ?? null;
  useEffect(() => {
    if (!data) return;
    const nextValues: Record<string, string> = {};
    const nextSelected: Record<string, boolean> = {};
    for (const field of SUGGESTION_FIELD_ORDER) {
      nextValues[field] = toInput(data.fields[field]);
      nextSelected[field] = nextValues[field] !== "";
    }
    setValues(nextValues);
    setSelected(nextSelected);
    setMessage(null);
  }, [data]);

  const setSuggestionData = (next: MetadataSuggestion) =>
    queryClient.setQueryData(["suggestion", documentId], next);
  const invalidateDocument = () => {
    void queryClient.invalidateQueries({ queryKey: ["document", documentId] });
    void queryClient.invalidateQueries({ predicate: (q) => q.queryKey[0] === "documents" });
  };

  const generate = useMutation({
    mutationFn: () => triggerSuggestion(documentId),
    onSuccess: setSuggestionData,
  });
  const apply = useMutation({
    mutationFn: (body: MetadataSuggestionApply) => applySuggestion(documentId, body),
    onSuccess: () => {
      invalidateDocument();
      void queryClient.invalidateQueries({ queryKey: ["suggestion", documentId] });
    },
  });
  const reject = useMutation({
    mutationFn: () => rejectSuggestion(documentId),
    onSuccess: setSuggestionData,
  });

  function currentValue(field: FieldName): string {
    if (!current) return "";
    switch (field) {
      case "department":
        return current.department ?? "";
      case "subdepartment":
        return current.subdepartment ?? "";
      case "project_code":
        return projects.data?.find((p) => p.id === current.project_id)?.code ?? "";
      case "document_type":
        return current.document_type;
      case "counterparty":
        return current.counterparty;
      case "document_date":
        return formatDate(current.document_date);
      case "status":
        return STATUS_LABELS[current.status];
      case "confidentiality":
        return CONFIDENTIALITY_LABELS[current.confidentiality];
      case "tags":
        return current.tags.join(", ");
    }
  }

  function buildBody(): MetadataSuggestionApply {
    const body: MetadataSuggestionApply = {};
    for (const field of SUGGESTION_FIELD_ORDER) {
      if (!selected[field]) continue;
      const raw = (values[field] ?? "").trim();
      switch (field) {
        case "department":
          body.department = raw || null;
          break;
        case "subdepartment":
          body.subdepartment = raw || null;
          break;
        case "project_code":
          body.project_code = raw || null;
          break;
        case "tags":
          body.tags = raw ? raw.split(",").map((t) => t.trim()).filter(Boolean) : [];
          break;
        case "status":
          if (raw) body.status = raw as DocumentStatus;
          break;
        case "confidentiality":
          if (raw) body.confidentiality = raw as Confidentiality;
          break;
        default:
          if (raw) body[field] = raw;
      }
    }
    return body;
  }

  function onApply() {
    const body = buildBody();
    if (Object.keys(body).length === 0) {
      setMessage(S.suggestion.nothingSelected);
      return;
    }
    setMessage(null);
    apply.mutate(body);
  }

  function renderInput(field: FieldName) {
    const value = values[field] ?? "";
    const onChange = (next: string) => setValues((v) => ({ ...v, [field]: next }));
    if (field === "status") {
      return (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">—</option>
          {SELECTABLE_STATUSES.map((s) => (
            <option key={s} value={s}>
              {STATUS_LABELS[s]}
            </option>
          ))}
        </select>
      );
    }
    if (field === "confidentiality") {
      return (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">—</option>
          {CONFIDENTIALITY_VALUES.map((c) => (
            <option key={c} value={c}>
              {CONFIDENTIALITY_LABELS[c]}
            </option>
          ))}
        </select>
      );
    }
    if (field === "department") {
      return (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">—</option>
          {(departments.data ?? []).map((d) => (
            <option key={d.id} value={d.slug}>
              {d.name} ({d.slug})
            </option>
          ))}
        </select>
      );
    }
    if (field === "project_code") {
      return (
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="">{S.upload.projectNone}</option>
          {(projects.data ?? []).map((p) => (
            <option key={p.id} value={p.code}>
              {p.name} ({p.code})
            </option>
          ))}
        </select>
      );
    }
    if (field === "document_date") {
      return <input type="date" value={value} onChange={(e) => onChange(e.target.value)} />;
    }
    return <input type="text" value={value} onChange={(e) => onChange(e.target.value)} />;
  }

  if (suggestion.isLoading) return <Spinner />;
  if (suggestion.isError) return <ErrorBox error={suggestion.error} />;

  return (
    <section className="card">
      <h2>{S.suggestion.title}</h2>
      {!data && (
        <>
          <p className="muted">{poll ? S.suggestion.waiting : S.suggestion.notYet}</p>
          {isAdmin && (
            <button type="button" onClick={() => generate.mutate()} disabled={generate.isPending}>
              {S.suggestion.generate}
            </button>
          )}
          {generate.isError && <ErrorBox error={generate.error} />}
        </>
      )}
      {data && data.status === "failed" && (
        <>
          <p className="error-box">
            {S.suggestion.failed} {data.error}
          </p>
          {isAdmin && (
            <button type="button" onClick={() => generate.mutate()} disabled={generate.isPending}>
              {S.suggestion.retry}
            </button>
          )}
          {generate.isError && <ErrorBox error={generate.error} />}
        </>
      )}
      {data && data.status !== "failed" && (
        <>
          <p className="muted">
            <span className={`badge ${data.status === "applied" ? "ok" : data.status === "rejected" ? "neutral" : ""}`}>
              {SUGGESTION_STATUS_LABELS[data.status]}
            </span>{" "}
            · {S.suggestion.model}: {data.model}
          </p>
          <div>
            {SUGGESTION_FIELD_ORDER.map((field) => {
              const info = data.fields[field];
              const editable = isAdmin && data.status === "pending";
              return (
                <div className="suggestion-row" key={field}>
                  <div>
                    {editable ? (
                      <input
                        type="checkbox"
                        checked={selected[field] ?? false}
                        onChange={(e) =>
                          setSelected((s) => ({ ...s, [field]: e.target.checked }))
                        }
                        aria-label={SUGGESTION_FIELD_LABELS[field]}
                      />
                    ) : null}
                  </div>
                  <div className="label">{SUGGESTION_FIELD_LABELS[field]}</div>
                  <div>
                    {editable ? renderInput(field) : toInput(info) || S.documents.none}
                    <div className="confidence" title={`${S.suggestion.confidence}: ${info?.confidence ?? 0}`}>
                      <span style={{ width: `${Math.round((info?.confidence ?? 0) * 100)}%` }} />
                    </div>
                  </div>
                  <div className="current">
                    {S.suggestion.currentValue}: {currentValue(field) || S.documents.none}
                  </div>
                </div>
              );
            })}
          </div>
          {isAdmin && data.status === "pending" && (
            <>
              <p className="muted">{S.suggestion.includeHint}</p>
              {message && <p className="error-box">{message}</p>}
              {apply.isError && <ErrorBox error={apply.error} />}
              {reject.isError && <ErrorBox error={reject.error} />}
              <div className="actions">
                <button type="button" onClick={onApply} disabled={apply.isPending}>
                  {S.suggestion.apply}
                </button>
                <button
                  type="button"
                  className="danger"
                  onClick={() => reject.mutate()}
                  disabled={reject.isPending}
                >
                  {S.suggestion.reject}
                </button>
              </div>
            </>
          )}
          {!isAdmin && data.status === "pending" && (
            <p className="muted">{S.suggestion.adminOnly}</p>
          )}
        </>
      )}
    </section>
  );
}
