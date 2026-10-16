"""İş Emri 2026-10-15A2 §4 — LLM-free exit measure for Şart 1 (project narrowing).

For every question of `questions.json` (99), inside the eval backend container (eval DB, no
LLM): the asking user's gate, the real FTS retrieval (`retrieve()`, top-80), then the Şart 1
narrowing **off** and **on**, side by side:

  (a) named questions: chunks of a project other than the one(s) named — target 0 with the
      filter on;
  (b) the project-axis decision (`named` / `dominant` / `disambiguate` / `none`) and whether
      the narrowed/decided project matches `expected_project`;
  (c) foreign project in the would-be F-3 list (the list `build_insufficient_assist` /
      `build_zero_chunk_assist` would show if the model declined) — same definition as the
      scorer's A6 counter (project ≠ expected_project among the shown documents) — target 0;
  (d) three synthetic "unknown project" questions → `term_mismatch` without retrieval;
  Aşama 1 guard: the target page (run_eval `_Targets`) in top-80 before vs after — identical.

    python -m scripts.measure_stage2 --out results/stage2
"""

from __future__ import annotations

import argparse
import datetime
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.document import Document
from app.models.project import Project
from app.repositories import document_repo, user_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.authorization import AuthorizationScope
from app.services import project_narrowing
from app.services.ask_router import route_without_llm
from app.services.assist import (
    available_from_chunks,
    available_from_metadata,
    build_insufficient_assist,
    build_zero_chunk_assist,
    classify_project_axis,
    downgrade_existence_disambiguate,
    named_project_codes,
    project_distribution,
)
from app.services.authorization import allowed_document_ids
from app.services.project_narrowing import narrow_allowed, narrow_chunks, unknown_project_names
from app.services.retrieval import RetrievalFilters, retrieve
from app.services.search_query import build_search_query, question_terms
from scripts import eval_lib
from scripts.run_eval import _Targets

SYNTHETIC = (
    ("SYN-UNK-001", "enerji", "Bursa RES'in kapasitesi nedir?"),
    ("SYN-UNK-002", "finans", "Manisa GES'in COD tarihi nedir?"),
    ("SYN-UNK-003", "finans", "Çanakkale RES için finansman sözleşmesi imzalandı mı?"),
)
_NAME_BY_CODE = {**eval_lib._ALL_PROJECT_NAME_BY_CODE}


@dataclass(frozen=True)
class Row:
    id: str
    user: str
    expected_project: str | None
    named: list[str]
    chunks_before: int
    chunks_after: int
    foreign_chunks_before: int
    foreign_chunks_after: int
    decision_before: str
    decision_after: str
    decided_project_before: str | None
    decided_project_after: str | None
    expected_match_before: bool | None
    expected_match_after: bool | None
    list_foreign_before: bool | None
    list_foreign_after: bool | None
    target_in_top80_before: bool | None
    target_in_top80_after: bool | None
    # İş Emri 2026-10-16N1: what `ask_router.route_without_llm` decides for the question
    # ("router" = no pre-route), and for an unnamed value question whether the code asks
    # the one project question ("…→soru") or the group-document exemption hands it to the
    # model ("…→model").
    route: str = "router"


def _code_of(session: Session) -> dict[Any, str]:
    return {p.id: p.code for p in session.scalars(select(Project)).all()}


