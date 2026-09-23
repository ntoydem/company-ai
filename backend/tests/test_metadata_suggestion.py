"""AI metadata suggestion (SPEC_02 §4, Phase 3.2): `metadata_suggestion.py` service +
`document_metadata_suggestion_repo`. No HTTP here — the endpoint-level tests (auth,
apply/reject wiring) live in `test_documents.py`."""

from __future__ import annotations

import json
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document, IngestionStatus
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.document_page import DocumentPage
from app.models.project import ProjectStage
from app.models.user import User
from app.repositories import department_repo, document_metadata_suggestion_repo, project_repo
from app.services import metadata_suggestion
from app.services.llm import LLMRateLimitError
from tests.fakes import FakeLLMClient


def _document(session: Session, *, text: str) -> Document:
    document = Document(
        title="Facility Agreement",
        document_type="facility_agreement",
        counterparty="PQR Bank",
        document_date=date(2023, 6, 1),
        storage_path=f"{uuid.uuid4()}/original.pdf",
    )
    session.add(document)
    session.flush()
    session.add(DocumentPage(document_id=document.id, page_number=1, text=text))
    session.commit()
    return document


def _classify_reply(
    *, department: str | None, project_code: str | None, document_type: str = "facility_agreement"
) -> str:
    def field(value: object, confidence: float = 0.9) -> dict[str, object]:
        return {"value": value, "confidence": confidence}

    return json.dumps(
        {
            "department": field(department),
            "subdepartment": field(None, 0.0),
            "project_code": field(project_code),
            "document_type": field(document_type),
            "counterparty": field("PQR Bank"),
            "document_date": field("2023-06-01"),
            "status": field("executed"),
            "confidentiality": field("normal"),
            "tags": field(["facility", "kredi"], 0.7),
        }
    )


def test_suggest_metadata_classifies_document_with_confidence(
    db_session: Session, settings: Settings
) -> None:
    """Kabul kriteri: Facility Agreement upload → öneri Finans/Ankara/Facility Agreement +
    confidence (docs/plans/PHASE_3_2_PLAN.md §9)."""
    department_repo.create(db_session, name="Finans", slug="finans")
    project_repo.create(
        db_session,
        name="Ankara RES",
        code="ANK_RES",
        stage=ProjectStage.operation,
        department_ids=[],
    )
    document = _document(db_session, text="Facility Agreement between DEF Enerji and PQR Bank...")
    fake = FakeLLMClient(replies=[_classify_reply(department="finans", project_code="ANK_RES")])

    suggestion = metadata_suggestion.suggest_metadata(db_session, document, fake, settings)

    assert suggestion.status == SuggestionStatus.pending
    assert suggestion.fields["department"] == {"value": "finans", "confidence": 0.9}
    assert suggestion.fields["project_code"] == {"value": "ANK_RES", "confidence": 0.9}
    assert suggestion.fields["document_type"]["value"] == "facility_agreement"
    assert document.ai_suggestion_id == suggestion.id
    # `response_format` reached the LLM as JSON mode, not the default `/api/ask` text mode.
    assert fake.requests[0].response_format == "json_object"
    assert fake.requests[0].model == settings.llm_model_classify


def test_suggest_metadata_llm_error_is_caught_and_stored_as_failed(
    db_session: Session, settings: Settings
) -> None:
    """Kabul kriteri: LLM hatası upload'ı bozmaz — burada "bozmaz" == exception dışarı
    sızmaz, `failed` durumunda bir satır yazılır."""
    document = _document(db_session, text="...")
    fake = FakeLLMClient(error=LLMRateLimitError("quota exceeded"))

    suggestion = metadata_suggestion.suggest_metadata(db_session, document, fake, settings)

    assert suggestion.status == SuggestionStatus.failed
    assert suggestion.error is not None and "quota exceeded" in suggestion.error
    assert suggestion.fields == {}
    assert document.ai_suggestion_id == suggestion.id


