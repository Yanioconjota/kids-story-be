import json
import os
from unittest.mock import AsyncMock, patch

os.environ.setdefault("LLM_PROVIDER", "mock")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "llm-service"}


def test_generate_story_mock():
    response = client.post(
        "/generate",
        json={"child_theme": "space adventure", "character_name": "Nova"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert len(data["content"]) > 10
    assert "Nova" in data["content"]
    assert data["child_theme"] == "space adventure"


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


def test_generate_story_with_max_words():
    response = client.post(
        "/generate",
        json={"child_theme": "dragon lands", "character_name": "Ember", "max_words": 150},
    )
    assert response.status_code == 200
    assert response.json()["character_name"] == "Ember"


def test_generate_story_missing_fields():
    response = client.post("/generate", json={"child_theme": "forest"})
    assert response.status_code == 422


def test_generate_story_max_words_out_of_range():
    response = client.post(
        "/generate",
        json={"child_theme": "forest", "character_name": "Leaf", "max_words": 9999},
    )
    assert response.status_code == 422


def test_generate_stream_returns_sse():
    with client.stream(
        "POST",
        "/generate/stream",
        json={"child_theme": "magic forest", "character_name": "Luna"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        lines = [line for line in response.iter_lines() if line.startswith("data: ")]
        assert len(lines) > 0
        events = [json.loads(line[6:]) for line in lines]
        assert any(e.get("done") is False for e in events)
        assert events[-1].get("done") is True


def test_generate_returns_502_on_provider_error():
    with patch("app.main.generate_content", new_callable=AsyncMock) as mock_gen:
        from fastapi import HTTPException  # noqa: PLC0415
        mock_gen.side_effect = HTTPException(status_code=502, detail="OpenAI error: api down")
        response = client.post(
            "/generate",
            json={"child_theme": "forest", "character_name": "Leaf"},
        )
    assert response.status_code == 502
