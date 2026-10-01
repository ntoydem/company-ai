"""Aşama C (B-20/1-5): the department tree matches the product owner's mind map, both from a
fresh seed (here) and from migration 0010 on an existing database (test_migrations). Slugs
are fixed; the `finans` demo user is Proje Finans only (P-5); sub-units are not
authorization units (ADR-004, PHASE_1_2_PLAN T7)."""

from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import Settings
from app.main import app
from app.models.department import Department
from app.models.document import Document, DocumentStatus
from app.repositories import department_repo, user_repo
from app.services.demo_departments_seed import (
    _DEPARTMENTS,
    ensure_demo_department_memberships,
    ensure_demo_departments,
)
from app.services.demo_users_seed import ensure_demo_users

MIND_MAP: list[tuple[str, str, str | None]] = sorted(
    [
        ("finans", "Proje Finans", None),
        ("mali_isler", "Mali İşler", None),
        ("mali_isler_muhasebe", "Muhasebe", "mali_isler"),
        ("mali_isler_finansal_muhasebe", "Finansal Muhasebe", "mali_isler"),
        ("hukuk", "Hukuk", None),
        ("idari_isler", "İdari İşler", None),
        ("ik", "İK", None),
        ("enerji_grubu", "Enerji", None),
        ("enerji_gelistirme", "Proje Geliştirme", "enerji_grubu"),
        ("enerji_bakim", "O&M (İşletme ve Bakım)", "enerji_grubu"),
        ("enerji_epc_insaat", "EPC (İnşaat)", "enerji_grubu"),
        ("enerji_uretim_piyasa", "Üretim/Piyasa", "enerji_grubu"),
    ],
    key=lambda row: row[1],
)


def tree_snapshot(departments: list[Department]) -> list[tuple[str, str, str | None]]:
    by_id = {d.id: d for d in departments}
    return sorted(
        ((d.slug, d.name, by_id[d.parent_id].slug if d.parent_id else None) for d in departments),
        key=lambda row: row[1],
    )


def _seed_all(session: Session, settings: Settings) -> None:
    ensure_demo_users(session, settings)
    ensure_demo_departments(session, settings)
    ensure_demo_department_memberships(session, settings)


def _document(session: Session, *, department: str, subdepartment: str | None = None) -> Document:
    document = Document(
        title=f"{department}/{subdepartment or '-'}",
        document_type="report",
        counterparty="x",
        document_date=date(2026, 1, 1),
        department=department,
        subdepartment=subdepartment,
        status=DocumentStatus.executed,
        storage_path="x/original.pdf",
    )
    session.add(document)
    session.commit()
    return document


def test_seed_tree_matches_mind_map(db_session: Session, settings: Settings) -> None:
    ensure_demo_departments(db_session, settings)
    assert tree_snapshot(department_repo.list_all(db_session)) == MIND_MAP
    assert sorted(_DEPARTMENTS, key=lambda r: r[1]) == MIND_MAP  # seed constant itself
    ensure_demo_departments(db_session, settings)  # idempotent
    assert len(department_repo.list_all(db_session)) == 12


def test_departments_endpoint_serves_the_new_names(
    client: TestClient, db_session: Session, settings: Settings, employee_user: object
) -> None:
    ensure_demo_departments(db_session, settings)
    body = client.get("/api/departments").json()
    by_slug = {d["slug"]: d for d in body}
    assert by_slug["finans"]["name"] == "Proje Finans"
    assert by_slug["enerji_grubu"]["name"] == "Enerji"
    assert by_slug["ik"]["parent_id"] is None
    assert by_slug["mali_isler_muhasebe"]["parent_id"] == by_slug["mali_isler"]["id"]
    assert by_slug["enerji_uretim_piyasa"]["parent_id"] == by_slug["enerji_grubu"]["id"]


def test_finans_demo_user_is_proje_finans_only_and_cannot_see_mali_isler(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    _seed_all(db_session, settings)
    finans = user_repo.get_by_username(db_session, "finans")
    assert finans is not None
    assert finans.department_slugs == ["finans"]
    assert finans.primary_department_slug == "finans"
    assert finans.display_name == "Proje Finans" and finans.title == "Proje Finans Uzmanı"
    own = _document(db_session, department="finans")
    hidden = _document(db_session, department="mali_isler")
    app.dependency_overrides[get_current_user] = lambda: finans
    try:
        listed = {row["id"] for row in client.get("/api/documents").json()}
        assert listed == {str(own.id)}
        assert client.get(f"/api/documents/{hidden.id}/download").status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_enerji_sees_all_four_sub_units_including_uretim_piyasa(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    _seed_all(db_session, settings)
    enerji = user_repo.get_by_username(db_session, "enerji")
    assert enerji is not None
    docs = [
        _document(db_session, department="enerji_grubu", subdepartment=sub)
        for sub in (
            "enerji_gelistirme",
            "enerji_bakim",
            "enerji_epc_insaat",
            "enerji_uretim_piyasa",
        )
    ]
    _document(db_session, department="ik")
    app.dependency_overrides[get_current_user] = lambda: enerji
    try:
        listed = {row["id"] for row in client.get("/api/documents").json()}
    finally:
        app.dependency_overrides.pop(get_current_user, None)
    assert listed == {str(d.id) for d in docs}
