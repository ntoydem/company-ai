"""Question router (ADR-010, Phase 4.3): one cheap `LLM_MODEL_CLASSIFY` call decides
whether a `/api/ask` question is answered from documents, from Excel workbooks, from both
(MIXED — two sub-questions) or from general knowledge (GENERAL — no company data).

Fixed interface (`Router.route`) so a later "Email AI" branch is a new implementation
detail, not a caller change. Any router failure — LLM error, malformed JSON, unknown type
— degrades to `DOCUMENT_QUERY` with the original question: the pre-4.3 behaviour, and the
safe direction (a wrongly-GENERAL answer would drop company sources; a wrongly-DOCUMENT
answer at worst says it found nothing)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, ValidationError

from app.core.config import Settings
from app.schemas.ask import QueryType
from app.services.llm import LLMClient, LLMError, LLMRequest

log = logging.getLogger(__name__)

ROUTER_SYSTEM_PROMPT = (
    "You classify ONE user question for a company knowledge system that holds (a) company "
    "documents — contracts, licences, amendments, reports; text with page-level sources — and "
    "(b) Excel workbooks — financial model, covenant report, budget vs actual, monthly "
    "production; figures computed by a calculation engine. Reply with ONE JSON object and "
    "nothing else:\n"
    '{"query_type":"DOCUMENT_QUERY"|"DATA_QUERY"|"MIXED_QUERY"|"GENERAL_QUERY",'
    '"document_question":<string or null>,"data_question":<string or null>,'
    '"reason":<short string>}\n'
    "Types:\n"
    "- DOCUMENT_QUERY: answered by reading what a document states (contract terms, covenant "
    "thresholds, dates, licence conditions, reasons written in a report). A number that is "
    "*stated* in a contract, licence or report — loan or tranche amounts, tenor, agreed "
    "thresholds, a reported test result — is still DOCUMENT_QUERY.\n"
    "- DATA_QUERY: answered by computing or reading a figure from workbook cells for a period "
    "(realised/actual values, totals, sums, variances, ratios, production, balances from the "
    "model).\n"
    "- MIXED_QUERY: needs BOTH a document statement AND a computed figure; or the question is "
    "ambiguous between a contractual/agreed value and a realised/measured value (e.g. 'current "
    "DSCR?' may mean the covenant threshold in the loan agreement or the realised DSCR in the "
    "covenant workbook). Then document_question asks for the contractual/stated side and "
    "data_question asks for the realised/computed side; each must be self-contained.\n"
    "- GENERAL_QUERY: general knowledge that refers to no company, project, document or figure "
    "(a definition, how a concept works).\n"
    "Rules: 1. If in doubt between DOCUMENT_QUERY and GENERAL_QUERY choose DOCUMENT_QUERY. "
    "2. Write sub-questions in the language of the original question. 3. For DOCUMENT_QUERY "
    "and DATA_QUERY the sub-question fields may be null. 4. Never answer the question.\n"
    "Examples:\n"
    'Q: Kredi sözleşmesindeki DSCR covenant nedir? -> {"query_type":"DOCUMENT_QUERY",'
    '"document_question":null,"data_question":null,"reason":"contract term"}\n'
    'Q: 2026 EBITDA variance hangi projede en yüksek? -> {"query_type":"DATA_QUERY",'
    '"document_question":null,"data_question":null,"reason":"computed figure"}\n'
    "Q: Ankara RES finansmanında yerli banka kredisi ne kadar? -> "
    '{"query_type":"DOCUMENT_QUERY","document_question":null,"data_question":null,'
    '"reason":"amount stated in the facility agreement"}\n'
    "Q: Üretim düşüşünün finansal etkisini ve teknik nedenini açıkla. -> "
    '{"query_type":"MIXED_QUERY","document_question":"Üretim düşüşünün teknik nedeni '
    'belgelerde ne olarak belirtilmiş?","data_question":"Üretim düşüşünün finansal etkisi '
    '(bütçe sapması) kaç?","reason":"reason from documents + figure from workbook"}\n'
    'Q: Güncel DSCR kaç? -> {"query_type":"MIXED_QUERY","document_question":"Kredi '
    'sözleşmesindeki güncel minimum DSCR covenant\'ı nedir?","data_question":"En son '
    'çeyreğin gerçekleşen DSCR değeri kaç?","reason":"ambiguous: covenant vs realised"}\n'
    'Q: DSCR ne demek? -> {"query_type":"GENERAL_QUERY","document_question":null,'
    '"data_question":null,"reason":"definition"}'
)

ROUTER_MAX_OUTPUT_TOKENS = 300


@dataclass(frozen=True)
class RoutedQuestion:
    query_type: QueryType
    document_question: str | None  # DOCUMENT/MIXED: what the document pipeline is asked
    data_question: str | None  # DATA/MIXED: what the Excel pipeline is asked
    reason: str = ""
    model: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0


class Router(Protocol):
    def route(self, question: str) -> RoutedQuestion: ...


class _RouterResponse(BaseModel):
    query_type: QueryType
    document_question: str | None = None
    data_question: str | None = None
    reason: str = ""


def _clean(text: str | None) -> str | None:
    text = (text or "").strip()
    return text or None


def _normalize(question: str, parsed: _RouterResponse) -> tuple[str | None, str | None]:
    """DOCUMENT/DATA always run the *original* question (retrieval and planning behave
    exactly as before the router); only MIXED uses the rewritten sub-questions, falling
    back to the original when the model left one empty."""
    document = _clean(parsed.document_question)
    data = _clean(parsed.data_question)
    if parsed.query_type == "DOCUMENT_QUERY":
        return question, None
    if parsed.query_type == "DATA_QUERY":
        return None, question
    if parsed.query_type == "MIXED_QUERY":
        return document or question, data or question
    return None, None


def fallback(question: str, reason: str) -> RoutedQuestion:
    return RoutedQuestion(
        query_type="DOCUMENT_QUERY", document_question=question, data_question=None, reason=reason
    )


class LLMRouter:
    def __init__(self, llm: LLMClient, settings: Settings) -> None:
        self._llm = llm
        self._settings = settings

    def route(self, question: str) -> RoutedQuestion:
        try:
            response = self._llm.complete(
                LLMRequest(
                    system=ROUTER_SYSTEM_PROMPT,
                    user=f"Q: {question}",
                    model=self._settings.llm_model_classify,
                    max_output_tokens=ROUTER_MAX_OUTPUT_TOKENS,
                    response_format="json_object",
                )
            )
            parsed = _RouterResponse.model_validate(json.loads(response.text))
        except (LLMError, json.JSONDecodeError, ValidationError) as exc:
            log.warning("router failed, falling back to DOCUMENT_QUERY", extra={"error": str(exc)})
            return fallback(question, f"fallback: {type(exc).__name__}")
        document_question, data_question = _normalize(question, parsed)
        routed = RoutedQuestion(
            query_type=parsed.query_type,
            document_question=document_question,
            data_question=data_question,
            reason=parsed.reason,
            model=response.model,
            tokens_in=response.tokens_in,
            tokens_out=response.tokens_out,
        )
        log.info(
            "question routed",
            extra={
                "query_type": routed.query_type,
                "reason": routed.reason,
                "document_question": document_question,
                "data_question": data_question,
            },
        )
        return routed
