"""`POST /api/ask` through the router (Phase 4.3, ADR-010): the three branches (DOCUMENT,
DATA, MIXED — GENERAL was removed 30.09.2026), the MIXED merge with both source kinds, and
the single audit row. Router and LLM are fakes; retrieval, authorization and the Excel
engine are real (over the committed demo workbooks and ledger-generated documents)."""

from __future__ import annotations

import json
import re
from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_router
from app.core.errors import LLM_UNAVAILABLE_MESSAGE
from app.main import app
from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories import company_settings_repo
from app.schemas.ask import (
    MISSING_DATA_WARNING,
    MIXED_NOTICE,
    NO_INTERPRETATION_NOTICE,
    PRODUCT_LIMIT_WARNING,
)
from app.schemas.excel import NO_INTERPRETATION_NOTICE as EXCEL_NOTICE
from app.services import excel_ask as excel_ask_module
from app.services.answer_prompt import NO_ANSWER_TEXT, NO_REASON_TEXT
from app.services.ask_router import DATA_PART_HEADING, DOCUMENT_PART_HEADING
from app.services.excel_ask import ANSWER_SYSTEM_PROMPT, PLAN_SYSTEM_PROMPT
from app.services.llm import LLMRateLimitError, LLMRequest
from app.services.router import ROUTER_SYSTEM_PROMPT
from tests.fakes import FakeLLMClient, FakeRouter
from tests.ledger_fixtures import ensure_generated_documents, load_ledger_documents
from tests.test_excel_api import _upload_workbook

AMBIGUOUS_DSCR = "Güncel DSCR kaç?"
COVENANT_SUBQUESTION = "Kredi sözleşmesindeki güncel minimum DSCR covenant'ı nedir?"
ACTUAL_SUBQUESTION = "En son çeyreğin gerçekleşen DSCR değeri kaç?"


def _ask(client: TestClient, question: str, **extra: object) -> dict[str, object]:
    response = client.post("/api/ask", json={"question": question, **extra})
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    return body


def _audit_rows(session: Session) -> list[AuditLog]:
    return list(session.scalars(select(AuditLog).order_by(AuditLog.timestamp)).all())


def _reply_by_pipeline(
    *, document_reply: str, plan: dict[str, object], excel_reply: str
) -> Callable[[LLMRequest], str]:
    """One fake for a MIXED call: the document pipeline, the Excel planning call and the
    Excel phrasing call are told apart by their system prompt."""

    def reply(request: LLMRequest) -> str:
        if request.system == PLAN_SYSTEM_PROMPT:
            return json.dumps(plan)
        if request.system == ANSWER_SYSTEM_PROMPT:
            return excel_reply
        return document_reply

    return reply


# ---------------------------------------------------------------- MIXED: ambiguous DSCR