def _decide(
    session: Session, allowed: set, chunks: list, question: str, settings: Any
) -> tuple[Any, list]:
    """The exact pre-LLM decision `ask.py` reaches, and the would-be F-3 list (what
    `render_no_data` would show if the model declined) — both without an LLM call."""
    named = named_project_codes(session, question)
    if not chunks:
        assist = build_zero_chunk_assist(
            session,
            allowed,
            question,
            ek_f=True,
            disambig_spread=settings.project_axis_disambig_spread,
            dominant_share=settings.project_axis_dominant_share,
        )
        terms = question_terms(question)
        cards = available_from_metadata(session, allowed, terms, limit=50, common_threshold=5)
        decision = downgrade_existence_disambiguate(
            classify_project_axis(
                project_distribution(cards),
                named,
                disambig_spread=settings.project_axis_disambig_spread,
                dominant_share=settings.project_axis_dominant_share,
            ),
            question,
        )
        return decision, list(assist.available)
    ids = list(dict.fromkeys(c.document_id for c in chunks))
    documents = document_repo.load_with_chains(session, ids, allowed_ids=allowed)
    by_id = {d.id: d for d in documents}
    cards = available_from_chunks(by_id, chunks, limit=50)
    decision = downgrade_existence_disambiguate(
        classify_project_axis(
            project_distribution(cards),
            named,
            disambig_spread=settings.project_axis_disambig_spread,
            dominant_share=settings.project_axis_dominant_share,
        ),
        question,
    )
    if decision.kind == "disambiguate":
        return decision, []
    assist = build_insufficient_assist(
        session,
        allowed,
        question,
        documents=by_id,
        chunks=chunks,
        model_question=None,
        ek_f=True,
        axis_decision=decision,
        disambig_spread=settings.project_axis_disambig_spread,
        dominant_share=settings.project_axis_dominant_share,
    )
    return decision, list(assist.available)


def _decided_project(decision: Any, named: set[str]) -> str | None:
    if decision.kind in ("named", "dominant"):
        return str(decision.project_code)
    if len(named) == 1:
        return next(iter(named))
    return None


def _route(session: Session, question: str, allowed: set, chunks: list) -> str:
    """The pre-route decision, LLM-free. Works on code before İş Emri 2026-10-16N1 too (no
    `unnamed_value_clarification` there → only the A2L2/A2L3 reasons can appear)."""
    routed = route_without_llm(session, question)
    if routed is None:
        return "router"
    clarification = getattr(project_narrowing, "unnamed_value_clarification", None)
    if routed.reason != "unnamed_value_question" or clarification is None:
        return routed.reason
    asks = clarification(session, allowed, chunks) is not None
    return f"{routed.reason}→{'soru' if asks else 'model'}"


def _foreign_in_list(cards: list, expected_code: str | None) -> bool | None:
    if expected_code is None or not cards:
        return None
    return any(c.project_code not in (None, expected_code) for c in cards)


def _foreign_chunks(chunks: list, named: set[str], doc_code: dict[Any, str | None]) -> int:
    if not named:
        return 0
    return sum(1 for c in chunks if doc_code.get(c.document_id) not in (None, *named))


def _target_hit(chunks: list, target: frozenset, title_of: dict[Any, str]) -> bool | None:
    if not target:
        return None
    return bool({(title_of.get(c.document_id, "?"), c.page_number) for c in chunks} & target)


def measure(session: Session, targets: _Targets, questions: list) -> list[Row]:
    settings = get_settings()
    code_of = _code_of(session)
    code_by_name = {v: k for k, v in _NAME_BY_CODE.items()}
    doc_code: dict[Any, str | None] = {
        d: code_of.get(p) for d, p in session.execute(select(Document.id, Document.project_id))
    }
    title_of = {d: t for d, t in session.execute(select(Document.id, Document.title))}
    rows: list[Row] = []
    for q in questions:
        user = user_repo.get_by_username(session, q.ask_as_user)
        if user is None:
            raise SystemExit(f"demo user missing: {q.ask_as_user}")
        allowed = allowed_document_ids(user, AuthorizationScope(), SqlDocumentIdsProvider(session))
        query = build_search_query(q.question)
        chunks = (
            retrieve(session, user, query, RetrievalFilters(), raw_question=q.question)
            if query
            else []
        )
        named = named_project_codes(session, q.question)
        narrowing = narrow_allowed(session, allowed, named)
        chunks_after = narrow_chunks(chunks, narrowing.scoped) if narrowing.active else chunks
        allowed_after = set(narrowing.scoped)
        expected_code = code_by_name.get(q.expected_project or "")

        target = targets.for_question(q)
        foreign_before = _foreign_chunks(chunks, named, doc_code)
        foreign_after = _foreign_chunks(chunks_after, named, doc_code)
        hit_before = _target_hit(chunks, target, title_of)
        hit_after = _target_hit(chunks_after, target, title_of)

        d_before, list_before = _decide(session, allowed, chunks, q.question, settings)
        d_after, list_after = _decide(session, allowed_after, chunks_after, q.question, settings)
        p_before, p_after = _decided_project(d_before, named), _decided_project(d_after, named)
        rows.append(
            Row(
                id=q.id,
                user=q.ask_as_user,
                expected_project=q.expected_project,
                named=sorted(named),
                chunks_before=len(chunks),
                chunks_after=len(chunks_after),
                foreign_chunks_before=foreign_before,
                foreign_chunks_after=foreign_after,
                decision_before=d_before.kind,
                decision_after=d_after.kind,
                decided_project_before=p_before,
                decided_project_after=p_after,
                expected_match_before=(
                    None if expected_code is None or p_before is None else p_before == expected_code
                ),
                expected_match_after=(
                    None if expected_code is None or p_after is None else p_after == expected_code
                ),
                list_foreign_before=_foreign_in_list(list_before, expected_code),
                list_foreign_after=_foreign_in_list(list_after, expected_code),
                target_in_top80_before=hit_before,
                target_in_top80_after=hit_after,
                route=_route(session, q.question, allowed, chunks),
            )
        )
    return rows


