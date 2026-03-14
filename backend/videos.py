from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User, Video, VideoStatus, SubscriptionPlan
import os
import uuid
from datetime import datetime, timezone

videos_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

class CreateVideoRequest(BaseModel):
    prompt: str
    video_length: str = "medium"
    voice_style: str = "professional"
    visual_style: str = "cinematic"
    language: str = "en"

class UpdateVideoRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    selected_thumbnail_url: Optional[str] = None

class ScheduleVideoRequest(BaseModel):
    channel_id: str
    scheduled_at: Optional[str] = None
    publish_now: bool = False

@videos_router.post("/create")
async def create_video(req: CreateVideoRequest, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    """Create a new video generation request"""
    # Check credits
    total_credits = user.video_credits + user.free_video_credits
    if total_credits <= 0:
        raise HTTPException(status_code=403, detail="Insufficient video credits. Please upgrade your plan.")
    
    # Create video record
    video_id = f"vid_{uuid.uuid4().hex[:12]}"
    video_doc = {
        "video_id": video_id,
        "user_id": user.user_id,
        "channel_id": None,
        "prompt": req.prompt,
        "video_length": req.video_length,
        "voice_style": req.voice_style,
        "visual_style": req.visual_style,
        "language": req.language,
        "status": VideoStatus.PENDING.value,
        "script": None,
        "voiceover_url": None,
        "video_url": None,
        "thumbnail_urls": [],
        "selected_thumbnail_url": None,
        "title": None,
        "description": None,
        "tags": [],
        "seo_score": 0,
        "youtube_video_id": None,
        "scheduled_at": None,
        "published_at": None,
        "error_message": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.videos.insert_one(video_doc)
    
    # Deduct credits (use free credits first)
    if user.free_video_credits > 0:
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$inc": {"free_video_credits": -1}}
        )
    else:
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$inc": {"video_credits": -1}}
        )
    
    # Start video generation in background
    from ai import generate_video_pipeline
    background_tasks.add_task(generate_video_pipeline, video_id)
    
    return {"video_id": video_id, "status": VideoStatus.PENDING.value, "message": "Video generation started"}

@videos_router.get("/")
async def list_videos(user: User = Depends(get_current_user)):
    """List all videos for the user"""
    videos = await db.videos.find({"user_id": user.user_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return videos

@videos_router.get("/{video_id}")
async def get_video(video_id: str, user: User = Depends(get_current_user)):
    """Get video details"""
    video = await db.videos.find_one({"video_id": video_id, "user_id": user.user_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video

@videos_router.patch("/{video_id}")
async def update_video(video_id: str, req: UpdateVideoRequest, user: User = Depends(get_current_user)):
    """Update video metadata"""
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if not update_data:
        return {"message": "No updates provided"}
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.videos.update_one(
        {"video_id": video_id, "user_id": user.user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return {"message": "Video updated"}

@videos_router.delete("/{video_id}")
async def delete_video(video_id: str, user: User = Depends(get_current_user)):
    """Delete a video"""
    result = await db.videos.delete_one({"video_id": video_id, "user_id": user.user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"message": "Video deleted"}

@videos_router.post("/{video_id}/publish")
async def publish_video(video_id: str, req: ScheduleVideoRequest, user: User = Depends(get_current_user)):
    """Publish or schedule video to YouTube"""
    video = await db.videos.find_one({"video_id": video_id, "user_id": user.user_id}, {"_id": 0})
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if video["status"] != VideoStatus.READY.value:
        raise HTTPException(status_code=400, detail="Video is not ready for publishing")
    
    # Update video status
    update_data = {
        "channel_id": req.channel_id,
        "status": VideoStatus.SCHEDULED.value if not req.publish_now else VideoStatus.PUBLISHED.value,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    if req.scheduled_at:
        update_data["scheduled_at"] = req.scheduled_at
    
    if req.publish_now:
        update_data["published_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.videos.update_one(
        {"video_id": video_id},
        {"$set": update_data}
    )
    
    return {"message": "Video publishing initiated", "status": update_data["status"]}