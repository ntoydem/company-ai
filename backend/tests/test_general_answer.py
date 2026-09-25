"""GENERAL_QUERY answering (Phase 4.3 SORU 4): notice prepended by code, leak guard."""

from __future__ import annotations

from app.core.config import Settings
from app.schemas.ask import GENERAL_NOTICE
from app.services.general_answer import (
    GENERAL_LEAK_TEXT,
    GENERAL_SYSTEM_PROMPT,
    answer_general,
    leaks_company_data,
)
from tests.fakes import FakeLLMClient


def test_definition_is_prefixed_with_the_notice(settings: Settings) -> None:
    fake = FakeLLMClient(replies=["DSCR, borç servisi karşılama oranıdır."])
    result = answer_general("DSCR ne demek?", fake, settings, forbidden_terms=["Ankara RES"])
    assert result.answered is True
    assert result.answer == f"{GENERAL_NOTICE}\n\nDSCR, borç servisi karşılama oranıdır."
    request = fake.requests[0]
    assert request.system == GENERAL_SYSTEM_PROMPT and request.user == "DSCR ne demek?"
    assert request.model == settings.llm_model_answer


def test_leak_guard_patterns() -> None:
    projects = ["Ankara RES", "İzmir RES"]
    assert leaks_company_data("Ankara RES'in DSCR'i 1,37x.", projects)
    assert leaks_company_data("izmir res için geçerlidir", projects)  # case-insensitive
    assert leaks_company_data("Örneğin 44.100.000 EUR kalan borç", [])
    assert leaks_company_data("yaklaşık 1,2 milyon TL", [])
    assert leaks_company_data("€ 5.000 civarı", [])
    assert not leaks_company_data(
        "DSCR = CFADS / borç servisi; 1,0 üzeri yeterli demektir.", projects
    )
    assert not leaks_company_data("RES, rüzgar enerji santrali demektir.", projects)


def test_company_like_reply_is_dropped(settings: Settings) -> None:
    fake = FakeLLMClient(replies=["Ankara RES'in güncel DSCR'i 1,37x'tir."])
    result = answer_general("DSCR ne demek?", fake, settings, forbidden_terms=["Ankara RES"])
    assert result.answered is False
    assert result.answer == f"{GENERAL_NOTICE}\n\n{GENERAL_LEAK_TEXT}"


def test_empty_reply_is_dropped(settings: Settings) -> None:
    fake = FakeLLMClient(replies=["   "])
    result = answer_general("DSCR ne demek?", fake, settings, forbidden_terms=[])
    assert result.answered is False and GENERAL_LEAK_TEXT in result.answer
