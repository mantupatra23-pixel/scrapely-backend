import uuid
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from app.db.session import get_db
from app.models.enterprise_lead import Lead, EmailStatusEnum, LeadPriorityEnum, BusinessStatusEnum
from app.schemas.lead import PaginatedLeadsResponse, LeadResponseSchema
from app.services.enterprise_scraper import EnterpriseScraperEngine
from app.services.tech_analyzer import TechnologyAnalyzerEngine

router = APIRouter(prefix="/leads", tags=["Lead Intelligence Engine"])


@router.get("/search", response_model=PaginatedLeadsResponse)
async def search_leads(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    postal_code: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0),
    min_reviews: Optional[int] = Query(None, ge=0),
    verified_only: bool = Query(False),
    has_website: bool = Query(False),
    has_email: bool = Query(False),
    has_phone: bool = Query(False),
    has_socials: bool = Query(False),
    sort_by: str = Query("lead_score_desc"),
    workspace_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
):
    target_keyword = (keyword or industry or "").strip()
    target_city = (city or "").strip()
    target_country = (country or "").strip()

    if not target_keyword or not target_country:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mandatory query parameters missing: 'keyword/industry' and 'country' are required."
        )

    # Build Dynamic Filter Tree
    filter_conditions = [
        Lead.is_deleted == False,
        Lead.workspace_id == workspace_id,
        Lead.country.ilike(f"%{target_country}%")
    ]

    if target_city:
        filter_conditions.append(Lead.city.ilike(f"%{target_city}%"))
    if state:
        filter_conditions.append(Lead.state.ilike(f"%{state}%"))
    if postal_code:
        filter_conditions.append(Lead.postal_code == postal_code)

    filter_conditions.append(
        or_(
            Lead.primary_category.ilike(f"%{target_keyword}%"),
            Lead.company_name.ilike(f"%{target_keyword}%")
        )
    )

    if min_rating is not None:
        filter_conditions.append(Lead.google_rating >= min_rating)
    if min_reviews is not None:
        filter_conditions.append(Lead.reviews_count >= min_reviews)
    if verified_only:
        filter_conditions.append(Lead.verified_email != None)
    if has_website:
        filter_conditions.append(Lead.website != None)
    if has_email:
        filter_conditions.append(Lead.verified_email != None)
    if has_phone:
        filter_conditions.append(Lead.phone != None)

    base_filter = and_(*filter_conditions)

    # Check database cache state
    query_stmt = select(Lead).where(base_filter)
    result = await db.execute(query_stmt.limit(limit))
    cached_leads = result.scalars().all()

    # Trigger Real-Time Multi-Tier Live Extraction Engine if Cache Incomplete
    if len(cached_leads) < limit:
        needed_count = limit - len(cached_leads)
        live_records = await EnterpriseScraperEngine.run_live_pipeline(
            keyword=target_keyword,
            city=target_city,
            country=target_country,
            limit=needed_count
        )

        for record in live_records:
            # Check Place Uniqueness within Workspace Isolation
            dup_stmt = select(Lead).where(
                and_(
                    Lead.workspace_id == workspace_id,
                    Lead.google_place_id == record["google_place_id"]
                )
            )
            exists = (await db.execute(dup_stmt)).scalar_one_or_none()

            if not exists:
                # Run Deep Domain Technical Analysis if website available
                tech_meta = {}
                if record.get("website"):
                    tech_meta = await TechnologyAnalyzerEngine.analyze_domain(record["website"])

                new_lead = Lead(
                    id=uuid.uuid4(),
                    workspace_id=workspace_id,
                    google_place_id=record["google_place_id"],
                    company_name=record["company_name"],
                    company_logo_url=record.get("company_logo_url"),
                    primary_category=target_keyword.title(),
                    source=record.get("source", "GOOGLE_MAPS"),
                    phone=record.get("phone"),
                    phone_formatted=record.get("phone"),
                    whatsapp_available=record.get("whatsapp_available", False),
                    verified_email=record.get("verified_email"),
                    email_status=record.get("email_status", EmailStatusEnum.NOT_FOUND),
                    email_source=record.get("email_source", "LIVE_SCRAPER"),
                    website=record.get("website"),
                    address=record.get("address"),
                    city=target_city or record.get("city"),
                    state=state or record.get("state"),
                    country=target_country,
                    postal_code=postal_code or record.get("postal_code"),
                    latitude=record.get("latitude"),
                    longitude=record.get("longitude"),
                    google_rating=record.get("google_rating", 0.0),
                    reviews_count=record.get("reviews_count", 0),
                    business_status=BusinessStatusEnum.OPERATIONAL,
                    opening_hours=record.get("opening_hours"),
                    google_maps_url=record.get("google_maps_url"),
                    social_profiles=record.get("social_profiles", {}),
                    
                    # Tech Metrics Integration
                    tech_stack=tech_meta.get("tech_stack", []),
                    ssl_status=tech_meta.get("ssl_status", False),
                    https_enabled=tech_meta.get("https_enabled", False),
                    cms=tech_meta.get("cms"),
                    hosting_provider=tech_meta.get("hosting_provider"),
                    pagespeed_score=tech_meta.get("pagespeed_score", 75),
                    mobile_friendly=tech_meta.get("mobile_friendly", True),
                    domain_authority=tech_meta.get("domain_authority", 20),
                    spam_score=tech_meta.get("spam_score", 1),
                    
                    seo_score=record.get("seo_score", 70),
                    lead_score=record.get("lead_score", 75),
                    ai_opportunity_score=record.get("ai_opportunity_score", 80),
                    lead_priority=LeadPriorityEnum.HIGH if record.get("verified_email") else LeadPriorityEnum.MEDIUM
                )
                db.add(new_lead)

        await db.commit()

    # Apply Sorting Strategies
    order_clause = Lead.lead_score.desc()
    if sort_by == "rating_desc":
        order_clause = Lead.google_rating.desc()
    elif sort_by == "reviews_desc":
        order_clause = Lead.reviews_count.desc()
    elif sort_by == "seo_score_asc":
        order_clause = Lead.seo_score.asc()

    # Execute Final Aggregation & Paginated Fetch
    count_stmt = select(func.count()).select_from(select(Lead.id).where(base_filter).subquery())
    total_records = (await db.execute(count_stmt)).scalar() or 0

    offset = (page - 1) * limit
    paginated_stmt = select(Lead).where(base_filter).order_by(order_clause).offset(offset).limit(limit)
    final_leads = (await db.execute(paginated_stmt)).scalars().all()

    return PaginatedLeadsResponse(
        total=total_records,
        page=page,
        limit=limit,
        leads=final_leads
    )
