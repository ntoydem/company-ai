import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { USERS_KEY, createUser, updateUser } from "../api/users";
import type { AdminUser, Department, UserRole } from "../api/types";
import { ROLE_LABELS, ROLE_VALUES } from "../lib/format";
import { S } from "../lib/strings";
import { ErrorBox } from "./ErrorBox";

/** Admin-only create/edit (Phase 5.2). `username` is immutable after creation — like
 * `Project.code`, there is no field for it in the update request at all. Editing one's
 * own account hides the role/active controls (backend rejects self-demote/disable, T6);
 * showing them anyway would just produce a confusing 409 on save. */
export function UserForm({
  departments,
  initial,
  isSelf,
  onDone,
  onCancel,
}: {
  departments: Department[];
  initial?: AdminUser;
  isSelf: boolean;
  onDone: () => void;
  onCancel: () => void;
}) {
  const queryClient = useQueryClient();
  const [username, setUsername] = useState(initial?.username ?? "");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState(initial?.display_name ?? "");
  const [role, setRole] = useState<UserRole>(initial?.role ?? "employee");
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [departmentIds, setDepartmentIds] = useState<string[]>(initial?.department_ids ?? []);

  const mutation = useMutation({
    mutationFn: () =>
      initial
        ? updateUser(initial.id, {
            display_name: displayName,
            role: isSelf ? undefined : role,
            is_active: isSelf ? undefined : isActive,
            department_ids: departmentIds,
          })
        : createUser({
            username: username.trim(),
            password,
            display_name: displayName,
            role,
            department_ids: departmentIds,
          }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: USERS_KEY });
      onDone();
    },
  });

  function toggleDepartment(id: string, checked: boolean) {
    setDepartmentIds((ids) => (checked ? [...ids, id] : ids.filter((d) => d !== id)));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  const t = S.admin.users;

  return (
    <form className="card" onSubmit={onSubmit}>
      <h2>{initial ? t.edit : t.new}</h2>
      <div className="form-grid">
        <div className="field">
          <label>{t.username}</label>
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            disabled={Boolean(initial)}
          />
        </div>
        {!initial && (
          <div className="field">
            <label>{t.password}</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
        )}
        <div className="field">
          <label>{t.displayName}</label>
          <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} required />
        </div>
        {!isSelf && (
          <div className="field">
            <label>{t.role}</label>
            <select value={role} onChange={(e) => setRole(e.target.value as UserRole)}>
              {ROLE_VALUES.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </div>
        )}
        {initial && !isSelf && (
          <div className="field">
            <label>{t.isActive}</label>
            <input
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              style={{ width: "auto" }}
            />
          </div>
        )}
      </div>
      <div className="field">
        <label>{t.departments}</label>
        <div className="chips">
          {departments
            .filter((d) => d.parent_id === null)
            .map((d) => (
              <label key={d.id} className="chip" style={{ display: "inline-flex", gap: 6 }}>
                <input
                  type="checkbox"
                  style={{ width: "auto" }}
                  checked={departmentIds.includes(d.id)}
                  onChange={(e) => toggleDepartment(d.id, e.target.checked)}
                />
                {d.name}
              </label>
            ))}
        </div>
      </div>
      {isSelf && <p className="notice">{t.selfEditHint}</p>}
      {mutation.isError && <ErrorBox error={mutation.error} />}
      <div className="actions">
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? t.saving : t.save}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          {t.cancel}
        </button>
      </div>
    </form>
  );
}
