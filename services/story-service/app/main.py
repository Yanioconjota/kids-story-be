from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo import DESCENDING

from shared.contracts.story import Story, StoryList
from app.database import ensure_indexes, get_stories_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    yield


app = FastAPI(title="story-service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "story-service"}


@app.post("/stories", response_model=Story, status_code=201)
async def create_story(
    story: Story,
    collection: AsyncIOMotorCollection = Depends(get_stories_collection),
) -> Story:
    doc = story.model_dump(mode="json")
    await collection.insert_one(doc)
    return story


@app.get("/stories", response_model=StoryList)
async def list_stories(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    collection: AsyncIOMotorCollection = Depends(get_stories_collection),
) -> StoryList:
    cursor = collection.find({}, {"_id": 0}).sort("created_at", DESCENDING).skip(offset).limit(limit)
    items = await cursor.to_list(length=limit)
    total = await collection.count_documents({})
    return StoryList(
        items=[Story(**doc) for doc in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get("/stories/{story_id}", response_model=Story)
async def get_story(
    story_id: str,
    collection: AsyncIOMotorCollection = Depends(get_stories_collection),
) -> Story:
    doc = await collection.find_one({"id": story_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")
    return Story(**doc)
