import { useMutation } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { login } from "../api/auth";
import { useAuth } from "../auth/useAuth";
import { ErrorBox } from "../components/ErrorBox";
import { S } from "../lib/strings";

export function LoginPage() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const mutation = useMutation({
    mutationFn: () => login(username.trim(), password),
    onSuccess: (data) => {
      setUser(data);
      navigate(from, { replace: true });
    },
  });

  if (user) return <Navigate to="/" replace />;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <main className="login-wrap">
      <form className="card" onSubmit={onSubmit}>
        <h1>
          {S.app} — {S.login.title}
        </h1>
        <div className="field">
          <label htmlFor="username">{S.login.username}</label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
            required
          />
        </div>
        <div className="field">
          <label htmlFor="password">{S.login.password}</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </div>
        {mutation.isError && <ErrorBox error={mutation.error} />}
        <button type="submit" disabled={mutation.isPending}>
          {mutation.isPending ? S.login.submitting : S.login.submit}
        </button>
      </form>
    </main>
  );
}
