# 04 — Redis Caching

**Status:** ✅ Done · **Owning service:** `api-gateway`

## Summary

Cache generated stories so identical Story Requests return instantly without re-calling the
LLM, saving tokens and latency. Redis is already wired into `docker-compose.yml` and the
`REDIS_URL` env var is set.

## Where to cache

Recommended: **`api-gateway`**, keyed on the moderated request, checked right before calling
`llm-service`. (Caching in `llm-service` is also valid; gateway keeps the LLM service stateless
and lets the cache short-circuit the network hop.)

## Cache key & value

- **Key:** prefixed + hashed over all inputs that affect output:
  `story:v1:{sha256(child_theme | character_name | prompt | max_words | model)}`
- **Value:** the serialized `Story` JSON.
- **TTL:** ~1 hour for generated stories (tune later).

## Implementation approach

1. Add a redis client (`redis.asyncio`) in the owning service; read `REDIS_URL` from env.
2. On `POST /stories` (after moderation passes):
   - compute key → `GET`. On hit, return the cached Story (optionally mark `cached: true`).
   - On miss, generate, persist, then `SET` with TTL.
3. **Degrade gracefully:** any Redis error (timeout, down) is caught and logged; the request
   proceeds as if it were a cache miss. The cache must never break the core flow.

## Rules applied

- `004-caching-patterns.md` — prefixed/hashed keys including all relevant params; sensible TTL;
  cache errors degrade gracefully.
- `002-fastapi-patterns.md` — async client, timeouts.

## Testing

- Test cache hit path (seed Redis or mock the client) returns without calling the LLM.
- Test that a simulated Redis failure still returns a story (graceful degradation).

## Out of scope

- Cache invalidation UI / manual purge endpoints.
- Caching streamed responses (revisit after `02-sse-streaming.md`).
