import uuid
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    Index, Enum as SQLEnum, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class EmailStatusEnum(str, Enum):
    VALID = "VALID"
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"
    RISKY = "RISKY"
    NOT_FOUND = "NOT_FOUND"


class LeadPriorityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("idx_geo_strict", "country", "city", "primary_category"),
        UniqueConstraint("google_place_id", name="uq_google_place_id"),
        {"extend_existing": True},
    )

    # Primary Identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), index=True, nullable=True)

    # Core Place Intelligence
    google_place_id = Column(String(255), unique=True, index=True, nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    website = Column(String(500), index=True, nullable=True)
    phone = Column(String(100), index=True, nullable=True)
    phone_formatted = Column(String(100), nullable=True)
    phone_country_code = Column(String(10), nullable=True)

    # Verified Contact Intelligence
    verified_email = Column(String(255), index=True, nullable=True)
    email_status = Column(
        SQLEnum(EmailStatusEnum, name="emailstatusenum"),
        default=EmailStatusEnum.NOT_FOUND,
        nullable=False
    )
    email_source = Column(String(100), nullable=True)

    # Data Source Identifier
    source = Column(String(100), default="GOOGLE_MAPS", nullable=False)

    # Strict Geolocation & Isolation Attributes
    address = Column(Text, nullable=True)
    city = Column(String(255), index=True, nullable=True)
    state = Column(String(255), index=True, nullable=True)
    postal_code = Column(String(50), nullable=True)
    country = Column(String(100), index=True, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Google Business Metrics (Strict Live Stream)
    google_rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    business_status = Column(String(100), default="OPERATIONAL")
    opening_hours = Column(JSONB, nullable=True)
    primary_category = Column(String(255), index=True, nullable=True)
    google_maps_url = Column(Text, nullable=True)

    # Audit & Scoring Data
    seo_score = Column(Integer, default=50)
    lead_score = Column(Integer, default=50)
    lead_priority = Column(
        SQLEnum(LeadPriorityEnum, name="leadpriorityenum"),
        default=LeadPriorityEnum.MEDIUM
    )
    seo_audit_details = Column(JSONB, nullable=True)

    # System Tracking
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
