# 📖 Kids Story Backend

> *A tiny story factory that turns a child's imagination into a bedtime tale — one microservice at a time.*

---

## 🌟 What Is This?

Kids Story Backend is the engine behind a children's story-generation platform. You give it a theme (like "magic forest") and a character name (like "Luna"), and it hands back a freshly written story.

**How does it work — in plain English?**

Think of it like a little book-making shop with four workers, each doing one job:

| Worker | Job |
|---|---|
| 🚪 **The Receptionist** (`api-gateway`) | Takes your order at the front desk and coordinates everyone else. |
| 🛡️ **The Safety Inspector** (`moderation-service`) | Checks that the story request is child-appropriate before anything gets written. |
| ✍️ **The Storyteller** (`llm-service`) | Actually writes the story (currently a stand-in writer; a real AI author is coming). |
| 📦 **The Librarian** (`story-service`) | Saves the finished story to the bookshelf (MongoDB) and lets you look it up later. |

If the Safety Inspector waves it through, the Storyteller writes the tale, and the Librarian files it away. If the Inspector flags it, the shop politely declines — no story is written.

---

## 🏗️ Architecture

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                         Your App / curl                         │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │  POST /stories
                                 ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │              api-gateway  :8000                                  │
  │  Entry point — receives story requests, orchestrates the flow    │
  └───────┬──────────────────────────────────────────────────────────┘
          │ POST /moderate
          ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │              moderation-service  :8001                          │
  │  Safety check — approves or rejects the request                 │
  │  (mock: always approved in MVP)                                 │
  └───────┬─────────────────────────────────────────────────────────┘
          │ POST /generate  (only if approved)
          ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │              llm-service  :8002                                 │
  │  Story generation — produces the story text                     │
  │  (mock: returns a fixed "Once upon a time…" in MVP)             │
  └───────┬─────────────────────────────────────────────────────────┘
          │ POST /stories
          ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │              story-service  :8003                               │
  │  Persistence — saves the story & serves it back by ID           │
  └───────┬─────────────────────────────────────────────────────────┘
          │
          ▼
  ┌───────────────────────┐     ┌──────────────────────────┐
  │   MongoDB  :27017     │     │   Redis  :6379            │
  │  Story storage        │     │  Wired, not yet used      │
  └───────────────────────┘     └──────────────────────────┘
```

---

## 🗂️ Service Summary

| Service | Port | Responsibility | Status |
|---|---|---|---|
| `api-gateway` | 8000 | Entry point, request orchestration | ✅ Live |
| `moderation-service` | 8001 | Child-safety validation | 🟡 Mock (always approved) |
| `llm-service` | 8002 | Story text generation | 🟡 Mock (fixed story) |
| `story-service` | 8003 | Story persistence & retrieval (MongoDB) | ✅ Live |
| `mongo` | 27017 | Story storage (MongoDB 7) | ✅ Live |
| `redis` | 6379 | Caching (wired, unused in MVP) | 🔵 Wired |

---

## 🚀 Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
- A terminal (bash, zsh, Git Bash on Windows, etc.).

### 1 — Copy the environment templates

Each service needs a `.env` file. Start from the provided templates:

```bash
cp services/api-gateway/.env.template        services/api-gateway/.env
cp services/moderation-service/.env.template services/moderation-service/.env
cp services/llm-service/.env.template        services/llm-service/.env
cp services/story-service/.env.template      services/story-service/.env
```

For the MVP the defaults in the templates work out of the box — no secret keys needed yet.

### 2 — Build and start everything

```bash
docker compose up --build
```

The first run downloads base images and installs dependencies. Subsequent starts are much faster. You should see all four services report `Application startup complete`.

### 3 — Create your first story

```bash
curl -X POST http://localhost:8000/stories \
  -H "Content-Type: application/json" \
  -d '{"child_theme": "magic forest", "character_name": "Luna"}'
