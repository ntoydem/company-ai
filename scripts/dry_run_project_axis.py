"""LLM-free dry run of the project axis detector (Adım 4, ADR-030, 09.10.2026) over a named
subset of `questions.json` — read-only, runs inside the backend container against the dev
DB, costs no quota:

    docker compose … run --rm -T backend python -m scripts.dry_run_project_axis

For each question: the asking user's allowed set, the real FTS retrieval (same call
`ask.py` makes), the real `assist.classify_project_axis` + `downgrade_existence_disambiguate`
— the exact decision `/api/ask` would reach *before* ever calling the LLM. No LLM call is
made anywhere in this script.

Dev AMB (`GEN-AMB-001..005`): every one is expected to classify as `disambiguate` (no
project named, a genuinely even split) — target ≥ 4/5 (`docs/plans/ADIM4_PLAN.md` §3).
Dev NEG (`ANK-NEG-001/002/003/004`, `CO-NEG-005`, `GEN-AMB-003-F`, `GEN-CMP-001/002/003`):
none of the nine may classify as `disambiguate` (a false alarm) — target 0/9.
`ANK-NEG-004` is additionally checked for the exact `dominant`/`ANK_RES` outcome this round
was written to fix.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.repositories import document_repo, user_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.services.assist import (
    ProjectAxisDecision,
    available_from_chunks,
    available_from_metadata,
    classify_project_axis,
    downgrade_existence_disambiguate,
    named_project_codes,
    project_distribution,
)
from app.services.authorization import allowed_document_ids
from app.services.retrieval import RetrievalFilters, retrieve
from app.services.search_query import build_search_query, question_terms
from scripts import eval_lib

AMB_IDS = ("GEN-AMB-001", "GEN-AMB-002", "GEN-AMB-003", "GEN-AMB-004", "GEN-AMB-005")
NEG_IDS = (
    "ANK-NEG-001",
    "ANK-NEG-002",
    "ANK-NEG-003",
    "ANK-NEG-004",
    "CO-NEG-005",
    "GEN-AMB-003-F",
    "GEN-CMP-001",
    "GEN-CMP-002",
    "GEN-CMP-003",
)


@dataclass(frozen=True)
class Row:
    id: str
    question: str
    user: str
    path: str  # "zero" | "chunks=N"
    decision: ProjectAxisDecision


def classify(session, user_name: str, question: str) -> tuple[str, ProjectAxisDecision]:
    settings = get_settings()
    user = user_repo.get_by_username(session, user_name)
    if user is None:
        raise SystemExit(f"demo user {user_name!r} not seeded")
    scope = AuthorizationScope(department=None)
    allowed = allowed_document_ids(user, scope, SqlDocumentIdsProvider(session))
    named = named_project_codes(session, question)
    query = build_search_query(question)
    chunks = (
        retrieve(session, user, query, RetrievalFilters(department=None), raw_question=question)
        if query
        else []
    )
    if not chunks:
        terms = question_terms(question)
        candidates = available_from_metadata(session, allowed, terms, limit=50, common_threshold=5)
        decision = classify_project_axis(
            project_distribution(candidates),
            named,
            disambig_spread=settings.project_axis_disambig_spread,
            dominant_share=settings.project_axis_dominant_share,
        )
        path = "zero"
    else:
        ids = list(dict.fromkeys(c.document_id for c in chunks))
        documents = document_repo.load_with_chains(session, ids, allowed_ids=allowed)
        by_id = {d.id: d for d in documents}
        cards = available_from_chunks(by_id, chunks, limit=50)
        decision = classify_project_axis(
            project_distribution(cards),
            named,
            disambig_spread=settings.project_axis_disambig_spread,
            dominant_share=settings.project_axis_dominant_share,
        )
        path = f"chunks={len(chunks)}"
    return path, downgrade_existence_disambiguate(decision, question)


def main() -> int:
    question_set = eval_lib.load_questions()
    by_id = {q.id: q for q in question_set.questions}
    amb_hits = 0
    neg_false_alarms: list[str] = []
    ank_neg_004_ok = False
    with get_session_factory()() as session:
        settings = get_settings()
        print(
            f"PROJECT_AXIS_DISAMBIG_SPREAD={settings.project_axis_disambig_spread} "
            f"PROJECT_AXIS_DOMINANT_SHARE={settings.project_axis_dominant_share}\n"
        )
        print("## Dev AMB (5) — beklenen: disambiguate, hedef ≥ 4/5\n")
        for qid in AMB_IDS:
            q = by_id[qid]
            path, decision = classify(session, q.ask_as_user, q.question)
            hit = decision.kind == "disambiguate"
            amb_hits += hit
            print(
                f"{qid} ({q.ask_as_user}, {path}) — {q.question!r}\n"
                f"  → {decision.kind} codes={decision.codes} {'✅' if hit else '❌'}"
            )
        print(f"\nAMB isabet: {amb_hits}/{len(AMB_IDS)}\n")

        print("## Dev NEG (9) — beklenen: disambiguate DEĞİL, hedef yanlış alarm 0/9\n")
        for qid in NEG_IDS:
            q = by_id[qid]
            path, decision = classify(session, q.ask_as_user, q.question)
            false_alarm = decision.kind == "disambiguate"
            if false_alarm:
                neg_false_alarms.append(qid)
            if qid == "ANK-NEG-004":
                ank_neg_004_ok = decision == ProjectAxisDecision("dominant", "ANK_RES")
            print(
                f"{qid} ({q.ask_as_user}, {path}) — {q.question!r}\n"
                f"  → {decision.kind} project_code={decision.project_code} codes={decision.codes}"
                f" {'🔥 YANLIŞ ALARM' if false_alarm else ''}"
            )
        print(f"\nNEG yanlış alarm: {len(neg_false_alarms)}/{len(NEG_IDS)} {neg_false_alarms}\n")
        print(f"ANK-NEG-004 == dominant/ANK_RES: {'✅' if ank_neg_004_ok else '❌'}")

    ok = amb_hits >= 4 and not neg_false_alarms and ank_neg_004_ok
    print(f"\nSonuç: {'✅ geçti' if ok else '❌ kaldı'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
