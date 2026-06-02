import os

os.environ.setdefault("MODERATION_PROVIDER", "mock")

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "moderation-service"}


def test_mock_approves_all():
    response = client.post(
        "/moderate",
        json={"child_theme": "magic forest", "character_name": "Luna"},
    )
    assert response.status_code == 200
    assert response.json()["approved"] is True


def test_mock_approves_with_prompt():
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


def test_missing_fields_returns_422():
    response = client.post("/moderate", json={"child_theme": "forest"})
    assert response.status_code == 422


def test_rules_provider_blocks_inappropriate_content():
    os.environ["MODERATION_PROVIDER"] = "rules"
    import importlib  # noqa: PLC0415
    import app.moderator as mod_module  # noqa: PLC0415
    importlib.reload(mod_module)

    from app.moderator import moderate  # noqa: PLC0415
    from shared.contracts.story import StoryRequest  # noqa: PLC0415
    import asyncio  # noqa: PLC0415

    request = StoryRequest(child_theme="violence and chaos", character_name="Hero")
    result = asyncio.run(moderate(request))
    assert result.approved is False
    assert result.reason is not None
    assert "local_rules" in result.categories

    os.environ["MODERATION_PROVIDER"] = "mock"
    importlib.reload(mod_module)


def test_rules_provider_approves_clean_content():
    import importlib  # noqa: PLC0415
    import app.moderator as mod_module  # noqa: PLC0415
    os.environ["MODERATION_PROVIDER"] = "rules"
    importlib.reload(mod_module)

    from app.moderator import moderate  # noqa: PLC0415
    from shared.contracts.story import StoryRequest  # noqa: PLC0415
    import asyncio  # noqa: PLC0415

    request = StoryRequest(child_theme="enchanted forest", character_name="Aria")
    result = asyncio.run(moderate(request))
    assert result.approved is True

    os.environ["MODERATION_PROVIDER"] = "mock"
    importlib.reload(mod_module)