def test_suggest_metadata_drops_department_outside_whitelist(
    db_session: Session, settings: Settings
) -> None:
    """The model cannot invent a department that doesn't exist — mirrors ADR-013's
    placeholder-only discipline for prose generation."""
    department_repo.create(db_session, name="Finans", slug="finans")
    document = _document(db_session, text="...")
    fake = FakeLLMClient(
        replies=[_classify_reply(department="hayali_departman", project_code=None)]
    )

    suggestion = metadata_suggestion.suggest_metadata(db_session, document, fake, settings)

    assert suggestion.fields["department"] == {"value": None, "confidence": 0.0}


def test_suggest_metadata_drops_unknown_project_code(
    db_session: Session, settings: Settings
) -> None:
    document = _document(db_session, text="...")
    fake = FakeLLMClient(replies=[_classify_reply(department=None, project_code="HAYALI_PRJ")])

    suggestion = metadata_suggestion.suggest_metadata(db_session, document, fake, settings)

    assert suggestion.fields["project_code"] == {"value": None, "confidence": 0.0}


def test_suggest_metadata_overwrites_a_previous_failed_attempt(
    db_session: Session, settings: Settings
) -> None:
    document = _document(db_session, text="...")
    failing = FakeLLMClient(error=LLMRateLimitError("quota exceeded"))
    first = metadata_suggestion.suggest_metadata(db_session, document, failing, settings)
    assert first.status == SuggestionStatus.failed

    ok = FakeLLMClient(replies=[_classify_reply(department=None, project_code=None)])
    second = metadata_suggestion.suggest_metadata(db_session, document, ok, settings)

    assert second.id == first.id  # same row, overwritten (one suggestion per document)
    assert second.status == SuggestionStatus.pending
    assert second.error is None


def test_fetch_pending_candidates_only_returns_ready_documents_without_a_suggestion(
    db_session: Session,
) -> None:
    ready = _document(db_session, text="a")
    ready.ingestion_status = IngestionStatus.ready
    not_ready = _document(db_session, text="b")
    db_session.commit()

    candidates = metadata_suggestion.fetch_pending_candidates(db_session, limit=10)

    assert [d.id for d in candidates] == [ready.id]
    assert not_ready.id not in [d.id for d in candidates]


def test_run_pending_scan_classifies_every_candidate_in_the_batch(
    db_session: Session, settings: Settings
) -> None:
    first = _document(db_session, text="a")
    first.ingestion_status = IngestionStatus.ready
    second = _document(db_session, text="b")
    second.ingestion_status = IngestionStatus.ready
    db_session.commit()
    fake = FakeLLMClient()
    fake.reply_fn = lambda _: _classify_reply(department=None, project_code=None)

    processed = metadata_suggestion.run_pending_scan(db_session, fake, settings, limit=10)

    assert processed == 2
    assert len(fake.requests) == 2
    assert first.ai_suggestion_id is not None
    assert second.ai_suggestion_id is not None


# --- document_metadata_suggestion_repo ---


def test_upsert_creates_then_overwrites_the_single_row_per_document(db_session: Session) -> None:
    document = _document(db_session, text="a")

    first = document_metadata_suggestion_repo.upsert(
        db_session,
        document_id=document.id,
        model="fake-model",
        status=SuggestionStatus.pending,
        fields={"department": {"value": "finans", "confidence": 0.5}},
    )
    second = document_metadata_suggestion_repo.upsert(
        db_session,
        document_id=document.id,
        model="fake-model",
        status=SuggestionStatus.failed,
        fields={},
        error="boom",
    )

    assert second.id == first.id
    assert second.status == SuggestionStatus.failed
    assert second.error == "boom"
    assert second.fields == {}


def test_mark_applied_and_mark_rejected(db_session: Session, admin_user: User) -> None:
    document = _document(db_session, text="a")
    suggestion = document_metadata_suggestion_repo.upsert(
        db_session,
        document_id=document.id,
        model="fake-model",
        status=SuggestionStatus.pending,
        fields={},
    )

    document_metadata_suggestion_repo.mark_applied(
        db_session, suggestion, applied_by_id=admin_user.id
    )
    assert suggestion.status == SuggestionStatus.applied
    assert suggestion.applied_by_id == admin_user.id
    assert suggestion.applied_at is not None

    document_metadata_suggestion_repo.mark_rejected(db_session, suggestion)
    assert suggestion.status == SuggestionStatus.rejected
