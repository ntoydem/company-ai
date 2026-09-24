import type { CurrentUser, Department } from "../api/types";

/** Card visibility (Phase 3.3 plan §2.2): `management`/`admin` see every department;
 * an `employee` sees only direct memberships. Sub-departments are never a permission
 * unit (Phase 1.2 T7) — a visible parent shows all its children. This is UX only; the
 * server-side gate (`allowed_document_ids`) is what actually protects data. */
export function canSeeDepartment(user: CurrentUser, slug: string): boolean {
  return user.role !== "employee" || user.department_slugs.includes(slug);
}

export function visibleTopLevel(user: CurrentUser, departments: Department[]): Department[] {
  return departments.filter((d) => d.parent_id === null && canSeeDepartment(user, d.slug));
}

export function childrenOf(departments: Department[], parentId: string): Department[] {
  return departments.filter((d) => d.parent_id === parentId);
}
