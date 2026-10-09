"""Ek-F rendering layer behind `EK_F_MODE` (ADR-030; `docs/plans/ADIM_EK-F_PLAN.md`): F-5
pattern in place of the fixed sentence, F-3 project-grouped list with the metadata quota,
Ç-3 "anladım" line, Ç-2 `previous_question`, F-8 gate, MIXED merge — and flag-off byte
identity. Every list still comes from `allowed_document_ids` (G3)."""

from __future__ import annotations

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.audit_log import AuditLog
from app.models.document import Document, DocumentStatus, IngestionStatus
from app.models.project import Project
from app.models.user import User
from app.services import ask as ask_module
from app.services import assist as assist_module
from app.services import retrieval as retrieval_module
from app.services.answer_prompt import NO_ANSWER_TEXT, NO_DATA_VERDICT
from app.services.ask_router import merge_mixed_answer
from app.services.assist import (
    CLARIFY_TEMPLATE,
    MAX_AVAILABLE_EKF,
    Assist,
    AvailableDocument,
    AvailableGroup,
    render_no_data,
)
from tests.fakes import FakeLLMClient
from tests.test_ask import _ask, _document


@pytest.fixture
def ek_f_on(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ek_f_enabled", True)
    assert settings.assist_computations is True
    assert settings.assist_mode_enabled is False  # one flag is enough (Naci SORU 1)


def _projects(session: Session) -> dict[str, Project]:
    ankara, izmir = (
        Project(name="Ankara RES", code="ANK_RES"),
        Project(name="İzmir RES", code="IZM_RES"),
    )
    session.add_all([ankara, izmir])
    session.commit()
    return {"ANK_RES": ankara, "IZM_RES": izmir}


def _metadata_only(
    session: Session, *, title: str, project: Project | None, day: int = 1
) -> Document:
    """A ready document without chunks (a workbook): reachable through metadata only."""
    document = Document(
        title=title,
        document_type="Karar",
        counterparty="c",
        document_date=date(2024, 6, day),
        status=DocumentStatus.executed,
        storage_path=f"{uuid.uuid4()}/original.xlsx",
        ingestion_status=IngestionStatus.ready,
        project_id=project.id if project else None,
    )
    session.add(document)
    session.commit()
    return document


def _card(title: str, code: str | None, day: int) -> AvailableDocument:
    return AvailableDocument(
        document_id=uuid.uuid4(),
        title=title,
        document_type="t",
        document_date=date(2024, 1, day),
        project_code=code,
        page_number=None,
    )


# ---------------------------------------------------------------- render_no_data (pure)


def test_render_lists_groups_with_dates_and_ends_with_the_question() -> None:
    a, b, c = (
        _card("Facility Agreement", "ANK_RES", 5),
        _card("Önlisans", "IZM_RES", 7),
        _card("YK Kararı", None, 9),
    )
    assist = Assist(
        kind="clarify",
        question=CLARIFY_TEMPLATE,
        available=(a, b, c),
        groups=(
            AvailableGroup("ANK_RES", "Ankara RES", (a,)),
            AvailableGroup("IZM_RES", "İzmir RES", (b,)),
            AvailableGroup(None, "Şirket geneli", (c,)),
        ),
        more_count=3,
    )
    text = render_no_data(assist, "Amendment var mı?")
    lines = text.splitlines()
    # Ç-3: glossary label, code-side; plain Turkish words ("kredi") get no such line
    assert lines[0] == "«amendment» ifadesini tadil (değişiklik sözleşmesi) olarak anladım."
    assert render_no_data(assist, "Kredi sözleşmesi var mı?").startswith(NO_DATA_VERDICT)
    assert lines[1] == NO_DATA_VERDICT
    assert lines[2] == "Elimde konuyla ilgili şunlar var:"
    assert lines[3] == "Ankara RES: Facility Agreement (05.01.2024)"
    assert lines[4] == "İzmir RES: Önlisans (07.01.2024)"
    assert lines[5] == "Şirket geneli: YK Kararı (09.01.2024)"
    assert lines[6] == "… ve 3 belge daha."  # N counted by code (SORU 4)
    assert lines[7] == "İsterseniz açayım."
    assert lines[-1] == CLARIFY_TEMPLATE
    assert "yüklenirse" not in text  # upload sentence only when nothing is listed (F-5)
    assert NO_ANSWER_TEXT not in text


def test_render_without_documents_offers_the_typical_document_type_last_but_one() -> None:
    assist = Assist(kind="clarify", question=CLARIFY_TEMPLATE)
    text = render_no_data(assist, "Ödeme planı yüklü mü?")
    lines = text.splitlines()
    assert lines[0].startswith("«ödeme planı» ifadesini")
    assert lines[1] == NO_DATA_VERDICT
    assert lines[2] == "Elimde konuyla ilgili bir kayıt bulunmuyor."
    assert lines[3].startswith("Aradığınız bilgi genellikle kredi sözleşmesinin geri ödeme maddesi")
    assert lines[3].endswith("yüklenirse cevaplayabilirim.")
    assert lines[-1] == CLARIFY_TEMPLATE


def test_render_skips_unknown_terms_and_types_and_keeps_a_term_mismatch_question() -> None:
    question = (
        "Şu ifadeyi belgelerde bu haliyle bulamadım: «Zımbırtı». "
        "Ne demek istediğinizi açar mısınız?"
    )
    assist = Assist(kind="term_mismatch", question=question)
    text = render_no_data(assist, "Zımbırtı nerede?")
    assert text.splitlines() == [
        NO_DATA_VERDICT,
        "Elimde konuyla ilgili bir kayıt bulunmuyor.",
        assist.question,
    ]


# ---------------------------------------------------------------- /api/ask paths


def test_flag_off_keeps_the_fixed_sentence_and_no_groups(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    _document(db_session, title="Facility Agreement", department=None, text="DSCR covenant")
    fake_llm.replies = [NO_ANSWER_TEXT]
    body = _ask(client, "DSCR covenant nedir?")
    assert body["answer"] == NO_ANSWER_TEXT and body["answered"] is False
    assert body["assist"] is None
    assert "ÖNCEKİ SORU" not in fake_llm.prompt_text()


def test_zero_chunks_render_the_pattern_without_any_llm_call(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    projects = _projects(db_session)
    wb = _metadata_only(db_session, title="Financial Model 2026", project=projects["ANK_RES"])

    body = _ask(client, "Finansal model var mı?")

    assert fake_llm.requests == []  # ADR-021 still holds
    assert body["answered"] is False
    lines = body["answer"].splitlines()
    assert lines[0].startswith("«finansal model» ifadesini")
    assert lines[1] == NO_DATA_VERDICT
    assert "Ankara RES: Financial Model 2026 (01.06.2024)" in lines
    assert lines[-1] == CLARIFY_TEMPLATE
    groups = body["assist"]["groups"]
    assert [g["project_name"] for g in groups] == ["Ankara RES"]
    assert groups[0]["documents"][0]["document_id"] == str(wb.id)


def test_insufficient_named_project_question_excludes_the_other_project_entirely(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    """Was `..._named_project_first` (both projects shown, named one first) until the
    09.10.2026 fix: this is the exact GEN-HAL-001 shape (a project-named question whose
    retrieval also touches the other project's documents) — now the other project's match
    is not a candidate at all, never merely ordered second (Ü-3)."""
    projects = _projects(db_session)
    ankara = _document(
        db_session, title="Ankara ÇED Kararı", department=None, text="ÇED olumlu kararı"
    )
    izmir = _document(
        db_session, title="İzmir ÇED Yazısı", department=None, text="ÇED süreci durumu"
    )
    ankara.project_id, izmir.project_id = projects["ANK_RES"].id, projects["IZM_RES"].id
    db_session.commit()
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "İzmir ÇED süreci ne durumda?")

    assert body["answered"] is False
    groups = body["assist"]["groups"]
    assert [g["project_name"] for g in groups] == ["İzmir RES"]
    text = body["answer"]
    assert "İzmir RES:" in text and "Ankara RES:" not in text and ankara.title not in text
    assert str(ankara.id) not in {a["document_id"] for a in body["assist"]["available"]}
    assert str(izmir.id) in {a["document_id"] for a in body["assist"]["available"]}
    assert NO_DATA_VERDICT in text and NO_ANSWER_TEXT not in text


def test_quota_keeps_places_for_metadata_matches(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ADIM1 DSC-007: six chunk-vouched pages must not push the ÇED decision out — the
    metadata matches get ≥ 3 places (here only 2 exist, so one place spills back to the
    chunk pages), total ≤ 7, the surplus is counted by code."""
    projects = _projects(db_session)
    chunk_docs = [
        _document(db_session, title=f"Belge {i}", department=None, text="ÇED rüzgar ölçüm")
        for i in range(6)
    ]
    decision = _metadata_only(
        db_session, title="Ankara RES ÇED Olumlu Kararı", project=projects["ANK_RES"]
    )
    letter = _metadata_only(
        db_session, title="ÇED Süreci Durum Yazısı", project=projects["IZM_RES"], day=2
    )
    ids = {d.id for d in chunk_docs}
    monkeypatch.setattr(assist_module, "specific_matched_terms", lambda *a, **k: {"ÇED": ids})
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "ÇED raporu nerede?")

    listed = {a["document_id"] for a in body["assist"]["available"]}
    assert str(decision.id) in listed and str(letter.id) in listed
    assert len(listed) == MAX_AVAILABLE_EKF
    assert sum(1 for d in chunk_docs if str(d.id) in listed) == 5  # 4 + the one spilled place
    assert "… ve 1 belge daha." in body["answer"]
    # the two ÇED documents sit under their own project headings, never mixed (Ü-3)
    names = [g["project_name"] for g in body["assist"]["groups"]]
    assert "Ankara RES" in names and "İzmir RES" in names


def test_hidden_document_never_reaches_groups_or_text(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    projects = _projects(db_session)
    hidden = _metadata_only(db_session, title="Gizli Finansal Model", project=projects["ANK_RES"])
    visible = _document(
        db_session, title="Facility Agreement", department=None, text="finansal model notu"
    )
    monkeypatch.setattr(retrieval_module, "allowed_document_ids", lambda *_: {visible.id})
    monkeypatch.setattr(ask_module, "allowed_document_ids", lambda *_: {visible.id})
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "Finansal model var mı?")

    assert "Gizli" not in body["answer"]
    assert str(hidden.id) not in str(body)


def test_previous_question_reaches_the_prompt_and_the_audit_context(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    _document(
        db_session, title="Facility Agreement Amendment 01", department=None, text="amendment tadil"
    )

    body = _ask(
        client, "peki amendment var mı hiç?", previous_question="Ankara RES kredi sözleşmesi nedir?"
    )

    prompt = fake_llm.prompt_text()
    assert (
        "ÖNCEKİ SORU (yalnızca bağlam, cevaplanmaz): Ankara RES kredi sözleşmesi nedir?" in prompt
    )
    assert prompt.index("ÖNCEKİ SORU") < prompt.index("SORU: peki amendment")
    row = db_session.scalar(select(AuditLog).where(AuditLog.id == uuid.UUID(body["audit_log_id"])))
    assert row is not None
    assert row.assist["context"] == {"previous_question": "Ankara RES kredi sözleşmesi nedir?"}


def test_answered_reply_passes_the_format_gate(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    _document(
        db_session, title="Facility Agreement", department=None, text="financial close 2021-11-15"
    )
    fake_llm.replies = [
        "Finansal kapanış 2021-11-15 00:00:00 tarihindedir, tutar 1,234,567.89 EUR [K1]."
    ]

    body = _ask(client, "Finansal kapanış ne zaman?")

    assert body["answered"] is True
    assert (
        body["answer"] == "Finansal kapanış 15.11.2021 tarihindedir, tutar 1.234.567,89 EUR [K1]."
    )
    assert [s["ref"] for s in body["sources"]] == ["K1"]


def test_mixed_merge_hides_the_empty_document_part_only_under_the_flag() -> None:
    doc, data = NO_ANSWER_TEXT, "İlk taksit 1.000.000 EUR."
    assert (
        merge_mixed_answer(doc, data, document_answered=False, data_answered=True, ek_f=True)
        == data
    )
    both = merge_mixed_answer(doc, data, document_answered=False, data_answered=True, ek_f=False)
    assert both.startswith("Belgelere göre:") and "Excel verisine göre:" in both
    # both answered → two parts even under the flag
    assert "Belgelere göre:" in merge_mixed_answer("A [K1].", data, ek_f=True)


# --- ADR-030 fix (09.10.2026, GEN-HAL-001): a project-named question narrows the list ---


def test_named_project_codes_matches_only_the_project_the_question_names(
    db_session: Session,
) -> None:
    from app.services.assist import named_project_codes

    projects = _projects(db_session)
    assert named_project_codes(db_session, "İzmir RES'in COD tarihi nedir?") == {"IZM_RES"}
    assert named_project_codes(db_session, "Ankara RES'in kapasitesi nedir?") == {"ANK_RES"}
    assert named_project_codes(db_session, "ÇED raporu nerede?") == set()
    both = named_project_codes(db_session, "Ankara RES ile İzmir RES'in kapasitesi?")
    assert both == {"ANK_RES", "IZM_RES"}
    del projects  # only used to seed the two rows


def test_zero_chunks_named_project_excludes_the_other_projects_matches(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    """GEN-HAL-001 shape: the question names İzmir RES only; an Ankara RES metadata match
    ("COD" acronym probe) must not appear in the list, the groups, or the "more" count."""
    projects = _projects(db_session)
    izmir_doc = _metadata_only(
        db_session, title="İzmir RES Önlisans Belgesi", project=projects["IZM_RES"]
    )
    ankara_doc = _metadata_only(
        db_session,
        title="Provisional Acceptance & COD Certificate",
        project=projects["ANK_RES"],
        day=2,
    )

    body = _ask(client, "İzmir RES'in COD tarihi nedir?")

    listed = {a["document_id"] for a in body["assist"]["available"]}
    assert str(izmir_doc.id) in listed
    assert str(ankara_doc.id) not in listed
    names = [g["project_name"] for g in body["assist"]["groups"]]
    assert names == ["İzmir RES"]
    assert "Ankara RES" not in body["answer"] and ankara_doc.title not in body["answer"]
    assert "belge daha" not in body["answer"]  # the excluded document isn't counted either


def test_insufficient_named_project_excludes_the_other_projects_chunk_and_metadata_matches(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    """Same shape through the chunk-retrieved path (`build_insufficient_assist`): an Ankara
    RES page the question's terms vouch for must not sit next to the named İzmir RES one."""
    projects = _projects(db_session)
    izmir_decision = _metadata_only(
        db_session, title="İzmir RES Bağlantı Görüşü Başvurusu", project=projects["IZM_RES"]
    )
    ankara_chunk = _document(
        db_session,
        title="EPC Change Order 01 (COD Deferral)",
        department=None,
        text="COD ticari işletme tarihi",
    )
    ankara_chunk.project_id = projects["ANK_RES"].id
    db_session.commit()
    fake_llm.replies = [NO_ANSWER_TEXT]

    body = _ask(client, "İzmir RES'in COD tarihi nedir?")

    listed = {a["document_id"] for a in body["assist"]["available"]}
    assert str(izmir_decision.id) in listed
    assert str(ankara_chunk.id) not in listed
    names = [g["project_name"] for g in body["assist"]["groups"]]
    assert "Ankara RES" not in names


def test_unnamed_project_question_still_shows_every_matching_project(
    client: TestClient,
    db_session: Session,
    admin_user: User,
    fake_llm: FakeLLMClient,
    ek_f_on: None,
) -> None:
    """No project named in the question (DSC-007 shape, "ÇED raporu nerede?") → unchanged:
    both projects' matches are candidates, as before this fix."""
    projects = _projects(db_session)
    ankara_doc = _metadata_only(
        db_session, title="Ankara RES ÇED Olumlu Kararı", project=projects["ANK_RES"]
    )
    izmir_doc = _metadata_only(
        db_session, title="ÇED Süreci Durum Yazısı", project=projects["IZM_RES"], day=2
    )

    body = _ask(client, "ÇED raporu nerede?")

    listed = {a["document_id"] for a in body["assist"]["available"]}
    assert {str(ankara_doc.id), str(izmir_doc.id)} <= listed
    names = {g["project_name"] for g in body["assist"]["groups"]}
    assert names == {"Ankara RES", "İzmir RES"}
