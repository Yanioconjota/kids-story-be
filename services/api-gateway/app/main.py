from fastapi import FastAPI, HTTPException

from shared.contracts.story import Story, StoryRequest
from app.clients import generate_story, moderate_story_request, save_story

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

    story = await generate_story(request)
    return await save_story(story)
