from fastapi import APIRouter, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User, PaymentTransaction, PaymentStatus, SubscriptionPlan
import os
import uuid
from datetime import datetime, timezone
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
from dotenv import load_dotenv

load_dotenv()

payments_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Subscription plans
SUBSCRIPTION_PLANS = {
    "free_trial": {"amount": 0, "credits": 2, "duration": "trial"},
    "pro_monthly": {"amount": 29.0, "credits": 7, "duration": "monthly", "discounted": 11.0},
    "pro_yearly": {"amount": 228.0, "credits": 15, "duration": "yearly", "monthly_equivalent": 19.0}
}

class CreateCheckoutRequest(BaseModel):
    plan_id: str
    origin_url: str

class CheckSessionStatusRequest(BaseModel):
    session_id: str

@payments_router.post("/checkout/session")
async def create_checkout_session(req: CreateCheckoutRequest, user: User = Depends(get_current_user)):
    """Create Stripe checkout session for subscription"""
    if req.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    plan = SUBSCRIPTION_PLANS[req.plan_id]
    amount = plan.get("discounted", plan["amount"])
    
    if amount == 0:
        raise HTTPException(status_code=400, detail="Cannot checkout free plan")
    
    # Build URLs
    success_url = f"{req.origin_url}/billing?session_id={{{{CHECKOUT_SESSION_ID}}}}"
    cancel_url = f"{req.origin_url}/billing"
    
    # Initialize Stripe
    api_key = os.getenv("STRIPE_API_KEY")
    webhook_url = f"{req.origin_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=amount,
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user.user_id,
            "plan_id": req.plan_id,
            "email": user.email
        }
    )
    
    session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
    
    # Create payment transaction record
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    transaction_doc = {
        "transaction_id": transaction_id,
        "user_id": user.user_id,
        "session_id": session.session_id,
        "amount": amount,
        "currency": "usd",
        "plan": req.plan_id,
        "payment_status": PaymentStatus.PENDING.value,
        "metadata": {"user_id": user.user_id, "plan_id": req.plan_id},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction_doc)
    
    return {"url": session.url, "session_id": session.session_id}

@payments_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, user: User = Depends(get_current_user)):
    """Get checkout session status"""
    # Find transaction
    transaction = await db.payment_transactions.find_one({"session_id": session_id}, {"_id": 0})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # If already processed, return status
    if transaction["payment_status"] == PaymentStatus.PAID.value:
        return {
            "status": "complete",
            "payment_status": "paid",
            "plan": transaction["plan"]
        }
    
    # Check with Stripe
    api_key = os.getenv("STRIPE_API_KEY")
    webhook_url = f"{os.getenv('REACT_APP_BACKEND_URL', '')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    checkout_status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
    
    # Update transaction
    if checkout_status.payment_status == "paid" and transaction["payment_status"] != PaymentStatus.PAID.value:
        # Update user subscription and credits
        plan_id = transaction["plan"]
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        await db.users.update_one(
            {"user_id": user.user_id},
            {"$set": {
                "subscription_plan": plan_id,
                "video_credits": plan["credits"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Check if user was referred and grant referrer bonus
        user_doc = await db.users.find_one({"user_id": user.user_id}, {"_id": 0})
        if user_doc and user_doc.get("referred_by"):
            referrer_id = user_doc["referred_by"]
            # Grant 1 free video credit to referrer
            await db.users.update_one(
                {"user_id": referrer_id},
                {"$inc": {"free_video_credits": 1}}
            )
            # Update referral record
            await db.referrals.update_one(
                {"referrer_id": referrer_id, "referred_user_id": user.user_id},
                {"$set": {"reward_granted": True, "status": "completed"}}
            )
        
        # Mark transaction as paid
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "payment_status": PaymentStatus.PAID.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    return {
        "status": checkout_status.status,
        "payment_status": checkout_status.payment_status,
        "amount_total": checkout_status.amount_total,
        "currency": checkout_status.currency,
        "plan": transaction["plan"]
    }

@payments_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    body = await request.body()
    signature = request.headers.get("Stripe-Signature")
    
    api_key = os.getenv("STRIPE_API_KEY")
    webhook_url = f"{os.getenv('REACT_APP_BACKEND_URL', '')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    try:
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        # Process webhook event
        return {"received": True, "event_id": webhook_response.event_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))