def test_ambiguous_dscr_returns_covenant_and_actual_with_both_source_kinds(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    """PHASES.md 4.3: belirsiz DSCR → iki değer, iki kaynak türü. The document side is the
    amendment page (covenant), the Excel side is `Covenant_Report.xlsx Q2_2026!D14`
    (realised, computed by the engine); one audit row carries both."""
    manifest = ensure_generated_documents()
    amendment_entry = next(
        e for e in manifest["documents"] if e["external_ref"] == "DOC-ANK-FIN-005"
    )
    documents = load_ledger_documents(db_session, ["DOC-ANK-FIN-004", "DOC-ANK-FIN-005"])
    amendment = documents["DOC-ANK-FIN-005"]
    amendment_page = amendment_entry["page_map"]["2. Amendments to the Original Agreement"]
    workbook = _upload_workbook(client)  # Covenant_Report.xlsx

    fake_router.query_type = "MIXED_QUERY"
    fake_router.document_question = COVENANT_SUBQUESTION
    fake_router.data_question = ACTUAL_SUBQUESTION

    def document_reply(request: LLMRequest) -> str:
        match = re.search(
            rf"\[(K\d+)\] Belge: {re.escape(amendment.title)} \|.*?Sayfa: {amendment_page}\n",
            request.user,
        )
        assert match, request.user
        return f"Güncel minimum DSCR covenant'ı 1,20x'tir [{match.group(1)}]."

    def reply(request: LLMRequest) -> str:
        if request.system == PLAN_SYSTEM_PROMPT:
            return json.dumps({"kind": "function", "name": "dscr", "params": {"period": "Q2_2026"}})
        if request.system == ANSWER_SYSTEM_PROMPT:
            return "2026 Q2 gerçekleşen DSCR 1,37x."
        return document_reply(request)

    fake_llm.reply_fn = reply

    body = _ask(client, AMBIGUOUS_DSCR)

    assert body["query_type"] == "MIXED_QUERY" and body["answered"] is True
    assert body["notice"] == MIXED_NOTICE
    answer = str(body["answer"])
    assert answer.startswith(f"{DOCUMENT_PART_HEADING}\n")
    assert f"\n\n{DATA_PART_HEADING}\n" in answer
    assert "1,20x" in answer and "1,37x" in answer
    assert answer.index("1,20x") < answer.index("1,37x")  # document part first, always
    sources = body["sources"]
    assert isinstance(sources, list) and sources[0]["title"] == amendment.title
    assert sources[0]["page_number"] == amendment_page and sources[0]["is_current"] is True
    excel_sources = body["excel_sources"]
    assert isinstance(excel_sources, list) and len(excel_sources) == 1
    assert excel_sources[0]["label"] == "Covenant_Report.xlsx Q2_2026!D14"
    assert excel_sources[0]["document_id"] == workbook["id"]
    assert str(amendment.id) in body["retrieved_document_ids"]  # type: ignore[operator]
    assert workbook["id"] in body["retrieved_document_ids"]  # type: ignore[operator]

    # The router saw the original question; each pipeline saw its own sub-question.
    assert fake_router.questions == [AMBIGUOUS_DSCR]
    excel_prompts = (PLAN_SYSTEM_PROMPT, ANSWER_SYSTEM_PROMPT)
    document_request = next(r for r in fake_llm.requests if r.system not in excel_prompts)
    assert COVENANT_SUBQUESTION in document_request.user
    assert AMBIGUOUS_DSCR not in document_request.user
    plan_request = next(r for r in fake_llm.requests if r.system == PLAN_SYSTEM_PROMPT)
    assert ACTUAL_SUBQUESTION in plan_request.user
    # No third "merge" LLM call: document answer + plan + phrasing = 3.
    assert len(fake_llm.requests) == 3

    # SORU 2: one audit row for the call, both source kinds, both file/page evidence.
    rows = _audit_rows(db_session)
    assert len(rows) == 1
    row = rows[0]
    assert row.query_type == "MIXED_QUERY" and row.question == AMBIGUOUS_DSCR
    assert {s["kind"] for s in row.sources} == {"document", "excel"}
    assert [s["label"] for s in row.sources if s["kind"] == "excel"] == [
        "Covenant_Report.xlsx Q2_2026!D14"
    ]
    assert row.excel_files_used == ["Covenant_Report.xlsx"]
    assert amendment.id in row.documents_retrieved and row.chunks_retrieved
    assert str(workbook["id"]) in [str(i) for i in row.documents_retrieved]
    assert row.tokens_in == 3 * 123 and row.answer == answer


# ---------------------------------------------------------------- MIXED: variance + reason


def test_budget_variance_with_reason_only_from_documents(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    """PHASES.md 4.3 (SORU 1 rewording): Q3 2024 bütçe sapması + sebep belgede var mı? →
    the Excel difference from the engine (`Summary!D5`) with its source, and — since the
    document states the figures but no reason — the rule-6 fixed sentence, verbatim, on
    the document side (the model is faked; the live test asks the real one)."""
    from tests.test_ask import _document

    _document(
        db_session,
        title="Production Report Q3 2024",
        department=None,
        text="Ankara RES Q3 2024 bütçe 26.000.000 TRY, gerçekleşen 25.106.000 TRY.",
    )
    _upload_workbook(client, "Budget_vs_Actual_2026.xlsx")
    fake_router.query_type = "MIXED_QUERY"
    fake_router.document_question = "Q3 2024 bütçe sapmasının sebebi belgelerde belirtilmiş mi?"
    fake_router.data_question = "Ankara RES Q3 2024 bütçe sapması kaç?"
    fake_llm.reply_fn = _reply_by_pipeline(
        document_reply=f"{NO_REASON_TEXT} [K1].",
        plan={"kind": "function", "name": "budget_variance", "params": {"period": "Q3_2024"}},
        excel_reply="Q3 2024 sapması yaklaşık -0,9 milyon TRY.",  # altered → template wins
    )

    body = _ask(client, "Ankara RES Q3 2024 bütçe sapması neydi ve sebebi belgelerde yazıyor mu?")

    assert body["query_type"] == "MIXED_QUERY" and body["answered"] is True
    answer = str(body["answer"])
    document_part, data_part = answer.split(f"\n\n{DATA_PART_HEADING}\n")
    assert NO_REASON_TEXT in document_part
    assert data_part.startswith("Sonuç: -894.000 TRY")  # ADR-011: never the model's number
    excel_sources = body["excel_sources"]
    assert isinstance(excel_sources, list)
    assert excel_sources[0]["label"] == "Budget_vs_Actual_2026.xlsx Summary!D5"
    assert len(_audit_rows(db_session)) == 1


def test_mixed_with_nothing_on_either_side_keeps_both_fixed_texts(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, fake_router: FakeRouter
) -> None:
    """Both branches always run; neither side is silently dropped."""
    fake_router.query_type = "MIXED_QUERY"
    body = _ask(client, AMBIGUOUS_DSCR)
    assert body["answered"] is False and body["query_type"] == "MIXED_QUERY"
    assert body["answer"] == (
        f"{DOCUMENT_PART_HEADING}\n{NO_ANSWER_TEXT}\n\n"
        f"{DATA_PART_HEADING}\n{excel_ask_module.NO_DATA_TEXT}"
    )
    assert fake_llm.requests == [] and body["sources"] == [] and body["excel_sources"] == []


# ---------------------------------------------------------------- DATA / DOCUMENT


def test_data_question_runs_the_excel_pipeline_through_api_ask(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    _upload_workbook(client)
    fake_router.query_type = "DATA_QUERY"
    fake_llm.replies = [
        json.dumps({"kind": "function", "name": "dscr", "params": {"period": "Q2_2026"}}),
        "Ankara RES'in 2026 Q2 DSCR değeri 1,37x.",
    ]
    body = _ask(client, "Ankara RES 2026 Q2 DSCR kaç?")
    assert body["query_type"] == "DATA_QUERY" and body["answered"] is True
    assert body["notice"] == EXCEL_NOTICE
    assert body["sources"] == []
    assert body["excel_sources"][0]["label"] == "Covenant_Report.xlsx Q2_2026!D14"  # type: ignore[index]
    assert "1,37x" in str(body["answer"])
    rows = _audit_rows(db_session)
    assert len(rows) == 1 and rows[0].query_type == "DATA_QUERY"
    assert rows[0].excel_files_used == ["Covenant_Report.xlsx"]
    assert rows[0].sources[0]["kind"] == "excel"


def test_data_miss_falls_back_to_the_document_pipeline(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    """Phase 4.3 eval finding: "yerli banka kredisi ne kadar?" was routed DATA, no workbook
    holds it → instead of the Excel dead end the original question runs through the
    document pipeline (pre-router behaviour); the audit row records the path taken."""
    from tests.test_ask import _document

    _document(
        db_session,
        title="Facility Agreement",
        department=None,
        text="Yerli banka kredisi 20.400.000 EUR, ECA kredisi 30.000.000 EUR.",
    )
    _upload_workbook(client)  # a workbook exists, but the planner finds nothing in it
    fake_router.query_type = "DATA_QUERY"
    fake_llm.replies = [
        json.dumps({"kind": "none", "reason": "not in workbooks"}),
        "Yerli banka kredisi 20.400.000 EUR'dur [K1].",
    ]
    body = _ask(client, "Ankara RES finansmanında yerli banka kredisi ne kadar?")
    assert body["query_type"] == "DOCUMENT_QUERY" and body["answered"] is True
    assert body["notice"] == NO_INTERPRETATION_NOTICE
    assert body["sources"][0]["title"] == "Facility Agreement"  # type: ignore[index]
    assert body["excel_sources"] == []
    assert len(fake_llm.requests) == 2  # plan (miss) + document answer, no phrasing call
    rows = _audit_rows(db_session)
    assert len(rows) == 1 and rows[0].query_type == "DOCUMENT_QUERY"
    assert rows[0].sources[0]["kind"] == "document" and rows[0].excel_files_used == []


def test_data_miss_without_documents_is_the_plain_no_answer(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient, fake_router: FakeRouter
) -> None:
    fake_router.query_type = "DATA_QUERY"
    body = _ask(client, "Ankara RES 2026 Q2 DSCR kaç?")  # no workbook, no document
    assert body["answered"] is False and body["answer"] == NO_ANSWER_TEXT
    assert body["query_type"] == "DOCUMENT_QUERY" and fake_llm.requests == []


def test_document_question_is_unchanged_and_tagged(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    from tests.test_ask import _document

    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    body = _ask(client, "DSCR covenant nedir?")
    assert body["query_type"] == "DOCUMENT_QUERY" and body["answered"] is True
    assert body["notice"] == NO_INTERPRETATION_NOTICE and body["excel_sources"] == []
    rows = _audit_rows(db_session)
    assert len(rows) == 1 and rows[0].query_type == "DOCUMENT_QUERY"
    assert rows[0].sources[0]["kind"] == "document"


# GENERAL_QUERY (general-knowledge answers with no company source) was removed 30.09.2026 —
# the system must never answer from the model's own world knowledge; every question,
# including definitions, now routes through DOCUMENT_QUERY. The tests that lived here
# (no-company-data notice, project-name leak guard) went with `general_answer.py`.


# ---------------------------------------------------------------- wiring / failure


def test_real_router_wiring_falls_back_to_document_on_bad_json(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    """`get_router` really builds an `LLMRouter` over the same LLM client: the first call is
    the classification (json_object, classify model); a garbage reply degrades to DOCUMENT."""
    from tests.test_ask import _document

    app.dependency_overrides.pop(get_router, None)
    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    fake_llm.replies = ["<<not json>>", "Covenant 1,25x [K1]."]
    body = _ask(client, "DSCR covenant nedir?")
    assert body["query_type"] == "DOCUMENT_QUERY" and body["answered"] is True
    assert fake_llm.requests[0].system == ROUTER_SYSTEM_PROMPT
    assert fake_llm.requests[0].response_format == "json_object"
    assert len(fake_llm.requests) == 2


def test_llm_failure_inside_a_mixed_call_writes_one_error_row_and_503s(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    from tests.test_ask import _document

    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    fake_router.query_type = "MIXED_QUERY"
    fake_llm.error = LLMRateLimitError("quota exceeded for key sk-secret")
    response = client.post("/api/ask", json={"question": AMBIGUOUS_DSCR})
    assert response.status_code == 503 and response.json()["detail"] == LLM_UNAVAILABLE_MESSAGE
    assert "sk-secret" not in response.text
    rows = _audit_rows(db_session)
    assert len(rows) == 1 and rows[0].query_type == "MIXED_QUERY"
    assert rows[0].error and "quota" in rows[0].error


# ---------------------------------------------------------------- Aşama A (30.09.2026)
# `audit_log_id`, `product_level`, `warnings` and the P1-only degrade rule — the
# AI-BalBal answer-loop contract (docs/plans/ASAMA_A_BALBAL_DONGUSU_PLAN.md).


def test_answer_returns_the_id_of_its_single_audit_row_with_product_level(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    _upload_workbook(client)
    fake_router.query_type = "DATA_QUERY"
    fake_llm.replies = [
        json.dumps({"kind": "function", "name": "dscr", "params": {"period": "Q2_2026"}}),
        "Ankara RES'in 2026 Q2 DSCR değeri 1,37x.",
    ]
    body = _ask(client, "Ankara RES 2026 Q2 DSCR kaç?")
    rows = _audit_rows(db_session)
    assert len(rows) == 1
    assert body["audit_log_id"] == str(rows[0].id)
    assert body["product_level"] == "P2" and rows[0].product_level == "P2"
    assert body["warnings"] == [] and rows[0].warnings == []


def test_product_level_follows_the_final_query_type(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    """DOCUMENT → P1. A DATA routing that misses and falls through to documents is a
    document answer, so it is P1 too — the level describes what was produced, not what
    the router guessed."""
    from tests.test_ask import _document

    _document(db_session, title="A", department=None, text="Yerli banka kredisi 20.400.000 EUR.")
    fake_llm.replies = ["Yerli banka kredisi 20.400.000 EUR'dur [K1]."]
    body = _ask(client, "Yerli banka kredisi ne kadar?")
    assert body["query_type"] == "DOCUMENT_QUERY" and body["product_level"] == "P1"

    _upload_workbook(client)
    fake_router.query_type = "DATA_QUERY"
    fake_llm.replies = [
        json.dumps({"kind": "none", "reason": "not in workbooks"}),
        "Yerli banka kredisi 20.400.000 EUR'dur [K1].",
    ]
    body = _ask(client, "Ankara RES finansmanında yerli banka kredisi ne kadar?")
    assert body["query_type"] == "DOCUMENT_QUERY" and body["product_level"] == "P1"
    rows = _audit_rows(db_session)
    assert [row.product_level for row in rows] == ["P1", "P1"]


def test_no_answer_carries_a_missing_data_warning_with_the_request_data_action(
    client: TestClient, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    body = _ask(client, "İzmir RES'in COD tarihi nedir?")  # nothing to retrieve
    assert body["answered"] is False
    assert body["warnings"] == [
        {"kind": "missing_data", "message": MISSING_DATA_WARNING, "action": "request_data"}
    ]


def test_p1_only_degrades_a_data_routing_to_documents_with_a_product_limit_warning(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    fake_router: FakeRouter,
) -> None:
    """NOT §6.2: P2 closed → the question is not refused; it is answered from documents
    only (the covenant report PDF, not the workbook), the answer says why, and the Excel
    engine is never consulted."""
    from tests.test_ask import _document

    _document(
        db_session,
        title="Covenant Report Q2 2026",
        department=None,
        text="2026 Q2 DSCR 1,37x olarak hesaplanmıştır.",
    )
    _upload_workbook(client)
    company_settings_repo.set_enabled_products(db_session, ["P1"])
    fake_router.query_type = "DATA_QUERY"
    fake_llm.replies = ["2026 Q2 DSCR 1,37x'tir [K1]."]

    body = _ask(client, "Ankara RES 2026 Q2 DSCR kaç?")

    assert fake_router.questions == ["Ankara RES 2026 Q2 DSCR kaç?"]  # still classified
    assert body["query_type"] == "DOCUMENT_QUERY" and body["product_level"] == "P1"
    assert body["answered"] is True and body["excel_sources"] == []
    assert body["sources"][0]["title"] == "Covenant Report Q2 2026"  # type: ignore[index]
    assert body["warnings"] == [
        {"kind": "product_limit", "message": PRODUCT_LIMIT_WARNING, "action": None}
    ]
    assert all(r.system != PLAN_SYSTEM_PROMPT for r in fake_llm.requests)
    rows = _audit_rows(db_session)
    assert len(rows) == 1 and rows[0].query_type == "DOCUMENT_QUERY"
    assert rows[0].product_level == "P1" and rows[0].warnings[0]["kind"] == "product_limit"


def test_p1_only_leaves_a_document_routing_untouched(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    from tests.test_ask import _document

    _document(db_session, title="A", department=None, text="DSCR covenant 1,25x")
    company_settings_repo.set_enabled_products(db_session, ["P1"])
    body = _ask(client, "DSCR covenant nedir?")
    assert body["query_type"] == "DOCUMENT_QUERY" and body["warnings"] == []
