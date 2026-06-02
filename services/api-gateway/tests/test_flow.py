import json
import os
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("REDIS_URL", "redis://localhost:6379")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from shared.contracts.story import ModerationResult, Story  # noqa: E402

client = TestClient(app)

_STORY = Story(
    id="test-story-id",
    child_theme="magic forest",
    character_name="Luna",
    content="Once upon a time in a magic forest, Luna lived happily.",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
)

_APPROVED = ModerationResult(approved=True)
_REJECTED = ModerationResult(approved=False, reason="inappropriate content")


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api-gateway"}


@patch("app.main.get_cached_story", new_callable=AsyncMock, return_value=None)
@patch("app.main.set_cached_story", new_callable=AsyncMock, return_value=None)
@patch("app.main.moderate_story_request", new_callable=AsyncMock, return_value=_APPROVED)
@patch("app.main.generate_story", new_callable=AsyncMock, return_value=_STORY)
@patch("app.main.save_story", new_callable=AsyncMock, return_value=_STORY)
def test_create_story_happy_path(mock_save, mock_gen, mock_mod, mock_set, mock_get):
    response = client.post(
        "/stories",
        json={"child_theme": "magic forest", "character_name": "Luna"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-story-id"
    assert data["character_name"] == "Luna"
    mock_mod.assert_called_once()
    mock_gen.assert_called_once()
    mock_save.assert_called_once()


@patch("app.main.get_cached_story", new_callable=AsyncMock, return_value=_STORY)
@patch("app.main.moderate_story_request", new_callable=AsyncMock, return_value=_APPROVED)
def test_create_story_cache_hit(mock_mod, mock_get):
    with patch("app.main.generate_story", new_callable=AsyncMock) as mock_gen:
        response = client.post(
            "/stories",
            json={"child_theme": "magic forest", "character_name": "Luna"},
        )
    assert response.status_code == 201
    assert response.json()["id"] == "test-story-id"
    mock_gen.assert_not_called()


@patch("app.main.moderate_story_request", new_callable=AsyncMock, return_value=_REJECTED)
def test_create_story_moderation_rejected(mock_mod):
    response = client.post(
        "/stories",
        json={"child_theme": "bad theme", "character_name": "Villain"},
    )
    assert response.status_code == 400
    assert "rejected" in response.json()["detail"].lower()


def test_create_story_missing_fields():
    response = client.post("/stories", json={"child_theme": "forest"})
    assert response.status_code == 422


@patch("app.main.moderate_story_request", new_callable=AsyncMock, return_value=_REJECTED)
def test_stream_story_moderation_rejected(mock_mod):
    response = client.post(
        "/stories/stream",
        json={"child_theme": "bad theme", "character_name": "Villain"},
    )
    assert response.status_code == 400


@patch("app.main.get_cached_story", new_callable=AsyncMock, return_value=_STORY)
@patch("app.main.moderate_story_request", new_callable=AsyncMock, return_value=_APPROVED)
def test_stream_story_cache_hit_returns_sse(mock_mod, mock_get):
    with client.stream(
        "POST",
        "/stories/stream",
        json={"child_theme": "magic forest", "character_name": "Luna"},
    ) as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        lines = [line for line in response.iter_lines() if line.startswith("data: ")]
        assert len(lines) > 0
        events = [json.loads(line[6:]) for line in lines]
        assert all(e.get("cached") is True for e in events)
        assert events[-1].get("done") is True
        assert "story_id" in events[-1]
