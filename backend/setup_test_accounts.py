#!/usr/bin/env python3
"""Script to setup test accounts with passwords"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid
import secrets
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

async def setup_accounts():
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    # Test accounts with passwords
    accounts = [
        {
            "email": "testuser@vidmatic.live",
            "password": "Test1234",
            "name": "Test User",
            "role": "user"
        },
        {
            "email": "admin@vidmatic.live",
            "password": "Admin1234",
            "name": "Admin User",
            "role": "admin"
        }
    ]
    
    for account in accounts:
        existing = await db.users.find_one({"email": account["email"]}, {"_id": 0})
        
        if existing:
            # Update existing account with password
            password_hash = hash_password(account["password"])
            await db.users.update_one(
                {"email": account["email"]},
                {"$set": {"password_hash": password_hash}}
            )
            print(f"✓ Updated {account['email']} with password")
        else:
            # Create new account
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            referral_code = secrets.token_urlsafe(8)
            password_hash = hash_password(account["password"])
            
            user_doc = {
                "user_id": user_id,
                "email": account["email"],
                "password_hash": password_hash,
                "name": account["name"],
                "picture": None,
                "role": account["role"],
                "subscription_plan": "pro_yearly" if account["role"] == "admin" else "free_trial",
                "video_credits": 100 if account["role"] == "admin" else 2,
                "free_video_credits": 0,
                "referral_code": referral_code,
                "referred_by": None,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            await db.users.insert_one(user_doc)
            print(f"✓ Created {account['email']}")
    
    client.close()
    print("\n✓ Test accounts ready!")
    print("  testuser@vidmatic.live / Test1234")
    print("  admin@vidmatic.live / Admin1234")

if __name__ == "__main__":
    asyncio.run(setup_accounts())
