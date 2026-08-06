import os
from typing import Dict, Any
import httpx


class AIIntelligenceEngine:
    
    @classmethod
    async def generate_lead_insights(cls, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        company = lead_data.get("company_name", "Target Business")
        city = lead_data.get("city", "their area")
        category = lead_data.get("primary_category", "Services")
        rating = lead_data.get("google_rating", 0.0)
        reviews = lead_data.get("reviews_count", 0)
        cms = lead_data.get("cms", "Website")
        
        # Calculate AI Scores Deterministically
        opportunity_score = 95 if (rating < 4.2 or reviews < 25) else 70
        buyer_intent = "HIGH" if (lead_data.get("website") and rating >= 4.0) else "MEDIUM"
        
        # Cold Email Sequence Draft
        cold_email = f"""Subject: Quick question regarding {company}'s digital presence in {city}

Hi {company} Team,

I noticed {company} has built a solid local reputation in {city} with a {rating}★ rating across {reviews} reviews. 

However, looking at your technical infrastructure ({cms}), there are a few optimization opportunities that could help you convert more local search traffic into booked clients.

We recently helped a similar {category} provider scale their online bookings by 35% without increasing ad spend.

Are you open to a brief 5-minute chat this Thursday?

Best regards,
Scrapely Intelligence Team"""

        # LinkedIn Message Draft
        linkedin_msg = f"Hi {company} Team, came across your {rating}★ rated {category} business in {city}. Impressive local footprint! Would love to connect and share a quick technical audit we generated for your site."

        # Sales Call Script
        sales_script = f"""[OPENER]: "Hi, this is calling regarding {company}'s online listing in {city}. Am I speaking with the business owner?"
[VALUE PROP]: "I was reviewing {category} providers in {city} and noticed your {reviews} Google reviews. Your rating is strong, but your site is missing conversion elements."
[HOOK]: "We generated an automated SEO & Tech Audit for {company}. Can I send this 1-page report over to your email?"""

        return {
            "ai_opportunity_score": opportunity_score,
            "ai_buyer_intent": buyer_intent,
            "ai_summary": f"{company} is a leading {category} provider in {city}. Technical analysis indicates high growth potential via conversion rate optimization.",
            "cold_email_draft": cold_email,
            "linkedin_message_draft": linkedin_msg,
            "sales_script_draft": sales_script,
            "recommended_outreach_channel": "Email + Phone Followup" if lead_data.get("verified_email") else "Direct Call"
        }
