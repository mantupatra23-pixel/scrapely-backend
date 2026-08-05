from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional, List
from app.services.intelligence import IntelligenceEngine
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/intelligence", tags=["AI Intelligence Engine"])

class EmailVerifyRequest(BaseModel):
    email: str

class SeoAuditRequest(BaseModel):
    url: str

class ColdEmailRequest(BaseModel):
    company_name: str
    category: Optional[str] = "Business"
    city: Optional[str] = "New Delhi"
    issues: Optional[List[str]] = []
    tone: Optional[str] = "Professional"

class LeadScoreRequest(BaseModel):
    company_name: str
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = 0.0
    reviews: Optional[int] = 0

@router.post("/email-verify")
async def verify_email_endpoint(payload: EmailVerifyRequest, current_user = Depends(get_current_user)):
    return IntelligenceEngine.verify_email(payload.email)

@router.post("/seo-audit")
async def seo_audit_endpoint(payload: SeoAuditRequest, current_user = Depends(get_current_user)):
    return await IntelligenceEngine.audit_seo(payload.url)

@router.post("/generate-email")
async def generate_email_endpoint(payload: ColdEmailRequest, current_user = Depends(get_current_user)):
    return IntelligenceEngine.generate_cold_email(
        company_name=payload.company_name,
        category=payload.category,
        city=payload.city,
        issues=payload.issues,
        tone=payload.tone
    )

@router.post("/lead-score")
async def calculate_lead_score_endpoint(payload: LeadScoreRequest, current_user = Depends(get_current_user)):
    seo_res = await IntelligenceEngine.audit_seo(payload.website) if payload.website else {"seo_score": 0, "issues": []}
    email_res = IntelligenceEngine.verify_email(payload.email) if payload.email else {"status": "UNKNOWN"}
    
    lead_data = payload.model_dump()
    intelligence = IntelligenceEngine.calculate_lead_score(lead_data, seo_res, email_res)
    
    return {
        "intelligence": intelligence,
        "seo_audit": seo_res,
        "email_verification": email_res
    }
