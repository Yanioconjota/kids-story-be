from fastapi import FastAPI

from shared.contracts.story import ModerationResult, StoryRequest

app = FastAPI(title="moderation-service")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "moderation-service"}


@app.post("/moderate", response_model=ModerationResult)
async def moderate(request: StoryRequest) -> ModerationResult:
    # MVP: mock — all story requests pass moderation
    return ModerationResult(approved=True)
