from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User
import os
import uuid
from datetime import datetime, timezone

referrals_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

class ReferralStats(BaseModel):
    referral_code: str
    referral_link: str
    total_referrals: int
    successful_referrals: int
    pending_referrals: int
    free_credits_earned: int

@referrals_router.get("/stats")
async def get_referral_stats(user: User = Depends(get_current_user)):
    """Get user's referral statistics"""
    # Count referrals
    total_referrals = await db.referrals.count_documents({"referrer_id": user.user_id})
    successful_referrals = await db.referrals.count_documents({
        "referrer_id": user.user_id,
        "status": "completed",
        "reward_granted": True
    })
    pending_referrals = await db.referrals.count_documents({
        "referrer_id": user.user_id,
        "status": "pending"
    })
    
    # Get referral link
    referral_link = f"https://vidmatic.com/ref/{user.referral_code}"
    
    return ReferralStats(
        referral_code=user.referral_code,
        referral_link=referral_link,
        total_referrals=total_referrals,
        successful_referrals=successful_referrals,
        pending_referrals=pending_referrals,
        free_credits_earned=user.free_video_credits
    )

@referrals_router.get("/list")
async def list_referrals(user: User = Depends(get_current_user)):
    """List all user's referrals"""
    referrals = await db.referrals.find(
        {"referrer_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with referred user details
    enriched_referrals = []
    for ref in referrals:
        if ref.get("referred_user_id"):
            referred_user = await db.users.find_one(
                {"user_id": ref["referred_user_id"]},
                {"_id": 0, "email": 1, "name": 1, "created_at": 1}
            )
            ref["referred_user_info"] = referred_user
        enriched_referrals.append(ref)
    
    return enriched_referrals

@referrals_router.post("/apply/{referral_code}")
async def apply_referral_code(referral_code: str, user: User = Depends(get_current_user)):
    """Apply a referral code to a new user"""
    # Check if user already has a referrer
    if user.referred_by:
        raise HTTPException(status_code=400, detail="You have already used a referral code")
    
    # Find referrer by referral code
    referrer = await db.users.find_one({"referral_code": referral_code}, {"_id": 0})
    if not referrer:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    
    if referrer["user_id"] == user.user_id:
        raise HTTPException(status_code=400, detail="You cannot refer yourself")
    
    # Update user with referrer
    await db.users.update_one(
        {"user_id": user.user_id},
        {"$set": {"referred_by": referrer["user_id"]}}
    )
    
    # Create referral record
    referral_id = f"ref_{uuid.uuid4().hex[:12]}"
    referral_doc = {
        "referral_id": referral_id,
        "referrer_id": referrer["user_id"],
        "referred_user_id": user.user_id,
        "referred_email": user.email,
        "status": "pending",
        "reward_granted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.referrals.insert_one(referral_doc)
    
    return {
        "message": "Referral code applied successfully",
        "referrer_name": referrer["name"]
    }