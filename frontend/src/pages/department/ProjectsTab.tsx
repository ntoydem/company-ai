import { useState } from "react";
import { useOutletContext } from "react-router-dom";

import { useDepartments } from "../../api/departments";
import { useProjects } from "../../api/projects";
import type { Project } from "../../api/types";
import { ErrorBox } from "../../components/ErrorBox";
import { ProjectForm } from "../../components/ProjectForm";
import { Spinner } from "../../components/Spinner";
import { STAGE_LABELS } from "../../lib/format";
import { S } from "../../lib/strings";
import type { DepartmentContext } from "../Department";

export function ProjectsTab() {
  const { department, isAdmin } = useOutletContext<DepartmentContext>();
  const projects = useProjects();
  const departments = useDepartments();
  const [editing, setEditing] = useState<Project | "new" | null>(null);

  if (projects.isLoading) return <Spinner />;
  if (projects.isError) return <ErrorBox error={projects.error} />;
  const linked = (projects.data ?? []).filter((p) => p.department_ids.includes(department.id));
  const t = S.projects;

  return (
    <>
      <div className="actions" style={{ justifyContent: "space-between", marginTop: 0 }}>
        <h2>{t.title}</h2>
        {isAdmin && editing === null && (
          <button type="button" className="small" onClick={() => setEditing("new")}>
            {t.new}
          </button>
        )}
      </div>
      {editing !== null && (
        <ProjectForm
          departments={departments.data ?? []}
          initial={editing === "new" ? undefined : editing}
          defaultDepartmentIds={[department.id]}
          onDone={() => setEditing(null)}
          onCancel={() => setEditing(null)}
        />
      )}
      {linked.length === 0 ? (
        <p className="muted">{t.empty}</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t.columns.name}</th>
                <th>{t.columns.code}</th>
                <th>{t.columns.stage}</th>
                <th>{t.columns.active}</th>
                {isAdmin && <th />}
              </tr>
            </thead>
            <tbody>
              {linked.map((p) => (
                <tr key={p.id}>
                  <td>{p.name}</td>
                  <td>{p.code}</td>
                  <td>{STAGE_LABELS[p.stage]}</td>
                  <td>
                    <span className={`badge ${p.is_active ? "ok" : "neutral"}`}>
                      {p.is_active ? t.active : t.inactive}
                    </span>
                  </td>
                  {isAdmin && (
                    <td>
                      <button
                        type="button"
                        className="secondary small"
                        onClick={() => setEditing(p)}
                      >
                        {t.edit}
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
