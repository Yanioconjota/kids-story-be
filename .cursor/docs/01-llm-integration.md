# 01 — Real LLM Integration

**Status:** ✅ Done · **Owning service:** `llm-service`

## Summary

Multi-provider LLM support via env vars. Switch between mock, OpenAI, Anthropic, or Ollama
without code changes. Stories are generated using a child-safe system prompt that ensures
age-appropriate tone, gentle vocabulary, and positive endings.

## Owning service

`llm-service` only. The `api-gateway` calls `POST /generate` (sync) or `POST /generate/stream`
(SSE) and forwards the result to `story-service`; contracts unchanged.

## Provider Configuration

Edit `services/llm-service/.env`:

```bash
# Provider: mock | openai | anthropic | ollama
LLM_PROVIDER=mock

# Model name (provider-specific, leave blank for defaults)
LLM_MODEL=

# API key (required for openai and anthropic; not used for mock/ollama)
LLM_API_KEY=

# Base URL override (required for ollama, optional for others)
LLM_BASE_URL=
```

### Provider Examples

**Mock (default, no API key):**
```bash
LLM_PROVIDER=mock
```

**OpenAI:**
```bash
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=sk-...
```

**Anthropic:**
```bash
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-haiku-20241022
LLM_API_KEY=sk-ant-...
```

**Ollama (local, free):**
```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://host.docker.internal:11434/v1
```

## Ollama Setup (Local, Free)

Ollama lets you run open-source models locally with no API costs.

### 1. Install Ollama

Download from [ollama.ai](https://ollama.ai/) or:

```bash
# macOS / Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows: download installer from ollama.ai
```

### 2. Pull a model

```bash
ollama pull llama3.2
```

Other good options: `mistral`, `gemma2`, `phi3`

### 3. Start the server

```bash
ollama serve
```

Ollama runs on `http://localhost:11434` by default.

### 4. Configure llm-service

Edit `services/llm-service/.env`:

```bash
LLM_PROVIDER=ollama
LLM_MODEL=llama3.2
LLM_BASE_URL=http://host.docker.internal:11434/v1
```

> **Why `host.docker.internal`?** Docker containers can't reach `localhost` on your host machine.
> `host.docker.internal` is a special DNS name that resolves to your host.

### 5. Rebuild and test

```bash
docker compose up --build
```

```bash
curl -X POST http://localhost:8000/stories \
  -H "Content-Type: application/json" \
  -d '{"child_theme": "enchanted forest", "character_name": "Luna"}'
```

You should now see a real AI-generated story instead of the mock template.

### Running Ollama in Docker (alternative)

If you want Ollama inside Docker Compose, add to `docker-compose.yml`:

```yaml
ollama:
  image: ollama/ollama
  ports:
    - "11434:11434"
  volumes:
    - ollama_data:/root/.ollama
```

Then use `LLM_BASE_URL=http://ollama:11434/v1` (container name, not `host.docker.internal`).

## Implementation details

- `app/llm_client.py` — `generate_content()` (sync) and `stream_content()` (async generator)
- Child-safe system prompt instructs gentle vocabulary, life lessons, happy endings
- `max_tokens=2000` supports stories up to ~1500 words (~10 min read-aloud)
- Provider errors surface as `HTTPException(502, ...)` with clear messages

## Request options

`StoryRequest` includes:

```python
max_words: int = Field(default=650, ge=50, le=1500)  # ~5 min read-aloud default
```

Pass `"max_words": 1000` in the request body for longer stories.

## Testing

- `LLM_PROVIDER=mock` keeps tests deterministic (no API calls)
- Tests cover mock output, streaming, and 502 error handling
