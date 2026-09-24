import { S } from "../lib/strings";

/** Fired on any 401 outside the login call so `AuthProvider` can drop the session
 * (cookie expired after 8 h, user disabled, …). */
export const UNAUTHORIZED_EVENT = "company-ai:unauthorized";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly requestId: string | null,
    public readonly fieldErrors: string[] = [],
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface ErrorBody {
  detail?: unknown;
  request_id?: string | null;
}

interface ValidationItem {
  loc?: unknown[];
  msg?: string;
}

/** Backend error bodies are `{detail, request_id}`; `detail` is a Turkish string except
 * for 422, where it is `{message, errors}` (app/core/errors.py). Never shows raw JSON. */
function describeError(status: number, body: ErrorBody | null): {
  message: string;
  fieldErrors: string[];
} {
  const detail = body?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return { message: detail, fieldErrors: [] };
  }
  if (detail && typeof detail === "object") {
    const record = detail as { message?: unknown; errors?: unknown };
    const message = typeof record.message === "string" ? record.message : S.errors.generic;
    const errors = Array.isArray(record.errors) ? (record.errors as ValidationItem[]) : [];
    const fieldErrors = errors
      .map((item) => {
        const loc = Array.isArray(item.loc) ? item.loc.filter((p) => p !== "body").join(".") : "";
        return loc && item.msg ? `${loc}: ${item.msg}` : (item.msg ?? "");
      })
      .filter((line) => line.length > 0);
    return { message, fieldErrors };
  }
  return { message: status >= 500 ? S.errors.generic : S.errors.generic, fieldErrors: [] };
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { credentials: "same-origin", ...init });
  } catch {
    throw new ApiError(0, S.errors.network, null);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  let body: unknown = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = null;
    }
  }
  if (!response.ok) {
    const errorBody = (body ?? null) as ErrorBody | null;
    const { message, fieldErrors } = describeError(response.status, errorBody);
    if (response.status === 401 && !path.startsWith("/api/auth/login")) {
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    throw new ApiError(response.status, message, errorBody?.request_id ?? null, fieldErrors);
  }
  return body as T;
}

export function getJson<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function postJson<T>(path: string, data?: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: data === undefined ? undefined : { "content-type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
}

export function patchJson<T>(path: string, data: unknown): Promise<T> {
  return request<T>(path, {
    method: "PATCH",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(data),
  });
}

/** Multipart upload — the browser sets the boundary, so no content-type header here. */
export function postForm<T>(path: string, form: FormData): Promise<T> {
  return request<T>(path, { method: "POST", body: form });
}

export function queryString(params: Record<string, string | undefined | null>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value) search.set(key, value);
  }
  const encoded = search.toString();
  return encoded ? `?${encoded}` : "";
}
