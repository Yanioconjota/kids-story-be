from fastapi import FastAPI

from shared.contracts.story import Story, StoryRequest

app = FastAPI(title="llm-service")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "llm-service"}


@app.post("/generate", response_model=Story)
async def generate(request: StoryRequest) -> Story:
    # MVP: mock story generation
    quest = (
        f"Their quest began when: {request.prompt}"
        if request.prompt
        else "Their adventure was just beginning."
    )
    content = (
        f"Once upon a time, in a land of {request.child_theme}, "
        f"there lived a brave hero named {request.character_name}. "
        f"{quest} "
        "And they lived happily ever after."
    )
    return Story(
        child_theme=request.child_theme,
        character_name=request.character_name,
        prompt=request.prompt,
        content=content,
    )
