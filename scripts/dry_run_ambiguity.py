"""LLM-free dry run of the code-side ambiguity detector (`app/services/ambiguity.py`) over
every question in `questions.json` (Adım 2, Naci 07.10.2026) — read-only, runs inside the
backend container against the dev DB, costs no quota:

    docker compose … run --rm -T backend python -m scripts.dry_run_ambiguity [--held-out]

For each question: the asking user's allowed set, the real FTS retrieval query, the real
detector. Prints one row per question (fired / not, both signals, groups, the fixed question
it would ask) and lists every fired question with its reason. Expected: fires only for the
`ambiguous` category; a fire anywhere else is a false positive to report. `--held-out`
appends the `held_out` block (Tansu's future questions) to the run.

NOTE (08.10.2026): the detector itself (`app/services/ambiguity.py`) was NOT merged to `main`
(held-out 2/5 ambiguous, 1 false alarm) — it lives at tag `ambiguity-v3-unmerged`. On `main`
this script exits with a message; it is kept so the held-out block can be re-run from that tag.
"""

from __future__ import annotations

import argparse
import sys
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models.document import Document
from app.repositories import user_repo
from app.repositories.document_chunk_repo import search_fts
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope

try:
    from app.services import ambiguity
except ImportError as exc:  # pragma: no cover — V3 is not merged to main
    raise SystemExit(
        "app/services/ambiguity.py yok: V3 tespit kodu main'e alınmadı (tag "
        "`ambiguity-v3-unmerged`, Naci 08.10.2026). Kuru koşu o tag'in checkout'unda çalışır."
    ) from exc
from app.services.authorization import allowed_document_ids
from app.services.search_query import build_search_query
from scripts import eval_lib


@dataclass(frozen=True)
class Row:
    id: str
    category: str
    user: str
    question: str
    expected_fire: bool
    fired: bool
    scope_less: bool
    groups: int
    chunks: int
    asked: str | None
    held_out: bool
    # category mixed/data: the router never sends these down DOCUMENT_QUERY
    route_excluded: bool
    allowed_count: int = 0
    # top-N chunks by project/type: 'ANK_RES/Type ×n (best rank)'
    distribution: str = ""


def run(questions_path: Path, *, include_held_out: bool) -> list[Row]:
    question_set = eval_lib.load_questions(questions_path)
    items = [(q, False) for q in question_set.questions]
    if include_held_out:
        items += [(q, True) for q in question_set.held_out]
    settings = get_settings()
    rows: list[Row] = []
    with get_session_factory()() as session:
        docs = {d.id: d for d in session.query(Document).all()}
        cache: dict[str, tuple] = {}
        for q, held in items:
            if q.ask_as_user not in cache:
                user = user_repo.get_by_username(session, q.ask_as_user)
                if user is None:
                    raise SystemExit(f"{q.id}: user {q.ask_as_user!r} not seeded")
                cache[q.ask_as_user] = (
                    user,
                    allowed_document_ids(
                        user, AuthorizationScope(), SqlDocumentIdsProvider(session)
                    ),
                )
            _, allowed = cache[q.ask_as_user]
            query = build_search_query(q.question)
            chunks = (
                search_fts(
                    session, allowed_ids=allowed, query=query, top_k=settings.retrieval_top_k
                )
                if query
                else []
            )
            groups: OrderedDict = ambiguity._groups(chunks, docs)
            dist: OrderedDict[str, list[float]] = OrderedDict()
            for c in chunks[: ambiguity.TOP_N]:
                doc = docs.get(c.document_id)
                if doc is None:
                    continue
                key = f"{doc.project.code if doc.project else 'CO'}/{doc.document_type}"
                dist.setdefault(key, []).append(c.rank)
            distribution = "; ".join(f"{k} ×{len(r)} ({max(r):.2f})" for k, r in dist.items())
            scope_less = ambiguity._scope_less(session, allowed, q.question) if chunks else False
            found = ambiguity.detect(session, allowed, q.question, chunks, docs)
            rows.append(
                Row(
                    q.id,
                    q.category,
                    q.ask_as_user,
                    q.question,
                    q.category == "ambiguous",
                    found is not None,
                    scope_less,
                    len(groups),
                    len(chunks),
                    found.question if found else None,
                    held,
                    q.category in ("mixed", "data"),
                    len(allowed),
                    distribution,
                )
            )
    return rows


