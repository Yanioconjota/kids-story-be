import os

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from pymongo import ASCENDING, DESCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "kids_story")

_client: AsyncIOMotorClient | None = None


def _get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URI)
    return _client


async def get_stories_collection() -> AsyncIOMotorCollection:
    return _get_client()[DB_NAME]["stories"]


async def ensure_indexes() -> None:
    try:
        collection = await get_stories_collection()
        await collection.create_index([("id", ASCENDING)], unique=True)
        await collection.create_index([("created_at", DESCENDING)])
    except Exception as exc:
        # Non-fatal at startup: indexes will be created on next healthy connection
        print(f"[story-service] Warning: could not create indexes: {exc}")
