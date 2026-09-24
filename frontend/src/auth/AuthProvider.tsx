import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useEffect, useMemo, type ReactNode } from "react";

import { ME_KEY, fetchMe, logout } from "../api/auth";
import { UNAUTHORIZED_EVENT } from "../api/client";
import type { CurrentUser } from "../api/types";
import { AuthContext, type AuthContextValue } from "./context";

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ME_KEY,
    queryFn: fetchMe,
    retry: false,
    staleTime: Infinity,
    gcTime: Infinity,
  });

  const setUser = useCallback(
    (user: CurrentUser | null) => queryClient.setQueryData(ME_KEY, user),
    [queryClient],
  );

  const signOut = useCallback(async () => {
    try {
      await logout();
    } finally {
      // Drop every cached server response of the previous session, keep only "me".
      queryClient.removeQueries({ predicate: (q) => q.queryKey[0] !== ME_KEY[0] });
      queryClient.setQueryData(ME_KEY, null);
    }
  }, [queryClient]);

  useEffect(() => {
    const onUnauthorized = () => queryClient.setQueryData(ME_KEY, null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, [queryClient]);

  const value = useMemo<AuthContextValue>(
    () => ({ user: data ?? null, isLoading, setUser, signOut }),
    [data, isLoading, setUser, signOut],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
