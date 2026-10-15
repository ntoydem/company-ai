"""Live smoke after a backend restart (İş Emri 2026-10-15A2L): the questions and expectations
in `seed_data/evaluation/smoke.json`, one attempt each, through Caddy. A row passes only when
the request is HTTP 200 **and** every expectation holds — "istek başarılı ≠ cevap doğru"
(Ortak Not 15.10 §5 ilke 5). Exit code 0 only when every row passes.

Passwords are read from `.env` inside this process and never printed or written. Raw answers
go to `logs/smoke_<stamp>_<letter>.json` (no secrets: the response bodies only) and a summary
table is printed.

Usage (repo root):  python scripts/smoke_live.py [--spec PATH] [--base-url URL] [--no-save]
"""

from __future__ import annotations

import argparse
import http.cookiejar
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SPEC = ROOT / "seed_data" / "evaluation" / "smoke.json"

# Must equal `app.services.ask_router.DATA_PART_HEADING` (asserted by the unit test): the
# Excel half of a MIXED answer starts here, and an expected *value* is looked for in that
# half, so a wrong engine figure is not rescued by the same number in the document half.
DATA_PART_HEADING = "Excel verisine göre:"

# F-8: thousands are grouped with a dot. "13,600,000" (two or more English groups) fails.
_EN_THOUSANDS = re.compile(r"(?<![\d.,])\d{1,3}(?:,\d{3}){2,}(?![\d])")
# G1: a clarifying question carries no digit, date, currency or percent (eval rule).
_FACT_TOKEN = re.compile(r"[0-9€$₺%]")
# A general-knowledge definition sentence (Ç-3) — never allowed in an unanswered reply.
_DEFINITION = re.compile(r"demektir|anlamına gel|ifade eder|olarak tanımlan", re.IGNORECASE)


def _tr_lower(text: str) -> str:
    """Turkish lowercase for substring checks: `str.casefold` turns İ into "i̇" (two code
    points) and I into "i", so "İmar" would never match "imar" and "ISO" would match "ıso"."""
    return text.replace("İ", "i").replace("I", "ı").lower()


ALLOWED_USERS = frozenset({"admin", "finans", "finans_mudur", "enerji", "yonetim", "hukuk"})
_EXPECT_TYPES: dict[str, type | tuple[type, ...]] = {
    "answered": bool,
    "value": str,
    "contains": list,
    "sources_min": int,
    "sources_empty": bool,
    "sources_projects": list,
    "answer_excludes": list,
    "response_excludes": list,
    "assist_kind": str,
    "assist_available_min": int,
    "unmatched_terms": list,
    "single_question": bool,
    "question_fact_free": bool,
    "no_definition": bool,
    "no_llm": bool,
}


# ------------------------------------------------------------------ spec


def load_spec(path: Path = DEFAULT_SPEC) -> dict[str, Any]:
    spec: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    validate_spec(spec)
    return spec


def validate_spec(spec: dict[str, Any]) -> None:
    """Raise `ValueError` on anything the evaluator would not understand — a typo in an
    expectation key must fail loudly, not silently pass the row."""
    questions = spec.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("spec.questions must be a non-empty list")
    letters: set[str] = set()
    for row in questions:
        for key in ("letter", "user", "question", "expect"):
            if key not in row:
                raise ValueError(f"row missing '{key}': {row}")
        if row["letter"] in letters:
            raise ValueError(f"duplicate letter {row['letter']!r}")
        letters.add(row["letter"])
        if row["user"] not in ALLOWED_USERS:
            raise ValueError(f"{row['letter']}: unknown user {row['user']!r}")
        if not isinstance(row["question"], str) or len(row["question"]) < 3:
            raise ValueError(f"{row['letter']}: question too short")
        expect = row["expect"]
        if not isinstance(expect, dict) or not expect:
            raise ValueError(f"{row['letter']}: expect must be a non-empty object")
        for key, value in expect.items():
            if key not in _EXPECT_TYPES:
                raise ValueError(f"{row['letter']}: unknown expectation {key!r}")
            if not isinstance(value, _EXPECT_TYPES[key]):
                raise ValueError(f"{row['letter']}: {key} must be {_EXPECT_TYPES[key]}")
        value = expect.get("value")
        if value is not None and _EN_THOUSANDS.search(value):
            raise ValueError(f"{row['letter']}: expected value must use F-8 grouping: {value}")


