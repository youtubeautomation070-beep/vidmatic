from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User, Channel
import os
import uuid
from datetime import datetime, timezone
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import httpx

youtube_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

class OAuthStartRequest(BaseModel):
    redirect_uri: str

class OAuthCallbackRequest(BaseModel):
    code: str
    redirect_uri: str

class UploadVideoRequest(BaseModel):
    channel_id: str
    video_file_path: str
    title: str
    description: str
    tags: List[str]
    thumbnail_path: Optional[str] = None
    scheduled_at: Optional[str] = None

@youtube_router.post("/oauth/start")
async def start_oauth(req: OAuthStartRequest, user: User = Depends(get_current_user)):
    """Start YouTube OAuth flow"""
    client_config = {
        "web": {
            "client_id": os.environ.get('YOUTUBE_CLIENT_ID'),
            "client_secret": os.environ.get('YOUTUBE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [req.redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=[
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube.force-ssl'
        ],
        redirect_uri=req.redirect_uri
    )
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return {"authorization_url": authorization_url, "state": state}

@youtube_router.post("/oauth/callback")
async def oauth_callback(req: OAuthCallbackRequest, user: User = Depends(get_current_user)):
    """Handle YouTube OAuth callback"""
    client_config = {
        "web": {
            "client_id": os.environ.get('YOUTUBE_CLIENT_ID'),
            "client_secret": os.environ.get('YOUTUBE_CLIENT_SECRET'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [req.redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=[
            'https://www.googleapis.com/auth/youtube.upload',
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube.force-ssl'
        ],
        redirect_uri=req.redirect_uri
    )
    
    flow.fetch_token(code=req.code)
    credentials = flow.credentials
    
    # Get channel info
    youtube = build('youtube', 'v3', credentials=credentials)
    request = youtube.channels().list(part='snippet,statistics', mine=True)
    response = request.execute()
    
    if not response.get('items'):
        raise HTTPException(status_code=404, detail="No channel found")
    
    channel_data = response['items'][0]
    youtube_channel_id = channel_data['id']
    
    # Check if channel already connected
    existing = await db.channels.find_one({
        "user_id": user.user_id,
        "youtube_channel_id": youtube_channel_id
    }, {"_id": 0})
    
    if existing:
        # Update refresh token
        await db.channels.update_one(
            {"channel_id": existing["channel_id"]},
            {"$set": {
                "refresh_token": credentials.refresh_token or existing["refresh_token"],
                "is_active": True,
                "connected_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        channel_id = existing["channel_id"]
    else:
        # Create new channel
        channel_id = f"ch_{uuid.uuid4().hex[:12]}"
        channel_doc = {
            "channel_id": channel_id,
            "user_id": user.user_id,
            "youtube_channel_id": youtube_channel_id,
            "channel_name": channel_data['snippet']['title'],
            "channel_avatar": channel_data['snippet']['thumbnails']['default']['url'],
            "subscriber_count": int(channel_data['statistics'].get('subscriberCount', 0)),
            "refresh_token": credentials.refresh_token,
            "connected_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True
        }
        await db.channels.insert_one(channel_doc)
    
    channel_doc = await db.channels.find_one({"channel_id": channel_id}, {"_id": 0})
    return channel_doc

@youtube_router.get("/channels")
async def get_channels(user: User = Depends(get_current_user)):
    """Get user's connected YouTube channels"""
    channels = await db.channels.find({"user_id": user.user_id, "is_active": True}, {"_id": 0}).to_list(100)
    return channels

@youtube_router.delete("/channels/{channel_id}")
async def disconnect_channel(channel_id: str, user: User = Depends(get_current_user)):
    """Disconnect a YouTube channel"""
    result = await db.channels.update_one(
        {"channel_id": channel_id, "user_id": user.user_id},
        {"$set": {"is_active": False}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    return {"message": "Channel disconnected"}

@youtube_router.post("/upload")
async def upload_video(req: UploadVideoRequest, user: User = Depends(get_current_user)):
    """Upload video to YouTube (placeholder - actual upload happens in background)"""
    # This is a simplified version - actual implementation would be in background task
    return {
        "message": "Video upload initiated",
        "status": "processing"
    }