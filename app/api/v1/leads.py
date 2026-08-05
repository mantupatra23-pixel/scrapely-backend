import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.session import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadResponse, LeadSearchRequest, PaginatedLeadsResponse
from app.services.scraper import GoogleMapsScraper
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/leads", tags=["Leads"])

@router.post("/scrape", response_model=list[LeadResponse], status_code=status.HTTP_201_CREATED)
async def scrape_and_save_leads(
    search_req: LeadSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Real-time Google Maps Scraper trigger karta hai aur DB me save karta hai.
    """
    scraper = GoogleMapsScraper()
    scraped_data = await scraper.scrape_leads(query=search_req.query, max_results=search_req.limit)
    
    saved_leads = []
    for item in scraped_data:
        # Deduplication check by company_name & phone
        stmt = select(Lead).where(
            Lead.company_name == item["company_name"],
            Lead.is_deleted == False
        )
        existing = (await db.execute(stmt)).scalars().first()
        
        if not existing:
            lead = Lead(**item)
            db.add(lead)
            saved_leads.append(lead)
            
    await db.commit()
    for lead in saved_leads:
        await db.refresh(lead)
        
    return saved_leads

@router.get("/search", response_model=PaginatedLeadsResponse)
async def search_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    city: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Database se Leads ko Filter, Search aur Paginate karta hai.
    """
    query = select(Lead).where(Lead.is_deleted == False)

    if city:
        query = query.where(Lead.city.ilike(f"%{city}%"))
    if category:
        query = query.where(Lead.category.ilike(f"%{category}%"))
    if search:
        query = query.where(
            or_(
                Lead.company_name.ilike(f"%{search}%"),
                Lead.address.ilike(f"%{search}%")
            )
        )

    # Count Total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    result = await db.execute(query)
    leads = result.scalars().all()

    return PaginatedLeadsResponse(
        total=total,
        page=page,
        limit=limit,
        leads=leads
    )
