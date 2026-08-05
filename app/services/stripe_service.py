import stripe
from typing import Optional
from app.config.settings import settings

if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY

class StripeService:
    @staticmethod
    def create_customer(email: str, name: Optional[str] = None) -> str:
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"source": "Scrapely SaaS"}
        )
        return customer.id

    @staticmethod
    def create_checkout_session(
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        org_id: str
    ) -> str:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"organization_id": org_id}
        )
        return session.url

    @staticmethod
    def create_customer_portal(customer_id: str, return_url: str) -> str:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url
        )
        return session.url
