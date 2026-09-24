import { Link } from "react-router-dom";

import type { Department } from "../api/types";

export function DepartmentCard({
  department,
  children,
}: {
  department: Department;
  children: Department[];
}) {
  return (
    <Link to={`/departman/${department.slug}`} className="dept-card">
      <div className="name">{department.name}</div>
      {children.length > 0 && (
        <div className="sub">{children.map((c) => c.name).join(" · ")}</div>
      )}
    </Link>
  );
}
