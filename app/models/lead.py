from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text, DateTime, Float, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.base import BaseMixin


class Lead(Base, BaseMixin):
    __tablename__ = "leads"

    company_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    reviews_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    source: Mapped[str] = mapped_column(String(50), default="google_maps", nullable=False)

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

    __table_args__ = (
        Index("idx_lead_search_lookup", "category", "city"),
    )
