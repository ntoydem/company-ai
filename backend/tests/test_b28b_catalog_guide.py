"""B-28b (ADR-025): tag catalogue, document-type guide, extra fields in the B-28 flow,
classifier prompt, metadata search, prompt source line, seed. Plan `docs/plans/B28B_PLAN.md`
X-01…X-09 (X-10 regression/live runs separately). No real LLM."""

from __future__ import annotations

import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.admin_event import AdminEvent
from app.models.document import Document
from app.models.document_metadata_suggestion import SuggestionStatus
from app.models.tag_catalog import TagKind
from app.repositories import department_repo, guide_repo, project_repo, tag_repo
from app.services import metadata_suggestion, type_family
from app.services.answer_prompt import describe_metadata
from app.services.demo_catalog_seed import ensure_demo_catalog
from app.services.document_review import (
    EXTRA_PREFIX,
    ExtraFieldsError,
    flatten_suggestion,
    merge_extra_fields,
    normalize_extra_updates,
)
from app.services.type_family import DEFAULT_CHANGE_TAGS, DEFAULT_GUIDE, match_family
from tests.fakes import FakeLLMClient
from tests.test_ask import _ask
from tests.test_ask import _document as _chunked_document
from tests.test_document_review import Cast, _as, _events, _make_ready_with_chunk, _seed_suggestion
from tests.test_documents import _upload
from tests.test_metadata_suggestion import _document as _page_document

# ------------------------------------------------------------------ pure rules


def test_match_family_picks_the_most_specific_pattern() -> None:
    guides = list(DEFAULT_GUIDE)
    assert match_family("Facility Agreement", guides) == "contract"
    assert match_family("Licence Amendment", guides) == "amendment"  # "amendment" > "licence"
    assert match_family("Üretim Lisansı", guides) == "licence_permit"
    assert match_family("Covenant Report", guides) == "workbook"  # "covenant report" > "report"
    assert match_family("Board Resolution", guides) == "resolution_minutes"
    assert match_family("Bilinmeyen Tür", guides) == "other"
    assert match_family(None, guides) == "other"


def test_extra_key_normalisation_and_cap() -> None:
    assert type_family.normalize_extra_key(" Sözleşme Bedeli ") == "sozlesme_bedeli"
    assert type_family.normalize_extra_key("contract-value") == "contract_value"
    assert type_family.normalize_extra_key("***") is None
    assert normalize_extra_updates({"Taraflar": " A, B ", "x": None}) == {
        "taraflar": "A, B",
        "x": None,
    }
    too_many = {f"k{i}": "v" for i in range(type_family.MAX_EXTRA_FIELDS + 1)}
    try:
        merge_extra_fields({}, too_many, actor_id=None, suggested={}, now_iso="t")
    except ExtraFieldsError:
        pass
    else:
        raise AssertionError("cap not enforced")


def test_merge_marks_ai_kept_values_and_user_additions() -> None:
    suggested = {"parties": {"value": "A, B", "confidence": 0.6}}
    merged, added, changed = merge_extra_fields(
        {}, {"parties": "A, B", "licence_no": "L-1"}, actor_id="u", suggested=suggested, now_iso="t"
    )
    assert merged["parties"]["source"] == "ai" and merged["parties"]["confidence"] == 0.6
    assert merged["licence_no"]["source"] == "user" and added == ["licence_no"]
    assert set(changed) == {"parties", "licence_no"}
    merged2, added2, changed2 = merge_extra_fields(
        merged, {"licence_no": None}, actor_id="u", suggested=suggested, now_iso="t"
    )
    assert "licence_no" not in merged2 and added2 == [] and changed2 == ["licence_no"]
    flat = flatten_suggestion({"department": {"value": "finans"}, "extra_fields": suggested})
    assert flat[f"{EXTRA_PREFIX}parties"] == suggested["parties"] and "extra_fields" not in flat


# ------------------------------------------------------------------ X-01 seed snapshot


