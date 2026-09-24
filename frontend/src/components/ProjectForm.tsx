import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";

import { PROJECTS_KEY, createProject, updateProject } from "../api/projects";
import type { Department, Project, ProjectStage } from "../api/types";
import { STAGE_LABELS, STAGE_VALUES } from "../lib/format";
import { S } from "../lib/strings";
import { ErrorBox } from "./ErrorBox";

/** Admin-only create/edit (SORU 3, Phase 3.3 plan). `code` is immutable after creation
 * (the API's PATCH has no `code`). */
export function ProjectForm({
  departments,
  initial,
  defaultDepartmentIds,
  onDone,
  onCancel,
}: {
  departments: Department[];
  initial?: Project;
  defaultDepartmentIds: string[];
  onDone: () => void;
  onCancel: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(initial?.name ?? "");
  const [code, setCode] = useState(initial?.code ?? "");
  const [stage, setStage] = useState<ProjectStage>(initial?.stage ?? "development");
  const [isActive, setIsActive] = useState(initial?.is_active ?? true);
  const [departmentIds, setDepartmentIds] = useState<string[]>(
    initial?.department_ids ?? defaultDepartmentIds,
  );

  const mutation = useMutation({
    mutationFn: () =>
      initial
        ? updateProject(initial.id, {
            name,
            stage,
            is_active: isActive,
            department_ids: departmentIds,
          })
        : createProject({ name, code: code.trim(), stage, department_ids: departmentIds }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PROJECTS_KEY });
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

  return (
    <form className="card" onSubmit={onSubmit}>
      <h2>{initial ? S.projects.edit : S.projects.new}</h2>
      <div className="form-grid">
        <div className="field">
          <label>{S.projects.name}</label>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label>{S.projects.code}</label>
          <input
            value={code}
            onChange={(e) => setCode(e.target.value.toUpperCase())}
            required
            disabled={Boolean(initial)}
            maxLength={32}
          />
        </div>
        <div className="field">
          <label>{S.projects.stage}</label>
          <select value={stage} onChange={(e) => setStage(e.target.value as ProjectStage)}>
            {STAGE_VALUES.map((s) => (
              <option key={s} value={s}>
                {STAGE_LABELS[s]}
              </option>
            ))}
          </select>
        </div>
        {initial && (
          <div className="field">
            <label>{S.projects.isActive}</label>
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
        <label>{S.projects.departments}</label>
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
      {mutation.isError && <ErrorBox error={mutation.error} />}
      <div className="actions">
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? S.projects.saving : S.projects.save}
        </button>
        <button type="button" className="secondary" onClick={onCancel}>
          {S.projects.cancel}
        </button>
      </div>
    </form>
  );
}
