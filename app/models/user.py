import enum
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Enum, ForeignKey, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import BaseMixin


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MEMBER = "member"


class User(Base, BaseMixin):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)

    memberships = relationship("Membership", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")


class Organization(Base, BaseMixin):
    __tablename__ = "organizations"
    __table_args__ = {'extend_existing': True}

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    memberships = relationship("Membership", back_populates="organization", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="organization", cascade="all, delete-orphan")


class Membership(Base, BaseMixin):
    __tablename__ = "memberships"
    __table_args__ = {'extend_existing': True}

    user_id: Mapped[BaseMixin.id] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id: Mapped[BaseMixin.id] = mapped_column(ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.MEMBER, nullable=False)

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")


class Lead(Base, BaseMixin):
    __tablename__ = "leads"
    __table_args__ = {'extend_existing': True}

    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    rating: Mapped[Optional[float]] = mapped_column(nullable=True, default=0.0)
    reviews: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)

    # AI Lead Intelligence Metrics
    lead_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lead_priority: Mapped[str] = mapped_column(String(20), default="LOW", nullable=False)
    seo_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    email_status: Mapped[str] = mapped_column(String(30), default="UNKNOWN", nullable=False)
    ssl_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mobile_friendly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    page_speed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meta_title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    robots_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sitemap_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    schema_found: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    domain_age: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_audit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
