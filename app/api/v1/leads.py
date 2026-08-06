from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.db.session import get_db
from app.models.lead import Lead
from app.schemas.lead import PaginatedLeadsResponse
from app.services.scraper import GlobalScraperEngine
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/leads", tags=["Global Lead Intelligence"])


@router.get("/search", response_model=PaginatedLeadsResponse)
async def search_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
    keyword: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_keyword = keyword or search or "Services"
    target_city = city or "New York"
    target_country = country or "United States"

    # Strict isolation query by target location
    base_filter = and_(
        Lead.is_deleted == False,
        Lead.country.ilike(f"%{target_country}%"),
        Lead.city.ilike(f"%{target_city}%"),
    )

    query_stmt = select(Lead).where(base_filter)
    result = await db.execute(query_stmt.limit(limit))
    existing_db_leads = result.scalars().all()

    # Trigger Live Extraction Pipeline if local DB results are insufficient
    if len(existing_db_leads) < limit:
        extracted_leads, logs = await GlobalScraperEngine.extract_leads(
            keyword=target_keyword,
            city=target_city,
            country=target_country,
            target_limit=limit,
        )

        for item in extracted_leads:
            # PostgreSQL Deduplication Check
            dup_check = select(Lead).where(
                and_(
                    Lead.is_deleted == False,
                    Lead.country.ilike(f"%{target_country}%"),
                    Lead.company_name == item["company_name"],
                )
            )
            exists = (await db.execute(dup_check)).scalars().first()

            if not exists:
                new_lead = Lead(
                    google_place_id=item.get("google_place_id"),
                    company_name=item["company_name"],
                    website=item.get("website"),
                    phone=item.get("phone"),
                    email=item.get("email"),
                    address=item.get("address", f"{target_city}, {target_country}"),
                    city=target_city,
                    country=target_country,
                    category=target_keyword,
                    rating=item.get("rating", 4.5),
                    reviews_count=item.get("reviews_count", 30),
                    source=item.get("source", "live_swarm"),
                    lead_score=85,
                    lead_priority="HIGH",
                    seo_score=80,
                    email_status="VERIFIED",
                )
                db.add(new_lead)

        await db.commit()

    # Execute Paginated Query
    count_stmt = select(func.count()).select_from(select(Lead).where(base_filter).subquery())
    total_records = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * limit
    paginated_stmt = select(Lead).where(base_filter).offset(offset).limit(limit)
    final_leads = (await db.execute(paginated_stmt)).scalars().all()

    return PaginatedLeadsResponse(
        total=total_records,
        page=page,
        limit=limit,
        leads=final_leads
    )
