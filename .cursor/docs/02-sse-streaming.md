# 02 — SSE Streaming

**Status:** ✅ Done · **Owning services:** `llm-service` (produces), `api-gateway` (forwards)

## Summary

Stream the story to the client token-by-token as the LLM generates it, instead of waiting for
the full text. Improves perceived speed for longer stories. Uses Server-Sent Events (SSE),
not WebSockets, per the project rules.

## Owning services

- `llm-service`: new streaming endpoint that yields chunks from the LLM.
- `api-gateway`: a streaming endpoint that proxies the SSE stream to the client and, on
  completion, persists the assembled Story via `story-service`.

## Contract / event shape

SSE events carry JSON with `chunk` / `done` fields (and `cached` when served from cache):

```
event: message
data: {"chunk": "Once upon a time", "done": false}

event: message
data: {"chunk": " ...happily ever after.", "done": false}

event: message
data: {"chunk": "", "done": true, "story_id": "uuid-here"}
```

Errors are yielded inside the generator as an `error` event, then the generator returns:

```
event: error
data: {"detail": "llm-service unavailable"}
```

## Implementation approach

1. `llm-service`: add `POST /generate/stream` returning `StreamingResponse` with
   `media_type="text/event-stream"`; the async generator yields chunks as the provider streams.
2. `api-gateway`: add `POST /stories/stream`:
   - moderate first (same as non-streaming flow; reject early on disapproval),
   - open an `httpx.AsyncClient.stream(...)` to `llm-service`, relay each event to the client,
   - accumulate chunks; when `done`, call `story-service` to persist and emit the final `story_id`.
3. Keep the existing non-streaming `POST /stories` for clients that don't need streaming.

## Rules applied

- `003-sse-streaming.md` — JSON `chunk`/`done` events; errors as `event: error` then `return`.
- `000-project-context.md` — "Do not introduce WebSockets unless a clear bidirectional requirement exists." Story streaming is one-directional → SSE.
- `002-fastapi-patterns.md` — async, timeouts, specific errors.

## Testing

- Backend integration test (per `007-testing-patterns.md`): consume the stream with
  `httpx.AsyncClient`, assert at least one `chunk` and a terminal `done: true`.
- Test the moderation-reject path returns before any stream starts.

## Out of scope

- Bidirectional/interactive editing (would require WebSockets — not in scope).
