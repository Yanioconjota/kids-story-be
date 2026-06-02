import json
import os
from collections.abc import AsyncGenerator

import httpx

from shared.contracts.story import ModerationResult, Story, StoryRequest
from shared.errors.exceptions import downstream_error

MODERATION_URL = os.getenv("MODERATION_URL", "http://moderation-service:8001")
LLM_URL = os.getenv("LLM_URL", "http://llm-service:8002")
STORY_URL = os.getenv("STORY_URL", "http://story-service:8003")

TIMEOUT = 30.0
STREAM_TIMEOUT = 120.0


async def moderate_story_request(request: StoryRequest) -> ModerationResult:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{MODERATION_URL}/moderate",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return ModerationResult(**response.json())
    except httpx.HTTPStatusError as exc:
        raise downstream_error("moderation-service", str(exc)) from exc
    except httpx.RequestError as exc:
        raise downstream_error("moderation-service", f"unreachable: {exc}") from exc


async def generate_story(request: StoryRequest) -> Story:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{LLM_URL}/generate",
                json=request.model_dump(),
            )
            response.raise_for_status()
            return Story(**response.json())
    except httpx.HTTPStatusError as exc:
        raise downstream_error("llm-service", str(exc)) from exc
    except httpx.RequestError as exc:
        raise downstream_error("llm-service", f"unreachable: {exc}") from exc


async def save_story(story: Story) -> Story:
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(
                f"{STORY_URL}/stories",
                json=story.model_dump(mode="json"),
            )
            response.raise_for_status()
            return Story(**response.json())
    except httpx.HTTPStatusError as exc:
        raise downstream_error("story-service", str(exc)) from exc
    except httpx.RequestError as exc:
        raise downstream_error("story-service", f"unreachable: {exc}") from exc


async def stream_story_chunks(request: StoryRequest) -> AsyncGenerator[str, None]:
    """Consume SSE from llm-service /generate/stream and yield raw text chunks."""
    try:
        async with httpx.AsyncClient(timeout=STREAM_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{LLM_URL}/generate/stream",
                json=request.model_dump(mode="json"),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                    except json.JSONDecodeError:
                        continue
                    if data.get("done"):
                        return
                    chunk = data.get("chunk", "")
                    if chunk:
                        yield chunk
    except httpx.HTTPStatusError as exc:
        raise downstream_error("llm-service", str(exc)) from exc
    except httpx.RequestError as exc:
        raise downstream_error("llm-service", f"unreachable: {exc}") from exc
