"""P1K pre-measurement (eval DB, read-only): project_question_for for the 15 N1 questions.

Run (eval project only): docker compose -p company-ai-eval --project-directory .
  -f infra/docker-compose.yml --env-file infra/.env.eval run --rm -T --no-deps backend
  python - < results/p1k/measure_p1k.py"""

import json
import time

from sqlalchemy import text

from app.core.db import get_session_factory
from app.models.user import User
from app.repositories import user_repo
from app.repositories.document_repo import SqlDocumentIdsProvider
from app.schemas.ask import AskRequest
from app.schemas.authorization import AuthorizationScope
from app.services.ask import project_question_for
from app.services.ask_router import route_without_llm
from app.services.authorization import allowed_document_ids
from app.services.project_narrowing import (
    projects_with_data,
    unnamed_project_question,
    visible_project_names,
)

B, K, KZ, Y, A, D = (
    "Boztepe RES",
    "Karatepe RES",
    "Kızılova RES",
    "Yeşilova RES",
    "Akyar GES",
    "Demirci RES",
)
EXPECTED = {  # plan §5, "Önerilen" column
    "GEN-DSC-003": [K],
    "GEN-DSC-004": [K, KZ],
    "ANK-MIX-001": [B, K, Y],
    "GEN-AMB-002": [B, K, Y],
    "ANK-NEG-003": [B, K, KZ, Y],
    "GEN-AMB-001": [B, K, KZ, Y],
    "GEN-AMB-003": [K],
    "GEN-AMB-003-F": [K],
    "GEN-AMB-004": [K, KZ],
    "ANK-NEG-004": [K, KZ],
    "GEN-AMB-006": [K, KZ],
    "GEN-GEN-002": [K, KZ],
    "GEN-GEN-003": [B, K, KZ, Y],
    "GEN-DSC-011": [B, K, KZ, Y],
    "GEN-DSC-011-K": [B, K, KZ, Y],
}
PHRASE_IDS = ("GEN-DSC-003", "GEN-DSC-004", "ANK-MIX-001")
REPEATS = 20

with open("seed_data/evaluation/questions.json") as fh:
    questions = {q["id"]: q for q in json.load(fh)["questions"]}
out = []
with get_session_factory()() as session:
    session.execute(text("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY"))
    session.commit()
    print(
        "db",
        session.execute(text("select current_database()")).scalar(),
        "read_only",
        session.execute(text("show transaction_read_only")).scalar(),
    )
    for qid, expected in EXPECTED.items():
        q = questions[qid]
        user: User | None = user_repo.get_by_username(session, q["ask_as_user"])
        assert user is not None, q["ask_as_user"]
        request = AskRequest(question=q["question"])
        routed = route_without_llm(session, q["question"])
        allowed = allowed_document_ids(user, AuthorizationScope(), SqlDocumentIdsProvider(session))
        visible = visible_project_names(session, allowed)
        times_total, times_pwd = [], []
        for _ in range(REPEATS):
            t0 = time.perf_counter()
            answer = project_question_for(session, user, request)
            times_total.append((time.perf_counter() - t0) * 1000)
            t0 = time.perf_counter()
            pwd = projects_with_data(session, allowed, q["question"])
            times_pwd.append((time.perf_counter() - t0) * 1000)
        expected_answer = unnamed_project_question(expected)
        row = {
            "id": qid,
            "user": q["ask_as_user"],
            "question": q["question"],
            "route": routed.reason if routed else None,
            "today": unnamed_project_question(visible),
            "projects_with_data": pwd,
            "answer": answer,
            "expected": expected_answer,
            "match": answer == expected_answer,
            "ms_total": times_total,
            "ms_pwd": times_pwd,
        }
        if qid in PHRASE_IDS:
            low = (answer or "").lower()
            row["required_phrases"] = q.get("required_phrases", [])
            row["forbidden_phrases"] = q.get("forbidden_phrases", [])
            row["required_missing"] = [p for p in row["required_phrases"] if p.lower() not in low]
            row["forbidden_hit"] = [p for p in row["forbidden_phrases"] if p.lower() in low]
        out.append(row)
    session.rollback()


def pct(values, p):
    values = sorted(values)
    return values[min(len(values) - 1, int(round(p / 100 * (len(values) - 1))))]


for r in out:
    head = f"{r['id']:14} {r['user']:8} match={r['match']} route={r['route']}"
    print(f"{head} pwd={r['projects_with_data']}")
    print(f"   today:    {r['today']}")
    print(f"   new:      {r['answer']}")
    print(f"   expected: {r['expected']}")
    if "required_missing" in r:
        print(
            f"   phrases: required={r['required_phrases']} missing={r['required_missing']} "
            f"forbidden_hit={r['forbidden_hit']}"
        )
all_total = [t for r in out for t in r["ms_total"]]
all_pwd = [t for r in out for t in r["ms_pwd"]]
for label, values in (("project_question_for", all_total), ("projects_with_data  ", all_pwd)):
    print(f"{label} ms: p50={pct(values, 50):.1f} p95={pct(values, 95):.1f} n={len(values)}")
print(f"matches: {sum(r['match'] for r in out)}/{len(out)}")
with open("results/p1k/premeasure.json", "w") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
