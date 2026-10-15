"""İş Emri 2026-10-15F0 E — re-score a finished eval run with the *current* scorer, LLM-free.

Input: a run directory's `results.json` (the raw answers as given) plus the run's audit rows
(`audit_log` export, one JSON object per line — `logs/s3_audit.jsonl`), joined 1:1 in run
order. Output: a fresh `results.json`/`results.md` under the new scorer, `rescore_diff.md`
(before/after, which question changed under which rule), optional `cost.json` from the
backend `llm call` log, and `kontrolor_20.md` (a seeded random sample for the controller's
independent scoring).

Run inside the backend container of the *eval* project (the G1 grounding text and the G3
visibility come from that DB — never the live one):

    python -m scripts.rescore --results results/s3_final_2026-10-14 \
        --audit logs/s3_audit.jsonl --llm-log logs/s3_eval_backend.log --out results/s3_rescored

`--no-db` skips the DB (safety checks "skipped") — a local dry run only, never a baseline.
"""

from __future__ import annotations

import argparse
import datetime
import json
import random
import sys
from pathlib import Path
from typing import Any

from scripts import eval_lib
from scripts.eval_lib import AskOutcome, QuestionResult

CONTROLLER_SEED = 20261015
RULE_LABELS = {
    "A1": "G2 — yalnız netleştirme sorusu sabit cümle istemez",
    "A2": "G3 görünürlük DB'den (finans_mudur)",
    "A3": "expect_no_answer + expect_assist → değer kontrolü atlanır",
    "A4": "yasak kaynak belge kimliğiyle (tür eşleşmesi kalktı)",
    "A5": "kaynak beklentisi: yetkili kaynak kümesi",
    "B": "questions.json v13 (IZM-ISO-004 / GEN-HAL-004)",
}


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rescore")
    parser.add_argument("--results", type=Path, required=True, help="run dir with results.json")
    parser.add_argument("--audit", type=Path, required=True, help="audit rows, JSON lines")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--questions", type=Path, default=eval_lib.DEFAULT_QUESTIONS)
    parser.add_argument("--master", type=Path, default=eval_lib.DEFAULT_MASTER)
    parser.add_argument("--manifest", type=Path, default=eval_lib.DEFAULT_MANIFEST)
    parser.add_argument("--llm-log", type=Path, default=None, help="backend JSON log (A7)")
    parser.add_argument("--controller-sample", type=int, default=20)
    parser.add_argument("--seed", type=int, default=CONTROLLER_SEED)
    parser.add_argument("--no-db", action="store_true", help="dry run: no grounding/visibility")
    return parser


# ---------------------------------------------------------------- reconstruction


def load_audit_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    rows.sort(key=lambda r: r["timestamp"])
    return rows


