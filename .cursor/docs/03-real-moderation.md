# 03 — Real Moderation

**Status:** ✅ Done · **Owning service:** `moderation-service`

## Summary

Replace the mock `approved: True` with real child-safety validation so unsafe Story Requests
are blocked before they reach the LLM. The gateway already stops the flow on disapproval.

## Current state

`services/moderation-service/app/main.py` returns `ModerationResult(approved=True)` for every
request. The gateway already raises `HTTPException(400, ...)` when `approved` is `False`, so no
gateway change is needed to enforce a real result.

## Owning service

`moderation-service` only.

## Contract changes

The existing `ModerationResult` already supports a `reason`. Optionally enrich it:

```python
class ModerationResult(BaseModel):
    approved: bool
    reason: Optional[str] = None
    categories: list[str] = Field(default_factory=list)   # optional: which checks tripped
```

Add provider config to `services/moderation-service/.env.template`:

```
MODERATION_PROVIDER=mock        # mock | openai | rules
MODERATION_API_KEY=
```

## Implementation approach

1. Add `app/moderator.py` with async `moderate(request) -> ModerationResult`.
2. Layered checks (cheap first):
   - a small local blocklist / rules pass on `child_theme`, `character_name`, `prompt`;
   - then an external moderation API (e.g. OpenAI Moderation) via `httpx.AsyncClient`.
3. On provider failure, **fail closed** for child safety: return `approved=False` with a clear
   reason (a kids' product should not pass content through when the safety check is down).
4. Keep `MODERATION_PROVIDER=mock` for dev/tests.

## Rules applied

- `000-project-context.md` — moderation-service owns "Child safety validation / Content moderation".
- `002-fastapi-patterns.md` — async, timeouts, clear errors.
- Domain language: this validates a **Story Request**, producing a **Moderation Result**.

## Testing

- `mock` provider keeps current tests green.
- Add tests: a blocklisted prompt returns `approved=False` with a reason; provider-down path
  fails closed (`approved=False`).
- Gateway test already covers the reject → `400` behavior.

## Out of scope

- Human review queues / appeals workflow.
