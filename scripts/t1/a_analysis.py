"""İş Emri 2026-10-15T1 §A — LLM-free review of the 70 questions that pass under scorer v2.0.

Runs inside the backend container (`docker exec -i company-ai-backend-1 python - < this`);
reads `results/` + `seed_data/` only — no DB, no LLM. Writes `results/t1/a_analysis.json`:
which F0 rule touched which question (same field comparison as `scripts.rescore.changed_rules`)
and, per passed question, the generosity flags of classes (a)–(d) of the order.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from scripts import eval_lib
from seed_data.generator.validate_ledger import resolve_path

OLD_PATH = Path("results/s3_final_2026-10-14/results.json")
NEW_PATH = Path("results/s3_rescored/results.json")
OUT_PATH = Path("results/t1/a_analysis.json")
QUESTION_CHANGED = frozenset({"IZM-ISO-004", "GEN-HAL-004"})  # questions.json v13

# "names a document" phrasings outside eval_lib._NAMED_DOCUMENT_MARKERS (possessive/locative on
# an English or Turkish title: "Amendment 02'de", "Financial Model'e göre", "lisansında").
_EXTRA_NAMING = re.compile(
    r"(['’](?:a|e|ya|ye) göre|['’](?:de|da|nde|nda)\b|['’](?:ı|i|u|ü)n(?:de|da)\b|"
    r"raporu(?:na|nda)|belgesi(?:ne|nde)|sözleşmesi(?:ne|nde)|lisans(?:ın|ında))",
    re.IGNORECASE,
)


def _g2(reasons: list[str]) -> bool:
    return any(r.startswith("G2") and "sabit cümle" in r for r in reasons)


def _g3_unauthorised(reasons: list[str]) -> bool:
    return any("yetkisiz belge" in r for r in reasons)


def _g3_forbidden(reasons: list[str]) -> bool:
    return any("yasak kaynak" in r for r in reasons)


def changed_rules(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    rules: list[str] = []
    old_safety = list(old.get("safety_reasons") or [])
    new_safety = list(new.get("safety_reasons") or [])
    if _g2(old_safety) and not _g2(new_safety):
        rules.append("A1")
    if _g3_unauthorised(old_safety) and not _g3_unauthorised(new_safety):
        rules.append("A2")
    if old.get("value_check") == "fail" and new["value_check"] == "skipped":
        rules.append("A3")
    if (old.get("forbidden_sources_hit") and not new["forbidden_sources_hit"]) or (
        _g3_forbidden(old_safety) and not _g3_forbidden(new_safety)
    ):
        rules.append("A4")
    if (
        old.get("required_sources_missing")
        and not new["required_sources_missing"]
        and new["source_rule"] == "set"
    ):
        rules.append("A5")
    if new["id"] in QUESTION_CHANGED:
        rules.append("B")
    return rules


def flags_for(
    q: Any, n: dict[str, Any], catalog: eval_lib.DocumentCatalog, has_ledger_path: bool
) -> list[str]:
    cited = set(n["cited_titles"])
    req = list(q.required_sources)
    req_exact = bool(req) and all(r in cited for r in req)
    foreign_cited = [
        t
        for t in cited
        if q.expected_project and catalog.title_to_project.get(t) not in (None, q.expected_project)
    ]
    kind = (n.get("assist") or {}).get("kind")
    flags: list[str] = []
    # (a) value matched, but the source/project could be wrong
    if n["answered"] and n["value_check"] == "pass":
        if not req:
            flags.append("a:required_sources yok (kaynak hiç denetlenmedi)")
        elif n["source_rule"] == "set" and not req_exact:
            flags.append("a:beklenen belge değil, küme üyesi gösterildi")
        elif n["source_rule"] == "n/a":
            flags.append("a:kaynak kuralı n/a")
        if foreign_cited:
            flags.append(f"a:yabancı proje kaynağı {foreign_cited}")
        if n.get("foreign_project_listed"):
            flags.append("a:listede yabancı proje")
        if len(cited) >= 5:
            flags.append(f"a:çok kaynak ({len(cited)})")
    # (b) passed by the authoritative-set rule where the exact document might be expected
    if n["source_rule"] == "set":
        if not req_exact:
            flags.append("b:set kuralıyla geçti, required_sources tam gösterilmedi")
        if _EXTRA_NAMING.search(q.question) and not any(
            m in q.question.lower() for m in eval_lib._NAMED_DOCUMENT_MARKERS
        ):
            flags.append("b:soru belgeyi adıyla anıyor olabilir (14 işaret dışı kalıp)")
    # (c) passed on a clarifying question although a value was asked
    if (
        not n["answered"]
        and kind in ("clarify", "disambiguate")
        and (has_ledger_path or q.category != "ambiguous")
    ):
        ledger = "var" if has_ledger_path else "yok"
        flags.append(f"c:netleştirmeyle geçti (kategori {q.category}, ledger yolu {ledger})")
    # (d) a relaxed rule could hide a confident wrong answer
    if n["answered"] and n["value_check"] == "skipped":
        flags.append(f"d:cevap var, değer doğrulanmadı ({n['value_check_reason']})")
    if n["answered"] and n["safety_check"] != "pass":
        flags.append(f"d:G1 denetimi {n['safety_check']}")
    if n["answered"] and n["query_type"] != "DOCUMENT_QUERY":
        flags.append(f"d:G1 yalnız DOCUMENT_QUERY'de; bu {n['query_type']}")
    if (
        not n["answered"]
        and q.expect_no_answer
        and eval_lib._FACT_CHAR.search(n["answer_text"] or "")
    ):
        flags.append("d:cevapsız yanıt metninde rakam/tarih var")
    if n["format_check"] == "fail":
        flags.append(f"d:F-8 biçim hatası puana girmiyor ({n['format_check_reason']})")
    return flags


def expected_raw(ea: Any, raws: dict[str, Any]) -> list[str]:
    """The ledger value behind `expected_answer`, as text, for the controller sheet — also
    when the scorer could not format it (value check skipped)."""
    out: list[str] = []
    for ref in ea if isinstance(ea, list) else [ea]:
        if isinstance(ref, str) and ref.startswith("ledger:"):
            file_key, _, path = ref.removeprefix("ledger:").partition(".")
            out.append(f"{path} = {resolve_path(raws[file_key], path)!r}")
        elif ref is not None:
            out.append(repr(ref))
    return out


def main() -> None:
    old_rows = json.loads(OLD_PATH.read_text(encoding="utf-8"))["questions"]
    new_rows = json.loads(NEW_PATH.read_text(encoding="utf-8"))["questions"]
    questions = {q.id: q for q in eval_lib.load_questions().questions}
    raws = eval_lib.load_ledger_raws()
    catalog = eval_lib.build_document_catalog(
        eval_lib.DEFAULT_MANIFEST, eval_lib.DEFAULT_EXCEL_MANIFEST
    )
    old_by_id = {r["id"]: r for r in old_rows}

    rule_rows: dict[str, list[list[Any]]] = {k: [] for k in ("A1", "A2", "A3", "A4", "A5", "B")}
    passed: dict[str, Any] = {}
    for n in new_rows:
        o = old_by_id[n["id"]]
        for rule in changed_rules(o, n):
            rule_rows[rule].append([n["id"], o["passed"], n["passed"]])
        if not n["passed"]:
            continue
        q = questions[n["id"]]
        expected = eval_lib.resolve_expected(q, raws)
        ea = q.expected_answer
        has_ledger_path = (isinstance(ea, str) and ea.startswith("ledger:")) or isinstance(ea, list)
        assist = n.get("assist") or {}
        cited = sorted(set(n["cited_titles"]))
        passed[n["id"]] = {
            "category": q.category,
            "user": q.ask_as_user,
            "question": q.question,
            "expected_project": q.expected_project,
            "expect_no_answer": q.expect_no_answer,
            "expect_assist": q.expect_assist,
            "expected_answer": ea,
            "expected_spellings": None if expected.skip else [list(g) for g in expected.required],
            "expected_raw": expected_raw(ea, raws),
            "required_sources": list(q.required_sources),
            "forbidden_sources": list(q.forbidden_sources),
            "answered": n["answered"],
            "answer_text": n["answer_text"],
            "cited_titles": cited,
            "cited_projects": sorted({catalog.title_to_project.get(t) or "—" for t in cited}),
            "source_rule": n["source_rule"],
            "authoritative_sources": n["authoritative_sources"],
            "source_hits": n["source_hits"],
            "value_check": n["value_check"],
            "value_check_reason": n["value_check_reason"],
            "safety_check": n["safety_check"],
            "query_type": n["query_type"],
            "assist_kind": assist.get("kind"),
            "assist_question": assist.get("question"),
            "assist_available": [str(i.get("title")) for i in (assist.get("available") or [])],
            "format_check": n["format_check"],
            "format_check_reason": n["format_check_reason"],
            "old_passed": o["passed"],
            "flags": flags_for(q, n, catalog, has_ledger_path),
        }
    out = {
        "rules": rule_rows,
        "set_rule_ids": [n["id"] for n in new_rows if n["source_rule"] == "set"],
        "passed": passed,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("written", len(passed))


if __name__ == "__main__":
    main()
