from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "llm-service"}


def test_generate_story():
    response = client.post(
        "/generate",
        json={"child_theme": "space adventure", "character_name": "Nova"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "content" in data
    assert "Nova" in data["content"]
    assert data["child_theme"] == "space adventure"
    assert data["character_name"] == "Nova"


def test_generate_story_with_prompt():
    response = client.post(
        "/generate",
        json={
            "child_theme": "underwater kingdom",
            "character_name": "Pearl",
            "prompt": "Pearl discovers a hidden treasure",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "Pearl discovers a hidden treasure" in data["content"]
    assert data["prompt"] == "Pearl discovers a hidden treasure"


def test_generate_story_missing_fields():
    response = client.post("/generate", json={"child_theme": "forest"})
    assert response.status_code == 422
