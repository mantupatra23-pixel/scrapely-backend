from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CreateCheckoutSessionRequest(BaseModel):
    price_id: str  # Stripe Price ID (e.g., price_1N...)
    success_url: str
    cancel_url: str

class CheckoutSessionResponse(BaseModel):
    checkout_url: str

class SubscriptionResponse(BaseModel):
    id: str
    status: str
    stripe_price_id: str
    current_period_end: datetime
    monthly_credits: int

    class Config:
        from_attributes = True

class CustomerPortalResponse(BaseModel):
    portal_url: str
