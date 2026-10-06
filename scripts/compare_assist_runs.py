"""ADR-027: lay a flag-off and a flag-on eval run side by side — per question, the exact
`answer` text the user saw and the `assist` block (not just scores). For Tansu.

    python -m scripts.compare_assist_runs <off_results.json> <on_results.json> [--ids a,b]

Both files are `results.json` from `scripts/run_eval.py` (single-pass mode) or the
`consistency_*.json` list from `--repeat` mode (first repetition of each id is used).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _rows(path: Path) -> dict[str, dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):  # results.json: the per-question list sits under one key
        items = next(
            v
            for v in data.values()
            if isinstance(v, list) and v and isinstance(v[0], dict) and "id" in v[0]
        )
    else:  # consistency_*.json: a flat list of repetitions
        items = data
    out: dict[str, dict[str, Any]] = {}
    for item in items:
        if item["id"] not in out:  # consistency mode: keep the first repetition
            out[item["id"]] = item
    return out


def _assist_text(assist: dict[str, Any] | None) -> str:
    if not assist:
        return "—"
    parts = [f"**{assist.get('kind')}**"]
    if assist.get("question"):
        parts.append(f"Soru: {assist['question']}")
    if assist.get("unmatched_terms"):
        parts.append("Eşleşmeyen: " + ", ".join(assist["unmatched_terms"]))
    if assist.get("candidate_terms"):
        parts.append("Yakın terimler: " + ", ".join(assist["candidate_terms"]))
    if assist.get("available"):
        titles = [
            f"{a['title']}" + (f" (s.{a['page_number']})" if a.get("page_number") else "")
            for a in assist["available"]
        ]
        parts.append("Elimde: " + "; ".join(titles))
    return "<br>".join(parts)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", "<br>")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("off", type=Path)
    parser.add_argument("on", type=Path)
    parser.add_argument("--ids", default=None)
    args = parser.parse_args(argv)
    off, on = _rows(args.off), _rows(args.on)
    ids = args.ids.split(",") if args.ids else sorted(set(off) | set(on))
    lines = [
        "| Soru | Bayrak KAPALI — kullanıcıya giden metin "
        "| Bayrak AÇIK — kullanıcıya giden metin | AÇIK — assist bloğu |",
        "|---|---|---|---|",
    ]
    for qid in ids:
        a, b = off.get(qid), on.get(qid)
        question = (a or b or {}).get("question", qid)
        off_text = _cell(a["answer_text"]) if a else "—"
        on_text = _cell(b["answer_text"]) if b else "—"
        on_assist = _cell(_assist_text(b.get("assist"))) if b else "—"
        lines.append(f"| **{qid}**<br>{_cell(question)} | {off_text} | {on_text} | {on_assist} |")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
