from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response, Request, BackgroundTasks, UploadFile, File, Header
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import asyncio
from contextlib import asynccontextmanager

# Import our custom modules
from auth import auth_router, get_current_user
from youtube import youtube_router
from payments import payments_router
from videos import videos_router
from ai import ai_router
from channels import channels_router
from referrals import referrals_router
from admin import admin_router

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.info("Starting up VIDMATIC...")
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("user_id", unique=True)
    await db.user_sessions.create_index("session_token", unique=True)
    await db.user_sessions.create_index("expires_at")
    await db.channels.create_index("user_id")
    await db.videos.create_index("user_id")
    await db.videos.create_index("status")
    await db.payment_transactions.create_index("session_id", unique=True)
    await db.referrals.create_index("referrer_id")
    await db.referrals.create_index("referred_user_id")
    yield
    # Shutdown
    logging.info("Shutting down VIDMATIC...")
    client.close()

# Create the main app
app = FastAPI(title="VIDMATIC API", version="1.0.0", lifespan=lifespan)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check endpoint (no prefix)
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "VIDMATIC"}

# Include all routers
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
api_router.include_router(payments_router, prefix="/payments", tags=["Payments"])
api_router.include_router(videos_router, prefix="/videos", tags=["Videos"])
api_router.include_router(ai_router, prefix="/ai", tags=["AI Generation"])
api_router.include_router(channels_router, prefix="/channels", tags=["Channels"])
api_router.include_router(referrals_router, prefix="/referrals", tags=["Referrals"])
api_router.include_router(admin_router, prefix="/admin", tags=["Admin"])

# Root API endpoint
@api_router.get("/")
async def api_root():
    return {
        "message": "VIDMATIC API",
        "version": "1.0.0",
        "endpoints": [
            "/api/auth",
            "/api/youtube",
            "/api/payments",
            "/api/videos",
            "/api/ai",
            "/api/channels",
            "/api/referrals",
            "/api/admin"
        ]
    }

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)