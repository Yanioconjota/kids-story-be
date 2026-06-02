from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class StoryRequest(BaseModel):
    child_theme: str = Field(..., max_length=120)
    character_name: str = Field(..., max_length=80)
    prompt: Optional[str] = Field(default=None, max_length=500)
    max_words: int = Field(default=650, ge=50, le=1500)

    @field_validator("child_theme", "character_name", "prompt", mode="before")
    @classmethod
    def normalize_whitespace(cls, v: object) -> object:
        """Collapse extra whitespace and strip edges on all text fields."""
        if isinstance(v, str):
            return " ".join(v.split())
        return v


class ModerationResult(BaseModel):
    approved: bool
    reason: Optional[str] = None
    categories: list[str] = Field(default_factory=list)


class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    child_theme: str
    character_name: str
    prompt: Optional[str] = None
    content: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class StoryList(BaseModel):
    items: list[Story]
    total: int
    limit: int
    offset: int
