"""P2A acceptance measure (eval DB, read-only, LLM-free): Excel answers for Yeşilova/Boztepe
questions with fixed plans — never another project's figure.

Run (eval project only): docker compose -p company-ai-eval --project-directory .
  -f infra/docker-compose.yml --env-file infra/.env.eval run --rm -T --no-deps backend
  python - before|after < results/p2a/measure_p2a.py"""

import inspect
import json
import sys
from typing import Any

from sqlalchemy import text

from app.api.deps import get_calculation_engine
from app.core.config import get_settings
from app.core.db import get_session_factory
from app.models.document import Document
from app.repositories import user_repo
from app.schemas.excel import ExcelAskRequest
from app.services.excel_ask import PLAN_SYSTEM_PROMPT, answer_data_question
from app.services.llm import LLMRequest, LLMResponse

LABEL = sys.argv[1] if len(sys.argv) > 1 else "run"
TODAY_DEBT = {"kind": "function", "name": "outstanding_debt", "params": {"as_of": "today"}}
DSCR = {"kind": "function", "name": "dscr", "params": {"period": "Q2_2026"}}
KARATEPE_DEBT_SQL = {
    "kind": "sql",
    "sql": "SELECT closing_usd FROM financial_model_2026__debt "
    "WHERE end_date <= DATE '2026-10-06' ORDER BY end_date DESC LIMIT 1",
}
YSV_12 = {
    "kind": "sql",
    "sql": "SELECT col_c FROM yesilova_repayment_schedule_2026_09__schedule "
    "WHERE deme_plan_ye_ilova_res = '12'",
    "future_ok": True,
}
BOZ_12 = {
    "kind": "sql",
    "sql": "SELECT col_d FROM boztepe_repayment_schedule_84_instalments__schedule "
    "WHERE boztepe_res_anapara_geri_deme_plan_84_taksit = '12'",
    "future_ok": True,
}
# (id, question, expected project code or None for unnamed, plan)
CASES = [
    ("Y1", "Yeşilova RES'in kalan kredi borcu ne kadar?", "YSV_RES", TODAY_DEBT),
    ("Y2", "Yeşilova RES'in güncel DSCR değeri kaç?", "YSV_RES", DSCR),
    ("Y3", "Yeşilova RES'in kalan kredi borcu ne kadar?", "YSV_RES", KARATEPE_DEBT_SQL),
    ("Y4", "Yeşilova RES ödeme planında 12. taksitin anaparası ne kadar?", "YSV_RES", YSV_12),
    ("B1", "Boztepe RES'in kalan kredi borcu ne kadar?", "BOZ_RES", TODAY_DEBT),
    ("B2", "Boztepe RES'in güncel DSCR değeri kaç?", "BOZ_RES", DSCR),
    ("B3", "Boztepe RES'in kalan kredi borcu ne kadar?", "BOZ_RES", KARATEPE_DEBT_SQL),
    ("B4", "Boztepe RES ödeme planında 12. taksitin anaparası ne kadar?", "BOZ_RES", BOZ_12),
    ("K1", "Karatepe RES'in kalan kredi borcu ne kadar?", "ANK_RES", TODAY_DEBT),
    ("K2", "Karatepe RES'in güncel DSCR değeri kaç?", "ANK_RES", DSCR),
    ("U1", "Kalan kredi borcu ne kadar?", None, TODAY_DEBT),
    ("U2", "Ödeme planında 12. taksitin anaparası ne kadar?", None, YSV_12),
]
USERS = ("finans", "yonetim")


class PlanOnlyLLM:
    """Planner → the case's fixed plan; answering model → a sentence without the figure, so
    the engine's template answer (ADR-011) is what the user would see."""

    def __init__(self, plan: dict[str, Any]) -> None:
        self.plan = plan
        self.calls: list[str] = []

    def complete(self, request: LLMRequest) -> LLMResponse:
        self.calls.append("plan" if request.system == PLAN_SYSTEM_PROMPT else "answer")
        reply = json.dumps(self.plan) if request.system == PLAN_SYSTEM_PROMPT else "-"
        return LLMResponse(
            text=reply,
            model="fake",
            tokens_in=0,
            tokens_out=0,
            tokens_reasoning=None,
            finish_reason="stop",
            latency_ms=0,
        )


settings = get_settings()
engine = get_calculation_engine()
takes_original = "original_question" in inspect.signature(answer_data_question).parameters
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
    for username in USERS:
        user = user_repo.get_by_username(session, username)
        assert user is not None, username
        for case_id, question, expected, plan in CASES:
            llm = PlanOnlyLLM(plan)
            extra = {"original_question": question} if takes_original else {}
            result = answer_data_question(
                session,
                user,
                ExcelAskRequest(question=question),
                llm,  # type: ignore[arg-type]
                settings,
                engine,
                write_audit=False,
                **extra,
            )
            projects = []
            for card in result.sources:
                document = session.get(Document, card.document_id)
                code = document.project.code if document and document.project else "GROUP"
                projects.append(code)
            foreign = bool(expected) and any(p != expected for p in projects) and result.answered
            row = {
                "label": LABEL,
                "user": username,
                "id": case_id,
                "question": question,
                "plan": plan.get("name") or "sql",
                "answered": result.answered,
                "value": result.formatted_value,
                "source_projects": projects,
                "files": result.excel_files,
                "project_question": getattr(result, "project_question", None),
                "answer": result.answer,
                "llm_calls": llm.calls,
                "foreign_project_value": foreign,
            }
            out.append(row)
            print(json.dumps(row, ensure_ascii=False))
    session.rollback()
print("FOREIGN_TOTAL", sum(r["foreign_project_value"] for r in out))
with open(f"results/p2a/measure_{LABEL}.json", "w") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1)
