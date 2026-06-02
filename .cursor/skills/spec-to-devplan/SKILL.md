---
name: spec-to-devplan
description: >-
  Extract specifications from user stories, technical documents, or prompts and generate
  a backend development plan aligned with project rules for the Kids Story platform
  (FastAPI microservices, MongoDB, Redis, SSE, Docker Compose). Detects conflicts between
  specs and coding standards or MVP constraints, consulting the user before proceeding.
  Use when the user mentions /spec-to-devplan, wants to create a backend feature or
  service from requirements, needs a dev plan from a story, or asks to analyze specs
  against project conventions.
---

# Spec to Dev Plan (Backend)

Extracts specifications from text and generates a backend development plan that complies with the project's coding standards, domain language, and MVP constraints.

This skill is scoped to the **Kids Story backend**: a backend-only MVP for a children's story generation platform built with FastAPI microservices (`api-gateway`, `story-service`, `moderation-service`, `llm-service`), MongoDB, Redis, SSE streaming, and Docker Compose.

## Quick Start

```
/spec-to-devplan [paste your user story, technical spec, or prompt]
/spec-to-devplan --service=story-service [specs...]
```

## Workflow

Copy this checklist and track progress:

```
Task Progress:
- [ ] Step 1: Parse input text
- [ ] Step 2: Extract technical specifications
- [ ] Step 3: Load project rules
- [ ] Step 4: Detect rule & MVP-constraint conflicts
- [ ] Step 5: Consult user on conflicts
- [ ] Step 6: Determine new service vs feature in existing service
- [ ] Step 7: Generate compliant dev plan
```

---

## Step 1: Parse Input Text

Identify the type of input:

| Input Type | Indicators |
|------------|------------|
| **User Story** | "As a [role], I want [feature], so that [benefit]" |
| **Technical Spec** | Structured document with requirements, acceptance criteria |
| **Prompt/Description** | Freeform feature request or conversation |

Extract key elements:
- Feature name/purpose
- Functional requirements
- Technical requirements (explicit or implied)
- Acceptance criteria
- Constraints mentioned
- **Which service(s)** the work belongs to (`api-gateway`, `story-service`, `moderation-service`, `llm-service`)

### Domain Language Check

Normalize requirements to the project's domain language. Prefer:

- Story, Story Request, Story Generation, Child Theme, Character Name, Story Prompt, Moderation Result

Flag (and rephrase) generic chat terms unless they refer to infrastructure code:

- Conversation, Message, Chat, Chat History, Assistant Response, User Message

> If the spec is phrased in chat/conversation terms, restate it in story-generation terms in your extracted spec and note the translation.

---

## Step 2: Extract Technical Specifications

Categorize extracted specs into backend concerns:

| Category | Keywords to Detect | Owning Service (typical) |
|----------|-------------------|--------------------------|
| **Request Orchestration / API** | "endpoint", "REST", "external API", "entry point", "gateway", "route" | api-gateway |
| **Story Persistence** | "save", "store", "retrieve", "list", "history", "metadata", "MongoDB", "collection" | story-service |
| **Moderation / Safety** | "validate prompt", "child safety", "moderate", "filter", "block content" | moderation-service |
| **Story Generation** | "generate", "LLM", "prompt", "provider", "streaming", "tokens" | llm-service |
| **Streaming** | "SSE", "stream", "real-time", "progress", "token-by-token" | llm-service / api-gateway |
| **Caching** | "cache", "Redis", "TTL", "deduplicate", "speed up repeated" | any |
| **Data Models** | "schema", "fields", "request body", "response shape", "Pydantic" | any |
| **Inter-service Communication** | "call service", "internal HTTP", "httpx", "forward request" | any |

**Output format:**

```markdown
## Extracted Specifications

### Domain Summary
[Restated in story-generation domain language]

### Functional Requirements
1. [Requirement]
2. [Requirement]

### Technical Requirements (Explicit)
- [Tech spec mentioned in text]

### Technical Requirements (Implied)
- [Inferred from functionality]

### Affected Service(s)
- [api-gateway | story-service | moderation-service | llm-service]

### Constraints
- [Any limitations mentioned]
```

---

## Step 3: Load Project Rules

Read rules from `.cursor/rules/` based on spec categories. `000-project-context.md` is the **highest-priority** rule and must always be loaded.

| Spec Category | Rules to Load |
|---------------|---------------|
| Always (domain, services, MVP scope) | `000-project-context.md` |
| Service structure / communication | `001-project-architecture.md` |
| Endpoints, Pydantic, errors, async, DI | `002-fastapi-patterns.md` |
| Streaming / SSE | `003-sse-streaming.md` |
| Caching | `004-caching-patterns.md` |
| Persistence / queries / documents | `005-mongodb-patterns.md` |
| API contracts consumed by frontend | `006-frontend-integration.md` |
| Tests | `007-testing-patterns.md` |

