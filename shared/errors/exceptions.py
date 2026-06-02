from typing import Optional

from fastapi import HTTPException


def downstream_error(service: str, detail: str) -> HTTPException:
    return HTTPException(
        status_code=502,
        detail=f"{service} error: {detail}",
    )


def not_found(resource: str, resource_id: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail=f"{resource} '{resource_id}' not found",
    )


def moderation_rejected(reason: Optional[str]) -> HTTPException:
    return HTTPException(
        status_code=400,
        detail=f"Story request rejected by moderation: {reason or 'content not allowed'}",
    )
