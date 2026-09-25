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
from typing import Any

import httpx
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.core.logging import setup_logging
from app.core.request_id import REQUEST_ID_HEADER
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.repositories import audit_log_repo, user_repo
from app.schemas.retrieval import RetrievalFilters
from app.services.retrieval import retrieve
from app.services.search_query import build_search_query
from scripts import eval_lib
from scripts.eval_lib import AskOutcome, Page, QuestionResult, RepeatOutcome, RetrievalProbe

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
                request_id=response.headers.get(REQUEST_ID_HEADER),
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
    parser.add_argument("--ids", default=None, help="comma-separated question ids (subset)")
    parser.add_argument(
        "--repeat", type=int, default=1, help="ask each question N times (consistency mode)"
    )
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="no LLM: run retrieve() in-process and measure page recall (Phase 3.2b)",
    )
    return parser


# ---------------------------------------------------------------- Phase 3.2b helpers


def _page_texts() -> dict[str, list[tuple[int, str]]]:
    """Document title -> [(page, text)] from the live DB (the eval runs inside the backend
    container, so this needs no API)."""
    out: dict[str, list[tuple[int, str]]] = {}
    with get_session_factory()() as session:
        rows = session.execute(
            select(Document.title, DocumentChunk.page_number, DocumentChunk.text).join(
                DocumentChunk, DocumentChunk.document_id == Document.id
            )
        ).all()
    for title, page, text in rows:
        out.setdefault(title, []).append((page, text))
    return out


def _title_by_document_id() -> dict[str, str]:
    with get_session_factory()() as session:
        rows = session.execute(select(Document.id, Document.title)).all()
    return {str(document_id): title for document_id, title in rows}


class _Targets:
    """Target (title, page) pairs per question — key_facts index + expected-text search."""

    def __init__(self, args: argparse.Namespace, raws: dict[str, Any]) -> None:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        self._raws = raws
        self._page_texts = _page_texts()
        self._index = eval_lib.build_target_index(raws, manifest, self._page_texts)
        self._catalog = eval_lib.build_document_catalog(args.manifest)

    def for_question(self, question: Any) -> frozenset[Page]:
        return eval_lib.target_pages(
            question,
            self._index,
            expected=eval_lib.resolve_expected(question, self._raws),
            catalog=self._catalog,
            page_texts=self._page_texts,
        )


def _select_questions(args: argparse.Namespace) -> list[Any]:
    questions = eval_lib.load_questions(args.questions).questions
    if args.ids:
        wanted = {i.strip() for i in args.ids.split(",") if i.strip()}
        questions = [q for q in questions if q.id in wanted]
    return questions


