import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { useDepartments } from "../api/departments";
import { editDocumentMetadata } from "../api/documents";
import { useProjects } from "../api/projects";
import type {
  Confidentiality,
  DocumentDetail,
  DocumentMetadataEdit,
  DocumentStatus,
} from "../api/types";
import {
  CONFIDENTIALITY_LABELS,
  CONFIDENTIALITY_VALUES,
  SELECTABLE_STATUSES,
  STATUS_LABELS,
  SUGGESTION_FIELD_LABELS,
} from "../lib/format";
import { S } from "../lib/strings";
import { ErrorBox } from "./ErrorBox";

function dateOnly(iso: string | null): string {
  return iso ? iso.slice(0, 10) : "";
}

/** Admin-only manual metadata edit (Phase 5.2), independent of the AI-suggestion flow —
 * works whether or not a suggestion was ever generated/applied for this document. Only
 * fields whose value actually changed are sent (SPEC_02 §4's "no silent overwrite"
 * applies here too — an untouched field must not be re-written with its own old value
 * by accident). No version-chain fields (ADR-012) — those stay upload/apply-only. Field
 * labels are shared with `MetadataSuggestionPanel` (`SUGGESTION_FIELD_LABELS`). */
export function DocumentMetadataEditForm({ current }: { current: DocumentDetail }) {
  const queryClient = useQueryClient();
  const departments = useDepartments();
  const projects = useProjects();
  const currentProjectCode = projects.data?.find((p) => p.id === current.project_id)?.code ?? "";

  const [title, setTitle] = useState(current.title);
  const [department, setDepartment] = useState(current.department ?? "");
  const [subdepartment, setSubdepartment] = useState(current.subdepartment ?? "");
  const [projectCode, setProjectCode] = useState(currentProjectCode);
  const [documentType, setDocumentType] = useState(current.document_type);
  const [counterparty, setCounterparty] = useState(current.counterparty);
  const [documentDate, setDocumentDate] = useState(dateOnly(current.document_date));
  const [status, setStatus] = useState<string>(current.status);
  const [confidentiality, setConfidentiality] = useState<string>(current.confidentiality);
  const [tags, setTags] = useState(current.tags.join(", "));
  const [effectiveDate, setEffectiveDate] = useState(dateOnly(current.effective_date));
  const [expirationDate, setExpirationDate] = useState(dateOnly(current.expiration_date));
  const [message, setMessage] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: (body: DocumentMetadataEdit) => editDocumentMetadata(current.id, body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["document", current.id] });
      void queryClient.invalidateQueries({ predicate: (q) => q.queryKey[0] === "documents" });
      setMessage(null);
    },
  });

  function buildBody(): DocumentMetadataEdit {
    const body: DocumentMetadataEdit = {};
    if (title !== current.title) body.title = title;
    if (department !== (current.department ?? "")) body.department = department || null;
    if (subdepartment !== (current.subdepartment ?? "")) {
      body.subdepartment = subdepartment || null;
    }
    if (projectCode !== currentProjectCode) body.project_code = projectCode || null;
    if (documentType !== current.document_type) body.document_type = documentType;
    if (counterparty !== current.counterparty) body.counterparty = counterparty;
    if (documentDate !== dateOnly(current.document_date)) body.document_date = documentDate;
    if (status !== current.status) body.status = status as DocumentStatus;
    if (confidentiality !== current.confidentiality) {
      body.confidentiality = confidentiality as Confidentiality;
    }
    const nextTags = tags
      ? tags
          .split(",")
          .map((tag) => tag.trim())
          .filter(Boolean)
      : [];
    if (JSON.stringify(nextTags) !== JSON.stringify(current.tags)) body.tags = nextTags;
    if (effectiveDate !== dateOnly(current.effective_date)) {
      body.effective_date = effectiveDate || null;
    }
    if (expirationDate !== dateOnly(current.expiration_date)) {
      body.expiration_date = expirationDate || null;
    }
    return body;
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const body = buildBody();
    if (Object.keys(body).length === 0) {
      setMessage(S.suggestion.nothingSelected);
      return;
    }
    mutation.mutate(body);
  }

  const t = S.admin.metadataEdit;
  const f = SUGGESTION_FIELD_LABELS;

  return (
    <form className="card" onSubmit={onSubmit}>
      <h2>{t.title}</h2>
      <p className="muted">{t.hint}</p>
      <div className="form-grid">
        <div className="field">
          <label>{S.upload.titleField}</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div className="field">
          <label>{f.document_type}</label>
          <input value={documentType} onChange={(e) => setDocumentType(e.target.value)} />
        </div>
        <div className="field">
          <label>{f.counterparty}</label>
          <input value={counterparty} onChange={(e) => setCounterparty(e.target.value)} />
        </div>
        <div className="field">
          <label>{f.document_date}</label>
          <input
            type="date"
            value={documentDate}
            onChange={(e) => setDocumentDate(e.target.value)}
          />
        </div>
        <div className="field">
          <label>{S.documents.effectiveDate}</label>
          <input
            type="date"
            value={effectiveDate}
            onChange={(e) => setEffectiveDate(e.target.value)}
          />
        </div>
        <div className="field">
          <label>{S.documents.expirationDate}</label>
          <input
            type="date"
            value={expirationDate}
            onChange={(e) => setExpirationDate(e.target.value)}
          />
        </div>
        <div className="field">
          <label>{f.subdepartment}</label>
          <input value={subdepartment} onChange={(e) => setSubdepartment(e.target.value)} />
        </div>
        <div className="field">
          <label>{f.status}</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {SELECTABLE_STATUSES.map((s) => (
              <option key={s} value={s}>
                {STATUS_LABELS[s]}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{f.confidentiality}</label>
          <select value={confidentiality} onChange={(e) => setConfidentiality(e.target.value)}>
            {CONFIDENTIALITY_VALUES.map((c) => (
              <option key={c} value={c}>
                {CONFIDENTIALITY_LABELS[c]}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{f.project_code}</label>
          <select value={projectCode} onChange={(e) => setProjectCode(e.target.value)}>
            <option value="">{S.upload.projectNone}</option>
            {(projects.data ?? []).map((p) => (
              <option key={p.id} value={p.code}>
                {p.name} ({p.code})
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{f.department}</label>
          <select value={department} onChange={(e) => setDepartment(e.target.value)}>
            <option value="">—</option>
            {(departments.data ?? []).map((d) => (
              <option key={d.id} value={d.slug}>
                {d.name} ({d.slug})
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label>{f.tags}</label>
          <input value={tags} onChange={(e) => setTags(e.target.value)} />
        </div>
      </div>
      {message && <p className="error-box">{message}</p>}
      {mutation.isError && <ErrorBox error={mutation.error} />}
      <div className="actions">
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? t.saving : t.save}
        </button>
      </div>
    </form>
  );
}
