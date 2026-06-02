# Kids Story Backend — Feature Knowledge Base

Design notes and implementation guides for features beyond the MVP bootstrap.
Each doc is a self-contained reference: what the feature is, which service owns it,
the contract changes, the implementation approach, and how it follows the project rules.

> Source of truth for scope/order: `.cursor/specs/kids-story-backend-devplan.md` (Post-MVP Roadmap).
> Highest-priority rules: `.cursor/rules/000-project-context.md`.

## Status legend

- ✅ Done — implemented and verified
- 🟡 Planned — designed here, not yet built
- ⚪ Later — out of current MVP scope

## Index

| # | Feature | Service(s) | Status | Doc |
|---|---------|-----------|--------|-----|
| 0 | MVP bootstrap (4 services, mock LLM/moderation) | all | ✅ Done | `../specs/kids-story-backend-devplan.md` |
| 1 | Real LLM integration | `llm-service` | 🟡 Planned | `01-llm-integration.md` |
| 2 | SSE streaming | `llm-service`, `api-gateway` | 🟡 Planned | `02-sse-streaming.md` |
| 3 | Real moderation | `moderation-service` | 🟡 Planned | `03-real-moderation.md` |
| 4 | Redis caching | `api-gateway` / `llm-service` | 🟡 Planned | `04-redis-caching.md` |
| 5 | Story listing + pagination | `story-service` | 🟡 Planned | `05-story-listing.md` |
| 6 | Lightweight user identity | `api-gateway`, `story-service` | ⚪ Later | — |
| 7 | Full authentication | `api-gateway` | ⚪ Later | — |

## Recommended build order

**LLM → SSE streaming → Caching**, then moderation and listing as they fit.
This reaches a genuinely useful product fastest, since the plumbing for all three
is already in place from the MVP.

## Conventions for new feature docs

When adding a feature doc, keep this structure:

1. **Summary** — one paragraph, plain English.
2. **Owning service(s)** — respect the four-service boundaries.
3. **Contract changes** — new/changed Pydantic models in `shared/contracts/`.
4. **Implementation approach** — endpoints, flow, key code touch-points.
5. **Rules applied** — which `.cursor/rules/*` files govern it and how.
6. **Testing** — what pytest coverage looks like.
7. **Out of scope** — what this feature deliberately does not do.