# ------------------------------------------------------------------ evaluation


def value_segment(answer: str, query_type: str | None) -> str:
    """Where an expected value must appear: the Excel half of a MIXED answer, else all."""
    if query_type == "MIXED_QUERY" and DATA_PART_HEADING in answer:
        return answer.split(DATA_PART_HEADING, 1)[1]
    return answer


def evaluate(expect: dict[str, Any], status: int, body: dict[str, Any]) -> list[str]:
    """Every failed expectation as one short reason; an empty list means the row passed."""
    failures: list[str] = []
    if status != 200:
        return [f"http {status}"]
    answer: str = body.get("answer") or ""
    answered = body.get("answered")
    sources: list[dict[str, Any]] = body.get("sources") or []
    assist: dict[str, Any] = body.get("assist") or {}
    question: str = assist.get("question") or ""
    query_type = body.get("query_type")

    if "answered" in expect and answered is not expect["answered"]:
        failures.append(f"answered={answered}, expected {expect['answered']}")
    if (value := expect.get("value")) is not None:
        segment = value_segment(answer, query_type)
        if value not in segment:
            failures.append(
                f"value {value!r} not in {'Excel part' if segment != answer else 'answer'}"
            )
    for needle in expect.get("contains", []):
        if needle not in answer:
            failures.append(f"missing {needle!r}")
    if en_grouping := _EN_THOUSANDS.search(answer):
        failures.append(f"F-8: English thousands grouping in answer: {en_grouping.group()!r}")
    if (minimum := expect.get("sources_min")) is not None and len(sources) < minimum:
        failures.append(f"sources={len(sources)}, expected ≥ {minimum}")
    if expect.get("sources_empty") and sources:
        failures.append(f"sources={len(sources)}, expected none")
    if (codes := expect.get("sources_projects")) is not None:
        foreign = sorted(
            {
                f"{s.get('project_code')}:{s.get('title')}"
                for s in sources
                if s.get("project_scope") != "group" and s.get("project_code") not in codes
            }
        )
        if foreign:
            failures.append(f"foreign-project sources: {foreign}")
    for needle in expect.get("answer_excludes", []):
        if _tr_lower(needle) in _tr_lower(answer):
            failures.append(f"answer mentions {needle!r}")
    if excludes := expect.get("response_excludes"):
        blob = _tr_lower(json.dumps(body, ensure_ascii=False))
        for needle in excludes:
            if _tr_lower(needle) in blob:
                failures.append(f"response mentions {needle!r}")
    if (kind := expect.get("assist_kind")) is not None and assist.get("kind") != kind:
        failures.append(f"assist.kind={assist.get('kind')!r}, expected {kind!r}")
    if (minimum := expect.get("assist_available_min")) is not None:
        available = assist.get("available") or []
        if len(available) < minimum:
            failures.append(f"assist.available={len(available)}, expected ≥ {minimum}")
    if (terms := expect.get("unmatched_terms")) is not None and (
        assist.get("unmatched_terms") or []
    ) != terms:
        failures.append(f"unmatched_terms={assist.get('unmatched_terms')!r}, expected {terms!r}")
    if expect.get("single_question"):
        if not question:
            failures.append("no assist.question")
        if answer.count("?") != 1:
            failures.append(f"{answer.count('?')} question marks in answer, expected exactly 1")
    if expect.get("question_fact_free") and _FACT_TOKEN.search(question):
        failures.append(f"assist.question carries a fact token: {question!r}")
    if expect.get("no_definition") and (hit := _DEFINITION.search(answer)):
        failures.append(f"definition sentence in answer: {hit.group()!r}")
    if expect.get("no_llm") and (
        body.get("model") is not None or body.get("tokens_in") or body.get("tokens_out")
    ):
        failures.append(
            f"LLM was called: model={body.get('model')!r} "
            f"tokens={body.get('tokens_in')}/{body.get('tokens_out')}"
        )
    return failures


# ------------------------------------------------------------------ HTTP


