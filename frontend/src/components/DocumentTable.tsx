import type { DocumentListItem, IngestionStatus } from "../api/types";
import { CONFIDENTIALITY_LABELS, INGESTION_LABELS, STATUS_LABELS, formatDate } from "../lib/format";
import { S } from "../lib/strings";

const INGESTION_CLASS: Record<IngestionStatus, string> = {
  uploaded: "neutral",
  ocr: "warn",
  ready: "ok",
  failed: "err",
};

export function DocumentTable({
  documents,
  projectNames,
  selectedId,
  onSelect,
  showSubdepartment,
  subdepartmentLabel = (value) => value,
}: {
  documents: DocumentListItem[];
  projectNames: Map<string, string>;
  selectedId: string | null;
  onSelect: (id: string) => void;
  showSubdepartment: boolean;
  /** Seeded documents store the child department's slug; show its name instead. */
  subdepartmentLabel?: (value: string) => string;
}) {
  if (documents.length === 0) {
    return <p className="muted">{S.documents.empty}</p>;
  }
  const c = S.documents.columns;
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>{c.title}</th>
            <th>{c.type}</th>
            <th>{c.counterparty}</th>
            <th>{c.date}</th>
            <th>{c.status}</th>
            <th>{c.confidentiality}</th>
            <th>{c.project}</th>
            {showSubdepartment && <th>{c.subdepartment}</th>}
            <th>{c.ingestion}</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((d) => (
            <tr
              key={d.id}
              className={`clickable${d.id === selectedId ? " selected" : ""}`}
              onClick={() => onSelect(d.id)}
            >
              <td>{d.title}</td>
              <td>{d.document_type}</td>
              <td>{d.counterparty}</td>
              <td>{formatDate(d.document_date)}</td>
              <td>{STATUS_LABELS[d.status]}</td>
              <td>{CONFIDENTIALITY_LABELS[d.confidentiality]}</td>
              <td>{(d.project_id && projectNames.get(d.project_id)) || S.documents.none}</td>
              {showSubdepartment && (
                <td>{d.subdepartment ? subdepartmentLabel(d.subdepartment) : S.documents.none}</td>
              )}
              <td>
                <span className={`badge ${INGESTION_CLASS[d.ingestion_status]}`}>
                  {INGESTION_LABELS[d.ingestion_status]}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