def test_seed_matches_the_migration_snapshot_and_is_idempotent(
    db_session: Session, settings: Settings
) -> None:
    """The migration already created the rows on this test database; the seed must find
    them (created=False) and agree with the starter constants."""
    results = ensure_demo_catalog(db_session, settings)
    assert all(r.created is False for r in results)
    tags = {t.slug: t for t in tag_repo.list_all(db_session)}
    for slug, label in DEFAULT_CHANGE_TAGS:
        assert tags[slug].kind == TagKind.change and tags[slug].label == label
    families = {g.family for g in guide_repo.list_all(db_session)}
    assert families == {g["family"] for g in DEFAULT_GUIDE}


# ------------------------------------------------------------------ X-04 catalogue API


def test_tag_catalogue_admin_crud_everyone_reads_active(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    created = client.post(
        "/api/admin/tags", json={"slug": "pf-kredi", "label": "PF kredi", "kind": "identity"}
    )
    assert created.status_code == 201, created.text
    assert (
        client.post("/api/admin/tags", json={"slug": "pf-kredi", "label": "x"}).status_code == 409
    )
    assert (
        client.post("/api/admin/tags", json={"slug": "Büyük Harf", "label": "x"}).status_code == 422
    )
    retired = client.patch("/api/admin/tags/pf-kredi", json={"is_active": False})
    assert retired.status_code == 200 and retired.json()["is_active"] is False
    with _as(cast.uploader):
        active = {t["slug"] for t in client.get("/api/tags").json()}
        assert "faiz-değişikliği" in active and "pf-kredi" not in active
        assert client.get("/api/admin/tags").status_code == 403
        assert client.post("/api/admin/tags", json={"slug": "x", "label": "x"}).status_code == 403
    kinds = [e.kind for e in db_session.scalars(select(AdminEvent).order_by(AdminEvent.created_at))]
    assert kinds == ["tag_created", "tag_updated"]
    events = client.get("/api/admin/events").json()
    assert {e["kind"] for e in events} == {"tag_created", "tag_updated"}


# ------------------------------------------------------------------ X-05 guide API


def test_guide_admin_edit_everyone_reads_active(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    patched = client.patch(
        "/api/admin/document-type-guide/contract",
        json={
            "suggested_extra_fields": [{"key": "parties", "label": "Taraflar", "hint": "virgülle"}]
        },
    )
    assert (
        patched.status_code == 200
        and patched.json()["suggested_extra_fields"][0]["key"] == "parties"
    )
    new = client.post(
        "/api/admin/document-type-guide",
        json={"family": "tender", "label": "İhale", "type_patterns": ["İhale", "tender"]},
    )
    assert new.status_code == 201 and new.json()["type_patterns"] == ["ihale", "tender"]
    assert (
        client.post(
            "/api/admin/document-type-guide", json={"family": "tender", "label": "x"}
        ).status_code
        == 409
    )
    with _as(cast.uploader):
        families = {g["family"] for g in client.get("/api/document-type-guide").json()}
        assert "tender" in families and "contract" in families
        assert (
            client.patch("/api/admin/document-type-guide/contract", json={"label": "x"}).status_code
            == 403
        )
    guides = guide_repo.as_dicts(guide_repo.list_all(db_session, active_only=True))
    assert match_family("İhale Dosyası", guides) == "tender"


# ------------------------------------------------ X-02 / X-03 extra fields, strict tags


def _pending_document(client: TestClient, session: Session, cast: Cast, suggestion: dict) -> str:
    with _as(cast.uploader):
        document_id = _upload(
            client, department="finans", document_type="Facility Agreement"
        ).json()["id"]
    _make_ready_with_chunk(session, document_id, "metin")
    _seed_suggestion(session, document_id, suggestion)
    return document_id


def test_submit_stores_extra_fields_with_source_and_events(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    document_id = _pending_document(
        client,
        db_session,
        cast,
        {
            "department": {"value": "finans", "confidence": 0.95},
            "extra_fields": {"parties": {"value": "DEF Enerji, PQR Bank", "confidence": 0.9}},
        },
    )
    with _as(cast.uploader):
        response = client.post(
            f"/api/documents/{document_id}/submit",
            json={
                "department": "finans",
                "tags": ["faiz-değişikliği"],
                "extra_fields": {"parties": "DEF Enerji, PQR Bank", "Lisans No": "L-42"},
            },
        )
        assert response.status_code == 200, response.text
        body = response.json()
    assert body["tags"] == ["faiz-değişikliği"]
    assert body["extra_fields"]["parties"]["source"] == "ai"
    assert body["extra_fields"]["parties"]["confidence"] == 0.9
    assert body["extra_fields"]["lisans_no"]["source"] == "user"
    assert body["extra_fields"]["lisans_no"]["added_by_id"] == str(cast.uploader.id)
    assert _events(db_session, document_id) == ["uploaded", "field_added", "submitted"]


def test_low_confidence_extra_field_needs_confirmation_and_unknown_tag_is_refused(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    document_id = _pending_document(
        client,
        db_session,
        cast,
        {"extra_fields": {"licence_no": {"value": "L-7", "confidence": 0.4}}},
    )
    with _as(cast.uploader):
        refused = client.post(
            f"/api/documents/{document_id}/submit",
            json={"department": "finans", "extra_fields": {"licence_no": "L-7"}},
        )
        assert refused.status_code == 422
        assert refused.json()["detail"]["fields"] == [f"{EXTRA_PREFIX}licence_no"]
        bad_tag = client.post(
            f"/api/documents/{document_id}/submit",
            json={"department": "finans", "tags": ["serbest-etiket"]},
        )
        assert bad_tag.status_code == 422
        assert bad_tag.json()["detail"]["code"] == "unknown_tag"
        assert bad_tag.json()["detail"]["unknown"] == ["serbest-etiket"]
        bad_key = client.post(
            f"/api/documents/{document_id}/submit",
            json={"department": "finans", "extra_fields": {"***": "x"}},
        )
        assert (
            bad_key.status_code == 422
            and bad_key.json()["detail"]["code"] == "invalid_extra_fields"
        )
        ok = client.post(
            f"/api/documents/{document_id}/submit",
            json={
                "department": "finans",
                "extra_fields": {"licence_no": "L-7"},
                "confirmed_fields": [f"{EXTRA_PREFIX}licence_no"],
            },
        )
        assert ok.status_code == 200, ok.text
        assert ok.json()["extra_fields"]["licence_no"]["source"] == "ai"
    assert "field_confirmed" in _events(db_session, document_id)


def test_admin_patch_edits_extra_fields_and_validates_tags(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    document = Document(
        title="Onaylı",
        document_type="Facility Agreement",
        counterparty="c",
        document_date="2026-01-01",
        department="finans",
        storage_path=f"{uuid.uuid4()}/original.pdf",
    )
    db_session.add(document)
    db_session.commit()
    bad = client.patch(f"/api/documents/{document.id}", json={"tags": ["yok-boyle"]})
    assert bad.status_code == 422 and bad.json()["detail"]["code"] == "unknown_tag"
    ok = client.patch(
        f"/api/documents/{document.id}",
        json={"tags": ["vade-değişikliği"], "extra_fields": {"parties": "A, B"}},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["extra_fields"]["parties"]["source"] == "user"
    assert ok.json()["review_status"] == "pending_review"  # T9: approved document re-opened
    assert "field_added" in _events(db_session, str(document.id))
    removed = client.patch(
        f"/api/documents/{document.id}", json={"extra_fields": {"parties": None}}
    )
    assert removed.json()["extra_fields"] == {}


# ------------------------------------------------------------------ X-06 classifier


def test_classifier_prompt_carries_catalogue_and_guide_and_sanitises_output(
    db_session: Session, settings: Settings
) -> None:
    department_repo.create(db_session, name="Finans", slug="finans")
    project_repo.create(
        db_session, name="Ankara RES", code="ANK_RES", stage="operation", department_ids=[]
    )
    document = _page_document(db_session, text="Facility Agreement between DEF Enerji and PQR Bank")
    reply = json.dumps(
        {
            "department": {"value": "finans", "confidence": 0.9},
            "subdepartment": {"value": None, "confidence": 0.0},
            "project_code": {"value": "ANK_RES", "confidence": 0.9},
            "document_type": {"value": "facility_agreement", "confidence": 0.9},
            "counterparty": {"value": "PQR Bank", "confidence": 0.9},
            "document_date": {"value": "2023-06-01", "confidence": 0.9},
            "status": {"value": "executed", "confidence": 0.9},
            "confidentiality": {"value": "normal", "confidence": 0.9},
            "tags": {"value": ["faiz-değişikliği", "serbest-etiket"], "confidence": 0.7},
            "extra_fields": {
                "Taraflar": {"value": ["DEF Enerji", "PQR Bank"], "confidence": 0.8},
                "***": {"value": "x", "confidence": 0.5},
                "contract_value": {"value": None, "confidence": 0.1},
            },
        }
    )
    fake = FakeLLMClient(replies=[reply])

    suggestion = metadata_suggestion.suggest_metadata(db_session, document, fake, settings)

    system = fake.requests[0].system
    assert "faiz-değişikliği" in system and "başka etiket üretme" in system
    assert "contract [" in system and "parties" in system  # guide block
    assert suggestion.status == SuggestionStatus.pending
    assert suggestion.fields["tags"]["value"] == ["faiz-değişikliği"]
    assert suggestion.fields["tags"]["dropped"] == ["serbest-etiket"]
    assert suggestion.fields["extra_fields"] == {
        "taraflar": {"value": "DEF Enerji, PQR Bank", "confidence": 0.8}
    }


# ------------------------------------------------------------------ X-07 search · X-08 prompt


def test_search_matches_tags_and_extra_fields_with_matched_on(
    client: TestClient, db_session: Session, admin_user, fake_llm: FakeLLMClient
) -> None:
    tagged = _chunked_document(
        db_session, title="Kredi Sözleşmesi", department=None, text="metin a"
    )
    tagged.tags = ["faiz-değişikliği"]
    extra = _chunked_document(db_session, title="Lisans", department=None, text="metin b")
    extra.extra_fields = {"licence_no": {"value": "EPDK-2020-77", "source": "user"}}
    db_session.commit()

    by_tag = client.get("/api/search", params={"q": "faiz-değişikliği"}).json()["documents"]
    by_extra = client.get("/api/search", params={"q": "EPDK-2020"}).json()["documents"]

    assert [(d["id"], d["matched_on"]) for d in by_tag] == [(str(tagged.id), "tag")]
    assert [(d["id"], d["matched_on"]) for d in by_extra] == [(str(extra.id), "extra_field")]


def test_prompt_source_carries_tags_and_extra_fields_only_when_present(
    client: TestClient, db_session: Session, admin_user, fake_llm: FakeLLMClient
) -> None:
    plain = _chunked_document(db_session, title="Düz", department=None, text="DSCR covenant düz")
    rich = _chunked_document(
        db_session, title="Zengin", department=None, text="DSCR covenant zengin"
    )
    rich.tags = ["faiz-değişikliği"]
    rich.extra_fields = {"parties": {"value": "DEF Enerji, PQR Bank", "source": "user"}}
    db_session.commit()
    assert describe_metadata(plain) == "Muhatap: PQR Bank"
    assert describe_metadata(rich) == (
        "Muhatap: PQR Bank | Etiketler: faiz-değişikliği | Ek alanlar: parties=DEF Enerji, PQR Bank"
    )

    _ask(client, "DSCR covenant nedir?")
    prompt = fake_llm.prompt_text()
    assert "Etiketler: faiz-değişikliği | Ek alanlar: parties=DEF Enerji, PQR Bank" in prompt
    assert prompt.count("Etiketler:") == 1  # the plain document carries no tags line


# ------------------------------------------------------------------ X-09 signals


def test_guide_signals_count_staff_added_keys_per_family(
    client: TestClient, db_session: Session, cast: Cast
) -> None:
    for _ in range(2):
        document_id = _pending_document(
            client, db_session, cast, {"department": {"value": "finans", "confidence": 0.9}}
        )
        with _as(cast.uploader):
            assert (
                client.post(
                    f"/api/documents/{document_id}/submit",
                    json={"department": "finans", "extra_fields": {"parties": "A, B"}},
                ).status_code
                == 200
            )
    signals = client.get("/api/admin/document-type-guide/signals").json()
    assert signals[0] == {"family": "contract", "key": "parties", "count": 2}
    with _as(cast.uploader):
        assert client.get("/api/admin/document-type-guide/signals").status_code == 403
    assert db_session.scalar(select(func.count()).select_from(AdminEvent)) == 0  # signals read only