---

## Step 4: Detect Rule & MVP-Constraint Conflicts

Compare each extracted spec against loaded rules **and** the MVP constraints in `000-project-context.md`.

### Common Conflicts

| Spec Says | Rule / Constraint Says | Conflict Type |
|-----------|------------------------|---------------|
| "use WebSockets for streaming" | SSE for story streaming; WebSockets only for true bidirectional need | Protocol Conflict |
| "add login / JWT / user accounts" | MVP excludes authentication & user accounts | MVP Scope Conflict |
| "add billing / image generation / narration" | MVP excludes these features | MVP Scope Conflict |
| "use Kafka / RabbitMQ / an event bus" | REST between services; no event buses in MVP | Architecture Conflict |
| "deploy on Kubernetes" | Docker Compose / Docker-first development | Infra Conflict |
| "accept a `dict` / `Any` request body" | Define request/response with Pydantic models | Type Safety Conflict |
| "use the `requests` library" | Use `httpx.AsyncClient` for async I/O | Async Conflict |
| "store everything in one service" | Respect service boundaries (gateway/story/moderation/llm) | Boundary Conflict |
| "model it as conversations/messages/chat" | Use story-generation domain language | Domain Language Conflict |
| "generic enterprise abstraction layer" | Readability over abstraction; avoid over-engineering | Over-engineering Conflict |
| "raise generic 500 on errors" | Specific `HTTPException` codes & clear messages | Error Handling Conflict |

### Conflict Report Template

```markdown
## ⚠️ Spec-Rule Conflict Detected

### Conflict #N: [Category]

**Spec requests:**
> [Quote from spec]

**Project rule / constraint states:**
> [Quote from rule file or 000-project-context.md]

**Rule source:** `.cursor/rules/[file].md`

**Why the rule exists:**
[Brief rationale from the rule]

**Documented exceptions:**
[If any exceptions apply, list them — e.g. WebSockets allowed only for bidirectional needs]

**Recommendation:**
🟢 Follow the rule: [Compliant approach to achieve same goal]
🟡 Exception may apply: [Explain why and conditions]
```

---

## Step 5: Consult User on Conflicts

**CRITICAL: Never proceed with rule violations or MVP scope expansions without explicit user approval.**

Present conflicts and wait for response:

```markdown
I found N conflicts between the specs and project rules/MVP constraints.

### Conflict 1: [Title]
[Conflict details]

**Options:**
A) ✅ Follow the rule (recommended) - [Brief compliant approach]
B) ⚠️ Document as exception - [Requires justification]
C) 💬 Discuss further - [If unclear]

Please select how to proceed for each conflict before I generate the dev plan.
```

**Wait for user response. Do not proceed until all conflicts are resolved.**

---

## Step 6: Determine New Service vs Feature in Existing Service

Ask the user if not clear from context:

```markdown
📦 **Scope**

Based on the specs, this could be:

**A) New Microservice**
- Creates a new folder at the repo root: `[service-name]/`
- Self-contained FastAPI container: `Dockerfile`, `requirements.txt`, `.env.template`, `app/`
- Added as a service in `docker-compose.yml`
- Communicates with other services via REST

**B) Feature in an Existing Service**
- Adds to one of `api-gateway/`, `story-service/`, `moderation-service/`, `llm-service/`
- Reuses existing models, database connections, and config
- New endpoints / routes within that service

Which approach should I use?
```

### Service Naming (if new service)

A new service should be justified against the four-service architecture before adding it. If approved, follow conventions:

| Responsibility | Suggested Name |
|----------------|----------------|
| request orchestration / external API | `api-gateway` |
| story CRUD / persistence / metadata | `story-service` |
| prompt validation / child safety | `moderation-service` |
| story generation / LLM provider | `llm-service` |

**Naming rules:**
- kebab-case ending in `-service` (except `api-gateway`)
- Descriptive of a single responsibility
- Do not create a new service when a feature fits an existing one (avoid over-engineering)

---

## Step 7: Generate Compliant Dev Plan

After resolving conflicts and determining scope, generate the plan.

### For New Service

