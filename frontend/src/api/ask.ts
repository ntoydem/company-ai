import { postJson } from "./client";
import type { AskRequest, AskResponse } from "./types";

export function ask(body: AskRequest): Promise<AskResponse> {
  return postJson<AskResponse>("/api/ask", body);
}
