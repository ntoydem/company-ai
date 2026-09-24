import { useState } from "react";
import { NavLink, Navigate, Outlet, useParams } from "react-router-dom";

import { useDepartments } from "../api/departments";
import type { Department } from "../api/types";
import { useAuth } from "../auth/useAuth";
import { ErrorBox } from "../components/ErrorBox";
import { Spinner } from "../components/Spinner";
import { S } from "../lib/strings";
import { canSeeDepartment, childrenOf } from "../lib/visibility";

export interface DepartmentContext {
  department: Department;
  children: Department[];
  /** Selected Enerji sub-card (a child department), or null = all. Filters the
   * document list only — `/api/ask` has no sub-department scope. */
  subdepartment: Department | null;
  isAdmin: boolean;
}

export function DepartmentPage() {
  const { slug } = useParams<{ slug: string }>();
  const { user } = useAuth();
  const departments = useDepartments();
  const [subdepartmentId, setSubdepartmentId] = useState<string | null>(null);

  if (!user) return null;
  if (departments.isLoading) return <Spinner />;
  if (departments.isError) return <ErrorBox error={departments.error} />;
  const all = departments.data ?? [];
  const department = all.find((d) => d.slug === slug);
  if (!department) return <p className="muted">{S.department.notFound}</p>;
  // Only top-level departments have a screen; a child slug goes to its parent's.
  if (department.parent_id !== null) {
    const parent = all.find((d) => d.id === department.parent_id);
    return <Navigate to={parent ? `/departman/${parent.slug}` : "/"} replace />;
  }
  if (!canSeeDepartment(user, department.slug)) return <Navigate to="/" replace />;

  const children = childrenOf(all, department.id);
  const subdepartment = children.find((c) => c.id === subdepartmentId) ?? null;
  const context: DepartmentContext = {
    department,
    children,
    subdepartment,
    isAdmin: user.role === "admin",
  };
  const tabs = S.department.tabs;

  return (
    <>
      <h1>{department.name}</h1>
      {children.length > 0 && (
        <>
          <div className="chips">
            <button
              type="button"
              className={`chip${subdepartmentId === null ? " active" : ""}`}
              onClick={() => setSubdepartmentId(null)}
            >
              {S.department.subAll}
            </button>
            {children.map((c) => (
              <button
                type="button"
                key={c.id}
                className={`chip${subdepartmentId === c.id ? " active" : ""}`}
                onClick={() => setSubdepartmentId(c.id)}
              >
                {c.name}
              </button>
            ))}
          </div>
          <p className="notice">{S.department.subNote}</p>
        </>
      )}
      <nav className="tabs">
        <NavLink to="" end>
          {tabs.ask}
        </NavLink>
        <NavLink to="belgeler">{tabs.documents}</NavLink>
        <NavLink to="yukle">{tabs.upload}</NavLink>
        <NavLink to="projeler">{tabs.projects}</NavLink>
      </nav>
      <Outlet context={context} />
    </>
  );
}
