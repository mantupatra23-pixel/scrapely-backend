import os
import json
from typing import Dict, Any
import httpx


class AIIntelligenceEngine:
    
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

    @classmethod
    async def generate_lead_insights(cls, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        
        company = lead_data.get("company_name", "Target Business")
        city = lead_data.get("city", "their area")
        category = lead_data.get("primary_category", "Services")
        rating = lead_data.get("google_rating", 0.0)
        reviews = lead_data.get("reviews_count", 0)
        website = lead_data.get("website", "")
        cms = lead_data.get("cms", "Website")

        # Deterministic Score Calculation
        opportunity_score = 95 if (rating < 4.2 or reviews < 30) else 75
        buyer_intent = "HIGH" if (website and rating >= 4.0) else "MEDIUM"

        # If Groq Key is available, invoke Groq LLaMA-3.3-70b-versatile for ultra-fast generation
        if groq_key:
            try:
                prompt = f"""
                You are a senior B2B Sales Strategist. Analyze this business lead and return a JSON object with 3 keys:
                - cold_email: A short, high-converting cold email pitch.
                - linkedin_msg: A crisp 2-sentence connection request.
                - sales_script: A 3-step phone cold call script (Opener, Hook, Call-to-action).

                Lead Info:
                Company: {company}
                Category: {category}
                City: {city}
                Rating: {rating} stars ({reviews} reviews)
                CMS/Tech: {cms}
                """

                headers = {
                    "Authorization": f"Bearer {groq_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5,
                    "response_format": {"type": "json_object"}
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    res = await client.post(cls.GROQ_API_URL, headers=headers, json=payload)
                    if res.status_code == 200:
                        ai_response = json.loads(res.json()["choices"][0]["message"]["content"])
                        return {
                            "ai_opportunity_score": opportunity_score,
                            "ai_buyer_intent": buyer_intent,
                            "ai_summary": f"{company} is a prominent {category} operator in {city}. Groq AI identified tech stack conversion gaps.",
                            "cold_email_draft": ai_response.get("cold_email"),
                            "linkedin_message_draft": ai_response.get("linkedin_msg"),
                            "sales_script_draft": ai_response.get("sales_script"),
                            "recommended_outreach_channel": "Email + Phone" if lead_data.get("verified_email") else "Direct Call"
                        }
            except Exception as e:
                print(f"[Groq AI Engine Fallback]: {e}")

        # Static Fallback Engine (Zero latency fallback)
        return {
            "ai_opportunity_score": opportunity_score,
            "ai_buyer_intent": buyer_intent,
            "ai_summary": f"{company} is a key {category} in {city}. High conversion potential via automated local SEO optimization.",
            "cold_email_draft": f"Subject: Optimization for {company}\n\nHi {company} team,\n\nI noticed your {rating}★ rating in {city}. We can help optimize your {cms} setup to convert more traffic.\n\nBest regards,",
            "linkedin_message_draft": f"Hi {company} team, loved seeing your {reviews} reviews in {city}. Would love to connect!",
            "sales_script_draft": f"Opener: Hi, calling for {company} in {city}.\nHook: Noticed your strong local reviews.\nCTA: Can I send our 1-page tech audit?",
            "recommended_outreach_channel": "Direct Call"
        }
