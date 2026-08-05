from typing import Optional
from sqlalchemy import String, Float, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base
from app.models.base import BaseMixin

class Lead(Base, BaseMixin):
    __tablename__ = "leads"

    company_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    reviews_count: Mapped[Optional[int]] = mapped_column(default=0)
    
    source: Mapped[str] = mapped_column(String(50), default="google_maps", index=True)

    __table_args__ = (
        Index("idx_lead_search_lookup", "category", "city"),
    )
