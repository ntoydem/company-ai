"""N1 — score one run's raw answers with v2.0 (all V21 flags off) and v2.1 (defaults)."""

import dataclasses
import json
import sys
from pathlib import Path

from scripts import eval_lib
from scripts.rescore import align, load_audit_rows, outcome_from
from scripts.run_eval import SafetyIndex

run, audit, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
old = json.loads((run / "results.json").read_text(encoding="utf-8"))
pairs = align(old["questions"], load_audit_rows(audit))
qs = eval_lib.load_questions(eval_lib.DEFAULT_QUESTIONS)
questions = {q.id: q for q in qs.questions + qs.held_out}
raws = eval_lib.load_ledger_raws(eval_lib.DEFAULT_MASTER)
catalog = eval_lib.build_document_catalog(eval_lib.DEFAULT_MANIFEST)
safety_index = SafetyIndex()
v20 = eval_lib.ScorerFlags(**{f.name: False for f in dataclasses.fields(eval_lib.ScorerFlags)})
res = {}
for label, flags in (("v20", v20), ("v21", eval_lib.DEFAULT_FLAGS)):
    per = {}
    for o, a in pairs:
        q = questions[o["id"]]
        outcome = outcome_from(o, a)
        r = eval_lib.score_question(
            q,
            eval_lib.resolve_expected(q, raws, flags),
            catalog,
            outcome,
            safety_index.context(q.ask_as_user, outcome),
            eval_lib.authoritative_sources(q, raws, catalog),
            flags,
        )
        per[r.id] = {"passed": r.passed, "safety": r.safety_check}
    res[label] = per
    print(
        label,
        sum(v["passed"] for v in per.values()),
        "/",
        len(per),
        "safety_pass",
        sum(v["safety"] == "pass" for v in per.values()),
    )
out.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
