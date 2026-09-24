import { S } from "../lib/strings";

export function Spinner({ label = S.loading }: { label?: string }) {
  return (
    <div className="spinner" role="status">
      {label}
    </div>
  );
}
