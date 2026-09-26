import { useState } from "react";

import { useAuditLog, useAuditLogDetail } from "../../api/audit-log";
import { useDepartments } from "../../api/departments";
import { useProjects } from "../../api/projects";
import type { AuditLogFilter, QueryType } from "../../api/types";
import { ErrorBox } from "../../components/ErrorBox";
import { Spinner } from "../../components/Spinner";
import { S } from "../../lib/strings";

const QUERY_TYPES: QueryType[] = [
  "DOCUMENT_QUERY",
  "DATA_QUERY",
  "MIXED_QUERY",
  "GENERAL_QUERY",
];

const PAGE_SIZE = 50;

function AuditLogDetailPanel({ id, onClose }: { id: string; onClose: () => void }) {
  const detail = useAuditLogDetail(id);
  const t = S.admin.auditLog;
  if (detail.isLoading) return <Spinner />;
  if (detail.isError) return <ErrorBox error={detail.error} />;
  const d = detail.data;
  if (!d) return null;
  return (
    <section className="card">
      <div className="actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
        <h2>{t.detail}</h2>
        <button type="button" className="secondary small" onClick={onClose}>
          {t.close}
        </button>
      </div>
      <dl className="detail-grid">
        <dt>{t.columns.time}</dt>
        <dd>{new Date(d.timestamp).toLocaleString("tr-TR")}</dd>
        <dt>{t.columns.question}</dt>
        <dd>{d.question}</dd>
        <dt>{t.answer}</dt>
        <dd>{d.answer || t.none}</dd>
        <dt>{t.columns.queryType}</dt>
        <dd>{d.query_type}</dd>
        <dt>{t.columns.model}</dt>
        <dd>{d.model ?? t.none}</dd>
        <dt>{t.columns.tokens}</dt>
        <dd>
          {d.tokens_in} / {d.tokens_out}
        </dd>
        <dt>{t.cost}</dt>
        <dd>{d.cost_estimate ?? t.none}</dd>
        <dt>{t.columns.duration}</dt>
        <dd>{d.execution_ms}</dd>
        <dt>{t.sources}</dt>
        <dd>{d.sources.length ? JSON.stringify(d.sources) : t.none}</dd>
        <dt>{t.excelFiles}</dt>
        <dd>{d.excel_files_used.length ? d.excel_files_used.join(", ") : t.none}</dd>
        <dt>{t.columns.error}</dt>
        <dd>{d.error ?? t.none}</dd>
        <dt>{t.requestId}</dt>
        <dd>{d.request_id ?? t.none}</dd>
      </dl>
    </section>
  );
}

export function AdminAuditLogPage() {
  const departments = useDepartments();
  const projects = useProjects();
  const [department, setDepartment] = useState("");
  const [projectId, setProjectId] = useState("");
  const [queryType, setQueryType] = useState("");
  const [fromTs, setFromTs] = useState("");
  const [toTs, setToTs] = useState("");
  const [hasError, setHasError] = useState(false);
  const [offset, setOffset] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filter: AuditLogFilter = {
    department: department || undefined,
    project_id: projectId || undefined,
    query_type: queryType || undefined,
    from_ts: fromTs || undefined,
    to_ts: toTs || undefined,
    has_error: hasError ? true : undefined,
    limit: PAGE_SIZE,
    offset,
  };
  const rows = useAuditLog(filter);
  const t = S.admin.auditLog;

  function applyFilters() {
    setOffset(0);
  }

  return (
    <>
      <h1>{t.title}</h1>
      <div className="card">
        <div className="form-grid">
          <div className="field">
            <label>{t.filters.department}</label>
            <select value={department} onChange={(e) => setDepartment(e.target.value)}>
              <option value="">{t.filters.allDepartments}</option>
              {(departments.data ?? []).map((d) => (
                <option key={d.id} value={d.slug}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t.filters.project}</label>
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}>
              <option value="">{t.filters.allProjects}</option>
              {(projects.data ?? []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t.filters.queryType}</label>
            <select value={queryType} onChange={(e) => setQueryType(e.target.value)}>
              <option value="">{t.filters.allTypes}</option>
              {QUERY_TYPES.map((qt) => (
                <option key={qt} value={qt}>
                  {S.ask.queryType[qt]}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>{t.filters.from}</label>
            <input
              type="datetime-local"
              value={fromTs}
              onChange={(e) => setFromTs(e.target.value)}
            />
          </div>
          <div className="field">
            <label>{t.filters.to}</label>
            <input type="datetime-local" value={toTs} onChange={(e) => setToTs(e.target.value)} />
          </div>
          <div className="field">
            <label>{t.filters.hasError}</label>
            <input
              type="checkbox"
              style={{ width: "auto" }}
              checked={hasError}
              onChange={(e) => setHasError(e.target.checked)}
            />
          </div>
        </div>
        <div className="actions">
          <button type="button" onClick={applyFilters}>
            {t.filters.apply}
          </button>
        </div>
      </div>

      {rows.isLoading && <Spinner />}
      {rows.isError && <ErrorBox error={rows.error} />}
      {rows.data && rows.data.length === 0 && <p className="muted">{t.empty}</p>}
      {rows.data && rows.data.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t.columns.time}</th>
                <th>{t.columns.question}</th>
                <th>{t.columns.queryType}</th>
                <th>{t.columns.department}</th>
                <th>{t.columns.model}</th>
                <th>{t.columns.tokens}</th>
                <th>{t.columns.duration}</th>
                <th>{t.columns.error}</th>
              </tr>
            </thead>
            <tbody>
              {rows.data.map((row) => (
                <tr
                  key={row.id}
                  className={`clickable${row.id === selectedId ? " selected" : ""}`}
                  onClick={() => setSelectedId(row.id)}
                >
                  <td>{new Date(row.timestamp).toLocaleString("tr-TR")}</td>
                  <td>{row.question}</td>
                  <td>{row.query_type}</td>
                  <td>{row.scope_department ?? t.none}</td>
                  <td>{row.model ?? t.none}</td>
                  <td>
                    {row.tokens_in}/{row.tokens_out}
                  </td>
                  <td>{row.execution_ms}</td>
                  <td>{row.error ? <span className="badge err">{row.error}</span> : t.none}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="actions">
        <button
          type="button"
          className="secondary small"
          disabled={offset === 0}
          onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
        >
          {t.prevPage}
        </button>
        <button
          type="button"
          className="secondary small"
          disabled={(rows.data?.length ?? 0) < PAGE_SIZE}
          onClick={() => setOffset((o) => o + PAGE_SIZE)}
        >
          {t.nextPage}
        </button>
      </div>

      {selectedId && (
        <AuditLogDetailPanel id={selectedId} onClose={() => setSelectedId(null)} />
      )}
    </>
  );
}
