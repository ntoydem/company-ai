import { useQuery } from "@tanstack/react-query";

import { getJson, patchJson, postJson } from "./client";
import type { Project, ProjectCreate, ProjectUpdate } from "./types";

export const PROJECTS_KEY = ["projects"] as const;

export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_KEY,
    queryFn: () => getJson<Project[]>("/api/projects"),
    staleTime: 60 * 1000,
  });
}

export function createProject(body: ProjectCreate): Promise<Project> {
  return postJson<Project>("/api/projects", body);
}

export function updateProject(id: string, body: ProjectUpdate): Promise<Project> {
  return patchJson<Project>(`/api/projects/${id}`, body);
}

/** `project_id` → display name; the list is small, so the join happens client-side. */
export function projectNameById(projects: Project[] | undefined): Map<string, string> {
  return new Map((projects ?? []).map((p) => [p.id, p.name]));
}
