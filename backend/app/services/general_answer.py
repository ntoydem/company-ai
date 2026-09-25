"""GENERAL_QUERY branch (ADR-010, Phase 4.3 SORU 4): a short definition from the model's
general knowledge, with no retrieval, no workbook, no authorization lookup — nothing from
the company reaches the prompt, and the answer says so (`GENERAL_NOTICE` is prepended by
code, never left to the model).

Leak guard: the model is told not to mention any company, project or figure; if the reply
still contains a project name or a money amount, the reply is dropped and a fixed text is
returned instead — a GENERAL answer must never look like a sourced company statement."""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass

from app.core.config import Settings
from app.schemas.ask import GENERAL_NOTICE
from app.services.llm import LLMClient, LLMRequest
from app.services.search_query import turkish_lower

log = logging.getLogger(__name__)

GENERAL_SYSTEM_PROMPT = (
    "Sen bir genel bilgi asistanısın. Kullanıcının sorusu şirkete özgü değil, genel bir "
    "kavram/tanım sorusudur. Türkçe, en fazla üç kısa cümleyle tanımı veya açıklamayı ver. "
    "KURALLAR: 1. Hiçbir şirkete, projeye, belgeye, sözleşmeye veya rakama atıf yapma; örnek "
    "tutar veya oran verme. 2. Yorum, tavsiye, tahmin, projeksiyon yazma. 3. Kaynak etiketi "
    "ekleme. 4. Soru başka dildeyse o dilde cevapla."
)

GENERAL_LEAK_TEXT = (
    "Genel tanım üretilirken şirket verisine benzeyen bir ifade tespit edildiği için cevap "
    "gösterilmiyor. Şirket belgelerine dayalı bir cevap için sorunuzu proje veya belge adıyla "
    "yeniden sorun."
)

# "44.100.000 EUR", "1,2 milyon TL", "€ 5.000" — a figure with a currency next to it.
_MONEY = re.compile(
    r"(\d[\d.,]*\s*(?:milyon|milyar|bin)?\s*(?:EUR|USD|TRY|TL|€|\$)|(?:EUR|USD|TRY|TL|€|\$)\s*\d)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GeneralResult:
    answer: str
    answered: bool
    model: str | None
    tokens_in: int
    tokens_out: int


def leaks_company_data(text: str, forbidden_terms: Iterable[str]) -> bool:
    lowered = turkish_lower(text)
    if any(turkish_lower(term) in lowered for term in forbidden_terms if term):
        return True
    return _MONEY.search(text) is not None


def answer_general(
    question: str, llm: LLMClient, settings: Settings, *, forbidden_terms: Iterable[str]
) -> GeneralResult:
    response = llm.complete(
        LLMRequest(
            system=GENERAL_SYSTEM_PROMPT,
            user=question,
            model=settings.llm_model_answer,
            max_output_tokens=settings.llm_max_output_tokens,
            reasoning_effort=settings.llm_reasoning_effort,
        )
    )
    text = response.text.strip()
    if not text or leaks_company_data(text, forbidden_terms):
        log.warning("general answer dropped (empty or company-like content)")
        return GeneralResult(
            answer=f"{GENERAL_NOTICE}\n\n{GENERAL_LEAK_TEXT}",
            answered=False,
            model=response.model,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
        )
    return GeneralResult(
        answer=f"{GENERAL_NOTICE}\n\n{text}",
        answered=True,
        model=response.model,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
    )
