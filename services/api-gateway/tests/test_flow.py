from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app
from shared.contracts.story import ModerationResult, Story

client = TestClient(app)

_STORY = Story(
    id="test-story-id",
    child_theme="magic forest",
    character_name="Luna",
    content="Once upon a time...",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
)

_APPROVED = ModerationResult(approved=True)
_REJECTED = ModerationResult(approved=False, reason="inappropriate content")


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "api-gateway"}


@patch("app.main.moderate_story_request", new_callable=AsyncMock, return_value=_APPROVED)
@patch("app.main.generate_story", new_callable=AsyncMock, return_value=_STORY)
@patch("app.main.save_story", new_callable=AsyncMock, return_value=_STORY)
def test_create_story_happy_path(mock_save, mock_generate, mock_moderate):
    response = client.post(
        "/stories",
        json={"child_theme": "magic forest", "character_name": "Luna"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-story-id"
    assert data["character_name"] == "Luna"
    mock_moderate.assert_called_once()
    mock_generate.assert_called_once()
    mock_save.assert_called_once()


@patch("app.main.moderate_story_request", new_callable=AsyncMock, return_value=_REJECTED)
def test_create_story_rejected_by_moderation(mock_moderate):
    response = client.post(
        "/stories",
        json={"child_theme": "bad theme", "character_name": "Villain"},
    )
    assert response.status_code == 400
    assert "rejected" in response.json()["detail"].lower()


def test_create_story_missing_required_fields():
    response = client.post("/stories", json={"child_theme": "forest"})
    assert response.status_code == 422
