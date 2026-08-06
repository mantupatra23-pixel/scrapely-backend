from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.session import Base

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    google_place_id = Column(String(255), nullable=True)
    company_name = Column(String(255), nullable=False)
    website = Column(String(500), nullable=True)
    phone = Column(String(100), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(255), nullable=False, default="New York")
    country = Column(String(100), nullable=False, default="United States")
    category = Column(String(255), nullable=True)
    rating = Column(Float, default=4.5)
    reviews_count = Column(Integer, default=0)
    source = Column(String(100), default="live_swarm")
    lead_score = Column(Integer, default=85)
    lead_priority = Column(String(50), default="HIGH")
    seo_score = Column(Integer, default=80)
    email_status = Column(String(50), default="VERIFIED")
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
