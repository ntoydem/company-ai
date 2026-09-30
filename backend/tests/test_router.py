"""`LLMRouter` (ADR-010, Phase 4.3) with a fake LLM: the four types, sub-question
normalisation, and the DOCUMENT fallback on every failure mode."""

from __future__ import annotations

import json

from app.core.config import Settings
from app.services.llm import LLMRateLimitError
from app.services.router import ROUTER_SYSTEM_PROMPT, LLMRouter, RoutedQuestion
from tests.fakes import FakeLLMClient

QUESTION = "Güncel DSCR kaç?"


def _route(settings: Settings, reply: str | None, *, error: bool = False) -> RoutedQuestion:
    fake = FakeLLMClient(
        replies=[reply] if reply is not None else [],
        error=LLMRateLimitError("quota") if error else None,
    )
    routed = LLMRouter(fake, settings).route(QUESTION)
    if not error:
        request = fake.requests[0]
        assert request.system == ROUTER_SYSTEM_PROMPT
        assert request.model == settings.llm_model_classify
        assert request.response_format == "json_object"
        assert request.user == f"Q: {QUESTION}"
    return routed


def test_document_type_always_runs_the_original_question(settings: Settings) -> None:
    reply = json.dumps(
        {"query_type": "DOCUMENT_QUERY", "document_question": "rewritten", "reason": "r"}
    )
    routed = _route(settings, reply)
    assert routed.query_type == "DOCUMENT_QUERY"
    assert routed.document_question == QUESTION  # never the model's rewrite
    assert routed.data_question is None
    assert (routed.model, routed.tokens_in, routed.tokens_out) == ("fake-model", 123, 45)


def test_data_type_runs_the_original_question(settings: Settings) -> None:
    routed = _route(settings, json.dumps({"query_type": "DATA_QUERY"}))
    assert routed.query_type == "DATA_QUERY"
    assert routed.document_question is None and routed.data_question == QUESTION


def test_mixed_uses_the_two_sub_questions(settings: Settings) -> None:
    reply = json.dumps(
        {
            "query_type": "MIXED_QUERY",
            "document_question": "Sözleşmedeki güncel minimum DSCR covenant'ı nedir?",
            "data_question": "En son çeyreğin gerçekleşen DSCR değeri kaç?",
            "reason": "ambiguous",
        }
    )
    routed = _route(settings, reply)
    assert routed.query_type == "MIXED_QUERY"
    assert routed.document_question == "Sözleşmedeki güncel minimum DSCR covenant'ı nedir?"
    assert routed.data_question == "En son çeyreğin gerçekleşen DSCR değeri kaç?"


def test_mixed_with_missing_sub_questions_falls_back_to_the_original(settings: Settings) -> None:
    reply = json.dumps(
        {"query_type": "MIXED_QUERY", "document_question": "  ", "data_question": None}
    )
    routed = _route(settings, reply)
    assert routed.query_type == "MIXED_QUERY"
    assert routed.document_question == QUESTION and routed.data_question == QUESTION


def test_malformed_json_unknown_type_and_llm_error_fall_back_to_document(
    settings: Settings,
) -> None:
    """The safe direction: a router failure degrades to the pre-4.3 behaviour. GENERAL_QUERY
    itself (removed 30.09.2026) is now just another unknown type — Pydantic rejects it as
    an invalid `QueryType` literal and it falls back to DOCUMENT_QUERY like `EMAIL_QUERY`,
    never to a general-knowledge answer without company sources."""
    for reply in (
        "not json",
        json.dumps({"query_type": "EMAIL_QUERY"}),
        json.dumps({"query_type": "GENERAL_QUERY", "reason": "definition"}),
        json.dumps([1, 2]),
    ):
        routed = _route(settings, reply)
        assert routed.query_type == "DOCUMENT_QUERY", reply
        assert routed.document_question == QUESTION and routed.data_question is None
        assert routed.reason.startswith("fallback:")
    routed = _route(settings, None, error=True)
    assert routed.query_type == "DOCUMENT_QUERY" and routed.reason == "fallback: LLMRateLimitError"
