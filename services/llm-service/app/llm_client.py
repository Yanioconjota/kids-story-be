"""
Multi-provider LLM client — sync and streaming.

Controlled by env vars:
  LLM_PROVIDER  = mock | openai | anthropic | ollama  (default: mock)
  LLM_MODEL     = model name for the chosen provider
  LLM_API_KEY   = API key (openai / anthropic)
  LLM_BASE_URL  = override base URL (e.g. http://ollama:11434/v1 for Ollama)
"""

import os
from collections.abc import AsyncGenerator

from fastapi import HTTPException

from shared.contracts.story import StoryRequest

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")

_SYSTEM_PROMPT = (
    "You are a warm, creative children's story writer. "
    "Write age-appropriate stories that:\n"
    "- Use simple, gentle vocabulary suitable for young children.\n"
    "- Include a small life lesson woven naturally into the plot.\n"
    "- Feature at least one friendly challenge or gentle enemy the hero overcomes.\n"
    "- End happily and leave the reader feeling good.\n"
    "Write only the story text — no title, no metadata, no commentary."
)


def _user_prompt(request: StoryRequest) -> str:
    parts = [
        f"Write a children's story about a brave hero named {request.character_name}",
        f"set in a world of {request.child_theme}.",
    ]
    if request.prompt:
        parts.append(f"Story direction: {request.prompt}")
    parts.append(f"Keep it around {request.max_words} words.")
    return " ".join(parts)


def _openai_client(provider: str):
    try:
        from openai import AsyncOpenAI  # noqa: PLC0415
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="openai package not installed") from exc

    if not LLM_API_KEY and provider == "openai":
        raise HTTPException(status_code=500, detail="LLM_API_KEY is not set for openai provider")

    base_url = LLM_BASE_URL if LLM_BASE_URL else (
        "http://ollama:11434/v1" if provider == "ollama" else None
    )
    api_key = LLM_API_KEY or "ollama"
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


def _default_model(provider: str) -> str:
    if LLM_MODEL:
        return LLM_MODEL
    return {
        "openai": "gpt-4o-mini",
        "ollama": "llama3.2",
        "anthropic": "claude-3-5-haiku-20241022",
    }.get(provider, "gpt-4o-mini")


# ---------------------------------------------------------------------------
# Mock provider
# ---------------------------------------------------------------------------

def _mock_generate(request: StoryRequest) -> str:
    quest = (
        f"Their quest began when: {request.prompt}"
        if request.prompt
        else "Their greatest adventure was just beginning."
    )
    return (
        f"Once upon a time, in a land of {request.child_theme}, "
        f"there lived a brave hero named {request.character_name}. "
        f"{quest} "
        f"Along the way, {request.character_name} faced a tricky shadow creature, "
        "but discovered that kindness was more powerful than fear. "
        "With a warm heart and a clever mind, the challenge was overcome, "
        "and the whole land celebrated together. "
        "And they all lived happily ever after."
    )


async def _mock_stream(request: StoryRequest) -> AsyncGenerator[str, None]:
    import asyncio  # noqa: PLC0415
    content = _mock_generate(request)
    for word in content.split():
        yield word + " "
        await asyncio.sleep(0.03)


# ---------------------------------------------------------------------------
# OpenAI / Ollama provider
# ---------------------------------------------------------------------------

async def _openai_generate(request: StoryRequest, provider: str = "openai") -> str:
    client = _openai_client(provider)
    try:
        response = await client.chat.completions.create(
            model=_default_model(provider),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(request)},
            ],
            max_tokens=2000,
            temperature=0.85,
        )
        return response.choices[0].message.content or ""
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI error: {exc}") from exc


async def _openai_stream(request: StoryRequest, provider: str = "openai") -> AsyncGenerator[str, None]:
    client = _openai_client(provider)
    try:
        stream = await client.chat.completions.create(
            model=_default_model(provider),
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(request)},
            ],
            max_tokens=2000,
            temperature=0.85,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI streaming error: {exc}") from exc


# ---------------------------------------------------------------------------
# Anthropic provider
# ---------------------------------------------------------------------------

async def _anthropic_generate(request: StoryRequest) -> str:
    try:
        from anthropic import AsyncAnthropic  # noqa: PLC0415
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="anthropic package not installed") from exc

    if not LLM_API_KEY:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is not set for anthropic provider")

    try:
        client = AsyncAnthropic(api_key=LLM_API_KEY)
        response = await client.messages.create(
            model=_default_model("anthropic"),
            max_tokens=2000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _user_prompt(request)}],
        )
        return response.content[0].text
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic error: {exc}") from exc


async def _anthropic_stream(request: StoryRequest) -> AsyncGenerator[str, None]:
    try:
        from anthropic import AsyncAnthropic  # noqa: PLC0415
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="anthropic package not installed") from exc

    if not LLM_API_KEY:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is not set for anthropic provider")

    try:
        client = AsyncAnthropic(api_key=LLM_API_KEY)
        async with client.messages.stream(
            model=_default_model("anthropic"),
            max_tokens=2000,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _user_prompt(request)}],
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic streaming error: {exc}") from exc


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

async def generate_content(request: StoryRequest) -> str:
    if LLM_PROVIDER == "mock":
        return _mock_generate(request)
    if LLM_PROVIDER in ("openai", "ollama"):
        return await _openai_generate(request, provider=LLM_PROVIDER)
    if LLM_PROVIDER == "anthropic":
        return await _anthropic_generate(request)
    raise HTTPException(
        status_code=500,
        detail=f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use: mock | openai | anthropic | ollama",
    )


async def stream_content(request: StoryRequest) -> AsyncGenerator[str, None]:
    if LLM_PROVIDER == "mock":
        async for chunk in _mock_stream(request):
            yield chunk
        return
    if LLM_PROVIDER in ("openai", "ollama"):
        async for chunk in _openai_stream(request, provider=LLM_PROVIDER):
            yield chunk
        return
    if LLM_PROVIDER == "anthropic":
        async for chunk in _anthropic_stream(request):
            yield chunk
        return
    raise HTTPException(
        status_code=500,
        detail=f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use: mock | openai | anthropic | ollama",
    )
