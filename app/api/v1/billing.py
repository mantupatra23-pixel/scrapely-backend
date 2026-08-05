from fastapi import APIRouter, Depends, HTTPException, Request, Header, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import stripe

from app.db.session import get_db
from app.config.settings import settings
from app.models.user import User, Organization
from app.models.billing import Subscription, SubscriptionStatus
from app.schemas.billing import (
    CreateCheckoutSessionRequest,
    CheckoutSessionResponse,
    CustomerPortalResponse
)
from app.services.stripe_service import StripeService
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/billing", tags=["Billing & Payments"])

@router.post("/checkout", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    req: CreateCheckoutSessionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stripe Hosted Checkout URL generate karta hai self-serve payment ke liye.
    """
    # Fetch User's Organization
    stmt = select(Organization).where(Organization.id == current_user.id) # Simplified for 1:1 demo
    result = await db.execute(stmt)
    org = result.scalars().first()

    if not org:
        # Auto-create org if missing
        org = Organization(name=f"{current_user.full_name or 'User'}'s Org", slug=str(current_user.id))
        db.add(org)
        await db.commit()
        await db.refresh(org)

    # Stripe Customer ID check/create
    if not org.stripe_customer_id:
        customer_id = StripeService.create_customer(email=current_user.email, name=current_user.full_name)
        org.stripe_customer_id = customer_id
        await db.commit()

    checkout_url = StripeService.create_checkout_session(
        customer_id=org.stripe_customer_id,
        price_id=req.price_id,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
        org_id=str(org.id)
    )

    return CheckoutSessionResponse(checkout_url=checkout_url)


@router.post("/portal", response_model=CustomerPortalResponse)
async def get_customer_portal(
    return_url: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    User ko Stripe Customer Portal redirection link deta hai (Cancel/Upgrade sub).
    """
    stmt = select(Organization).where(Organization.id == current_user.id)
    result = await db.execute(stmt)
    org = result.scalars().first()

    if not org or not org.stripe_customer_id:
        raise HTTPException(status_code=400, detail="No billing profile found")

    portal_url = StripeService.create_customer_portal(
        customer_id=org.stripe_customer_id,
        return_url=return_url
    )
    return CustomerPortalResponse(portal_url=portal_url)


@router.post("/webhook/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="stripe-signature"),
    db: AsyncSession = Depends(get_db)
):
    """
    Stripe Events Listener: Automatically activates or cancels user subscriptions.
    """
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook Error: {str(e)}")

    event_type = event["type"]
    data = event["data"]["object"]

    # Handle Successful Subscription Payment
    if event_type in ["checkout.session.completed", "customer.subscription.updated"]:
        stripe_sub_id = data.get("subscription") or data.get("id")
        customer_id = data.get("customer")
        
        if stripe_sub_id and customer_id:
            # Find Org by Stripe Customer
            stmt = select(Organization).where(Organization.stripe_customer_id == customer_id)
            org = (await db.execute(stmt)).scalars().first()

            if org:
                # Update or Insert Subscription
                sub_stmt = select(Subscription).where(Subscription.organization_id == org.id)
                sub = (await db.execute(sub_stmt)).scalars().first()

                period_end = datetime.fromtimestamp(data.get("current_period_end", 0), tz=timezone.utc)
                
                if not sub:
                    sub = Subscription(
                        organization_id=org.id,
                        stripe_subscription_id=stripe_sub_id,
                        stripe_price_id=data.get("items", {}).get("data", [{}])[0].get("price", {}).get("id", "price_default"),
                        status=SubscriptionStatus.ACTIVE,
                        current_period_end=period_end
                    )
                    db.add(sub)
                else:
                    sub.status = SubscriptionStatus.ACTIVE
                    sub.current_period_end = period_end

                await db.commit()

    # Handle Subscription Cancellation
    elif event_type == "customer.subscription.deleted":
        stripe_sub_id = data.get("id")
        sub_stmt = select(Subscription).where(Subscription.stripe_subscription_id == stripe_sub_id)
        sub = (await db.execute(sub_stmt)).scalars().first()

        if sub:
            sub.status = SubscriptionStatus.CANCELED
            await db.commit()

    return {"status": "success"}
