"""
Multi-provider moderation client.

MODERATION_PROVIDER = mock | rules | openai  (default: mock)
MODERATION_API_KEY  = API key for openai moderation
"""

import os
from typing import Optional

import httpx

from shared.contracts.story import ModerationResult, StoryRequest

MODERATION_PROVIDER = os.getenv("MODERATION_PROVIDER", "mock")
MODERATION_API_KEY = os.getenv("MODERATION_API_KEY", "")

# Conservative keyword blocklist for a children's platform
_BLOCKLIST: set[str] = {
    "violence", "blood", "gore", "kill", "murder", "death", "weapon", "gun", "knife",
    "drug", "alcohol", "sex", "nude", "naked", "explicit", "adult", "horror",
    "hate", "racist", "racist", "abuse", "bully",
}


def _rules_check(request: StoryRequest) -> Optional[str]:
    """Return a reason string if any field trips the blocklist, else None."""
    fields = [
        request.child_theme or "",
        request.character_name or "",
        request.prompt or "",
    ]
    combined = " ".join(fields).lower()
    for word in _BLOCKLIST:
        if word in combined:
            return f"Content contains inappropriate term: '{word}'"
    return None


async def _openai_moderation(text: str) -> ModerationResult:
    if not MODERATION_API_KEY:
        # Fail closed: can't verify safety without a key
        return ModerationResult(
            approved=False,
            reason="Moderation API key not configured",
            categories=["config_error"],
        )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/moderations",
                headers={"Authorization": f"Bearer {MODERATION_API_KEY}"},
                json={"input": text},
            )
            response.raise_for_status()
            result = response.json()
            flagged_categories = [
                cat for cat, hit in result["results"][0]["categories"].items() if hit
            ]
            flagged = result["results"][0]["flagged"]
            return ModerationResult(
                approved=not flagged,
                reason="Content flagged by safety check" if flagged else None,
                categories=flagged_categories,
            )
    except Exception as exc:
        # Fail closed for child safety
        return ModerationResult(
            approved=False,
            reason=f"Moderation provider unavailable: {exc}",
            categories=["provider_error"],
        )


async def moderate(request: StoryRequest) -> ModerationResult:
    if MODERATION_PROVIDER == "mock":
        return ModerationResult(approved=True)

    # Always run local rules first (free and fast)
    reason = _rules_check(request)
    if reason:
        return ModerationResult(approved=False, reason=reason, categories=["local_rules"])

    if MODERATION_PROVIDER == "rules":
        return ModerationResult(approved=True)

    if MODERATION_PROVIDER == "openai":
        combined_text = " ".join(filter(None, [
            request.child_theme,
            request.character_name,
            request.prompt,
        ]))
        return await _openai_moderation(combined_text)

    # Unknown provider → fail closed
    return ModerationResult(
        approved=False,
        reason=f"Unknown MODERATION_PROVIDER '{MODERATION_PROVIDER}'",
        categories=["config_error"],
    )
