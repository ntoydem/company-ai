import { Navigate, Outlet, useLocation } from "react-router-dom";

import { Spinner } from "../components/Spinner";
import { useAuth } from "./useAuth";

export function RequireAuth() {
  const { user, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return <Spinner />;
  if (!user) return <Navigate to="/giris" replace state={{ from: location.pathname }} />;
  return <Outlet />;
}
