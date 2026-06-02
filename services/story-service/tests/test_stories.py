from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from fastapi.testclient import TestClient

from app.database import get_stories_collection
from app.main import app
from shared.contracts.story import Story

_STORY = Story(
    id="test-story-id-456",
    child_theme="enchanted forest",
    character_name="Aria",
    content="Once upon a time in an enchanted forest...",
    created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
)


def _make_collection(find_result=None):
    collection = AsyncMock()
    collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="test-story-id-456"))
    collection.find_one = AsyncMock(return_value=find_result)
    return collection


def _override_with(find_result):
    col = _make_collection(find_result)
    app.dependency_overrides[get_stories_collection] = lambda: col
    return col


_override_with(_STORY.model_dump(mode="json"))
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "story-service"}


def test_create_story():
    response = client.post("/stories", json=_STORY.model_dump(mode="json"))
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-story-id-456"
    assert data["character_name"] == "Aria"


def test_get_story():
    response = client.get(f"/stories/{_STORY.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-story-id-456"
    assert data["child_theme"] == "enchanted forest"


def test_get_story_not_found():
    _override_with(None)
    response = client.get("/stories/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    _override_with(_STORY.model_dump(mode="json"))


def test_create_story_missing_content():
    payload = _STORY.model_dump(mode="json")
    del payload["content"]
    response = client.post("/stories", json=payload)
    assert response.status_code == 422
