import { downloadUrl, useDocument } from "../api/documents";
import { CONFIDENTIALITY_LABELS, INGESTION_LABELS, STATUS_LABELS, formatDate } from "../lib/format";
import { S } from "../lib/strings";
import { ErrorBox } from "./ErrorBox";
import { MetadataSuggestionPanel } from "./MetadataSuggestionPanel";
import { Spinner } from "./Spinner";

export function DocumentDetailPanel({
  id,
  isAdmin,
  projectNames,
  onClose,
}: {
  id: string;
  isAdmin: boolean;
  projectNames: Map<string, string>;
  onClose: () => void;
}) {
  const document = useDocument(id);
  if (document.isLoading) return <Spinner />;
  if (document.isError) return <ErrorBox error={document.error} />;
  const d = document.data;
  if (!d) return null;
  const none = S.documents.none;
  const t = S.documents;
  return (
    <>
      <section className="card">
        <div className="actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
          <h2>
            {t.detail}: {d.title}
          </h2>
          <button type="button" className="secondary small" onClick={onClose}>
            {t.close}
          </button>
        </div>
        <dl className="detail-grid">
          <dt>{t.columns.type}</dt>
          <dd>{d.document_type}</dd>
          <dt>{t.columns.counterparty}</dt>
          <dd>{d.counterparty}</dd>
          <dt>{t.columns.date}</dt>
          <dd>{formatDate(d.document_date)}</dd>
          <dt>{t.effectiveDate}</dt>
          <dd>{formatDate(d.effective_date)}</dd>
          <dt>{t.columns.status}</dt>
          <dd>{STATUS_LABELS[d.status]}</dd>
          <dt>{t.version}</dt>
          <dd>{d.version}</dd>
          <dt>{t.columns.confidentiality}</dt>
          <dd>{CONFIDENTIALITY_LABELS[d.confidentiality]}</dd>
          <dt>{t.columns.project}</dt>
          <dd>{(d.project_id && projectNames.get(d.project_id)) || none}</dd>
          <dt>{t.columns.subdepartment}</dt>
          <dd>{d.subdepartment ?? none}</dd>
          <dt>{t.tags}</dt>
          <dd>{d.tags.length ? d.tags.join(", ") : none}</dd>
          <dt>{t.supersedes}</dt>
          <dd>{d.supersedes_document_id ?? none}</dd>
          <dt>{t.supersededBy}</dt>
          <dd>{d.superseded_by_document_id ?? none}</dd>
          <dt>{t.columns.ingestion}</dt>
          <dd>
            {INGESTION_LABELS[d.ingestion_status]}
            {d.page_count !== null && ` · ${t.pages}: ${d.page_count}`}
            {d.ingestion_error && (
              <div className="error-box">
                {t.ingestionError}: {d.ingestion_error}
              </div>
            )}
          </dd>
        </dl>
        <div className="actions">
          <a className="button secondary" href={downloadUrl(d.id)} target="_blank" rel="noreferrer">
            {t.download}
          </a>
        </div>
      </section>
      {d.ingestion_status === "ready" && (
        <MetadataSuggestionPanel documentId={d.id} poll={false} isAdmin={isAdmin} current={d} />
      )}
    </>
  );
}
