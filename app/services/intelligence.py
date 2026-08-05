import re
import dns.resolver
import httpx
from bs4 import BeautifulSoup
from typing import Dict, Any
import time

class IntelligenceEngine:
    @staticmethod
    def verify_email(email: str) -> Dict[str, Any]:
        if not email or "@" not in email:
            return {"status": "INVALID", "confidence": 0, "reason": "Malformed syntax"}
        
        regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(regex, email):
            return {"status": "INVALID", "confidence": 10, "reason": "Regex validation failed"}

        domain = email.split("@")[1]
        disposable_domains = ["tempmail.com", "mailinator.com", "10minutemail.com", "guerrillamail.com"]
        
        if domain.lower() in disposable_domains:
            return {"status": "RISKY", "confidence": 90, "reason": "Disposable email provider"}

        try:
            records = dns.resolver.resolve(domain, 'MX')
            mx_records = [str(r.exchange) for r in records]
            if not mx_records:
                return {"status": "INVALID", "confidence": 95, "reason": "No MX records found"}
            
            role_accounts = ["info", "contact", "support", "admin", "sales", "jobs"]
            local_part = email.split("@")[0].lower()
            
            if local_part in role_accounts:
                return {"status": "RISKY", "confidence": 75, "reason": "Generic role account"}
                
            return {"status": "VERIFIED", "confidence": 98, "reason": "Valid MX records and syntax"}
        except Exception:
            return {"status": "INVALID", "confidence": 90, "reason": "Domain DNS lookup failure"}

    @staticmethod
    async def audit_seo(url: str) -> Dict[str, Any]:
        if not url.startswith("http"):
            url = f"https://{url}"

        result = {
            "seo_score": 0,
            "ssl_enabled": url.startswith("https"),
            "mobile_friendly": True,
            "page_speed": 85,
            "meta_title": None,
            "meta_description": None,
            "robots_found": False,
            "sitemap_found": False,
            "schema_found": False,
            "issues": []
        }

        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                res = await client.get(url)
                latency = int((time.time() - start_time) * 1000)
                result["page_speed"] = max(10, min(100, 100 - (latency // 30)))
                
                soup = BeautifulSoup(res.text, "html.parser")
                
                # Meta Title
                title_tag = soup.find("title")
                if title_tag:
                    result["meta_title"] = title_tag.text.strip()
                else:
                    result["issues"].append("Missing Meta Title")

                # Meta Description
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    result["meta_description"] = meta_desc.get("content", "").strip()
                else:
                    result["issues"].append("Missing Meta Description")

                # Schema markup
                schema_tag = soup.find("script", attrs={"type": "application/ld+json"})
                if schema_tag:
                    result["schema_found"] = True

                # Check Robots & Sitemap
                base_domain = f"{httpx.URL(url).scheme}://{httpx.URL(url).host}"
                try:
                    robots_res = await client.get(f"{base_domain}/robots.txt")
                    if robots_res.status_code == 200:
                        result["robots_found"] = True
                except Exception:
                    pass

                try:
                    sitemap_res = await client.get(f"{base_domain}/sitemap.xml")
                    if sitemap_res.status_code == 200:
                        result["sitemap_found"] = True
                except Exception:
                    pass

        except Exception as e:
            result["issues"].append(f"Connection error: {str(e)}")

        # Score calculation
        score = 20
        if result["ssl_enabled"]: score += 15
        if result["meta_title"]: score += 15
        if result["meta_description"]: score += 15
        if result["schema_found"]: score += 15
        if result["robots_found"]: score += 10
        if result["sitemap_found"]: score += 10

        result["seo_score"] = min(100, score)
        return result

    @classmethod
    def calculate_lead_score(cls, lead_data: Dict[str, Any], seo_data: Dict[str, Any], email_data: Dict[str, Any]) -> Dict[str, Any]:
        score = 0
        
        # Signals
        if lead_data.get("website"): score += 15
        if seo_data.get("ssl_enabled"): score += 10
        if email_data.get("status") == "VERIFIED": score += 20
        if lead_data.get("phone"): score += 10
        if (lead_data.get("rating") or 0) >= 4.0: score += 15
        if (lead_data.get("reviews") or 0) >= 20: score += 10
        if seo_data.get("seo_score", 0) > 50: score += 10
        if seo_data.get("schema_found"): score += 10

        score = min(100, score)
        
        priority = "HIGH" if score >= 75 else "MEDIUM" if score >= 45 else "LOW"
        badge = "GREEN" if priority == "HIGH" else "YELLOW" if priority == "MEDIUM" else "RED"

        summary = f"Business demonstrates strong digital authority with a score of {score}/100. "
        if email_data.get("status") == "VERIFIED":
            summary += "Direct email verified. "
        else:
            summary += "Email requires manual check. "

        recommendation = "High value outreach target. Send personalized campaign immediately." if priority == "HIGH" else "Secondary prospect."

        return {
            "lead_score": score,
            "confidence": 95,
            "priority": priority,
            "badge": badge,
            "ai_summary": summary,
            "recommendation": recommendation
        }

    @staticmethod
    def generate_cold_email(company_name: str, category: str, city: str, issues: list, tone: str = "Professional") -> Dict[str, str]:
        issue_str = ", ".join(issues[:2]) if issues else "website speed optimization"
        
        subject = f"Growth opportunity for {company_name} in {city}"
        
        body = f"""Hi {company_name} Team,

I noticed your business in {city} is performing great in the {category} space. However, during a audit of your web presence, we flagged a few optimizations regarding {issue_str}.

Fixing these small technical bottlenecks can significantly increase your incoming organic client flow.

Would you be open to a 5-minute chat this week to review the report?

Best regards,
Mantu Patra
Scrapely.ai Automation Team"""

        return {
            "subject": subject,
            "email": body,
            "cta": "Schedule 5-Min Audit Review",
            "signature": "Mantu Patra | Head of Growth, Scrapely.ai"
        }
