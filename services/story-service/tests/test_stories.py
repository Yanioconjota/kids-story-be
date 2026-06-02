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

_STORY_DOC = _STORY.model_dump(mode="json")


def _make_collection(find_one_result=None, find_results=None, count=0):
    collection = AsyncMock()
    collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id=_STORY.id))
    collection.find_one = AsyncMock(return_value=find_one_result)
    collection.count_documents = AsyncMock(return_value=count)

    cursor = AsyncMock()
    cursor.sort = MagicMock(return_value=cursor)
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=find_results or [])
    collection.find = MagicMock(return_value=cursor)

    return collection


def _override(find_one_result=None, find_results=None, count=0):
    col = _make_collection(find_one_result, find_results, count)
    app.dependency_overrides[get_stories_collection] = lambda: col
    return col


_override(find_one_result=_STORY_DOC, find_results=[_STORY_DOC], count=1)
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "story-service"}


def test_create_story():
    response = client.post("/stories", json=_STORY_DOC)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "test-story-id-456"
    assert data["character_name"] == "Aria"


def test_get_story():
    response = client.get(f"/stories/{_STORY.id}")
    assert response.status_code == 200
    assert response.json()["id"] == "test-story-id-456"


def test_get_story_not_found():
    _override(find_one_result=None)
    response = client.get("/stories/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
    _override(find_one_result=_STORY_DOC, find_results=[_STORY_DOC], count=1)


def test_list_stories():
    response = client.get("/stories")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == "test-story-id-456"


def test_list_stories_pagination_params():
    response = client.get("/stories?limit=5&offset=10")
    assert response.status_code == 200
    data = response.json()
    assert data["limit"] == 5
    assert data["offset"] == 10


def test_list_stories_invalid_limit():
    response = client.get("/stories?limit=999")
    assert response.status_code == 422


def test_create_story_missing_content():
    payload = _STORY_DOC.copy()
    del payload["content"]
    response = client.post("/stories", json=payload)
    assert response.status_code == 422
