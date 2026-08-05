import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import BaseMixin

class APIKey(Base, BaseMixin):
    __tablename__ = "api_keys"

    key_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[BaseMixin.id] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="api_keys")


class SubscriptionStatus(str, enum.Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"


class Subscription(Base, BaseMixin):
    __tablename__ = "subscriptions"

    organization_id: Mapped[BaseMixin.id] = mapped_column(ForeignKey("organizations.id"), nullable=False)
    stripe_subscription_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    stripe_price_id: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.TRIALING)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    monthly_credits: Mapped[int] = mapped_column(Integer, default=1000)

    organization = relationship("Organization", back_populates="subscriptions")
