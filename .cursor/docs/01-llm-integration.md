# 01 — Real LLM Integration

**Status:** ✅ Done · **Owning service:** `llm-service`

## Summary

Replace the string-template mock in `POST /generate` with a real LLM call so stories are
actually generated from the Child Theme, Character Name, and Story Prompt. This is the
highest-value post-MVP change; the rest of the system (orchestration, moderation,
persistence) stays untouched.

## Current state

`services/llm-service/app/main.py` builds `content` from an f-string template. It echoes the
prompt back verbatim and has no narrative understanding — hence the "bland" output.

## Owning service

`llm-service` only. The `api-gateway` already calls `POST /generate` and forwards the result
to `story-service`; that contract does not change.

## Contract changes

No change to the public `Story` shape returned. Internally, add provider config via env vars
(never hardcode keys):

```
# services/llm-service/.env.template
LLM_PROVIDER=openai          # openai | anthropic | ollama
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=                 # left blank in template
LLM_BASE_URL=                # optional, e.g. http://ollama:11434 for local
```

Optionally extend `StoryRequest` (in `shared/contracts/story.py`) with safe, typed knobs:

```python
class StoryRequest(BaseModel):
    child_theme: str = Field(..., max_length=120)
    character_name: str = Field(..., max_length=80)
    prompt: Optional[str] = Field(default=None, max_length=500)
    max_words: int = Field(default=300, ge=50, le=1000)   # optional length control
```

## Implementation approach

1. Add an `app/llm_client.py` in `llm-service` with an async `generate_content(request) -> str`.
2. Build a child-safe system prompt (age-appropriate tone, gentle vocabulary, positive ending).
3. Call the provider with `httpx.AsyncClient` (or the provider SDK if it's async-safe).
4. Map provider failures to a clear `HTTPException(502, ...)` so the gateway surfaces a useful error.
5. Keep the existing mock behind `LLM_PROVIDER=mock` for offline/dev runs and tests.

## Rules applied

- `002-fastapi-patterns.md` — `async def`, `httpx.AsyncClient` with timeout, specific `HTTPException`.
- `000-project-context.md` — story-generation domain language; no scope creep (no narration/images).
- `001-project-architecture.md` — config via `.env.template`, never commit keys.

## Testing

- `LLM_PROVIDER=mock` keeps existing deterministic tests green.
- Add a test that mocks the provider HTTP call and asserts a non-empty `content` and 502 on provider error.

## Out of scope

- Streaming (see `02-sse-streaming.md`).
- Image generation, narration/audio — excluded by MVP constraints.