def render_detail(rows: list[Row]) -> str:
    """Per-question detail (Naci, 08.10.2026): visible documents, top-N chunk distribution by
    project/type, whether the stated intent held, and what the detector would ask."""
    out = [
        "| Soru | Kullanıcı | Niyet | Görebildiği belge "
        "| Parça (top-N dağılımı: proje/tür ×n (en iyi rank)) "
        "| Grup | Niyet tuttu mu | V3 | Eksen / soru |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        intent = "belirsiz" if r.expected_fire else "net"
        held = (r.groups >= 2) if r.expected_fire else (r.groups <= 1 or not r.fired)
        axis = ""
        if r.asked:
            axis = (
                "proje: " if r.asked.startswith("Hangi projeyi") else "belge: "
            ) + r.asked.replace("|", "/")
        mark = "✅" if held else "⚠️"
        out.append(
            f"| {r.id} | {r.user} | {intent} | {r.allowed_count} | {r.distribution or '—'} "
            f"| {r.groups} | {mark} | {'🔥' if r.fired else '–'} | {axis} |"
        )
    return "\n".join(out)


def render(rows: list[Row]) -> str:
    fired = [r for r in rows if r.fired]
    fp = [r for r in fired if not r.expected_fire and not r.route_excluded]
    routed_out = [r for r in fired if not r.expected_fire and r.route_excluded]
    fn = [r for r in rows if r.expected_fire and not r.fired]
    out = [
        f"dry-run-ambiguity — TOP_N={ambiguity.TOP_N} CLOSE={ambiguity.CLOSE}: {len(rows)} soru, "
        f"ateşlendi {len(fired)}, yanlış pozitif {len(fp)}, yanlış negatif {len(fn)}, "
        f"router (MIXED/DATA) tarafından yolda dışlanan {len(routed_out)}",
        "",
        "| Soru | Kategori | Kullanıcı | Beklenen | Ateşlendi | (i) kapsamsız | (ii) grup | parça "
        "| Sorulacak |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        tag = " (held-out)" if r.held_out else ""
        expected = "🔶 belirsiz" if r.expected_fire else "–"
        fired_mark = "🔥" if r.fired else "–"
        scope = "✓" if r.scope_less else "–"
        asked = (r.asked or "").replace("|", "/")
        out.append(
            f"| {r.id}{tag} | {r.category} | {r.user} | {expected} | {fired_mark} | {scope} "
            f"| {r.groups} | {r.chunks} | {asked} |"
        )
    out += ["", "Ateşlenen sorular ve gerekçe:"]
    for r in fired:
        out.append(
            f'- {r.id} ({r.category}, {r.user}) — "{r.question}": kapsamsız (yalnızca belge-sınıfı '
            f"terim, proje/liste kelimesi yok) + {r.groups} grup → {r.asked}"
        )
    out += [
        "",
        f"Yanlış pozitif: {[r.id for r in fp]}",
        f"Yanlış negatif: {[r.id for r in fn]}",
        f"Yolda dışlanan (MIXED/DATA): {[r.id for r in routed_out]}",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dry_run_ambiguity")
    parser.add_argument("--questions", type=Path, default=eval_lib.DEFAULT_QUESTIONS)
    parser.add_argument("--held-out", action="store_true")
    parser.add_argument("--detail", action="store_true", help="per-question distribution table")
    parser.add_argument("--only-held-out", action="store_true")
    args = parser.parse_args(argv)
    rows = run(args.questions, include_held_out=args.held_out or args.only_held_out)
    if args.only_held_out:
        rows = [r for r in rows if r.held_out]
    print(render(rows))
    if args.detail:
        print()
        print(render_detail(rows))
    return 1 if any(r.fired and not r.expected_fire and not r.route_excluded for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
