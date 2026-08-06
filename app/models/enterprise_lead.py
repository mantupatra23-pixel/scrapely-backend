import enum
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    Index, Enum as SQLEnum, UniqueConstraint, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db.session import Base


class EmailStatusEnum(str, enum.Enum):
    VALID = "VALID"
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"
    RISKY = "RISKY"
    NOT_FOUND = "NOT_FOUND"


class LeadPriorityEnum(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BusinessStatusEnum(str, enum.Enum):
    OPERATIONAL = "OPERATIONAL"
    CLOSED_TEMPORARILY = "CLOSED_TEMPORARILY"
    CLOSED_PERMANENTLY = "CLOSED_PERMANENTLY"


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("idx_geo_strict", "country", "state", "city", "primary_category"),
        Index("idx_workspace_lead", "workspace_id", "is_deleted"),
        UniqueConstraint("google_place_id", "workspace_id", name="uq_place_workspace"),
        {"extend_existing": True},
    )

    # Primary Identifiers & Isolation
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=True)

    # Core Geolocation & Identity Attributes
    google_place_id = Column(String(255), index=True, nullable=False)
    company_name = Column(String(255), nullable=False, index=True)
    company_logo_url = Column(Text, nullable=True)
    primary_category = Column(String(255), index=True, nullable=True)
    source = Column(String(100), default="GOOGLE_MAPS", nullable=False)

    # Direct Verified Contact Information
    phone = Column(String(100), index=True, nullable=True)
    phone_formatted = Column(String(100), nullable=True)
    phone_country_code = Column(String(10), nullable=True)
    whatsapp_available = Column(Boolean, default=False)
    
    verified_email = Column(String(255), index=True, nullable=True)
    email_status = Column(
        SQLEnum(EmailStatusEnum, name="emailstatusenum"),
        default=EmailStatusEnum.NOT_FOUND,
        nullable=False
    )
    email_source = Column(String(100), nullable=True)

    # Web Presence & Physical Address
    website = Column(String(500), index=True, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(255), index=True, nullable=True)
    state = Column(String(255), index=True, nullable=True)
    country = Column(String(100), index=True, nullable=True)
    postal_code = Column(String(50), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Google Business Analytics
    google_rating = Column(Float, default=0.0)
    reviews_count = Column(Integer, default=0)
    business_status = Column(
        SQLEnum(BusinessStatusEnum, name="businessstatusenum"),
        default=BusinessStatusEnum.OPERATIONAL,
        nullable=False
    )
    opening_hours = Column(JSONB, nullable=True)
    google_maps_url = Column(Text, nullable=True)

    # Expanded B2B Firmographics
    founded_year = Column(Integer, nullable=True)
    employee_count_range = Column(String(100), nullable=True)
    estimated_revenue_range = Column(String(100), nullable=True)
    social_profiles = Column(JSONB, default=dict)  # {linkedin, facebook, instagram, twitter, youtube}

    # Deep Website, Tech Stack & SEO Health Metrics
    tech_stack = Column(JSONB, default=list)       # ["WordPress", "Shopify", "React", "Cloudflare"]
    ssl_status = Column(Boolean, default=False)
    https_enabled = Column(Boolean, default=False)
    cms = Column(String(100), nullable=True)
    hosting_provider = Column(String(100), nullable=True)
    pagespeed_score = Column(Integer, nullable=True)
    mobile_friendly = Column(Boolean, default=True)
    domain_authority = Column(Integer, default=0)
    spam_score = Column(Integer, default=0)

    # AI Intelligence, Scoring & Audit Outputs
    seo_score = Column(Integer, default=50)
    lead_score = Column(Integer, default=50)
    ai_opportunity_score = Column(Integer, default=50)
    ai_buyer_intent = Column(String(50), default="MEDIUM")
    lead_priority = Column(
        SQLEnum(LeadPriorityEnum, name="leadpriorityenum"),
        default=LeadPriorityEnum.MEDIUM,
        nullable=False
    )
    ai_summary = Column(Text, nullable=True)
    ai_audit_payload = Column(JSONB, nullable=True)  # Detailed pros, cons, and outreach suggestions

    # System Auditing & Soft Delete
    is_saved = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    tags = Column(JSONB, default=list)
    assigned_to = Column(String(255), nullable=True)
    internal_notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
