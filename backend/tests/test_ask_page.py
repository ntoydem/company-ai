from fastapi.testclient import TestClient


def test_ask_page_is_served(client: TestClient) -> None:
    response = client.get("/ask")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Sorunuzu yazın" in response.text
    assert "/api/ask" in response.text
