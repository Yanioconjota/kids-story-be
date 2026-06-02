from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection

from shared.contracts.story import Story
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


@app.get("/stories/{story_id}", response_model=Story)
async def get_story(
    story_id: str,
    collection: AsyncIOMotorCollection = Depends(get_stories_collection),
) -> Story:
    doc = await collection.find_one({"id": story_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Story '{story_id}' not found")
    return Story(**doc)
