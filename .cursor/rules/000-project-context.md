# Update Project Rules for Kids Story Backend

Review all existing rules under:

* `.cursor/rules`
* `.cursor/commands`
* `.cursor/skills`
* `.cursor/specs`

and adapt them to the current project context.

## Current Project

This repository is not a generic LLM chat backend.

It is a backend-only MVP for a children's story generation platform.

Architecture:

* api-gateway
* story-service
* moderation-service
* llm-service
* MongoDB
* Redis
* Docker Compose

## Required Changes

Create a new rule file:

```txt
.cursor/rules/000-project-context.md
```

This file must become the highest-priority project rule.

The rule should define:

### Domain Language

Use these domain terms consistently:

* Story
* Story Request
* Story Generation
* Child Theme
* Character Name
* Story Prompt
* Moderation Result

Avoid using:

* Conversation
* Message
* Chat
* Chat History
* Assistant Response
* User Message

unless explicitly required by infrastructure code.

### Service Responsibilities

api-gateway

* Entry point
* Request orchestration
* External API

story-service

* Story persistence
* Story retrieval
* Story metadata

moderation-service

* Prompt validation
* Child safety validation
* Content moderation

llm-service

* Story generation
* LLM provider integration
* Streaming generation

### Communication Rules

Default communication:

* REST between services
* SSE for story generation streaming
* MongoDB persistence
* Redis caching

Do not introduce WebSockets unless a clear bidirectional requirement exists.

### MVP Constraints

Do not add:

* Authentication
* User accounts
* Billing
* Image generation
* Narration
* Event buses
* Kafka
* RabbitMQ
* Kubernetes
* Complex infrastructure

unless explicitly requested.

### Development Philosophy

Prefer:

* Simple implementations
* Clear service boundaries
* FastAPI best practices
* Pydantic models
* Docker-first development
* Readability over abstraction

Avoid:

* Premature optimization
* Over-engineering
* Generic enterprise patterns without a real need

## Refactor Existing Rules

Review all existing rules and examples.

When examples use:

* conversations
* messages
* chat
* Ollama-specific concepts

replace them with equivalent story-generation examples whenever possible.

Keep the existing architectural and engineering principles that remain applicable.
