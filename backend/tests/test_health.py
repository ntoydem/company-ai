from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from app import __version__
from app.core.db import get_engine
from app.core.request_id import REQUEST_ID_HEADER
from app.main import app


def test_health_returns_200_with_db_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "database": "ok"}
    assert response.headers[REQUEST_ID_HEADER]


def test_health_propagates_client_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={REQUEST_ID_HEADER: "abc-123"})
    assert response.headers[REQUEST_ID_HEADER] == "abc-123"


def test_health_replaces_malformed_request_id(client: TestClient) -> None:
    response = client.get("/health", headers={REQUEST_ID_HEADER: "bad id with spaces!"})
    rid = response.headers[REQUEST_ID_HEADER]
    assert rid != "bad id with spaces!"
    assert len(rid) == 32


@pytest.fixture
def _unreachable_database() -> Iterator[None]:
    broken = create_engine(
        "postgresql+psycopg://x:x@127.0.0.1:1/x", connect_args={"connect_timeout": 1}
    )
    app.dependency_overrides[get_engine] = lambda: broken
    yield
    app.dependency_overrides.pop(get_engine, None)
    broken.dispose()


@pytest.mark.usefixtures("_unreachable_database")
def test_health_returns_503_when_database_unreachable(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
    assert response.json()["database"] == "unavailable"
