"""
Payment Models - Subscription-based payments
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class SubscriptionStatus(str, Enum):
    """Stripe subscription status"""
    ACTIVE = "active"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"
    PAUSED = "paused"
    TRIALING = "trialing"
    UNPAID = "unpaid"


class PaymentStatus(str, Enum):
    """Payment transaction status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    """Request to create a payment/subscription"""
    success_url: str = Field(description="URL to redirect after successful payment")
    cancel_url: str = Field(description="URL to redirect if payment is canceled")


class CheckoutSessionResponse(BaseModel):
    """Stripe checkout session response"""
    session_id: str
    checkout_url: str


class PaymentResponse(BaseModel):
    """Payment record response"""
    id: str
    user_id: str
    stripe_subscription_id: Optional[str] = None
    amount: float
    currency: str
    status: PaymentStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class SubscriptionResponse(BaseModel):
    """Subscription status response"""
    is_active: bool
    status: Optional[SubscriptionStatus] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False


class PaymentInDB(BaseModel):
    """Full payment model as stored in database"""
    user_id: str
    stripe_customer_id: Optional[str] = None
    stripe_session_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_payment_intent: Optional[str] = None
    amount: float
    currency: str = "usd"
    status: PaymentStatus = PaymentStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    subscription_status: Optional[SubscriptionStatus] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None


class WebhookEvent(BaseModel):
    """Stripe webhook event data"""
    event_type: str
    event_id: str
    data: dict