def read_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            env[key.strip()] = value.strip()
    return env


def password_for(user: str, env: dict[str, str]) -> tuple[str, str]:
    """(username, password) — the admin account has its own `.env` lines."""
    if user == "admin":
        return env.get("ADMIN_USERNAME", "admin"), env["ADMIN_PASSWORD"]
    return user, env["DEMO_USER_PASSWORD"]


def post_json(
    opener: urllib.request.OpenerDirector, url: str, body: dict[str, Any], timeout: float
) -> tuple[int, dict[str, Any]]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode())
        except Exception:  # noqa: BLE001
            payload = {}
        return exc.code, payload if isinstance(payload, dict) else {}
    except (urllib.error.URLError, TimeoutError) as exc:
        return 0, {"error": str(exc)}


@dataclass
class RowResult:
    letter: str
    user: str
    question: str
    http: int
    query_type: str | None
    answered: bool | None
    elapsed_s: float
    audit_log_id: str | None
    failures: list[str] = field(default_factory=list)
    body: dict[str, Any] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.failures


def run_row(row: dict[str, Any], base_url: str, env: dict[str, str], timeout: float) -> RowResult:
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    username, password = password_for(row["user"], env)
    status, _ = post_json(
        opener, f"{base_url}/api/auth/login", {"username": username, "password": password}, 30
    )
    if status != 200:
        return RowResult(
            row["letter"],
            row["user"],
            row["question"],
            status,
            None,
            None,
            0.0,
            None,
            failures=[f"login failed (http {status})"],
        )
    t0 = time.perf_counter()
    status, body = post_json(opener, f"{base_url}/api/ask", {"question": row["question"]}, timeout)
    elapsed = round(time.perf_counter() - t0, 1)
    return RowResult(
        letter=row["letter"],
        user=row["user"],
        question=row["question"],
        http=status,
        query_type=body.get("query_type"),
        answered=body.get("answered"),
        elapsed_s=elapsed,
        audit_log_id=body.get("audit_log_id"),
        failures=evaluate(row["expect"], status, body),
        body=body,
    )


def render_table(results: list[RowResult]) -> str:
    lines = [
        "| # | user | http | type | answered | s | sonuç |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in results:
        verdict = "✅" if r.passed else "❌ " + "; ".join(r.failures)
        lines.append(
            f"| {r.letter} | {r.user} | {r.http} | {r.query_type or '-'} | {r.answered} | "
            f"{r.elapsed_s} | {verdict} |"
        )
    passed = sum(r.passed for r in results)
    lines.append(f"\n{passed}/{len(results)} geçti")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    parser.add_argument("--env", type=Path, default=ROOT / ".env")
    parser.add_argument("--base-url", default=None, help="default http://localhost:$CADDY_PORT")
    parser.add_argument("--timeout", type=float, default=180.0, help="seconds per /api/ask")
    parser.add_argument("--no-save", action="store_true", help="do not write logs/smoke_*.json")
    args = parser.parse_args(argv)

    spec = load_spec(args.spec)
    env = read_env(args.env)
    base_url = args.base_url or f"http://localhost:{env.get('CADDY_PORT', '8080')}"
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M")
    out_dir = ROOT / "logs"
    if not args.no_save:
        out_dir.mkdir(exist_ok=True)

    results: list[RowResult] = []
    for row in spec["questions"]:
        result = run_row(row, base_url, env, args.timeout)
        results.append(result)
        print(
            f"{result.letter} {result.user} http={result.http} type={result.query_type} "
            f"answered={result.answered} {result.elapsed_s}s "
            f"{'OK' if result.passed else 'FAIL: ' + '; '.join(result.failures)}",
            flush=True,
        )
        if not args.no_save:
            (out_dir / f"smoke_{stamp}_{result.letter}.json").write_text(
                json.dumps(result.body, ensure_ascii=False, indent=1), encoding="utf-8"
            )
    if not args.no_save:
        summary = [
            {k: v for k, v in vars(r).items() if k != "body"} | {"passed": r.passed}
            for r in results
        ]
        (out_dir / f"smoke_{stamp}_summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8"
        )
    print()
    print(render_table(results))
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
