#!/usr/bin/env python3
"""Script to create test users"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid
import secrets
import os
from dotenv import load_dotenv

load_dotenv()

async def create_test_users():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Regular user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    referral_code = secrets.token_urlsafe(8)
    
    user_doc = {
        "user_id": user_id,
        "email": "masteruser@vidmatic.live",
        "name": "Master User",
        "picture": None,
        "role": "user",
        "subscription_plan": "free_trial",
        "video_credits": 2,
        "free_video_credits": 0,
        "referral_code": referral_code,
        "referred_by": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        await db.users.insert_one(user_doc)
        print(f"✓ Created regular user: masteruser@vidmatic.live")
    except:
        print("Regular user already exists")
    
    # Admin user
    admin_id = f"user_{uuid.uuid4().hex[:12]}"
    admin_referral_code = secrets.token_urlsafe(8)
    
    admin_doc = {
        "user_id": admin_id,
        "email": "admin@vidmatic.live",
        "name": "Admin User",
        "picture": None,
        "role": "admin",
        "subscription_plan": "pro_yearly",
        "video_credits": 100,
        "free_video_credits": 0,
        "referral_code": admin_referral_code,
        "referred_by": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    try:
        await db.users.insert_one(admin_doc)
        print(f"✓ Created admin user: admin@vidmatic.live")
    except:
        print("Admin user already exists")
    
    client.close()
    print("\\nTest users created successfully!")
    print("Login via Emergent Google OAuth with these emails")

if __name__ == "__main__":
    asyncio.run(create_test_users())
