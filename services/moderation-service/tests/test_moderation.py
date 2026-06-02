from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "moderation-service"}


def test_moderate_approves_valid_request():
    response = client.post(
        "/moderate",
        json={"child_theme": "magic forest", "character_name": "Luna"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["approved"] is True


def test_moderate_approves_with_prompt():
    response = client.post(
        "/moderate",
        json={
            "child_theme": "ocean adventure",
            "character_name": "Pearl",
            "prompt": "Pearl finds a hidden treasure",
        },
    )
    assert response.status_code == 200
    assert response.json()["approved"] is True


def test_moderate_rejects_missing_fields():
    response = client.post("/moderate", json={"child_theme": "forest"})
    assert response.status_code == 422
