from pydantic import BaseModel, HttpUrl
from typing import Optional, List


class LeadBase(BaseModel):
    google_place_id: Optional[str] = None
    company_name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    verified_email: Optional[str] = None
    email_status: Optional[str] = "unverified"
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    google_rating: Optional[float] = 0.0
    reviews_count: Optional[int] = 0
    lead_score: Optional[int] = 50
    seo_score: Optional[int] = 50


class LeadCreate(LeadBase):
    pass


# Exact Schema required by app/api/v1/leads.py
class LeadResponseSchema(LeadBase):
    id: str

    class Config:
        from_attributes = True


class PaginatedLeadsResponse(BaseModel):
    total: int
    page: int
    limit: int
    leads: List[LeadResponseSchema]
