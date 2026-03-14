from fastapi import APIRouter, HTTPException, Depends, Request, Response, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from auth import get_current_user
from models import User, PaymentTransaction, PaymentStatus, SubscriptionPlan
import os
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
import base64

load_dotenv()

payments_router = APIRouter()

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Payment Methods Configuration
PAYMENT_METHODS = {
    "usdt_bep20": {
        "name": "USDT (BEP20)",
        "network": "Binance Smart Chain (BEP20)",
        "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb5",
        "qr_code": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb5",
        "instructions": "Send exact USDT amount to this BEP20 address. Upload transaction screenshot after payment."
    },
    "usdt_trc20": {
        "name": "USDT (TRC20)",
        "network": "TRON Network (TRC20)",
        "wallet_address": "TXvKhjdYqzMVFZQQpQvQbFmvPzfQYqXVKP",
        "qr_code": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=TXvKhjdYqzMVFZQQpQvQbFmvPzfQYqXVKP",
        "instructions": "Send exact USDT amount to this TRC20 address. Upload transaction screenshot after payment."
    },
    "jazzcash": {
        "name": "JazzCash",
        "account_number": "03001234567",
        "account_name": "VIDMATIC",
        "qr_code": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=jazzcash:03001234567",
        "instructions": "Send payment to JazzCash number. Upload payment receipt screenshot."
    },
    "easypaisa": {
        "name": "EasyPaisa",
        "account_number": "03007654321",
        "account_name": "VIDMATIC",
        "qr_code": "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=easypaisa:03007654321",
        "instructions": "Send payment to EasyPaisa number. Upload payment receipt screenshot."
    },
    "bank_transfer": {
        "name": "Bank Transfer",
        "bank_name": "HBL Bank",
        "account_number": "12345678901234",
        "account_name": "VIDMATIC PVT LTD",
        "iban": "PK36HABB0012345678901234",
        "branch_code": "1234",
        "instructions": "Transfer exact amount to bank account. Upload bank receipt/screenshot."
    }
}

# Subscription plans with USDT prices
SUBSCRIPTION_PLANS = {
    "free_trial": {"amount_usd": 0, "amount_pkr": 0, "credits": 2, "duration": "trial"},
    "pro_monthly": {"amount_usd": 11.0, "amount_pkr": 3080, "credits": 7, "duration": "monthly"},
    "pro_yearly": {"amount_usd": 228.0, "amount_pkr": 63840, "credits": 15, "duration": "yearly"}
}

class CreatePaymentRequest(BaseModel):
    plan_id: str
    payment_method: str
    currency: str = "usd"

class UploadPaymentProofRequest(BaseModel):
    transaction_id: str
    proof_base64: str
    transaction_hash: Optional[str] = None
    notes: Optional[str] = None

class VerifyPaymentRequest(BaseModel):
    transaction_id: str
    approved: bool
    admin_notes: Optional[str] = None

@payments_router.get("/methods")
async def get_payment_methods():
    """Get all available payment methods"""
    return {"payment_methods": PAYMENT_METHODS, "plans": SUBSCRIPTION_PLANS}

