import uuid
from pydantic import BaseModel
from typing import Optional, List

class LeadBase(BaseModel):
    company_name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = 0
    source: str = "google_maps"

class LeadResponse(LeadBase):
    id: uuid.UUID

    class Config:
        from_attributes = True

class LeadSearchRequest(BaseModel):
    query: str
    limit: int = 10

class PaginatedLeadsResponse(BaseModel):
    total: int
    page: int
    limit: int
    leads: List[LeadResponse]
