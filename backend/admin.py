from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User, UserRole
import os
from datetime import datetime, timezone

admin_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def require_admin(user: User = Depends(get_current_user)):
    """Require admin role"""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

class PlatformStats(BaseModel):
    total_users: int
    total_videos: int
    total_channels: int
    active_subscriptions: int
    total_revenue: float

class UpdateUserRequest(BaseModel):
    video_credits: Optional[int] = None
    free_video_credits: Optional[int] = None
    subscription_plan: Optional[str] = None
    role: Optional[str] = None

@admin_router.get("/stats")
async def get_platform_stats(admin: User = Depends(require_admin)):
    """Get platform-wide statistics"""
    total_users = await db.users.count_documents({})
    total_videos = await db.videos.count_documents({})
    total_channels = await db.channels.count_documents({"is_active": True})
    active_subscriptions = await db.users.count_documents({
        "subscription_plan": {"$in": ["pro_monthly", "pro_yearly"]}
    })
    
    # Calculate revenue (sum of paid transactions)
    pipeline = [
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ]
    revenue_result = await db.payment_transactions.aggregate(pipeline).to_list(1)
    total_revenue = revenue_result[0]["total"] if revenue_result else 0.0
    
    return PlatformStats(
        total_users=total_users,
        total_videos=total_videos,
        total_channels=total_channels,
        active_subscriptions=active_subscriptions,
        total_revenue=total_revenue
    )

@admin_router.get("/users")
async def list_all_users(skip: int = 0, limit: int = 50, admin: User = Depends(require_admin)):
    """List all users (admin only)"""
    users = await db.users.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents({})
    
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@admin_router.get("/users/{user_id}")
async def get_user_details(user_id: str, admin: User = Depends(require_admin)):
    """Get detailed user information"""
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's videos
    videos = await db.videos.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get user's channels
    channels = await db.channels.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get user's transactions
    transactions = await db.payment_transactions.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Get referrals
    referrals = await db.referrals.find({"referrer_id": user_id}, {"_id": 0}).to_list(100)
    
    return {
        "user": user,
        "videos": videos,
        "channels": channels,
        "transactions": transactions,
        "referrals": referrals
    }

@admin_router.patch("/users/{user_id}")
async def update_user(user_id: str, req: UpdateUserRequest, admin: User = Depends(require_admin)):
    """Update user (admin only)"""
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    if not update_data:
        return {"message": "No updates provided"}
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated successfully"}

@admin_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: User = Depends(require_admin)):
    """Delete user (admin only)"""
    # Delete user and all associated data
    await db.users.delete_one({"user_id": user_id})
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.channels.delete_many({"user_id": user_id})
    await db.videos.delete_many({"user_id": user_id})
    await db.payment_transactions.delete_many({"user_id": user_id})
    await db.referrals.delete_many({"referrer_id": user_id})
    await db.referrals.delete_many({"referred_user_id": user_id})
    
    return {"message": "User and all associated data deleted"}

@admin_router.get("/videos")
async def list_all_videos(skip: int = 0, limit: int = 50, admin: User = Depends(require_admin)):
    """List all videos (admin only)"""
    videos = await db.videos.find({}, {"_id": 0}).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    total = await db.videos.count_documents({})
    
    return {
        "videos": videos,
        "total": total,
        "skip": skip,
        "limit": limit
    }