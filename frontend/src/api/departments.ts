import { useQuery } from "@tanstack/react-query";

import { getJson } from "./client";
import type { Department } from "./types";

export const DEPARTMENTS_KEY = ["departments"] as const;

export function useDepartments() {
  return useQuery({
    queryKey: DEPARTMENTS_KEY,
    queryFn: () => getJson<Department[]>("/api/departments"),
    staleTime: 5 * 60 * 1000,
  });
}
