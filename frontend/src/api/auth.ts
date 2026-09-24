import { ApiError, getJson, postJson } from "./client";
import type { CurrentUser } from "./types";

export const ME_KEY = ["me"] as const;

/** The only source of truth for "am I logged in": the cookie is httpOnly, the app
 * never sees the JWT (ADR-003). 401 → not logged in, anything else is a real error. */
export async function fetchMe(): Promise<CurrentUser | null> {
  try {
    return await getJson<CurrentUser>("/api/auth/me");
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export function login(username: string, password: string): Promise<CurrentUser> {
  return postJson<CurrentUser>("/api/auth/login", { username, password });
}

export function logout(): Promise<void> {
  return postJson<void>("/api/auth/logout");
}
