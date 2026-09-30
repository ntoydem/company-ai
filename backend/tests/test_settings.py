"""B-25 product layer key (Aşama A, ADR-022): `company_settings.enabled_products` via
`GET/PATCH /api/admin/settings` and the CLI, surfaced on `/login` + `/me`, enforced by
`require_product` on `POST /api/excel/ask`. BAGLANTI_YOL_HARITASI.md T-01..T-03."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import cli
from app.api.deps import PRODUCT_NOT_ENABLED_DETAIL
from app.core.config import Settings
from app.models.user import User
from app.repositories import company_settings_repo
from app.services.admin_seed import ensure_admin_user
from tests.fakes import FakeLLMClient
from tests.test_excel_api import _upload_workbook

# ---------------------------------------------------------------- /login + /me


def test_login_and_me_carry_enabled_products_default_all_open(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    ensure_admin_user(db_session, settings)
    login = client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password.get_secret_value(),
        },
    )
    assert login.status_code == 200
    assert login.json()["enabled_products"] == ["P1", "P2", "P3"]
    assert client.get("/api/auth/me").json()["enabled_products"] == ["P1", "P2", "P3"]


def test_me_reflects_a_package_change_without_relogin(
    client: TestClient, db_session: Session, settings: Settings
) -> None:
    ensure_admin_user(db_session, settings)
    client.post(
        "/api/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password.get_secret_value(),
        },
    )
    company_settings_repo.set_enabled_products(db_session, ["P1"])
    assert client.get("/api/auth/me").json()["enabled_products"] == ["P1"]


# ---------------------------------------------------------------- admin API


def test_admin_reads_and_updates_enabled_products_in_canonical_order(
    client: TestClient, admin_user: User
) -> None:
    assert client.get("/api/admin/settings").json() == {"enabled_products": ["P1", "P2", "P3"]}
    response = client.patch("/api/admin/settings", json={"enabled_products": ["P2", "P1", "P2"]})
    assert response.status_code == 200
    assert response.json() == {"enabled_products": ["P1", "P2"]}
    assert client.get("/api/admin/settings").json() == {"enabled_products": ["P1", "P2"]}


@pytest.mark.parametrize("body", [{"enabled_products": []}, {"enabled_products": ["P4"]}])
def test_admin_update_rejects_empty_and_unknown_products(
    client: TestClient, admin_user: User, body: dict[str, list[str]]
) -> None:
    assert client.patch("/api/admin/settings", json=body).status_code == 422


def test_settings_endpoints_require_admin(client: TestClient, employee_user: User) -> None:
    assert client.get("/api/admin/settings").status_code == 403
    assert client.patch("/api/admin/settings", json={"enabled_products": ["P1"]}).status_code == 403


# ---------------------------------------------------------------- CLI


def test_cli_set_enabled_products(db_session: Session) -> None:
    assert cli.cmd_set_enabled_products("P2, P1") == 0
    assert company_settings_repo.enabled_products(db_session) == ["P1", "P2"]
    assert cli.cmd_set_enabled_products("P1,P9") == 2
    assert cli.cmd_set_enabled_products("") == 2
    assert company_settings_repo.enabled_products(db_session) == ["P1", "P2"]  # unchanged


# ---------------------------------------------------------------- require_product


def test_excel_ask_is_closed_in_p1_but_inspect_stays_open(
    client: TestClient, db_session: Session, admin_user: User, fake_llm: FakeLLMClient
) -> None:
    """NOT §6.2: a P1 customer still uploads and inspects workbooks (no computation);
    only the computing endpoint is a P2 capability."""
    workbook = _upload_workbook(client)
    company_settings_repo.set_enabled_products(db_session, ["P1"])

    response = client.post("/api/excel/ask", json={"question": "2026 Q2 DSCR?"})
    assert response.status_code == 403
    assert response.json()["detail"] == PRODUCT_NOT_ENABLED_DETAIL
    assert fake_llm.requests == []
    assert client.get(f"/api/excel/{workbook['id']}/inspect").status_code == 200

    company_settings_repo.set_enabled_products(db_session, ["P1", "P2"])
    fake_llm.replies = [
        '{"kind": "function", "name": "dscr", "params": {"period": "Q2_2026"}}',
        "2026 Q2 DSCR 1,37x.",
    ]
    assert client.post("/api/excel/ask", json={"question": "2026 Q2 DSCR?"}).status_code == 200


def test_product_gate_answers_401_before_403(client: TestClient, db_session: Session) -> None:
    company_settings_repo.set_enabled_products(db_session, ["P1"])
    assert client.post("/api/excel/ask", json={"question": "DSCR?"}).status_code == 401