def run_retrieval_only(args: argparse.Namespace) -> int:
    setup_logging()  # JSON lines, so `retrieve()`'s "retrieval explain" extras are readable
    settings = get_settings()
    raws = eval_lib.load_ledger_raws(args.master)
    targets = _Targets(args, raws)
    questions = _select_questions(args)
    probes: list[RetrievalProbe] = []
    with get_session_factory()() as session:
        for question in questions:
            user = user_repo.get_by_username(session, question.ask_as_user)
            if user is None:
                raise SystemExit(f"demo user missing: {question.ask_as_user}")
            query = build_search_query(question.question)
            chunks = (
                retrieve(session, user, query, RetrievalFilters(), raw_question=question.question)
                if query
                else []
            )
            titles = _title_by_document_id()
            retrieved = tuple((titles[str(c.document_id)], c.page_number) for c in chunks)
            probes.append(
                RetrievalProbe(
                    id=question.id,
                    category=question.category,
                    ask_as_user=question.ask_as_user,
                    targets=tuple(sorted(targets.for_question(question))),
                    retrieved=retrieved,
                )
            )
    mode = "on" if settings.embeddings_enabled else "off"
    label = f"embeddings={mode} top_k={settings.retrieval_top_k}"
    markdown = eval_lib.render_retrieval_markdown(
        probes, top_k=settings.retrieval_top_k, label=label
    )
    out_dir = args.out_dir / f"retrieval-only_{datetime.date.today().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%H%M%S")
    (out_dir / f"recall_{stamp}.md").write_text(markdown, encoding="utf-8")
    (out_dir / f"recall_{stamp}.json").write_text(
        json.dumps(eval_lib.retrieval_probes_to_json(probes), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(markdown)
    print(f"sonuçlar: {out_dir}/recall_{stamp}.*", file=sys.stderr)
    return 0


def _target_in_prompt(request_id: str | None, targets: frozenset[Page]) -> bool | None:
    if not targets or request_id is None:
        return None
    titles = _title_by_document_id()
    with get_session_factory()() as session:
        row = audit_log_repo.get_by_request_id(session, request_id)
        if row is None:
            return None
        in_prompt = {
            (titles.get(c["document_id"], "?"), c["page_number"]) for c in row.chunks_retrieved
        }
    return bool(in_prompt & targets)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    args = build_arg_parser().parse_args(argv)
    if args.retrieval_only:
        return run_retrieval_only(args)
    settings = get_settings()

    raws = eval_lib.load_ledger_raws(args.master)
    catalog = eval_lib.build_document_catalog(args.manifest)
    questions = _select_questions(args)
    if args.repeat > 1:
        return run_consistency(args, questions, raws, settings)
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


def run_consistency(
    args: argparse.Namespace, questions: list[Any], raws: dict[str, Any], settings: Any
) -> int:
    """`--repeat N`: every question N times, each joined with its own audit_log row so a
    retrieval miss (target page not in prompt) and a model refusal (target page in prompt,
    still "bilgi bulamadım") are counted separately (plan §1)."""
    targets_index = _Targets(args, raws)
    password = settings.demo_user_password.get_secret_value()
    sessions: dict[str, EvalSession] = {}
    rate_limiter = RateLimiter(args.min_interval_s)
    outcomes: list[RepeatOutcome] = []
    try:
        for question in questions:
            expected = eval_lib.resolve_expected(question, raws)
            targets = targets_index.for_question(question)
            for repeat in range(1, args.repeat + 1):
                log.info("asking %s repeat %s/%s", question.id, repeat, args.repeat)
                if question.ask_as_user not in sessions:
                    sessions[question.ask_as_user] = EvalSession(
                        args.base_url,
                        question.ask_as_user,
                        password,
                        timeout_s=args.request_timeout_s,
                    )
                outcome = ask_with_retry(
                    sessions[question.ask_as_user],
                    rate_limiter,
                    question.question,
                    max_retries=args.max_retries,
                    retry_base_delay_s=args.retry_base_delay_s,
                )
                value_ok: bool | None = None
                if outcome.error is None and not expected.skip:
                    value_ok = eval_lib.value_check_passes(expected, outcome.answer_text)
                outcomes.append(
                    RepeatOutcome(
                        id=question.id,
                        repeat=repeat,
                        target_in_prompt=_target_in_prompt(outcome.request_id, targets)
                        if outcome.error is None
                        else None,
                        answered=outcome.answered,
                        value_ok=value_ok,
                        error=outcome.error,
                    )
                )
    finally:
        for session in sessions.values():
            session.close()

    mode = "on" if settings.embeddings_enabled else "off"
    label = f"{settings.llm_model_answer} · embeddings={mode} · top_k={settings.retrieval_top_k}"
    markdown = eval_lib.render_consistency_markdown(outcomes, label=label)
    out_dir = args.out_dir / f"consistency_{datetime.date.today().isoformat()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%H%M%S")
    (out_dir / f"consistency_{stamp}.md").write_text(markdown, encoding="utf-8")
    (out_dir / f"consistency_{stamp}.json").write_text(
        json.dumps([o.__dict__ for o in outcomes], indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(markdown)
    print(f"sonuçlar: {out_dir}/consistency_{stamp}.*", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
