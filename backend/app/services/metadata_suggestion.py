"""AI metadata suggestion (SPEC_02 §4, Phase 3.2).

`suggest_metadata()` classifies one `ready` document with `LLM_MODEL_CLASSIFY` and stores
the result in `document_metadata_suggestions`; nothing here ever writes to `documents` —
only `POST /api/documents/{id}/metadata-suggestion/apply` does that, on an explicit admin
call (ADR-006: a suggestion, and its failure, never touches the upload/document itself).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document
from app.models.document_metadata_suggestion import DocumentMetadataSuggestion, SuggestionStatus
from app.repositories import (
    department_repo,
    document_metadata_suggestion_repo,
    document_repo,
    project_repo,
)
from app.services.llm import LLMClient, LLMError, LLMRequest

log = logging.getLogger(__name__)

MAX_LEADING_PAGES = 3

_DOCUMENT_TYPE_CHOICES = (
    "facility_agreement, licence, licence_amendment, epc_contract, technical_report, "
    "cod_certificate, covenant_report, production_report, board_resolution, eia_status_letter, "
    "land_acquisition_report, pre_licence_document"
)
_STATUS_CHOICES = (
    "draft, executed, amended"  # `superseded`/`active` are system-managed, never AI-suggested
)
_CONFIDENTIALITY_CHOICES = "normal, restricted, board"

_FIELDS = (
    "department",
    "subdepartment",
    "project_code",
    "document_type",
    "counterparty",
    "document_date",
    "status",
    "confidentiality",
    "tags",
)


class _FieldGuess(BaseModel):
    value: str | list[str] | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class _ClassifyResponse(BaseModel):
    department: _FieldGuess = Field(default_factory=_FieldGuess)
    subdepartment: _FieldGuess = Field(default_factory=_FieldGuess)
    project_code: _FieldGuess = Field(default_factory=_FieldGuess)
    document_type: _FieldGuess = Field(default_factory=_FieldGuess)
    counterparty: _FieldGuess = Field(default_factory=_FieldGuess)
    document_date: _FieldGuess = Field(default_factory=_FieldGuess)
    status: _FieldGuess = Field(default_factory=_FieldGuess)
    confidentiality: _FieldGuess = Field(default_factory=_FieldGuess)
    tags: _FieldGuess = Field(default_factory=_FieldGuess)


def _build_prompt(
    text: str, *, department_slugs: list[str], project_codes: list[str]
) -> tuple[str, str]:
    system = (
        "Sen bir belge sınıflandırma asistanısın. Sana bir şirket belgesinin ilk sayfalarının "
        "metni verilir; görevin metadata alanlarını tahmin etmektir. Yalnızca verilen metinden "
        "çıkarım yap, uydurma. Emin değilsen alanın değerini null bırak ve confidence'ı düşük "
        "tut. Yalnızca geçerli bir JSON nesnesi döndür, başka hiçbir metin ekleme.\n\n"
        f"department: yalnızca şu listeden bir slug, veya null: {', '.join(department_slugs)}\n"
        f"project_code: yalnızca şu listeden bir kod, veya null (belge bir projeye ait değilse "
        f"null): {', '.join(project_codes)}\n"
        f"document_type: tercihen şunlardan biri: {_DOCUMENT_TYPE_CHOICES}\n"
        f"status: yalnızca şunlardan biri: {_STATUS_CHOICES}\n"
        f"confidentiality: yalnızca şunlardan biri: {_CONFIDENTIALITY_CHOICES}\n"
        "document_date: YYYY-MM-DD biçiminde.\n"
        "tags: kısa anahtar kelimelerden oluşan bir liste.\n"
        'Her alan için {"value": ..., "confidence": 0.0-1.0} şeklinde bir nesne döndür; '
        f"tam olarak şu alanları içer: {', '.join(_FIELDS)}."
    )
    user = f"BELGE METNİ (ilk {MAX_LEADING_PAGES} sayfa):\n\n{text}"
    return system, user


def _sanitize(
    parsed: _ClassifyResponse, *, department_slugs: set[str], project_codes: set[str]
) -> dict[str, Any]:
    """Values outside the given whitelist are dropped (confidence 0) rather than trusted —
    the model cannot invent a department/project that does not exist (mirrors the
    placeholder-only discipline of ADR-013's prose generation)."""
    fields = parsed.model_dump()
    department = fields["department"]
    if isinstance(department["value"], str) and department["value"] not in department_slugs:
        department["value"], department["confidence"] = None, 0.0
    project = fields["project_code"]
    if isinstance(project["value"], str) and project["value"] not in project_codes:
        project["value"], project["confidence"] = None, 0.0
    status = fields["status"]
    if isinstance(status["value"], str) and status["value"] not in {"draft", "executed", "amended"}:
        status["value"], status["confidence"] = None, 0.0
    confidentiality = fields["confidentiality"]
    if isinstance(confidentiality["value"], str) and confidentiality["value"] not in {
        "normal",
        "restricted",
        "board",
    }:
        confidentiality["value"], confidentiality["confidence"] = None, 0.0
    return fields


def suggest_metadata(
    session: Session, document: Document, llm: LLMClient, settings: Settings
) -> DocumentMetadataSuggestion:
    """Classify `document` (must be `ready`) and store the result — overwriting any
    previous suggestion for it. LLM failure is caught here and stored as `status=failed`;
    it never propagates (ADR-006: a suggestion failure never breaks anything else)."""
    department_slugs = [d.slug for d in department_repo.list_all(session)]
    project_codes = [p.code for p in project_repo.list_all(session)]
    text = document_repo.get_leading_page_text(session, document.id, max_pages=MAX_LEADING_PAGES)
    system, user = _build_prompt(
        text, department_slugs=department_slugs, project_codes=project_codes
    )

    try:
        response = llm.complete(
            LLMRequest(
                system=system,
                user=user,
                model=settings.llm_model_classify,
                max_output_tokens=settings.llm_max_output_tokens,
                reasoning_effort=settings.llm_reasoning_effort,
                response_format="json_object",
            )
        )
        parsed = _ClassifyResponse.model_validate(json.loads(response.text))
    except (LLMError, json.JSONDecodeError, ValidationError) as exc:
        log.warning(
            "metadata suggestion failed", extra={"document_id": str(document.id), "error": str(exc)}
        )
        suggestion = document_metadata_suggestion_repo.upsert(
            session,
            document_id=document.id,
            model=settings.llm_model_classify,
            status=SuggestionStatus.failed,
            fields={},
            error=str(exc),
        )
    else:
        fields = _sanitize(
            parsed, department_slugs=set(department_slugs), project_codes=set(project_codes)
        )
        suggestion = document_metadata_suggestion_repo.upsert(
            session,
            document_id=document.id,
            model=response.model,
            status=SuggestionStatus.pending,
            fields=fields,
        )

    document.ai_suggestion_id = suggestion.id
    session.commit()
    log.info(
        "metadata suggestion stored",
        extra={"document_id": str(document.id), "status": suggestion.status.value},
    )
    return suggestion


def fetch_pending_candidates(session: Session, *, limit: int) -> list[Document]:
    """`ready` documents with no suggestion attempt yet (Phase 3.2 background scan and the
    explicit `POST .../suggest-metadata` endpoint share this same candidate set)."""
    ids = document_repo.list_ids_pending_suggestion(session, limit=limit)
    return document_repo.get_many(session, ids)


def run_pending_scan(session: Session, llm: LLMClient, settings: Settings, *, limit: int) -> int:
    """One batch of the background scan (§3 of the plan): classify up to `limit` waiting
    documents. Returns how many were processed."""
    candidates = fetch_pending_candidates(session, limit=limit)
    for document in candidates:
        suggest_metadata(session, document, llm, settings)
    return len(candidates)
