import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "./useAuth";

/** Guard for `/yonetim/*` (Phase 5.2). Silent redirect to home for a non-admin — same
 * pattern `DepartmentPage` uses for a slug the user can't see, no separate 403 page. */
export function RequireAdmin() {
  const { user } = useAuth();
  if (!user || user.role !== "admin") return <Navigate to="/" replace />;
  return <Outlet />;
}
