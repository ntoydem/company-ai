"""P2C Aşama 1 driver (eval only): runs results/p2c/spec.json through scripts/smoke_live.py
against the eval backend, N passes for one arm; moves each pass's raw JSON to
results/p2c/<arm>/rep<k>/; stops before a pass when the logged LLM cost (all arms'
backend.log, request_id set) plus one worst-case pass would exceed the budget.

  python3 results/p2c/drive_p2c.py <arm> <first_rep> <last_rep> <base_url> [budget_usd]"""

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P2C = ROOT / "results" / "p2c"
PRICING = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0)}  # run_eval
WORST_PASS_USD = 0.25


def logged_cost() -> tuple[float, int, int]:
    """(USD, priced calls, unpriced calls) over every arm's backend.log."""
    usd, priced, unpriced = 0.0, 0, 0
    for log in P2C.glob("*/backend.log"):
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"llm call"' not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not row.get("request_id"):
                continue  # background metadata calls, reported separately
            price = PRICING.get(row.get("model") or "")
            if price is None:
                unpriced += 1
                continue
            usd += (row["tokens_in"] * price[0] + row["tokens_out"] * price[1]) / 1_000_000
            priced += 1
    return usd, priced, unpriced


def main() -> int:
    arm, first, last, base_url = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    budget = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
    if "localhost" in base_url or "8080" in base_url or "127.0.0.1" in base_url:
        print(f"REFUSED: {base_url} may be the live Caddy")
        return 2
    for rep in range(first, last + 1):
        usd, priced, unpriced = logged_cost()
        if usd + WORST_PASS_USD > budget:
            print(f"BUDGET STOP before {arm} rep{rep}: logged ${usd:.4f} + ${WORST_PASS_USD}")
            return 3
        started = time.time()
        out = subprocess.run(
            [sys.executable, "scripts/smoke_live.py", "--spec", "results/p2c/spec.json",
             "--env", "infra/.env.eval", "--base-url", base_url],
            cwd=ROOT, capture_output=True, text=True,
        )
        dest = P2C / arm / f"rep{rep}"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "smoke_stdout.txt").write_text(out.stdout + out.stderr, encoding="utf-8")
        for f in (ROOT / "logs").glob("smoke_*.json"):
            if f.stat().st_mtime >= started - 1:
                shutil.move(str(f), dest / f.name)
        summary = [ln for ln in out.stdout.splitlines() if "geçti" in ln]
        usd, priced, unpriced = logged_cost()
        print(f"{arm} rep{rep}: {summary[-1] if summary else 'no summary'} | "
              f"{len(list(dest.glob('smoke_*.json')))} files | cost ${usd:.4f} "
              f"({priced} priced, {unpriced} unpriced) | {time.time() - started:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