```

A successful response looks like:

```json
{
  "id": "a1b2c3d4-...",
  "child_theme": "magic forest",
  "character_name": "Luna",
  "prompt": null,
  "content": "Once upon a time, Luna ventured into the magic forest...",
  "created_at": "2026-06-02T18:00:00Z"
}
```

Copy the `id` — you can retrieve the story later:

```bash
curl http://localhost:8003/stories/<id>
```

### 4 — Health checks

Confirm every service is up:

```bash
curl http://localhost:8000/health   # api-gateway
curl http://localhost:8001/health   # moderation-service
curl http://localhost:8002/health   # llm-service
curl http://localhost:8003/health   # story-service
```

Each returns `{"status": "ok", "service": "<name>"}`.

---

## 📁 Project Structure

```
kids-story-be/
│
├── services/                         # One folder per microservice
│   ├── api-gateway/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.template             # Copy to .env before running
│   │   └── app/
│   │       ├── main.py               # POST /stories + GET /health
│   │       └── clients.py            # httpx calls to downstream services
│   │
│   ├── moderation-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.template
│   │   └── app/
│   │       └── main.py               # POST /moderate + GET /health
│   │
│   ├── llm-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── .env.template
│   │   └── app/
│   │       └── main.py               # POST /generate + GET /health
│   │
│   └── story-service/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── .env.template
│       └── app/
│           ├── main.py               # POST /stories, GET /stories/{id}, GET /health
│           └── database.py           # MongoDB connection + index setup
│
├── shared/                           # Code shared by all services
│   ├── contracts/
│   │   └── story.py                  # Pydantic models: StoryRequest, Story, ModerationResult
│   └── errors/
│       └── exceptions.py             # Consistent HTTP error helpers
│
├── docker-compose.yml
│   └── docker-compose.yml            # Wires all 6 containers together
│
├── .gitignore                        # Ignores .env, __pycache__, *.pyc
└── README.md                         # You are here
```

---

## 📚 How a Story Is Born

Here is what happens, step by step, when you call `POST /stories` — explained like you're watching the book-making shop from the inside:

1. **You walk up to the front desk.**
   Your request (`child_theme`, `character_name`, optional `prompt`) arrives at the **api-gateway** on port 8000. The receptionist writes it down and gets to work.

2. **The receptionist sends it to the Safety Inspector.**
   The gateway calls `POST /moderate` on the **moderation-service** (port 8001), forwarding your request. The inspector looks it over.
   - ✅ *Approved?* Great — carry on.
   - ❌ *Rejected?* The receptionist sends you back a `400 Bad Request` with an explanation. No story is written, nothing is saved.

3. **The Storyteller gets the brief.**
   With the green light, the gateway calls `POST /generate` on the **llm-service** (port 8002). The storyteller reads the theme and character name and produces the story text. Right now this is a friendly stand-in writer (mocked); a real AI will take this desk later.

4. **The Librarian files the finished book.**
   The gateway takes the completed story and calls `POST /stories` on the **story-service** (port 8003). The librarian saves it to MongoDB with a unique ID and a timestamp.

5. **The book arrives in your hands.**
   The api-gateway returns the full `Story` object — ID, content, theme, and all — with HTTP `201 Created`. You can retrieve it any time using `GET /stories/{id}` directly on the story-service.

---

## 🧪 Running Tests

Each service has its own `tests/` directory with [pytest](https://docs.pytest.org/).

### Option A — Run per service (recommended during development)

```bash
# api-gateway
cd services/api-gateway
pip install -r requirements.txt
pytest

# story-service
cd services/story-service
pip install -r requirements.txt
pytest

# moderation-service
cd services/moderation-service
pip install -r requirements.txt
pytest

# llm-service
cd services/llm-service
pip install -r requirements.txt
pytest
```

### Option B — Run from the repo root with PYTHONPATH

This ensures `shared/` is importable without installing it as a package:

```bash
PYTHONPATH=. pytest services/api-gateway/tests/
PYTHONPATH=. pytest services/story-service/tests/
PYTHONPATH=. pytest services/moderation-service/tests/
PYTHONPATH=. pytest services/llm-service/tests/
```

Or run everything at once:

```bash
PYTHONPATH=. pytest services/
```

---

## 🚧 MVP Constraints (Intentionally Out of Scope)

This is a **bootstrap MVP**. The following are deliberate non-goals for this iteration:

| Feature | Why it's out of scope |
|---|---|
| Authentication / user accounts | No users model yet; auth adds significant surface area |
| Image generation | Requires a separate image-model pipeline |
| Audio narration | Deferred; depends on a real LLM being wired in first |
| Event buses (Kafka, RabbitMQ) | Sync HTTP is enough for the current load |
| Real LLM integration | `llm-service` returns a mock story; real provider next |
| SSE streaming | Planned for the next iteration in `llm-service` |

Redis is **wired into Docker Compose** and the `REDIS_URL` env var is set — but no caching logic is implemented yet. It's ready to plug in.

---

## 🔭 What Comes Next

Here is the short list of what's planned right after this MVP:

1. **Real LLM** — Replace the mock `llm-service` with an actual provider call (e.g. OpenAI, Gemini, or a local model).
2. **SSE Streaming** — Stream story tokens from `llm-service` back to the client as they are generated, so readers see words appearing live.
3. **Real Moderation** — Swap the mock approval for a proper content-safety API (e.g. OpenAI Moderation, Perspective API).
4. **Redis Caching** — Cache recently generated stories or repeated prompts to reduce LLM costs.
5. **Story listing** — Add `GET /stories` with pagination to browse the saved library.
6. **User accounts & auth** — Associate stories with a child's profile once the user model is designed.

---

## 🤝 Contributing

This project follows the conventions defined in `.cursor/rules/`. Key highlights:

- **FastAPI** with async handlers and Pydantic validation throughout.
- **Shared contracts** in `shared/contracts/story.py` — never duplicate the models.
- **No `.env` files committed** — always use `.env.template` as the source of truth.
- **Tests first** — new endpoints need a `tests/test_*.py` covering the happy path and at least one error case.

If you are adding a new service, model it after `story-service`: `Dockerfile` with `build.context: .`, a `.env.template`, and tests runnable with `PYTHONPATH=.`.
