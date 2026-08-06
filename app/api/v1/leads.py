import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.db.session import get_db
from app.models.enterprise_lead import Lead, EmailValidationStatus
from app.schemas.lead import PaginatedLeadsResponse
from app.services.enterprise_scraper import EnterpriseScraperEngine

router = APIRouter(prefix="/leads", tags=["Enterprise Intelligence Pipeline"])


@router.get("/search", response_model=PaginatedLeadsResponse)
async def search_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=500),
    keyword: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    target_keyword = keyword.strip() if keyword else "Services"
    target_city = city.strip() if city else "New York"
    target_country = country.strip() if country else "United States"

    # Strict multi-parameter country & city isolation filter
    base_filter = and_(
        Lead.is_deleted == False,
        Lead.country.ilike(f"%{target_country}%"),
        Lead.city.ilike(f"%{target_city}%"),
        or_(
            Lead.primary_category.ilike(f"%{target_keyword}%"),
            Lead.company_name.ilike(f"%{target_keyword}%")
        )
    )

    query_stmt = select(Lead).where(base_filter)
    result = await db.execute(query_stmt.limit(limit))
    existing_db_leads = result.scalars().all()

    # Trigger Live Multi-Source Extraction if local isolated DB records are lower than limit
    if len(existing_db_leads) < limit:
        extracted_leads = await EnterpriseScraperEngine.run_live_pipeline(
            keyword=target_keyword,
            city=target_city,
            country=target_country,
            limit=limit,
        )

        for item in extracted_leads:
            dup_check = select(Lead).where(
                and_(
                    Lead.is_deleted == False,
                    Lead.google_place_id == item["google_place_id"]
                )
            )
            exists = (await db.execute(dup_check)).scalars().first()

            if not exists:
                new_lead = Lead(
                    id=uuid.uuid4(),
                    google_place_id=item["google_place_id"],
                    company_name=item["company_name"],
                    website=item.get("website"),
                    phone=item.get("phone"),
                    verified_email=item.get("verified_email"),
                    email_status=item.get("email_status", EmailValidationStatus.UNKNOWN),
                    address=item.get("address"),
                    city=target_city,
                    country=target_country,
                    latitude=item.get("latitude"),
                    longitude=item.get("longitude"),
                    google_rating=item.get("google_rating", 0.0),
                    reviews_count=item.get("reviews_count", 0),
                    primary_category=target_keyword.title(),
                    google_maps_url=item.get("google_maps_url"),
                    seo_score=item.get("seo_score", 0),
                    lead_score=item.get("lead_score", 0)
                )
                db.add(new_lead)

        await db.commit()

    # Query filtered live persisted records
    count_stmt = select(func.count()).select_from(select(Lead).where(base_filter).subquery())
    total_records = (await db.execute(count_stmt)).scalar_one()

    offset = (page - 1) * limit
    paginated_stmt = select(Lead).where(base_filter).offset(offset).limit(limit)
    final_leads = (await db.execute(paginated_stmt)).scalars().all()

    return PaginatedLeadsResponse(
        total=total_records,
        page=page,
        limit=limit,
        leads=final_leads,
    )
