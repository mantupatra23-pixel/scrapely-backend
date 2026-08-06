import uuid
from enum import Enum
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text, 
    Index, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class EmailValidationStatus(str, Enum):
    VALID = "VALID"
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"
    RISKY = "RISKY"
    UNKNOWN = "UNKNOWN"


class LeadPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = {'extend_existing': True}

    # Primary Identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), index=True, nullable=True)

    # Core Place Intelligence
    google_place_id = Column(String(255), unique=True, index=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    website = Column(String(500), index=True, nullable=True)
    phone = Column(String(100), index=True, nullable=True)
    phone_formatted = Column(String(100), nullable=True)
    phone_country_code = Column(String(10), nullable=True)
    is_mobile = Column(Boolean, default=False)
    has_whatsapp = Column(Boolean, default=False)

    # Email & Contact Intelligence
    verified_email = Column(String(255), index=True, nullable=True)
    email_status = Column(
        SQLEnum(EmailValidationStatus), 
        default=EmailValidationStatus.UNKNOWN, 
        nullable=False
    )
    email_source = Column(String(100), nullable=True)
    email_syntax_valid = Column(Boolean, default=False)
    email_mx_valid = Column(Boolean, default=False)
    email_smtp_valid = Column(Boolean, default=False)
    email_is_disposable = Column(Boolean, default=False)
    email_is_catch_all = Column(Boolean, default=False)
    email_is_role_based = Column(Boolean, default=False)

    # Location & Isolation Attributes
    address = Column(Text, nullable=True)
    city = Column(String(255), index=True, nullable=False)
    state = Column(String(255), index=True, nullable=True)
    postal_code = Column(String(50), nullable=True)
    country = Column(String(100), index=True, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Google Business Metrics
    google_rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    business_status = Column(String(100), default="OPERATIONAL")
    opening_hours = Column(JSONB, nullable=True)
    primary_category = Column(String(255), index=True, nullable=True)
    secondary_categories = Column(JSONB, nullable=True)
    google_maps_url = Column(Text, nullable=True)
    directions_url = Column(Text, nullable=True)
    photos_url = Column(Text, nullable=True)
    business_description = Column(Text, nullable=True)

    # Audit & Scoring Data
    seo_score = Column(Integer, default=0)
    lead_score = Column(Integer, default=0)
    lead_priority = Column(SQLEnum(LeadPriority), default=LeadPriority.MEDIUM)
    seo_audit_details = Column(JSONB, nullable=True)
    tech_stack = Column(JSONB, nullable=True)

    # Meta Management
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
