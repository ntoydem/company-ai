from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import GENERIC_ERROR_MESSAGE
from app.core.request_id import REQUEST_ID_HEADER
from app.main import create_app


def _app_with_failing_route() -> FastAPI:
    test_app = create_app()

    def boom() -> None:
        raise RuntimeError("secret internal detail")

    test_app.add_api_route("/_boom", boom)
    return test_app


def test_unhandled_exception_returns_turkish_message_without_stack_trace() -> None:
    with TestClient(_app_with_failing_route(), raise_server_exceptions=False) as client:
        response = client.get("/_boom", headers={REQUEST_ID_HEADER: "req-err-1"})
    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == GENERIC_ERROR_MESSAGE
    assert body["request_id"] == "req-err-1"
    assert "secret internal detail" not in response.text
    assert "Traceback" not in response.text


def test_not_found_includes_request_id() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert response.json()["request_id"] == response.headers[REQUEST_ID_HEADER]
