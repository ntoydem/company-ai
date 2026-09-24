import { ApiError } from "../api/client";
import { S } from "../lib/strings";

/** Renders any thrown value as a Turkish sentence + request id — never a stack trace or
 * raw JSON (SPEC_02 §13). */
export function ErrorBox({ error }: { error: unknown }) {
  if (!error) return null;
  const apiError = error instanceof ApiError ? error : null;
  const message = apiError ? apiError.message : S.errors.generic;
  return (
    <div className="error-box" role="alert">
      {message}
      {apiError && apiError.fieldErrors.length > 0 && (
        <ul>
          {apiError.fieldErrors.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      )}
      {apiError?.requestId && (
        <span className="rid">
          {S.errors.requestId}: {apiError.requestId}
        </span>
      )}
    </div>
  );
}
