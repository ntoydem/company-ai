import { useState } from "react";

import { useDepartments } from "../../api/departments";
import { useUsers } from "../../api/users";
import type { AdminUser } from "../../api/types";
import { ErrorBox } from "../../components/ErrorBox";
import { Spinner } from "../../components/Spinner";
import { UserForm } from "../../components/UserForm";
import { useAuth } from "../../auth/useAuth";
import { ROLE_LABELS } from "../../lib/format";
import { S } from "../../lib/strings";

export function AdminUsersPage() {
  const { user: currentUser } = useAuth();
  const users = useUsers();
  const departments = useDepartments();
  const [editing, setEditing] = useState<AdminUser | "new" | null>(null);

  if (users.isLoading) return <Spinner />;
  if (users.isError) return <ErrorBox error={users.error} />;
  const t = S.admin.users;
  const rows = users.data ?? [];

  return (
    <>
      <div className="actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
        <h1>{t.title}</h1>
        {editing === null && (
          <button type="button" className="small" onClick={() => setEditing("new")}>
            {t.new}
          </button>
        )}
      </div>
      {editing !== null && (
        <UserForm
          departments={departments.data ?? []}
          initial={editing === "new" ? undefined : editing}
          isSelf={editing !== "new" && editing.id === currentUser?.id}
          onDone={() => setEditing(null)}
          onCancel={() => setEditing(null)}
        />
      )}
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>{t.columns.username}</th>
              <th>{t.columns.displayName}</th>
              <th>{t.columns.role}</th>
              <th>{t.columns.active}</th>
              <th>{t.columns.departments}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {rows.map((u) => (
              <tr key={u.id}>
                <td>{u.username}</td>
                <td>{u.display_name}</td>
                <td>{ROLE_LABELS[u.role]}</td>
                <td>
                  <span className={`badge ${u.is_active ? "ok" : "neutral"}`}>
                    {u.is_active ? t.active : t.inactive}
                  </span>
                </td>
                <td>{u.department_slugs.join(", ") || "—"}</td>
                <td>
                  <button type="button" className="secondary small" onClick={() => setEditing(u)}>
                    {t.edit}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