```markdown
# Development Plan: [service-name]

## Overview
[Brief description based on specs, in story-generation domain language]

## Service Setup

### Service Location
📁 **Root folder:** `[service-name]/`
📍 **Path:** `[repo-root]/[service-name]/`

### Initialization
- [ ] Create `[service-name]/Dockerfile` (Python base image, uvicorn entrypoint)
- [ ] Create `[service-name]/requirements.txt` (fastapi, uvicorn, pydantic, httpx, + as needed: pymongo/motor, redis)
- [ ] Create `[service-name]/.env.template` (never commit `.env`)
- [ ] Add service block to `docker-compose.yml` (ports, env, depends_on)

## Service Structure

[service-name]/
├── Dockerfile
├── requirements.txt
├── .env.template
└── app/
    ├── main.py           # FastAPI app, routes (or include_router for 10+ endpoints)
    ├── models.py         # Pydantic request/response models
    ├── database.py       # MongoDB / Redis connections
    ├── routes/           # Route modules (only for large services)
    │   └── [feature].py
    └── utils/
        └── helpers.py
```

### For Feature in an Existing Service

```markdown
# Development Plan: [Feature Name]

## Overview
[Brief description based on specs, in story-generation domain language]

## Target Service
📁 **Service:** `[api-gateway | story-service | moderation-service | llm-service]`
📍 **Path:** `[service-name]/app/`

## Changes
- [ ] Add Pydantic models to `app/models.py`
- [ ] Add endpoint(s) to `app/main.py` (or `app/routes/[feature].py` if service has 10+ endpoints)
- [ ] Wire any new MongoDB collection / index in `app/database.py`
- [ ] Add cache read/write if applicable
```

### Common Sections (Both)

```markdown
## Specs Summary

| Requirement | Compliant Implementation |
|-------------|-------------------------|
| [Spec 1] | [How it follows rules] |
| [Spec 2] | [How it follows rules] |

## Resolved Conflicts

| Original Spec | Resolution | Justification |
|---------------|------------|---------------|
| [Conflict] | [Chosen approach] | [Why] |

## Implementation Checklist

### Data Models (Pydantic)
- [ ] Define request/response models with explicit types and `Field()` defaults
- [ ] Use UUID string `id` (`default_factory=lambda: str(uuid4())`) for persisted documents
- [ ] No `dict` / `Any` request bodies

### API Endpoints (FastAPI)
- [ ] `async def` handlers for I/O
- [ ] Specific `HTTPException` status codes with clear `detail` messages
- [ ] `Depends()` for shared logic (DB connection, etc.)
- [ ] Tags for OpenAPI grouping when using routers

### Inter-service Communication
- [ ] REST via `httpx.AsyncClient` with timeout (no blocking `requests`)
- [ ] Respect service boundaries; gateway orchestrates, services own their data

### Persistence (MongoDB) — if applicable
- [ ] Document uses UUID `id`; `_id` left for internal use
- [ ] Create indexes on startup for queried fields
- [ ] Atomic updates with `$set` / `$inc` (no read-modify-write)
- [ ] Hard delete by default; soft delete only if audit trail required

### Caching (Redis) — if applicable
- [ ] Prefixed, hashed cache keys including all relevant params
- [ ] Appropriate TTL (e.g. generated stories ~1h)
- [ ] Cache errors degrade gracefully (never break the request)

### Streaming (SSE) — if applicable
- [ ] JSON events with `chunk` / `done` (and `cached`) fields
- [ ] Errors yielded as `event: error` inside the generator, then `return`
- [ ] SSE (not WebSocket) unless a bidirectional need was approved

### Error Handling
- [ ] Validation handled by Pydantic at the boundary
- [ ] Specific, actionable error messages

### Testing (pytest)
- [ ] Test endpoints via FastAPI `TestClient` (behavior, not internals)
- [ ] Cover error paths (404, validation, limits)
- [ ] Integration test for SSE streams when applicable

### Docker / Config
- [ ] `.env.template` updated with any new variables
- [ ] `docker-compose.yml` updated (new service or new env)
- [ ] No hardcoded connection strings

## Files to Create / Modify

| File | Purpose |
|------|---------|
| `[service-name]/app/models.py` | Pydantic models |
| `[service-name]/app/main.py` | Endpoints / routes |
| `[service-name]/app/database.py` | DB connections & indexes |
| `[service-name]/tests/test_[feature].py` | pytest coverage |
| `docker-compose.yml` | Service / env wiring |

## Estimated Complexity
- **Endpoints:** N
- **Pydantic models:** N
- **External service calls:** N
- **Effort:** Low | Medium | High
```

---

## Notes

- Always quote the specific rule being referenced (file + section).
- Provide the rationale, not just the rule.
- Suggest compliant alternatives that achieve the same goal.
- Keep the four-service architecture and MVP scope intact; flag anything that expands it.
- Use story-generation domain language, not chat/conversation terms.
- Prefer simple, readable implementations over generic enterprise patterns.
- **Never generate code that violates rules or MVP constraints without explicit approval.**
- When in doubt, ask the user.
