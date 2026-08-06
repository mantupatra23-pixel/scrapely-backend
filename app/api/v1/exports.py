import io
import pandas as pd
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import Lead
from app.auth.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/exports", tags=["Exports"])


@router.get("/csv")
async def export_leads_csv(
    city: str = Query(None),
    category: str = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Lead).where(Lead.is_deleted == False)
    if city:
        query = query.where(Lead.city.ilike(f"%{city}%"))
    if category:
        query = query.where(
            (Lead.primary_category.ilike(f"%{category}%"))
            | (Lead.company_name.ilike(f"%{category}%"))
        )

    result = await db.execute(query)
    leads = result.scalars().all()

    # Convert to DataFrame
    data = [
        {
            "Company Name": l.company_name,
            "Phone": l.phone or "",
            "Email": getattr(l, "verified_email", None) or getattr(l, "email", "") or "",
            "Email Status": getattr(l, "email_status", "UNKNOWN"),
            "Address": l.address or "",
            "City": l.city,
            "Country": getattr(l, "country", ""),
            "Category": getattr(l, "primary_category", None) or getattr(l, "category", "") or "",
            "Rating": getattr(l, "google_rating", None) or getattr(l, "rating", 0.0),
            "Lead Score": getattr(l, "lead_score", 0),
            "Website": l.website or "",
        }
        for l in leads
    ]

    df = pd.DataFrame(data)
    stream = io.StringIO()
    df.to_csv(stream, index=False)

    return Response(
        content=stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leads_export.csv"},
    )
