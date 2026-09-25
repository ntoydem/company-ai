"""Phase 4.1 — `questions.json` -> real `/api/ask` calls -> `seed_data/evaluation/results/
<model>_<date>/`. Network/CLI layer; pure scoring lives in `scripts/eval_lib.py` (covered
by `backend/tests/test_eval_lib.py` without a running server).

Usage (inside the backend container, `postgres`+`backend` already up — see `make eval`):
    python -m scripts.run_eval [--min-interval-s 13] [--model-label gemini-3.5-flash]
"""

from __future__ import annotations

import argparse
import datetime
import json
import logging
import re
import sys
import time
from collections import Counter
from pathlib import Path

import httpx

from app.core.config import get_settings
from scripts import eval_lib
from scripts.eval_lib import AskOutcome, QuestionResult

log = logging.getLogger("run_eval")

_RETRYABLE_STATUS = 503


class RateLimiter:
    """Enforces a minimum gap between `/api/ask` calls, shared across every demo-user
    session (Gemini free tier is ~5 req/min *total*, not per session) — plan §3."""

    def __init__(self, min_interval_s: float) -> None:
        self._min_interval_s = min_interval_s
        self._last_at: float | None = None

    def wait(self) -> None:
        if self._last_at is not None:
            remaining = self._min_interval_s - (time.monotonic() - self._last_at)
            if remaining > 0:
                time.sleep(remaining)
        self._last_at = time.monotonic()


class EvalSession:
    """One logged-in `httpx.Client` per demo user (`ask_as_user`); logs in once, reuses
    the cookie for every question that user asks."""

    def __init__(self, base_url: str, username: str, password: str, *, timeout_s: float) -> None:
        self._client = httpx.Client(base_url=base_url, timeout=timeout_s)
        response = self._client.post(
            "/api/auth/login", json={"username": username, "password": password}
        )
        response.raise_for_status()

    def post_ask(self, question: str) -> httpx.Response:
        return self._client.post("/api/ask", json={"question": question})

    def close(self) -> None:
        self._client.close()


def ask_with_retry(
    session: EvalSession,
    rate_limiter: RateLimiter,
    question_text: str,
    *,
    max_retries: int,
    retry_base_delay_s: float,
) -> AskOutcome:
    started = time.monotonic()
    attempt = 0
    while True:
        rate_limiter.wait()
        transport_error: str | None = None
        response: httpx.Response | None = None
        try:
            response = session.post_ask(question_text)
        except httpx.HTTPError as exc:
            transport_error = f"{type(exc).__name__}: {exc}"

        latency_ms = round((time.monotonic() - started) * 1000)
        if response is not None and response.status_code == 200:
            data = response.json()
            return AskOutcome(
                answered=data["answered"],
                answer_text=data["answer"],
                cited_titles=tuple(s["title"] for s in data["sources"]),
                model=data["model"],
                tokens_in=data["tokens_in"],
                tokens_out=data["tokens_out"],
                latency_ms=latency_ms,
            )
        if response is not None and response.status_code != _RETRYABLE_STATUS:
            # Not a rate-limit/availability issue (e.g. 401/422) — retrying won't help.
            return AskOutcome(
                error=f"http {response.status_code}: {response.text[:200]}", latency_ms=latency_ms
            )

        attempt += 1
        if attempt > max_retries:
            reason = transport_error or f"http 503 after {max_retries} retries"
            return AskOutcome(error=reason, latency_ms=latency_ms)
        delay = retry_base_delay_s * (2 ** (attempt - 1))
        log.warning(
            "ask retry",
            extra={"attempt": attempt, "delay_s": delay, "error": transport_error or "http 503"},
        )
        time.sleep(delay)


def _majority_model(results: list[QuestionResult]) -> str | None:
    counts = Counter(r.model for r in results if r.model)
    return counts.most_common(1)[0][0] if counts else None


def _slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "-", text)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="run_eval")
    parser.add_argument("--questions", type=Path, default=eval_lib.DEFAULT_QUESTIONS)
    parser.add_argument("--master", type=Path, default=eval_lib.DEFAULT_MASTER)
    parser.add_argument("--manifest", type=Path, default=eval_lib.DEFAULT_MANIFEST)
    parser.add_argument("--out-dir", type=Path, default=eval_lib.DEFAULT_RESULTS_DIR)
    parser.add_argument("--base-url", default="http://backend:8000")
    parser.add_argument("--min-interval-s", type=float, default=13.0)
    parser.add_argument("--max-retries", type=int, default=3)
    parser.add_argument("--retry-base-delay-s", type=float, default=10.0)
    parser.add_argument("--consecutive-error-limit", type=int, default=5)
    parser.add_argument("--request-timeout-s", type=float, default=90.0)
    parser.add_argument(
        "--model-label",
        default=None,
        help="output folder name override; default = the model AskResponse actually reports",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_arg_parser().parse_args(argv)
    settings = get_settings()

    question_set = eval_lib.load_questions(args.questions)
    raws = eval_lib.load_ledger_raws(args.master)
    catalog = eval_lib.build_document_catalog(args.manifest)
    password = settings.demo_user_password.get_secret_value()

    sessions: dict[str, EvalSession] = {}

    def session_for(user: str) -> EvalSession:
        if user not in sessions:
            sessions[user] = EvalSession(
                args.base_url, user, password, timeout_s=args.request_timeout_s
            )
        return sessions[user]

    rate_limiter = RateLimiter(args.min_interval_s)
    results: list[QuestionResult] = []
    consecutive_errors = 0
    partial = False
    partial_reason: str | None = None

    questions = question_set.questions
    try:
        for i, question in enumerate(questions, start=1):
            log.info("asking %s/%s: %s", i, len(questions), question.id)
            expected = eval_lib.resolve_expected(question, raws)
            session = session_for(question.ask_as_user)
            outcome = ask_with_retry(
                session,
                rate_limiter,
                question.question,
                max_retries=args.max_retries,
                retry_base_delay_s=args.retry_base_delay_s,
            )
            result = eval_lib.score_question(question, expected, catalog, outcome)
            results.append(result)

            if outcome.error is not None:
                consecutive_errors += 1
                log.warning("question %s errored: %s", question.id, outcome.error)
            else:
                consecutive_errors = 0

            if consecutive_errors >= args.consecutive_error_limit:
                partial = True
                partial_reason = (
                    f"{consecutive_errors} ardışık istek hatası ({question.id}'de durdu) — "
                    "günlük kota tükenmiş olabilir, bkz. Gemini konsolu"
                )
                log.error("aborting eval run: %s", partial_reason)
                break
    finally:
        for session in sessions.values():
            session.close()

    model_label = args.model_label or _majority_model(results) or "unknown-model"
    today = datetime.date.today().isoformat()
    report = eval_lib.build_report(
        results,
        model=model_label,
        date_str=today,
        demo_today=settings.demo_today.isoformat(),
        embeddings_enabled=settings.embeddings_enabled,
        partial=partial,
        partial_reason=partial_reason,
    )

    out_dir = args.out_dir / f"{_slugify(model_label)}_{today}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "results.json").write_text(
        json.dumps(eval_lib.report_to_json(report), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    markdown = eval_lib.render_markdown(report)
    (out_dir / "results.md").write_text(markdown, encoding="utf-8")

    print(markdown)
    print(f"sonuçlar: {out_dir}", file=sys.stderr)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
