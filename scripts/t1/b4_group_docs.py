"""İş Emri 2026-10-15T1 §B4 — are the group documents (`project_scope = group`) in the
candidate package of the questions that name a project?

LLM-free, DB read-only (the same SELECT path as `scripts/measure_stage2.py`: user gate →
`retrieve()` top-80 → `named_project_codes` → Şart 1 narrowing → would-be F-3 list). Run inside
the backend container: `docker exec -i company-ai-backend-1 python - < scripts/t1/b4_group_docs.py`.
Writes `results/t1/b4_group_docs.json`.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models.document import Document, ProjectScope
from app.repositories import user_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.services.assist import named_project_codes
from app.services.authorization import allowed_document_ids
from app.services.project_narrowing import narrow_allowed, narrow_chunks
from app.services.retrieval import RetrievalFilters, retrieve
from app.services.search_query import build_search_query
from scripts import eval_lib
from scripts.measure_stage2 import _decide

OUT_PATH = Path("results/t1/b4_group_docs.json")


def main() -> None:
    questions = list(eval_lib.load_questions().questions)
    settings = get_settings()
    rows: list[dict[str, Any]] = []
    with get_session_factory()() as session:
        group_ref = {
            d: str(ref or title)
            for d, ref, title in session.execute(
                select(Document.id, Document.external_ref, Document.title).where(
                    Document.project_scope == ProjectScope.group
                )
            )
        }
        for q in questions:
            named = named_project_codes(session, q.question)
            if not named:
                continue
            user = user_repo.get_by_username(session, q.ask_as_user)
            if user is None:
                raise SystemExit(f"demo user missing: {q.ask_as_user}")
            allowed = allowed_document_ids(
                user, AuthorizationScope(), SqlDocumentIdsProvider(session)
            )
            narrowing = narrow_allowed(session, allowed, named)
            query = build_search_query(q.question)
            chunks = (
                retrieve(session, user, query, RetrievalFilters(), raw_question=q.question)
                if query
                else []
            )
            chunks_after = narrow_chunks(chunks, narrowing.scoped)
            group_chunks = [c for c in chunks_after if c.document_id in group_ref]
            decision, cards = _decide(
                session, set(narrowing.scoped), chunks_after, q.question, settings
            )
            rows.append(
                {
                    "id": q.id,
                    "user": q.ask_as_user,
                    "named": sorted(named),
                    "expected_project": q.expected_project,
                    "allowed": len(allowed),
                    "scoped": len(narrowing.scoped),
                    "allowed_group_docs": sorted(
                        group_ref[d] for d in narrowing.scoped if d in group_ref
                    ),
                    "chunks_after": len(chunks_after),
                    "group_chunks": len(group_chunks),
                    "group_docs_in_chunks": sorted(
                        {group_ref[c.document_id] for c in group_chunks}
                    ),
                    "decision": decision.kind,
                    "list_len": len(cards),
                    "group_docs_in_list": sorted(
                        {str(c.title) for c in cards if c.project_code is None}
                    ),
                }
            )
    summary = {
        "named_questions": len(rows),
        "with_group_doc_in_chunks": sum(1 for r in rows if r["group_chunks"]),
        "with_group_doc_in_list": sum(1 for r in rows if r["group_docs_in_list"]),
        "with_any_group_doc_allowed": sum(1 for r in rows if r["allowed_group_docs"]),
        "group_doc_chunk_hits": Counter(d for r in rows for d in r["group_docs_in_chunks"]),
        "group_doc_list_hits": Counter(d for r in rows for d in r["group_docs_in_list"]),
        "group_docs": sorted(group_ref.values()),
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