def synthetic(session: Session) -> list[dict[str, Any]]:
    out = []
    for qid, user_name, text in SYNTHETIC:
        unknown = unknown_project_names(session, text)
        out.append(
            {
                "id": qid,
                "user": user_name,
                "question": text,
                "unknown": unknown,
                "outcome": "term_mismatch (LLM yok, retrieval yok)" if unknown else "—",
                "ok": bool(unknown),
            }
        )
    return out


def _count(rows: list[Row], attr: str) -> tuple[int, int]:
    values = [getattr(r, attr) for r in rows]
    return sum(1 for v in values if v), sum(1 for v in values if v is not None)


def _mark(value: bool | None) -> str:
    return "—" if value is None else ("✅" if value else "❌")


def render(rows: list[Row], syn: list[dict[str, Any]]) -> str:
    named_rows = [r for r in rows if r.named]
    unnamed_rows = [r for r in rows if not r.named]
    measurable = [r for r in rows if r.target_in_top80_before is not None]
    mb, mt = _count(rows, "expected_match_before")
    ma, _ = _count(rows, "expected_match_after")
    lb, lt = _count(rows, "list_foreign_before")
    la, _ = _count(rows, "list_foreign_after")
    nlb, _ = _count(named_rows, "list_foreign_before")
    nla, _ = _count(named_rows, "list_foreign_after")
    hb, _ = _count(measurable, "target_in_top80_before")
    ha, _ = _count(measurable, "target_in_top80_after")
    syn_ok = sum(1 for s in syn if s["ok"])
    before = Counter(r.decision_before for r in rows)
    after = Counter(r.decision_after for r in rows)
    kinds = ("named", "dominant", "disambiguate", "none")
    lines = [
        "# Aşama 2 ölçüsü — proje daraltma (LLM'siz, eval DB, 99 soru)",
        "",
        f"Tarih {datetime.date.today().isoformat()} · adlı soru {len(named_rows)} · "
        f"adsız {len(unnamed_rows)}",
        "",
        "| Ölçü | Süzgeç kapalı | Süzgeç açık | Hedef |",
        "|---|---|---|---|",
        f"| (a) adlı sorularda yabancı proje parçası (toplam) | "
        f"{sum(r.foreign_chunks_before for r in named_rows)} | "
        f"{sum(r.foreign_chunks_after for r in named_rows)} | 0 |",
        f"| (a) yabancı parça taşıyan adlı soru | "
        f"{sum(1 for r in named_rows if r.foreign_chunks_before)} | "
        f"{sum(1 for r in named_rows if r.foreign_chunks_after)} | 0 |",
        f"| (b) karar = beklenen proje (ölçülebilir) | {mb}/{mt} | {ma}/{mt} | ↑ |",
        f"| (c) F-3 listesinde yabancı proje (ölçülebilir) | {lb}/{lt} | {la}/{lt} | 0 (adlı) |",
        f"| (c) … yalnız adlı sorular | {nlb} | {nla} | 0 |",
        f"| (d) sentetik olmayan proje → term_mismatch | — | {syn_ok}/{len(syn)} | "
        f"{len(syn)}/{len(syn)} |",
        f"| Aşama 1: hedef sayfa top-80'de (ölçülebilir {len(measurable)}) | {hb} | {ha} | aynı |",
        "",
        "Karar dağılımı (önce → sonra): " + ", ".join(f"{k} {before[k]}→{after[k]}" for k in kinds),
        "",
        "## Adsız sorular — karar değişmedi mi?",
        "",
        "| Soru | Önce | Sonra | Parça önce/sonra |",
        "|---|---|---|---|",
    ]
    changed = [
        r
        for r in unnamed_rows
        if r.decision_before != r.decision_after or r.chunks_before != r.chunks_after
    ]
    lines += [
        f"| {r.id} | {r.decision_before} | {r.decision_after} | "
        f"{r.chunks_before}/{r.chunks_after} |"
        for r in changed
    ] or ["| — | aynı | aynı | aynı |"]
    lines += [
        "",
        "## Adlı sorular — tek tek",
        "",
        "| Soru | Adlı | Parça önce→sonra | Yabancı önce→sonra | Karar önce→sonra | "
        "Liste yabancı önce→sonra | Hedef top-80 önce→sonra |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in named_rows:
        lines.append(
            f"| {r.id} | {','.join(r.named)} | {r.chunks_before}→{r.chunks_after} | "
            f"{r.foreign_chunks_before}→{r.foreign_chunks_after} | "
            f"{r.decision_before}→{r.decision_after} | "
            f"{_mark(r.list_foreign_before)}→{_mark(r.list_foreign_after)} | "
            f"{_mark(r.target_in_top80_before)}→{_mark(r.target_in_top80_after)} |"
        )
    routes = Counter(r.route for r in rows)
    lines += [
        "",
        "## Yönlendirme — `route_without_llm` (İş Emri 2026-10-16N1)",
        "",
        "Dağılım: " + ", ".join(f"{k} {v}" for k, v in sorted(routes.items())),
        "",
        "| Soru | Adlı | Yönlendirme |",
        "|---|---|---|",
    ]
    lines += [
        f"| {r.id} | {','.join(r.named) or '—'} | {r.route} |" for r in rows if r.route != "router"
    ] or ["| — | — | hepsi router |"]
    lines += [
        "",
        "## (d) Sentetik olmayan proje soruları",
        "",
        "| Soru | Kullanıcı | Metin | Tanınmayan | Sonuç |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {s['id']} | {s['user']} | {s['question']} | {s['unknown']} | {s['outcome']} |"
        for s in syn
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="measure_stage2")
    parser.add_argument("--out", type=Path, default=eval_lib.DEFAULT_RESULTS_DIR / "stage2")
    parser.add_argument("--questions", type=Path, default=eval_lib.DEFAULT_QUESTIONS)
    parser.add_argument("--master", type=Path, default=eval_lib.DEFAULT_MASTER)
    parser.add_argument("--manifest", type=Path, default=eval_lib.DEFAULT_MANIFEST)
    args = parser.parse_args(argv)
    from app.core.db import get_session_factory

    raws = eval_lib.load_ledger_raws(args.master)
    targets = _Targets(args, raws)
    questions = list(eval_lib.load_questions(args.questions).questions)
    with get_session_factory()() as session:
        rows = measure(session, targets, questions)
        syn = synthetic(session)
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.date.today().isoformat()
    markdown = render(rows, syn)
    (args.out / f"measure_{stamp}.md").write_text(markdown, encoding="utf-8")
    (args.out / f"measure_{stamp}.json").write_text(
        json.dumps(
            {"rows": [asdict(r) for r in rows], "synthetic": syn}, indent=2, ensure_ascii=False
        ),
        encoding="utf-8",
    )
    print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
