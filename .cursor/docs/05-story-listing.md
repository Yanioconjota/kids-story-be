# 05 — Story Listing + Pagination

**Status:** ✅ Done · **Owning service:** `story-service`

## Summary

Add a paginated `GET /stories` so saved stories can be browsed most-recent-first. The MongoDB
index on `created_at` (created at startup) already supports this efficiently.

## Owning service

`story-service`. Optionally expose a passthrough on `api-gateway` later if the external API
should surface listing.

## Contract changes

Add a response model in `shared/contracts/story.py`:

```python
class StoryList(BaseModel):
    items: list[Story]
    total: int
    limit: int
    offset: int
```

## Endpoint

```
GET /stories?limit=20&offset=0
```

- `limit`: `Query(default=20, ge=1, le=100)`
- `offset`: `Query(default=0, ge=0)`

## Implementation approach

1. Add `GET /stories` to `services/story-service/app/main.py`:
   - `find({}, {"_id": 0}).sort("created_at", -1).skip(offset).limit(limit)`
   - `count_documents({})` for `total`.
2. Return a `StoryList`. Validate `limit`/`offset` via `Query(...)` bounds.

## Rules applied

- `005-mongodb-patterns.md` — list-with-pagination pattern (`sort` + `skip` + `limit`),
  `count_documents` for metadata, query by indexed fields.
- `002-fastapi-patterns.md` — typed query params with bounds, async handler.

## Testing

- Seed/mocked collection: assert ordering (newest first), `limit`/`offset` behavior, and
  `total` correctness.
- Validation: `limit` above max / negative `offset` → `422`.

## Out of scope

- Filtering/search by theme or character (could come with user identity — see roadmap #6).
- Cursor-based pagination (offset paging is fine at MVP scale).
