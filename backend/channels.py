from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User
import os

channels_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

@channels_router.get("/")
async def list_channels(user: User = Depends(get_current_user)):
    """List all connected channels for user"""
    channels = await db.channels.find({"user_id": user.user_id, "is_active": True}, {"_id": 0}).to_list(100)
    return channels

@channels_router.get("/{channel_id}/analytics")
async def get_channel_analytics(channel_id: str, user: User = Depends(get_current_user)):
    """Get channel analytics"""
    channel = await db.channels.find_one(
        {"channel_id": channel_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    # Get videos for this channel
    videos = await db.videos.find({"channel_id": channel_id}, {"_id": 0}).to_list(100)
    
    # Calculate stats
    total_videos = len(videos)
    published_videos = len([v for v in videos if v.get("status") == "published"])
    
    return {
        "channel": channel,
        "stats": {
            "total_videos": total_videos,
            "published_videos": published_videos,
            "total_views": 0,
            "subscriber_count": channel.get("subscriber_count", 0)
        }
    }