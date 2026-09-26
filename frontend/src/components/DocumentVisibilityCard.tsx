import { useDocumentVisibility } from "../api/documents";
import { ROLE_LABELS } from "../lib/format";
import { S } from "../lib/strings";
import { ErrorBox } from "./ErrorBox";
import { Spinner } from "./Spinner";

/** Admin-only "bu belgeyi kim görebilir" card (Phase 5.2) — reads
 * `GET /api/documents/{id}/visibility`, which reuses `allowed_document_ids` in reverse
 * (ADR-004 concretization) rather than a second permission engine. */
export function DocumentVisibilityCard({ documentId }: { documentId: string }) {
  const visibility = useDocumentVisibility(documentId, true);
  const t = S.admin.visibility;

  if (visibility.isLoading) return <Spinner />;
  if (visibility.isError) return <ErrorBox error={visibility.error} />;
  const data = visibility.data;
  if (!data) return null;

  return (
    <section className="card">
      <h2>{t.title}</h2>
      {data.users.length === 0 ? (
        <p className="muted">{t.empty}</p>
      ) : (
        <ul>
          {data.users.map((user) => (
            <li key={user.id}>
              {user.display_name} ({user.username}) · {ROLE_LABELS[user.role]}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
