from fastapi import FastAPI

from shared.contracts.story import ModerationResult, StoryRequest
from app.moderator import moderate

app = FastAPI(title="moderation-service")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "moderation-service"}


@app.post("/moderate", response_model=ModerationResult)
async def moderate_request(request: StoryRequest) -> ModerationResult:
    return await moderate(request)
