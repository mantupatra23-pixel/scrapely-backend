import os
import asyncio
from celery import Celery
from app.services.intelligence import IntelligenceEngine

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery("scrapely_workers", broker=REDIS_URL, backend=REDIS_URL)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="tasks.process_lead_intelligence")
def process_lead_intelligence_task(lead_id: str, company_name: str, website: str, email: str, phone: str):
    """
    Background job triggered automatically after scraping a business lead.
    """
    loop = asyncio.get_event_loop()
    
    # 1. Run Email Verification
    email_res = IntelligenceEngine.verify_email(email) if email else {"status": "UNKNOWN"}
    
    # 2. Run Async SEO Audit
    seo_res = loop.run_until_complete(IntelligenceEngine.audit_seo(website)) if website else {"seo_score": 0}
    
    # 3. Calculate Composite Lead Score
    lead_data = {"company_name": company_name, "website": website, "email": email, "phone": phone}
    score_res = IntelligenceEngine.calculate_lead_score(lead_data, seo_res, email_res)
    
    return {
        "lead_id": lead_id,
        "email_verification": email_res,
        "seo_audit": seo_res,
        "intelligence": score_res
    }
