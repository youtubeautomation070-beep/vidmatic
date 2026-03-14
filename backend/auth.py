from fastapi import APIRouter, HTTPException, Response, Request, Depends, Header, BackgroundTasks
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
from typing import Optional
import os
import httpx
import uuid
from dotenv import load_dotenv
from models import User, UserSession, UserRole, SubscriptionPlan
import secrets
import bcrypt
import re

load_dotenv()

auth_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

class SessionDataRequest(BaseModel):
    session_id: str

class EmailSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    reset_token: str
    new_password: str

class LoginResponse(BaseModel):
    user: User
    redirect_url: str

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    return True

async def create_session(user_id: str, response: Response) -> str:
    """Create new session for user"""
    session_token = f"session_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.user_sessions.delete_many({"user_id": user_id})
    await db.user_sessions.insert_one(session_doc)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=60*60*24*7
    )
    
    return session_token

async def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> User:
    """Get current user from session token (cookie or Authorization header)"""
    session_token = None
    
    session_token = request.cookies.get("session_token")
    
    if not session_token and authorization:
        if authorization.startswith("Bearer "):
            session_token = authorization.replace("Bearer ", "")
        else:
            session_token = authorization
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_doc = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user_doc = await db.users.find_one({"user_id": session_doc["user_id"]}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=404, detail="User not found")
    
    return User(**user_doc)

@auth_router.post("/signup")
async def email_signup(req: EmailSignupRequest, response: Response):
    """Sign up with email and password"""
    if not validate_password(req.password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with letters and numbers"
        )
    
    existing = await db.users.find_one({"email": req.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    referral_code = secrets.token_urlsafe(8)
    password_hash = hash_password(req.password)
    
    new_user = {
        "user_id": user_id,
        "email": req.email,
        "password_hash": password_hash,
        "name": req.name,
        "picture": None,
        "role": UserRole.USER.value,
        "subscription_plan": SubscriptionPlan.FREE_TRIAL.value,
        "video_credits": 2,
        "free_video_credits": 0,
        "referral_code": referral_code,
        "referred_by": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(new_user)
    
    await create_session(user_id, response)
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return {"user": user_doc, "message": "Account created successfully"}

@auth_router.post("/login")
async def email_login(req: EmailLoginRequest, response: Response):
    """Login with email and password"""
    user_doc = await db.users.find_one({"email": req.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if "password_hash" not in user_doc:
        raise HTTPException(status_code=400, detail="This account uses Google login")
    
    if not verify_password(req.password, user_doc["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    await create_session(user_doc["user_id"], response)
    
    user_doc.pop("password_hash", None)
    return {"user": user_doc, "message": "Login successful"}

@auth_router.post("/password-reset/request")
async def request_password_reset(req: PasswordResetRequest):
    """Request password reset"""
    user = await db.users.find_one({"email": req.email}, {"_id": 0})
    if not user:
        return {"message": "If email exists, reset link will be sent"}
    
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.password_resets.insert_one({
        "user_id": user["user_id"],
        "reset_token": reset_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # TODO: Send email with reset link
    # For now, return token (in production, send via email)
    return {
        "message": "If email exists, reset link will be sent",
        "reset_token": reset_token  # Remove this in production
    }

@auth_router.post("/password-reset/confirm")
async def confirm_password_reset(req: PasswordResetConfirm):
    """Confirm password reset with token"""
    if not validate_password(req.new_password):
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters with letters and numbers"
        )
    
    reset_doc = await db.password_resets.find_one(
        {"reset_token": req.reset_token},
        {"_id": 0}
    )
    
    if not reset_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    expires_at = datetime.fromisoformat(reset_doc["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset token expired")
    
    password_hash = hash_password(req.new_password)
    
    await db.users.update_one(
        {"user_id": reset_doc["user_id"]},
        {"$set": {"password_hash": password_hash}}
    )
    
    await db.password_resets.delete_one({"reset_token": req.reset_token})
    
    return {"message": "Password reset successful"}

@auth_router.post("/session")
async def exchange_session(request: Request, response: Response):
    """
    Exchange session_id for session_token (Google OAuth)
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    
    async with httpx.AsyncClient() as http_client:
        try:
            auth_response = await http_client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            auth_response.raise_for_status()
            session_data = auth_response.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=401, detail=f"Failed to authenticate: {str(e)}")
    
    email = session_data["email"]
    user_doc = await db.users.find_one({"email": email}, {"_id": 0})
    
    if user_doc:
        user_id = user_doc["user_id"]
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": session_data.get("name", user_doc["name"]),
                "picture": session_data.get("picture", user_doc.get("picture")),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        referral_code = secrets.token_urlsafe(8)
        
        new_user = {
            "user_id": user_id,
            "email": email,
            "name": session_data.get("name", ""),
            "picture": session_data.get("picture"),
            "role": UserRole.USER.value,
            "subscription_plan": SubscriptionPlan.FREE_TRIAL.value,
            "video_credits": 2,
            "free_video_credits": 0,
            "referral_code": referral_code,
            "referred_by": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
    
    session_token = await create_session(user_id, response)
    
    user_doc = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    
    return {"user": user_doc, "session_token": session_token}

@auth_router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return user

@auth_router.post("/logout")
async def logout(request: Request, response: Response, user: User = Depends(get_current_user)):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out successfully"}