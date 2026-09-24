import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/useAuth";
import { ROLE_LABELS } from "../lib/format";
import { S } from "../lib/strings";

export function Layout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  async function onLogout() {
    await signOut();
    navigate("/giris", { replace: true });
  }

  return (
    <>
      <header className="topbar">
        <Link to="/" className="brand">
          {S.app}
        </Link>
        <nav>
          <NavLink to="/" end>
            {S.nav.home}
          </NavLink>
          <NavLink to="/sor">{S.nav.ask}</NavLink>
        </nav>
        <div className="user">
          {user && (
            <span>
              {user.display_name} · {ROLE_LABELS[user.role]}
            </span>
          )}
          <button type="button" className="secondary small" onClick={onLogout}>
            {S.nav.logout}
          </button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  );
}
