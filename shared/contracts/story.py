from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class StoryRequest(BaseModel):
    child_theme: str = Field(..., max_length=120)
    character_name: str = Field(..., max_length=80)
    prompt: Optional[str] = Field(default=None, max_length=500)


class ModerationResult(BaseModel):
    approved: bool
    reason: Optional[str] = None


class Story(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    child_theme: str
    character_name: str
    prompt: Optional[str] = None
    content: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
