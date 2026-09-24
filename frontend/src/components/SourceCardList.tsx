import { downloadUrl } from "../api/documents";
import type { SourceCard } from "../api/types";
import { STATUS_LABELS, formatDate } from "../lib/format";
import { S } from "../lib/strings";

/** One card per cited (document, page) — SPEC_02 §10: belge, sayfa, tarih, versiyon,
 * proje. Project comes from a client-side `document_id → project name` lookup. */
export function SourceCardList({
  sources,
  projectOfDocument,
}: {
  sources: SourceCard[];
  projectOfDocument: (documentId: string) => string | null;
}) {
  if (sources.length === 0) return <p className="muted">{S.ask.noSources}</p>;
  return (
    <div>
      {sources.map((s) => {
        const project = projectOfDocument(s.document_id);
        return (
          <div className="source" key={`${s.ref}-${s.document_id}-${s.page_number}`}>
            <span className="ref">[{s.ref}]</span>
            <strong>{s.title}</strong> — {S.ask.page} {s.page_number}
            {s.is_current && <span className="badge ok">{S.ask.current}</span>}
            <div className="meta">
              {S.ask.date}: {formatDate(s.document_date)}
              {s.effective_date && ` · ${S.ask.effective}: ${formatDate(s.effective_date)}`}
              {` · ${S.ask.version}: ${s.version}`}
              {` · ${STATUS_LABELS[s.status]}`}
              {project && ` · ${S.ask.project}: ${project}`}
              {s.supersedes_title && <div>{S.ask.supersedes(s.supersedes_title)}</div>}
              {s.superseded_by_title && <div>{S.ask.supersededBy(s.superseded_by_title)}</div>}
              <div>
                <a href={downloadUrl(s.document_id)} target="_blank" rel="noreferrer">
                  {S.ask.download}
                </a>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
