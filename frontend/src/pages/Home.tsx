import { Link } from "react-router-dom";

import { useDepartments } from "../api/departments";
import { useAuth } from "../auth/useAuth";
import { DepartmentCard } from "../components/DepartmentCard";
import { ErrorBox } from "../components/ErrorBox";
import { Spinner } from "../components/Spinner";
import { S } from "../lib/strings";
import { childrenOf, visibleTopLevel } from "../lib/visibility";

export function HomePage() {
  const { user } = useAuth();
  const departments = useDepartments();
  if (!user) return null;
  if (departments.isLoading) return <Spinner />;
  if (departments.isError) return <ErrorBox error={departments.error} />;
  const all = departments.data ?? [];
  const visible = visibleTopLevel(user, all);

  return (
    <>
      <h1>{S.home.title}</h1>
      {visible.length === 0 ? (
        <p className="muted">{S.home.noDepartments}</p>
      ) : (
        <div className="card-grid">
          {visible.map((d) => (
            <DepartmentCard key={d.id} department={d} children={childrenOf(all, d.id)} />
          ))}
        </div>
      )}
      <section className="card">
        <h2>{S.home.askTitle}</h2>
        <p className="muted">{S.home.askHint}</p>
        <Link to="/sor" className="button">
          {S.home.askButton}
        </Link>
      </section>
    </>
  );
}
