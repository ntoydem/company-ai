"""P2C analysis (no LLM, no DB): joins results/p2c/<arm>/rep<k>/smoke_*_<letter>.json with
results/p2c/audit.jsonl (audit_log_id -> request_id) and results/p2c/<arm>/backend.log
(`question routed`, `excel plan`, `excel sql result …`, `llm call`) and writes
results/p2c/rows.jsonl + results/p2c/summary.md. Numbers only — no cause is inferred.

  python3 results/p2c/analyze_p2c.py"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

P2C = Path(__file__).resolve().parent
sys.path.insert(0, str(P2C.parents[1] / "scripts"))
from smoke_live import evaluate, load_spec, value_segment  # noqa: E402

PRICING = {"claude-haiku-5-5": (0.10, 0.50), "claude-sonnet-5-5": (2.0, 10.0)}
ARMS = ("base", "all")
PROJECT_OF = {"a": "ANK", "b": "ANK", "g": "ANK", "l": "ANK", "m": "ANK", "j": "YSV", "o": "YSV",
              "p": "YSV", "q": "YSV", "k": "BOZ", "r": "BOZ", "n": None}
# value that must appear (in the Excel half of a MIXED answer, else anywhere) for "doğru"
CORRECT = {"a": ["13.600.000"], "b": ["13.600.000"], "g": ["11.671.800"], "l": ["11.671.800"],
           "m": ["13 yıl"], "o": ["98.000", "98000"], "q": ["14.10.2026"],
           "r": ["178.571,43", "178571.43"]}
# another project's figure, anywhere in the answer
FOREIGN_FIGURE = {"j": ["11.671.800"], "k": ["1,37"], "o": ["11.671.800"], "p": ["11.671.800"],
                  "q": ["11.671.800"], "r": ["11.671.800", "1,37"], "n": []}
NOT_FOUND = ("bulamadım",)
EXCEL_HEADING = "Excel verisine göre"


def workbook_project(file: str) -> str:
    if file.startswith("Yesilova"):
        return "YSV"
    if file.startswith("Boztepe"):
        return "BOZ"
    return "ANK"


def excel_part(answer: str, query_type: str) -> str | None:
    if query_type == "DATA_QUERY":
        return answer
    if query_type == "MIXED_QUERY" and EXCEL_HEADING in answer:
        return answer.split(EXCEL_HEADING, 1)[1]
    return None


def load_logs() -> dict[str, dict]:
    by_rid: dict[str, dict] = defaultdict(lambda: {"plans": [], "excel_events": [], "llm": []})
    for log in P2C.glob("*/backend.log"):
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.startswith("{"):
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            rid = row.get("request_id")
            if not rid:
                continue
            msg = row.get("message")
            if msg == "question routed":
                by_rid[rid]["router"] = {k: row.get(k) for k in
                                         ("query_type", "reason", "document_question", "data_question")}
            elif msg == "excel plan":
                by_rid[rid]["plans"].append(row.get("plan"))
            elif msg and msg.startswith("excel "):
                by_rid[rid]["excel_events"].append(msg)
            elif msg == "llm call":
                by_rid[rid]["llm"].append((row.get("model"), row.get("tokens_in"), row.get("tokens_out")))
    return by_rid


def main() -> None:
    spec = {q["letter"]: q for q in load_spec(P2C / "spec.json")["questions"]}
    audit = {}
    for line in (P2C / "audit.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        audit[row["id"]] = row
    logs = load_logs()
    rows = []
    for arm in ARMS:
        for rep_dir in sorted((P2C / arm).glob("rep*"), key=lambda p: int(p.name[3:])):
            for f in sorted(rep_dir.glob("smoke_*_?.json")):
                letter = f.stem.rsplit("_", 1)[1]
                body = json.loads(f.read_text(encoding="utf-8"))
                answer, qtype = body.get("answer", ""), body.get("query_type")
                rid = (audit.get(body.get("audit_log_id")) or {}).get("request_id")
                log = logs.get(rid, {}) if rid else {}
                files = [s["file"] for s in body.get("excel_sources") or []]
                xpart = excel_part(answer, qtype)
                http_500 = "answer" not in body
                # a/b/g/l: like smoke (Excel half of a MIXED answer); others: the whole answer
                segment = value_segment(answer, qtype) if letter in ("a", "b", "g", "l") else answer
                correct = None
                if letter in CORRECT:
                    correct = any(v in segment for v in CORRECT[letter])
                foreign_wb = PROJECT_OF[letter] is not None and any(
                    workbook_project(x) != PROJECT_OF[letter] for x in files)
                foreign_fig = any(v in answer for v in FOREIGN_FIGURE.get(letter, []))
                cost = sum(
                    (ti * PRICING[m][0] + to * PRICING[m][1]) / 1e6
                    for m, ti, to in log.get("llm", []) if m in PRICING)
                rows.append({
                    "arm": arm, "rep": int(rep_dir.name[3:]), "letter": letter,
                    "question": spec[letter]["question"], "query_type": qtype,
                    "answered": body.get("answered"),
                    "http_500": http_500,
                    "smoke_pass": not http_500 and not evaluate(spec[letter]["expect"], 200, body),
                    "correct": correct,
                    "excel_files": files,
                    "excel_correct": (None if letter not in ("o", "q", "r") else
                                      bool(xpart and files and any(v in xpart for v in CORRECT[letter]))),
                    "excel_not_found": bool(xpart and any(n in xpart for n in NOT_FOUND)),
                    "foreign_workbook": foreign_wb, "foreign_figure": foreign_fig,
                    "router": log.get("router"), "plans": log.get("plans", []),
                    "excel_events": log.get("excel_events", []),
                    "llm_calls": len(log.get("llm", [])), "cost_usd": round(cost, 6),
                    "request_id": rid, "file": str(f.relative_to(P2C)),
                })
    with open(P2C / "rows.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    def short(c: Counter) -> str:
        names = {"DOCUMENT_QUERY": "DOC", "DATA_QUERY": "DATA", "MIXED_QUERY": "MIX"}
        return " ".join(f"{names.get(k, k)} {v}" for k, v in c.most_common())

    lines = ["| Soru | Kol | N | Router | Excel kaynağı | Doğru | Excel'den doğru | Smoke geçti "
             "| Excel 'bulamadım' | HTTP 500 | Başka proje (workbook / rakam) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for letter in spec:
        for arm in ARMS:
            sel = [r for r in rows if r["arm"] == arm and r["letter"] == letter]
            if not sel:
                continue
            n = len(sel)
            wb = Counter(re.sub(r"\.xlsx$", "", x) for r in sel for x in sorted(set(r["excel_files"])))
            wb_txt = ", ".join(f"{k} {v}" for k, v in wb.most_common()) or "—"
            corr = sum(1 for r in sel if r["correct"]) if letter in CORRECT else None
            lines.append(
                f"| {letter} | {arm} | {n} | {short(Counter(r['query_type'] for r in sel))} | {wb_txt} "
                f"| {'—' if corr is None else f'{corr}/{n}'} "
                f"| {'—' if letter not in ('o', 'q', 'r') else str(sum(1 for r in sel if r['excel_correct'])) + '/' + str(n)} "
                f"| {sum(r['smoke_pass'] for r in sel)}/{n} "
                f"| {sum(r['excel_not_found'] for r in sel)}/{n} | {sum(r['http_500'] for r in sel)} "
                f"| {sum(r['foreign_workbook'] for r in sel)} / {sum(r['foreign_figure'] for r in sel)} |")
    total = {}
    for arm in ARMS:
        usd = 0.0
        for line in (P2C / arm / "backend.log").read_text(encoding="utf-8").splitlines():
            if '"llm call"' in line:
                row = json.loads(line)
                if row.get("request_id") and row.get("model") in PRICING:
                    m = PRICING[row["model"]]
                    usd += (row["tokens_in"] * m[0] + row["tokens_out"] * m[1]) / 1e6
        total[arm] = usd
    lines += ["", "Maliyet (backend.log, request_id'li bütün llm call satırları): "
              + ", ".join(f"{a} ${c:.4f}" for a, c in total.items())
              + f", toplam ${sum(total.values()):.4f}; satır {len(rows)}"]
    (P2C / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
