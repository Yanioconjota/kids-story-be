# Kids Story Backend

Backend-only MVP for a children's story generation platform.

## Architecture

```
Client → POST /stories (api-gateway :8000)
  → POST /moderate  (moderation-service :8001)   # mock: always approved
  → POST /generate  (llm-service :8002)           # mock: generates story text
  → POST /stories   (story-service :8003) → MongoDB
  → 201 Story (back to client)
```

### Services

| Service | Port | Responsibility |
|---------|------|----------------|
| `api-gateway` | 8000 | Entry point, request orchestration |
| `moderation-service` | 8001 | Story Request validation, child safety |
| `llm-service` | 8002 | Story generation (mock → real LLM later) |
| `story-service` | 8003 | Story persistence & retrieval (MongoDB) |
| `mongo` | 27017 | Story storage |
| `redis` | 6379 | Caching (wired, not yet used) |

## Running with Docker Compose

**1. Copy env templates and fill in values:**

```bash
cp services/api-gateway/.env.template     services/api-gateway/.env
cp services/moderation-service/.env.template services/moderation-service/.env
cp services/llm-service/.env.template     services/llm-service/.env
cp services/story-service/.env.template   services/story-service/.env
```

**2. Build and start all services:**

```bash
docker compose -f infra/docker-compose.yml up --build
```

**3. Create a story:**

```bash
curl -X POST http://localhost:8000/stories \
  -H "Content-Type: application/json" \
  -d '{"child_theme": "magic forest", "character_name": "Luna"}'
```

**4. Health checks:**

```bash
curl http://localhost:8000/health   # api-gateway
curl http://localhost:8001/health   # moderation-service
curl http://localhost:8002/health   # llm-service
curl http://localhost:8003/health   # story-service
```

## Running Tests Locally

Install dependencies for each service, then run pytest from the service directory:

```bash
# Example: api-gateway
cd services/api-gateway
pip install -r requirements.txt
pytest

# Example: story-service
cd services/story-service
pip install -r requirements.txt
pytest
```

Or from the repo root with PYTHONPATH set:

```bash
PYTHONPATH=. pytest services/api-gateway/tests/
PYTHONPATH=. pytest services/story-service/tests/
```

## Project Structure

```
kids-story-be/
├── services/
│   ├── api-gateway/          # Orchestration entry point
│   ├── moderation-service/   # Content moderation
│   ├── llm-service/          # Story generation
│   └── story-service/        # Persistence & retrieval
├── shared/
│   ├── contracts/story.py    # Pydantic: StoryRequest, Story, ModerationResult
│   └── errors/exceptions.py  # Shared error helpers
├── infra/
│   └── docker-compose.yml
└── .cursor/                  # Project rules, specs, skills
```

## MVP Constraints

The following are **intentionally out of scope** for this MVP:

- Authentication / user accounts
- Image generation or narration
- Event buses (Kafka, RabbitMQ)
- Real LLM integration (llm-service is mocked)
- SSE streaming (planned for next iteration in llm-service)
