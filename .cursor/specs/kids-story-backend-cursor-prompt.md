# Cursor Prompt — Kids Story Backend MVP

Create the initial backend-only MVP for `kids-story-backend` using a microservices structure.

## Goal
Set up a Dockerized Python/FastAPI backend with these services:

- `api-gateway`
- `story-service`
- `moderation-service`
- `llm-service`

Also include:

- MongoDB
- Redis
- Docker Compose
- shared contracts/utilities folder

## Expected structure

```txt
kids-story-backend/
  services/
    api-gateway/
    story-service/
    moderation-service/
    llm-service/
  shared/
    contracts/
    errors/
    logging/
    config/
  infra/
    docker-compose.yml
  README.md
```

## Requirements

- Each service must be a minimal FastAPI app.
- Each service must expose a `/health` endpoint.
- Dockerize each service with its own `Dockerfile`.
- `docker-compose.yml` must run all services, MongoDB, and Redis.
- Use clear environment variables for service URLs, MongoDB URL, and Redis URL.
- Keep the code simple and MVP-focused.
- Avoid authentication, frontend, image generation, narration, queues, and advanced infrastructure for now.

## Initial flow

Implement a basic story creation flow:

```txt
POST /stories -> api-gateway -> moderation-service -> llm-service -> story-service -> MongoDB
```

For now:

- `moderation-service` can return a mock approval response.
- `llm-service` can return a mock generated story.
- `story-service` must save the story in MongoDB.
- `api-gateway` must orchestrate the full flow.

## Output

Generate the project files and keep the implementation clean, readable, and easy to extend.
