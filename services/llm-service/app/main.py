import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from shared.contracts.story import Story, StoryRequest
from app.llm_client import generate_content, stream_content

app = FastAPI(title="llm-service")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "llm-service"}


@app.post("/generate", response_model=Story)
async def generate(request: StoryRequest) -> Story:
    content = await generate_content(request)
    return Story(
        child_theme=request.child_theme,
        character_name=request.character_name,
        prompt=request.prompt,
        content=content,
    )


@app.post("/generate/stream")
async def generate_stream(request: StoryRequest) -> StreamingResponse:
    async def event_generator():
        try:
            async for chunk in stream_content(request):
                yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
            yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
