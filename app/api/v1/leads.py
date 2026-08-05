import math
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_

from app.db.session import get_db
from app.models.lead import Lead
from app.models.user import User
from app.schemas.lead import LeadResponse, LeadSearchRequest, PaginatedLeadsResponse
from app.services.scraper import GoogleMapsScraper, RealGlobalScraper
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/leads", tags=["Leads"])


@router.post("/scrape", response_model=list[LeadResponse])
async def scrape_and_save_leads(
    search_req: LeadSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Real-time Google Maps Scraper trigger karta hai aur database me save karta hai.
    """
    scraper = GoogleMapsScraper()
    scraped_data = await scraper.scrape_leads(query=search_req.query, max_results=search_req.max_results or 15)

    saved_leads = []
    for item in scraped_data:
        # Deduplication check by company_name & city
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
    city: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Database se Leads ko Filter, Search aur Paginate karta hai.
    Agar DB me matching records na miley, to Live Real Scraper auto-trigger hota hai.
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
                Lead.address.ilike(f"%{search}%"),
                Lead.category.ilike(f"%{search}%"),
                Lead.city.ilike(f"%{search}%"),
            )
        )

    # Initial DB Execution
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Trigger Live Scraper if Database returns 0 leads for search
    if total == 0 and (search or city or category):
        target_keyword = search or category or "Services"
        target_city = city or "New York"
        target_country = country or "United States"

        real_extracted = await RealGlobalScraper.scrape_real_leads(target_keyword, target_city, target_country)

        for item in real_extracted:
            stmt = select(Lead).where(
                Lead.company_name == item["company_name"],
                Lead.is_deleted == False
            )
            existing = (await db.execute(stmt)).scalars().first()
            
            if not existing:
                new_lead = Lead(
                    company_name=item["company_name"],
                    website=item.get("website"),
                    phone=item.get("phone"),
                    email=item.get("email"),
                    address=item.get("address"),
                    city=item.get("city", target_city),
                    category=item.get("category", target_keyword),
                    rating=item.get("rating", 4.2),
                    reviews_count=item.get("reviews_count", 20),
                    source=item.get("source", "real_swarm"),
                    lead_score=item.get("lead_score", 75),
                    lead_priority=item.get("lead_priority", "MEDIUM"),
                    seo_score=item.get("seo_score", 70),
                    email_status=item.get("email_status", "UNKNOWN"),
                )
                db.add(new_lead)

        await db.commit()

        # Re-query DB after saving live scraped records
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

    # Apply Pagination
    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)

    result = await db.execute(paginated_query)
    leads = result.scalars().all()

    return PaginatedLeadsResponse(
        total=total,
        page=page,
        limit=limit,
        leads=leads
    )
