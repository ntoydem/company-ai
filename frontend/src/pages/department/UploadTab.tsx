import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useOutletContext } from "react-router-dom";

import { uploadDocument, useDocument, useDocumentStatus, useDocuments } from "../../api/documents";
import { useProjects } from "../../api/projects";
import type { Confidentiality, DocumentStatus } from "../../api/types";
import { ErrorBox } from "../../components/ErrorBox";
import { MetadataSuggestionPanel } from "../../components/MetadataSuggestionPanel";
import {
  CONFIDENTIALITY_LABELS,
  CONFIDENTIALITY_VALUES,
  SELECTABLE_STATUSES,
  STATUS_LABELS,
} from "../../lib/format";
import { S } from "../../lib/strings";
import type { DepartmentContext } from "../Department";

const EMPTY = {
  title: "",
  documentType: "",
  counterparty: "",
  documentDate: "",
  status: "executed" as DocumentStatus,
  confidentiality: "normal" as Confidentiality,
  projectId: "",
  subdepartment: "",
  effectiveDate: "",
  version: "1",
  supersedesId: "",
};

/** SPEC_02 §1 form → `/upload` → `/status` polling → AI suggestion panel (SPEC_02 §4).
 * `department` is the current screen's slug, not a form field. */
export function UploadTab() {
  const { department, children, isAdmin } = useOutletContext<DepartmentContext>();
  const queryClient = useQueryClient();
  const projects = useProjects();
  const documents = useDocuments({ department: department.slug });
  const [form, setForm] = useState(EMPTY);
  const [file, setFile] = useState<File | null>(null);
  const [uploadedId, setUploadedId] = useState<string | null>(null);
  const status = useDocumentStatus(uploadedId);
  const ready = status.data?.ingestion_status === "ready";
  const detail = useDocument(ready ? uploadedId : null);

  const upload = useMutation({
    mutationFn: (data: FormData) => uploadDocument(data),
    onSuccess: (data) => {
      setUploadedId(data.id);
      void queryClient.invalidateQueries({ predicate: (q) => q.queryKey[0] === "documents" });
    },
  });

  function set<K extends keyof typeof EMPTY>(key: K, value: (typeof EMPTY)[K]) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!file) return;
    const data = new FormData();
    data.set("file", file);
    data.set("title", form.title);
    data.set("document_type", form.documentType);
    data.set("counterparty", form.counterparty);
    data.set("document_date", form.documentDate);
    data.set("status", form.status);
    data.set("confidentiality", form.confidentiality);
    data.set("department", department.slug);
    data.set("version", form.version || "1");
    if (form.projectId) data.set("project_id", form.projectId);
    if (form.subdepartment) data.set("subdepartment", form.subdepartment);
    if (form.effectiveDate) data.set("effective_date", form.effectiveDate);
    if (form.supersedesId) data.set("supersedes_document_id", form.supersedesId);
    upload.mutate(data);
  }

  function reset() {
    setUploadedId(null);
    setForm(EMPTY);
    setFile(null);
    upload.reset();
  }

  const t = S.upload;
  const ingestion = status.data?.ingestion_status;

  if (uploadedId) {
    return (
      <>
        <h2>{t.title}</h2>
        <section className="card">
          {status.isError && <ErrorBox error={status.error} />}
          {ingestion === "failed" ? (
            <div className="error-box">
              {t.failed} {status.data?.ingestion_error}
            </div>
          ) : ingestion === "ready" ? (
            <p>
              <span className="badge ok">{t.ready}</span>
            </p>
          ) : (
            <p className="muted">{t.processing}</p>
          )}
          <button type="button" className="secondary" onClick={reset}>
            {t.another}
          </button>
        </section>
        {ingestion === "ready" && (
          <MetadataSuggestionPanel
            documentId={uploadedId}
            poll
            isAdmin={isAdmin}
            current={detail.data}
          />
        )}
      </>
    );
  }

  return (
    <>
      <h2>{t.title}</h2>
      <form className="card" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="file">{t.file}</label>
          <input
            id="file"
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            required
          />
        </div>
        <div className="form-grid">
          <div className="field">
            <label>{t.titleField}</label>
            <input value={form.title} onChange={(e) => set("title", e.target.value)} required />
          </div>
          <div className="field">
            <label>{t.type}</label>
            <input
              value={form.documentType}
              onChange={(e) => set("documentType", e.target.value)}
              placeholder="facility_agreement"
              required
            />
          </div>
          <div className="field">
            <label>{t.counterparty}</label>
            <input
              value={form.counterparty}
              onChange={(e) => set("counterparty", e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label>{t.date}</label>
            <input
              type="date"
              value={form.documentDate}
              onChange={(e) => set("documentDate", e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label>{t.status}</label>
            <select value={form.status} onChange={(e) => set("status", e.target.value as DocumentStatus)}>
              {SELECTABLE_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {STATUS_LABELS[s]}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t.confidentiality}</label>
            <select
              value={form.confidentiality}
              onChange={(e) => set("confidentiality", e.target.value as Confidentiality)}
            >
              {CONFIDENTIALITY_VALUES.map((c) => (
                <option key={c} value={c}>
                  {CONFIDENTIALITY_LABELS[c]}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t.project}</label>
            <select value={form.projectId} onChange={(e) => set("projectId", e.target.value)}>
              <option value="">{t.projectNone}</option>
              {(projects.data ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.code})
                </option>
              ))}
            </select>
          </div>
          {children.length > 0 && (
            <div className="field">
              <label>{t.subdepartment}</label>
              <select
                value={form.subdepartment}
                onChange={(e) => set("subdepartment", e.target.value)}
              >
                <option value="">{t.subNone}</option>
                {children.map((c) => (
                  <option key={c.id} value={c.slug}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="field">
            <label>{t.effectiveDate}</label>
            <input
              type="date"
              value={form.effectiveDate}
              onChange={(e) => set("effectiveDate", e.target.value)}
            />
          </div>
          <div className="field">
            <label>{t.version}</label>
            <input
              type="number"
              min={1}
              value={form.version}
              onChange={(e) => set("version", e.target.value)}
            />
          </div>
          <div className="field">
            <label>{t.supersedes}</label>
            <select value={form.supersedesId} onChange={(e) => set("supersedesId", e.target.value)}>
              <option value="">{t.supersedesNone}</option>
              {(documents.data ?? []).map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>
          </div>
        </div>
        {upload.isError && <ErrorBox error={upload.error} />}
        <button type="submit" disabled={upload.isPending || !file}>
          {upload.isPending ? t.submitting : t.submit}
        </button>
      </form>
    </>
  );
}