def align(
    old_rows: list[dict[str, Any]], audit_rows: list[dict[str, Any]]
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run order == audit order (one `/api/ask` per question, sequential). Every pair must
    agree on question text and answer text, else the join is wrong and we stop."""
    if len(old_rows) != len(audit_rows):
        raise SystemExit(f"{len(old_rows)} results vs {len(audit_rows)} audit rows")
    pairs = []
    for i, (old, audit) in enumerate(zip(old_rows, audit_rows, strict=True)):
        if old["question"] != audit["question"] or old["answer_text"] != audit["answer"]:
            raise SystemExit(f"row {i} ({old['id']}): results.json and audit row disagree")
        pairs.append((old, audit))
    return pairs


def outcome_from(old: dict[str, Any], audit: dict[str, Any]) -> AskOutcome:
    # The audit row keeps document cards (`kind: document`, with title/page) and Excel cells
    # (`kind: excel`, with file/sheet/range) in one `sources` list; `/api/ask` returns them
    # as `sources` and `excel_sources` — rebuild that split.
    sources = [s for s in audit.get("sources") or [] if s.get("kind", "document") == "document"]
    excel = [s for s in audit.get("sources") or [] if s.get("kind") == "excel"]
    files = {str(f) for f in audit.get("excel_files_used") or []}
    files |= {str(s["file"]) for s in excel if s.get("file")}
    return AskOutcome(
        answered=bool(old["answered"]),
        answer_text=old["answer_text"],
        cited_titles=tuple(str(s["title"]) for s in sources),
        cited_files=tuple(sorted(files)),
        query_type=audit.get("query_type") or old.get("query_type"),
        model=old.get("model"),
        tokens_in=int(old.get("tokens_in") or 0),
        tokens_out=int(old.get("tokens_out") or 0),
        latency_ms=int(old.get("latency_ms") or 0),
        request_id=audit.get("request_id"),
        cited_pages=tuple(
            (str(s["document_id"]), int(s["page_number"]))
            for s in sources
            if s.get("document_id") is not None and s.get("page_number") is not None
        ),
        assist=old.get("assist") if old.get("assist") is not None else audit.get("assist"),
        retrieved_document_ids=tuple(str(i) for i in audit.get("documents_retrieved") or []),
        audit_log_id=str(audit["id"]) if audit.get("id") else None,
        router_fallback=bool(old.get("router_fallback")),
    )


# ---------------------------------------------------------------- attribution


def _g2_flag(reasons: list[str]) -> bool:
    return any(r.startswith("G2") and "sabit cümle" in r for r in reasons)


def _g3_unauthorised(reasons: list[str]) -> bool:
    return any("yetkisiz belge" in r for r in reasons)


def _g3_forbidden(reasons: list[str]) -> bool:
    return any("yasak kaynak" in r for r in reasons)


def changed_rules(old: dict[str, Any], new: QuestionResult, question_changed: bool) -> list[str]:
    """Which F0 rule(s) explain the difference between the old row and the new result —
    derived from the per-check fields, not guessed."""
    rules: list[str] = []
    old_safety = list(old.get("safety_reasons") or [])
    new_safety = list(new.safety_reasons)
    if _g2_flag(old_safety) and not _g2_flag(new_safety):
        rules.append("A1")
    if _g3_unauthorised(old_safety) and not _g3_unauthorised(new_safety):
        rules.append("A2")
    if old.get("value_check") == "fail" and new.value_check == "skipped":
        rules.append("A3")
    if (old.get("forbidden_sources_hit") and not new.forbidden_sources_hit) or (
        _g3_forbidden(old_safety) and not _g3_forbidden(new_safety)
    ):
        rules.append("A4")
    if (
        old.get("required_sources_missing")
        and not new.required_sources_missing
        and new.source_rule == "set"
    ):
        rules.append("A5")
    if question_changed:
        rules.append("B")
    return rules


def failure_reasons(r: QuestionResult) -> list[str]:
    reasons = []
    if not r.answered_ok:
        reasons.append(f"answered={r.answered}, beklenen {not r.expect_no_answer}")
    if r.required_sources_missing:
        if r.source_rule == "set":
            reasons.append(f"kaynak kümede değil (küme {list(r.authoritative_sources)})")
        else:
            reasons.append(f"eksik kaynak {list(r.required_sources_missing)}")
    if r.forbidden_sources_hit:
        reasons.append(f"yasak kaynak {list(r.forbidden_sources_hit)}")
    if r.value_check == "fail":
        reasons.append("beklenen değer metinde yok")
    if r.phrase_check == "fail":
        reasons.append(f"ifade: {r.phrase_check_reason}")
    if r.safety_check == "fail":
        reasons.append("güvenlik: " + "; ".join(r.safety_reasons))
    if r.assist_check == "fail":
        reasons.append(f"assist: {r.assist_check_reason}")
    if r.discovery_check == "fail":
        reasons.append(f"discovery: {r.discovery_check_reason}")
    return reasons


# ---------------------------------------------------------------- rendering


def render_diff(
    old_report: dict[str, Any],
    new_report: eval_lib.EvalReport,
    rows: list[tuple[dict[str, Any], QuestionResult, list[str]]],
    source_sets: dict[str, eval_lib.SourceExpectation],
    required_by_id: dict[str, list[str]],
) -> str:
    old_pass = sum(1 for q in old_report["questions"] if q["passed"])
    new_pass = sum(1 for r in new_report.results if r.passed)
    n = len(new_report.results)
    lines = [
        f"# Yeniden puanlama — {old_report.get('model')} ({old_report.get('date')}) → "
        f"puanlayıcı v{eval_lib.SCORER_VERSION}",
        "",
        f"**Önce {old_pass}/{n} → sonra {new_pass}/{n}** (LLM çağrısı yok; aynı ham cevaplar).",
        "",
        "## Kategori tablosu (önce → sonra)",
        "",
        "| Kategori | Eşik | Önce | Sonra | Eşik |",
        "|---|---|---|---|---|",
    ]
    old_cats = {c["category"]: c for c in old_report["categories"]}
    for c in new_report.categories:
        o = old_cats.get(c.category, {})
        mark = "✅" if c.meets_threshold else "❌"
        before = f"{o.get('passed', '?')}/{o.get('evaluated', '?')}"
        lines.append(
            f"| {c.category} | ≥%{c.threshold_pct:g} | {before}"
            f" | {c.passed}/{c.evaluated} | {mark} |"
        )
    lines.append(
        f"| **TOPLAM** | ≥%75 | **{old_pass}/{n}** | **{new_pass}/{n}** | "
        f"{'✅' if n and 100.0 * new_pass / n >= 75 else '❌'} |"
    )
    old_safety_fail = sum(1 for q in old_report["questions"] if q["safety_check"] == "fail")
    new_safety_ok = new_report.safety_evaluated - len(new_report.safety_failed)
    lines += [
        "",
        f"Güvenlik G1–G3: önce {n - old_safety_fail}/{n} → sonra "
        f"{new_safety_ok}/{new_report.safety_evaluated}",
        "",
        "## Değişen sorular (hangi madde)",
        "",
        "| Soru | Kategori | Önce | Sonra | Madde | Not |",
        "|---|---|---|---|---|---|",
    ]
    rule_counts: dict[str, int] = {}
    for old, new, rules in rows:
        if bool(old["passed"]) == new.passed and not rules:
            continue
        for rule in rules:
            rule_counts[rule] = rule_counts.get(rule, 0) + 1
        flip = f"{'✅' if old['passed'] else '❌'} | {'✅' if new.passed else '❌'}"
        note = "" if new.passed else "; ".join(failure_reasons(new))
        lines.append(f"| {new.id} | {new.category} | {flip} | {', '.join(rules) or '—'} | {note} |")
    lines += [
        "",
        "Madde başına etkilenen soru: "
        + ", ".join(f"{k} ({RULE_LABELS[k]}): {v}" for k, v in sorted(rule_counts.items())),
    ]
    lines += [
        "",
        "## Hâlâ kalan kayıplar (huni girdisi)",
        "",
        "| Soru | Kategori | Sebep |",
        "|---|---|---|",
    ]
    for _, new, _rules in rows:
        if not new.passed:
            lines.append(f"| {new.id} | {new.category} | {'; '.join(failure_reasons(new))} |")
    lines += [
        "",
        "## Yetkili kaynak kümesi — kontrolör onayına (A5)",
        "",
        "Türetme: `required_sources` (tür → sorunun kendi projesinin canlı belgeleri) + "
        "ledger'da `key_facts` ile aynı yolu taşıyan belgeler; `draft` hiç, `superseded` yalnız "
        'canlı taşıyıcı yoksa; belgeyi adıyla soran soru ("… raporuna göre") tam belge şartında.',
        "",
        "| Soru | Kural | Küme | Gösterilen | Not |",
        "|---|---|---|---|---|",
    ]
    for qid in ("ANK-FIN-005", "ANK-FIN-011", "ANK-FIN-014", "ANK-OPS-003", "IZM-DEV-007"):
        se = source_sets.get(qid)
        new = next((r for _, r, _ in rows if r.id == qid), None)
        if se is None or new is None:
            continue
        rule = "tam belge" if se.strict else "küme"
        members = sorted(se.titles) if not se.strict else required_by_id.get(qid, [])
        verdict = "✅" if new.passed else "❌ " + "; ".join(failure_reasons(new))
        cited = list(new.cited_titles)
        lines.append(f"| {qid} | {rule} ({se.derivation}) | {members} | {cited} | {verdict} |")
    return "\n".join(lines) + "\n"


def render_controller(
    sample: list[tuple[dict[str, Any], QuestionResult, list[str]]], seed: int
) -> str:
    lines = [
        "# Kontrolör örneklemi — 20 soru (bağımsız puanlama için)",
        "",
        f"Seçim: `random.Random({seed}).sample(ids, 20)` — soru kimlikleri sıralı listeden; "
        "cevap/kaynak metni S3 ham sonucundan aynen; puan ve gerekçe yeni puanlayıcıdan.",
        "",
    ]
    for old, new, rules in sample:
        assist = new.assist or {}
        available = [str(i.get("title")) for i in (assist.get("available") or [])]
        lines += [
            f"## {new.id} ({new.category}, kullanıcı `{new.ask_as_user}`)",
            "",
            f"**Soru:** {new.question}",
            f"**Beklenti:** {'cevap yok' if new.expect_no_answer else 'cevap var'}"
            + (
                f"; kaynak kümesi {list(new.authoritative_sources)}"
                if new.authoritative_sources
                else ""
            ),
            "",
            "**Cevap (aynen):**",
            "",
            "```",
            new.answer_text,
            "```",
            "",
            f"**Kaynaklar:** {list(new.cited_titles) or '—'}"
            + (
                f" · assist `{assist.get('kind')}`: {assist.get('question')!r}; liste {available}"
                if assist
                else ""
            ),
            f"**Puan:** önce {'✅' if old['passed'] else '❌'} → sonra "
            f"{'✅' if new.passed else '❌'}" + (f" (madde {', '.join(rules)})" if rules else ""),
            f"**Gerekçe:** {'; '.join(failure_reasons(new)) or 'tüm kontroller geçti: '}"
            + (
                f"value={new.value_check}, kaynak kuralı={new.source_rule}, "
                f"güvenlik={new.safety_check}, assist={new.assist_check}, "
                f"discovery={new.discovery_check}"
                if new.passed
                else ""
            ),
            "",
            "**Kontrolör kararı:** ☐ katılıyorum ☐ katılmıyorum — not: ",
            "",
        ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- main


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    old_report = json.loads((args.results / "results.json").read_text(encoding="utf-8"))
    audit_rows = load_audit_rows(args.audit)
    pairs = align(old_report["questions"], audit_rows)

    question_set = eval_lib.load_questions(args.questions)
    questions = {q.id: q for q in question_set.questions + question_set.held_out}
    raws = eval_lib.load_ledger_raws(args.master)
    catalog = eval_lib.build_document_catalog(args.manifest)
    # The expectations the old run was scored with, to tell a question-set change (B) apart.
    old_expectations = {
        q["id"]: (q["expect_no_answer"], tuple(q.get("required_sources_missing") or ()))
        for q in old_report["questions"]
    }

    safety_index = None
    if not args.no_db:
        from scripts.run_eval import SafetyIndex  # DB-backed; imported only when used

        safety_index = SafetyIndex()

    rows: list[tuple[dict[str, Any], QuestionResult, list[str]]] = []
    results: list[QuestionResult] = []
    source_sets: dict[str, eval_lib.SourceExpectation] = {}
    for old, audit in pairs:
        question = questions[old["id"]]
        outcome = outcome_from(old, audit)
        expected = eval_lib.resolve_expected(question, raws)
        sources_expected = eval_lib.authoritative_sources(question, raws, catalog)
        source_sets[question.id] = sources_expected
        safety = safety_index.context(question.ask_as_user, outcome) if safety_index else None
        result = eval_lib.score_question(
            question, expected, catalog, outcome, safety, sources_expected=sources_expected
        )
        question_changed = old_expectations[question.id][0] != question.expect_no_answer
        rows.append((old, result, changed_rules(old, result, question_changed)))
        results.append(result)

    today = datetime.date.today().isoformat()
    report = eval_lib.build_report(
        results,
        model=f"{old_report.get('model')} (yeniden puanlama {today})",
        date_str=str(old_report.get("date")),
        demo_today=str(old_report.get("demo_today")),
        embeddings_enabled=bool(old_report.get("embeddings_enabled")),
    )
    args.out.mkdir(parents=True, exist_ok=True)
    payload = eval_lib.report_to_json(report)
    payload["rescored_from"] = str(args.results)
    payload["rescored_at"] = today
    payload["visibility_resolved"] = safety_index.visibility.resolved if safety_index else None
    (args.out / "results.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (args.out / "results.md").write_text(eval_lib.render_markdown(report), encoding="utf-8")
    required_by_id = {q.id: list(q.required_sources) for q in questions.values()}
    diff = render_diff(old_report, report, rows, source_sets, required_by_id)
    (args.out / "rescore_diff.md").write_text(diff, encoding="utf-8")

    if args.llm_log is not None:
        from scripts.run_eval import cost_from_llm_log

        request_ids = [a["request_id"] for _, a in pairs if a.get("request_id")]
        tracker = cost_from_llm_log(
            args.llm_log.read_text(encoding="utf-8").splitlines(), request_ids
        )
        (args.out / "cost.json").write_text(
            json.dumps(tracker.summary(), indent=2, ensure_ascii=False), encoding="utf-8"
        )

    if args.controller_sample:
        ids = sorted(r.id for r in results)
        chosen = set(random.Random(args.seed).sample(ids, min(args.controller_sample, len(ids))))
        sample = [row for row in rows if row[1].id in chosen]
        (args.out / f"kontrolor_{len(sample)}.md").write_text(
            render_controller(sample, args.seed), encoding="utf-8"
        )

    print(diff)
    print(f"sonuçlar: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
