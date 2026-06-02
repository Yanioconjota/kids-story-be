import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from shared.contracts.story import Story, StoryRequest
from app.cache import (
    clear_all_story_cache,
    delete_cached_story,
    get_cached_story,
    set_cached_story,
)
from app.clients import (
    generate_story,
    moderate_story_request,
    save_story,
    stream_story_chunks,
)

app = FastAPI(title="api-gateway")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.post("/stories", response_model=Story, status_code=201)
async def create_story(request: StoryRequest) -> Story:
    moderation = await moderate_story_request(request)

    if not moderation.approved:
        raise HTTPException(
            status_code=400,
            detail=f"Story request rejected by moderation: {moderation.reason or 'content not allowed'}",
        )

    cached = await get_cached_story(request)
    if cached:
        return cached

    story = await generate_story(request)
    saved = await save_story(story)
    await set_cached_story(request, saved)
    return saved


@app.post("/stories/stream")
async def stream_story(request: StoryRequest) -> StreamingResponse:
    moderation = await moderate_story_request(request)

    if not moderation.approved:
        raise HTTPException(
            status_code=400,
            detail=f"Story request rejected by moderation: {moderation.reason or 'content not allowed'}",
        )

    cached = await get_cached_story(request)
    if cached:
        return StreamingResponse(
            _stream_from_cache(cached),
            media_type="text/event-stream",
        )

    return StreamingResponse(
        _stream_from_llm(request),
        media_type="text/event-stream",
    )


@app.delete("/cache", status_code=200)
async def clear_cache():
    """Remove all cached story entries."""
    deleted = await clear_all_story_cache()
    return {"deleted_keys": deleted, "message": f"Cleared {deleted} cached story entries"}


@app.delete("/cache/story", status_code=200)
async def invalidate_story_cache(request: StoryRequest):
    """Remove the cache entry for a specific story request."""
    removed = await delete_cached_story(request)
    return {"removed": removed, "message": "Cache entry removed" if removed else "No cache entry found"}


async def _stream_from_cache(story: Story):
    """Replay a cached story word-by-word so the client gets a consistent streaming UX."""
    import asyncio  # noqa: PLC0415
    for word in story.content.split():
        yield f"data: {json.dumps({'chunk': word + ' ', 'done': False, 'cached': True})}\n\n"
        await asyncio.sleep(0.02)
    yield f"data: {json.dumps({'chunk': '', 'done': True, 'cached': True, 'story_id': story.id})}\n\n"


async def _stream_from_llm(request: StoryRequest):
    """Stream from llm-service, accumulate, persist, and emit story_id at completion."""
    from uuid import uuid4  # noqa: PLC0415
    story_id = str(uuid4())
    chunks: list[str] = []

    try:
        async for chunk in stream_story_chunks(request):
            chunks.append(chunk)
            yield f"data: {json.dumps({'chunk': chunk, 'done': False, 'cached': False})}\n\n"

        content = "".join(chunks)
        story = Story(
            id=story_id,
            child_theme=request.child_theme,
            character_name=request.character_name,
            prompt=request.prompt,
            content=content,
        )
        saved = await save_story(story)
        await set_cached_story(request, saved)
        yield f"data: {json.dumps({'chunk': '', 'done': True, 'cached': False, 'story_id': story_id})}\n\n"

    except Exception as exc:
        yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
