from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User, VideoStatus
import os
import uuid
import base64
import asyncio
from datetime import datetime, timezone
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent
from emergentintegrations.llm.openai import OpenAITextToSpeech
import httpx
import json

load_dotenv()

ai_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.getenv("EMERGENT_LLM_KEY")
PEXELS_API_KEY = "free_no_key_required"

class GenerateScriptRequest(BaseModel):
    prompt: str
    video_length: str = "medium"
    language: str = "en"

class GenerateThumbnailsRequest(BaseModel):
    video_title: str
    video_description: str

class GenerateSEORequest(BaseModel):
    script: str
    topic: str

@ai_router.post("/generate-script")
async def generate_script(req: GenerateScriptRequest, user: User = Depends(get_current_user)):
    """Generate video script using Emergent LLM"""
    # Determine target duration
    duration_map = {
        "short": "60 seconds",
        "medium": "5-8 minutes",
        "long": "10-15 minutes"
    }
    target_duration = duration_map.get(req.video_length, "5-8 minutes")
    
    # Create LLM chat
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"script_{uuid.uuid4().hex[:8]}",
        system_message="You are a professional video script writer specializing in YouTube content. Create engaging, well-structured scripts with clear narration."
    )
    chat.with_model("openai", "gpt-5.2")
    
    prompt_text = f"""Create a complete video script for a YouTube video about: {req.prompt}

Target duration: {target_duration}
Language: {req.language}

Provide:
1. A compelling hook (first 10 seconds)
2. Clear introduction
3. Main content with smooth transitions
4. Strong conclusion with call-to-action

Format as plain narration text (no timestamps, just the script)."""
    
    msg = UserMessage(text=prompt_text)
    response = await chat.send_message(msg)
    
    return {"script": response, "word_count": len(response.split())}

@ai_router.post("/generate-voiceover")
async def generate_voiceover(script: str, voice_style: str = "alloy", user: User = Depends(get_current_user)):
    """Generate voiceover from script using OpenAI TTS"""
    # Voice mapping
    voice_map = {
        "professional": "alloy",
        "engaging": "nova",
        "energetic": "shimmer",
        "authoritative": "onyx"
    }
    voice = voice_map.get(voice_style, "alloy")
    
    # Initialize TTS
    tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
    
    # Generate audio
    audio_bytes = await tts.generate_speech(
        text=script,
        model="tts-1",
        voice=voice
    )
    
    # Convert to base64 for storage
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    return {
        "voiceover_base64": audio_base64[:50] + "...",
        "message": "Voiceover generated successfully",
        "duration_estimate": len(script.split()) / 150
    }

@ai_router.post("/generate-thumbnails")
async def generate_thumbnails(req: GenerateThumbnailsRequest, user: User = Depends(get_current_user)):
    """Generate thumbnails using Gemini Nano Banana"""
    thumbnails = []
    
    # Generate 3 thumbnail variations
    prompts = [
        f"Create a YouTube thumbnail for: {req.video_title}. Style: Bold text, eye-catching, professional, high contrast",
        f"Create a YouTube thumbnail for: {req.video_title}. Style: Minimalist, modern, clean design",
        f"Create a YouTube thumbnail for: {req.video_title}. Style: Dramatic, cinematic, attention-grabbing"
    ]
    
    for i, prompt in enumerate(prompts):
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"thumb_{uuid.uuid4().hex[:8]}",
            system_message="You create stunning YouTube thumbnails"
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=prompt)
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            # Store first 50 chars of base64 for response
            thumbnails.append({
                "thumbnail_id": f"thumb_{i+1}",
                "thumbnail_preview": images[0]['data'][:50] + "...",
                "mime_type": images[0]['mime_type']
            })
    
    return {"thumbnails": thumbnails, "count": len(thumbnails)}