@payments_router.post("/create")
async def create_payment(req: CreatePaymentRequest, user: User = Depends(get_current_user)):
    """Create a new payment transaction"""
    if req.plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    if req.payment_method not in PAYMENT_METHODS:
        raise HTTPException(status_code=400, detail="Invalid payment method")
    
    plan = SUBSCRIPTION_PLANS[req.plan_id]
    amount = plan["amount_usd"] if req.currency == "usd" else plan["amount_pkr"]
    
    if amount == 0:
        raise HTTPException(status_code=400, detail="Cannot create payment for free plan")
    
    # Create payment transaction record
    transaction_id = f"txn_{uuid.uuid4().hex[:12]}"
    transaction_doc = {
        "transaction_id": transaction_id,
        "user_id": user.user_id,
        "plan": req.plan_id,
        "payment_method": req.payment_method,
        "amount": amount,
        "currency": req.currency.upper(),
        "payment_status": PaymentStatus.PENDING.value,
        "proof_uploaded": False,
        "proof_image": None,
        "transaction_hash": None,
        "admin_verified": False,
        "admin_notes": None,
        "metadata": {"user_email": user.email, "plan_name": plan["duration"]},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.payment_transactions.insert_one(transaction_doc)
    
    # Get payment method details
    method_details = PAYMENT_METHODS[req.payment_method]
    
    return {
        "transaction_id": transaction_id,
        "payment_method": req.payment_method,
        "method_details": method_details,
        "amount": amount,
        "currency": req.currency.upper(),
        "status": "pending",
        "message": "Please complete payment and upload proof"
    }

@payments_router.post("/upload-proof")
async def upload_payment_proof(req: UploadPaymentProofRequest, user: User = Depends(get_current_user)):
    """Upload payment proof for verification"""
    # Find transaction
    transaction = await db.payment_transactions.find_one(
        {"transaction_id": req.transaction_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction["payment_status"] == PaymentStatus.PAID.value:
        raise HTTPException(status_code=400, detail="Payment already verified")
    
    # Update transaction with proof
    await db.payment_transactions.update_one(
        {"transaction_id": req.transaction_id},
        {"$set": {
            "proof_uploaded": True,
            "proof_image": req.proof_base64[:100] + "...",  # Store preview
            "transaction_hash": req.transaction_hash,
            "user_notes": req.notes,
            "payment_status": "pending_verification",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "message": "Payment proof uploaded successfully. Please wait for admin verification.",
        "transaction_id": req.transaction_id,
        "status": "pending_verification"
    }

@payments_router.get("/status/{transaction_id}")
async def get_payment_status(transaction_id: str, user: User = Depends(get_current_user)):
    """Get payment transaction status"""
    transaction = await db.payment_transactions.find_one(
        {"transaction_id": transaction_id, "user_id": user.user_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return {
        "transaction_id": transaction["transaction_id"],
        "plan": transaction["plan"],
        "amount": transaction["amount"],
        "currency": transaction["currency"],
        "payment_method": transaction["payment_method"],
        "status": transaction["payment_status"],
        "proof_uploaded": transaction.get("proof_uploaded", False),
        "admin_verified": transaction.get("admin_verified", False),
        "admin_notes": transaction.get("admin_notes"),
        "created_at": transaction["created_at"]
    }

@payments_router.post("/verify")
async def verify_payment(req: VerifyPaymentRequest, user: User = Depends(get_current_user)):
    """Admin: Verify payment proof and activate subscription"""
    # Check admin permission
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    transaction = await db.payment_transactions.find_one(
        {"transaction_id": req.transaction_id},
        {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if req.approved:
        # Update user subscription
        plan_id = transaction["plan"]
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        await db.users.update_one(
            {"user_id": transaction["user_id"]},
            {"$set": {
                "subscription_plan": plan_id,
                "video_credits": plan["credits"],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Check referral bonus
        user_doc = await db.users.find_one({"user_id": transaction["user_id"]}, {"_id": 0})
        if user_doc and user_doc.get("referred_by"):
            referrer_id = user_doc["referred_by"]
            await db.users.update_one(
                {"user_id": referrer_id},
                {"$inc": {"free_video_credits": 1}}
            )
            await db.referrals.update_one(
                {"referrer_id": referrer_id, "referred_user_id": transaction["user_id"]},
                {"$set": {"reward_granted": True, "status": "completed"}}
            )
        
        # Mark transaction as paid
        await db.payment_transactions.update_one(
            {"transaction_id": req.transaction_id},
            {"$set": {
                "payment_status": PaymentStatus.PAID.value,
                "admin_verified": True,
                "admin_notes": req.admin_notes,
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Payment verified and subscription activated", "approved": True}
    else:
        # Reject payment
        await db.payment_transactions.update_one(
            {"transaction_id": req.transaction_id},
            {"$set": {
                "payment_status": PaymentStatus.FAILED.value,
                "admin_verified": False,
                "admin_notes": req.admin_notes,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"message": "Payment rejected", "approved": False, "reason": req.admin_notes}

@payments_router.get("/pending")
async def get_pending_payments(user: User = Depends(get_current_user)):
    """Admin: Get all pending payment verifications"""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pending = await db.payment_transactions.find(
        {"payment_status": "pending_verification"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return {"pending_payments": pending, "count": len(pending)}

@payments_router.get("/my-transactions")
async def get_my_transactions(user: User = Depends(get_current_user)):
    """Get user's payment history"""
    transactions = await db.payment_transactions.find(
        {"user_id": user.user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return {"transactions": transactions}