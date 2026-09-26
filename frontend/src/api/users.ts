import { useQuery, useQueryClient } from "@tanstack/react-query";

import { getJson, patchJson, postJson } from "./client";
import type { AdminUser, UserCreate, UserUpdate } from "./types";

export const USERS_KEY = ["users"] as const;

export function useUsers() {
  return useQuery({
    queryKey: USERS_KEY,
    queryFn: () => getJson<AdminUser[]>("/api/users"),
  });
}

export function useInvalidateUsers() {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: USERS_KEY });
}

export function createUser(body: UserCreate): Promise<AdminUser> {
  return postJson<AdminUser>("/api/users", body);
}

export function updateUser(id: string, body: UserUpdate): Promise<AdminUser> {
  return patchJson<AdminUser>(`/api/users/${id}`, body);
}