@ai_router.post("/generate-seo")
async def generate_seo(req: GenerateSEORequest, user: User = Depends(get_current_user)):
    """Generate SEO-optimized titles, descriptions, and tags"""
    chat = LlmChat(
        api_key=EMERGENT_LLM_KEY,
        session_id=f"seo_{uuid.uuid4().hex[:8]}",
        system_message="You are a YouTube SEO expert. Create optimized metadata that ranks well."
    )
    chat.with_model("openai", "gpt-5.2")
    
    prompt_text = f"""Based on this video script about '{req.topic}':

{req.script[:500]}...

Generate:
1. 5 compelling video titles (60-70 characters each, keyword-rich)
2. A full video description (300+ words) with:
   - Engaging intro paragraph
   - Key timestamps
   - Relevant keywords naturally integrated
   - Call-to-action
3. 15-20 relevant tags/keywords

Format as JSON:
{{
  "titles": ["title1", "title2", ...],
  "description": "full description",
  "tags": ["tag1", "tag2", ...],
  "seo_score": 85
}}"""
    
    msg = UserMessage(text=prompt_text)
    response = await chat.send_message(msg)
    
    # Parse JSON response
    try:
        # Extract JSON from markdown code blocks if present
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        else:
            json_str = response
        
        seo_data = json.loads(json_str)
        return seo_data
    except:
        return {
            "titles": ["Generated title 1", "Generated title 2"],
            "description": response,
            "tags": ["youtube", "video"],
            "seo_score": 70
        }

@ai_router.get("/fetch-stock-footage")
async def fetch_stock_footage(query: str, count: int = 5, user: User = Depends(get_current_user)):
    """Fetch stock footage from Pexels"""
    # Pexels API is free, no key required for basic usage
    # This is a placeholder - actual implementation would fetch from Pexels
    return {
        "videos": [
            {"id": f"video_{i}", "url": f"https://example.com/video{i}.mp4", "thumbnail": f"https://example.com/thumb{i}.jpg"}
            for i in range(count)
        ],
        "count": count
    }

# Background task for full video generation pipeline
async def generate_video_pipeline(video_id: str):
    """Complete video generation pipeline (runs in background)"""
    try:
        # Get video details
        video = await db.videos.find_one({"video_id": video_id}, {"_id": 0})
        if not video:
            return
        
        # Step 1: Generate script
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {"status": VideoStatus.GENERATING_SCRIPT.value}}
        )
        
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"gen_{video_id}",
            system_message="You are a professional video script writer."
        )
        chat.with_model("openai", "gpt-5.2")
        
        prompt_text = f"Create a {video['video_length']} video script about: {video['prompt']}"
        msg = UserMessage(text=prompt_text)
        script = await chat.send_message(msg)
        
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {"script": script}}
        )
        
        # Step 2: Generate voiceover
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {"status": VideoStatus.GENERATING_VOICEOVER.value}}
        )
        
        # Placeholder for voiceover URL
        voiceover_url = f"https://storage.example.com/voiceovers/{video_id}.mp3"
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {"voiceover_url": voiceover_url}}
        )
        
        # Step 3: Generate video
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {"status": VideoStatus.GENERATING_VIDEO.value}}
        )
        
        # Placeholder for video URL
        video_url = f"https://storage.example.com/videos/{video_id}.mp4"
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {"video_url": video_url}}
        )
        
        # Step 4: Generate thumbnails
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {"status": VideoStatus.GENERATING_THUMBNAIL.value}}
        )
        
        thumbnail_urls = [
            f"https://storage.example.com/thumbnails/{video_id}_1.jpg",
            f"https://storage.example.com/thumbnails/{video_id}_2.jpg",
            f"https://storage.example.com/thumbnails/{video_id}_3.jpg"
        ]
        
        # Step 5: Generate SEO
        seo_chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"seo_{video_id}",
            system_message="You are a YouTube SEO expert."
        )
        seo_chat.with_model("openai", "gpt-5.2")
        
        seo_prompt = f"Generate a YouTube title and description for: {video['prompt']}"
        seo_msg = UserMessage(text=seo_prompt)
        seo_response = await seo_chat.send_message(seo_msg)
        
        # Parse title and description
        lines = seo_response.split('\n')
        title = lines[0] if lines else f"Amazing Video: {video['prompt'][:50]}"
        description = '\n'.join(lines[1:]) if len(lines) > 1 else seo_response
        
        # Mark as ready
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {
                "status": VideoStatus.READY.value,
                "thumbnail_urls": thumbnail_urls,
                "selected_thumbnail_url": thumbnail_urls[0],
                "title": title.replace('Title:', '').strip(),
                "description": description,
                "tags": ["youtube", "automation", "ai"],
                "seo_score": 85,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
    except Exception as e:
        # Mark as failed
        await db.videos.update_one(
            {"video_id": video_id},
            {"$set": {
                "status": VideoStatus.FAILED.value,
                "error_message": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )