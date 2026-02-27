"""
Payments API - Stripe subscriptions
"""

from fastapi import APIRouter, HTTPException, Request, Depends
from datetime import datetime
from bson import ObjectId
from db import get_database
from middleware import get_current_user
from services.stripe_service import stripe_service
from models.payment import PaymentCreate, CheckoutSessionResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/create-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(data: PaymentCreate, current_user: dict = Depends(get_current_user)):
    """Create Stripe checkout session for subscription"""
    db = get_database()
    user_id = current_user["id"]
    
    # Get or create Stripe customer
    customer_id = current_user.get("stripe_customer_id")
    if not customer_id:
        customer_id = await stripe_service.create_customer(current_user["email"], user_id)
        await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"stripe_customer_id": customer_id}})
    
    session_id, checkout_url = await stripe_service.create_checkout_session(
        customer_id, data.success_url, data.cancel_url, user_id
    )
    
    return CheckoutSessionResponse(session_id=session_id, checkout_url=checkout_url)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {e}")
    
    result = await stripe_service.handle_webhook_event(event)
    
    if result.get("action") == "activate" and result.get("user_id"):
        db = get_database()
        await db.users.update_one(
            {"_id": ObjectId(result["user_id"])},
            {"$set": {"is_paid": True, "subscription_id": result.get("subscription_id"), "subscription_status": "active"}}
        )
        await db.scans.update_many({"user_id": result["user_id"]}, {"$set": {"is_unlocked": True}})
    
    return {"status": "ok"}


@router.get("/status")
async def get_subscription_status(current_user: dict = Depends(get_current_user)):
    """Get subscription status"""
    sub_id = current_user.get("subscription_id")
    if not sub_id:
        return {"is_active": False}
    
    sub = await stripe_service.get_subscription(sub_id)
    return {"is_active": sub.get("status") == "active" if sub else False, "subscription": sub}


@router.post("/test-activate")
async def test_activate_subscription(current_user: dict = Depends(get_current_user)):
    """
    DEV ONLY: Manually activate subscription for testing.
    This bypasses Stripe webhooks which don't work on localhost.
    """
    from config import settings
    if settings.app_env != "development":
        raise HTTPException(status_code=403, detail="Only available in development mode")
    
    db = get_database()
    user_id = current_user["id"]
    
    # Activate user
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"is_paid": True, "subscription_status": "active"}}
    )
    
    # Unlock all scans
    await db.scans.update_many({"user_id": user_id}, {"$set": {"is_unlocked": True}})
    
    return {"status": "activated", "message": "Subscription activated for testing"}
