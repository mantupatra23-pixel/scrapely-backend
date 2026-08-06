import asyncio
import re
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
import httpx
from bs4 import BeautifulSoup
from app.config.settings import settings


class EnterpriseScraperEngine:
    SUPPORTED_COUNTRIES = {
        "United States": {"code": "US", "gl": "us", "hl": "en", "tld": "com", "prefix": "+1"},
        "India": {"code": "IN", "gl": "in", "hl": "en", "tld": "co.in", "prefix": "+91"},
        "United Kingdom": {"code": "GB", "gl": "uk", "hl": "en", "tld": "co.uk", "prefix": "+44"},
        "Canada": {"code": "CA", "gl": "ca", "hl": "en", "tld": "ca", "prefix": "+1"},
        "Australia": {"code": "AU", "gl": "au", "hl": "en", "tld": "com.au", "prefix": "+61"},
    }

    @classmethod
    async def run_live_pipeline(
        cls, keyword: str, city: str, country: str, limit: int = 20
    ) -> List[Dict[str, Any]]:
        country_cfg = cls.SUPPORTED_COUNTRIES.get(country)
        if not country_cfg:
            return []

        # Step 1: Geocoding Validation
        coords = await cls._geocode_location(city, country, country_cfg)
        
        # Step 2: Primary Search - Google Places API
        raw_places = await cls._fetch_google_places(keyword, city, country, country_cfg, limit, coords)

        # Step 3: Secondary Fallback - OpenStreetMap Overpass (Strictly Live Entities Only)
        if len(raw_places) < limit:
            osm_places = await cls._fetch_overpass_osm(keyword, city, country, country_cfg, limit - len(raw_places))
            raw_places.extend(osm_places)

        if not raw_places:
            return []

        # Step 4: Live Verification, SEO Audit, and Lead Scoring
        enriched_leads = []
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            tasks = [cls._enrich_place_entity(client, place, country_cfg) for place in raw_places[:limit]]
            enriched_leads = await asyncio.gather(*tasks)

        # Deduplicate results based on google_place_id or website
        return cls._deduplicate(enriched_leads)

    @classmethod
    async def _geocode_location(
        cls, city: str, country: str, country_cfg: dict
    ) -> Optional[Tuple[float, float]]:
        if not getattr(settings, "GOOGLE_MAPS_API_KEY", None):
            return None
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": f"{city}, {country}",
            "key": settings.GOOGLE_MAPS_API_KEY,
            "region": country_cfg["gl"]
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    results = res.json().get("results", [])
                    if results:
                        loc = results[0]["geometry"]["location"]
                        return loc["lat"], loc["lng"]
        except Exception:
            pass
        return None

    @classmethod
    async def _fetch_google_places(
        cls, keyword: str, city: str, country: str, country_cfg: dict, limit: int, coords: Optional[Tuple[float, float]]
    ) -> List[Dict[str, Any]]:
        if not getattr(settings, "GOOGLE_MAPS_API_KEY", None):
            return []

        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{keyword} in {city}, {country}",
            "key": settings.GOOGLE_MAPS_API_KEY,
            "language": country_cfg["hl"],
            "region": country_cfg["gl"],
        }
        if coords:
            params["location"] = f"{coords[0]},{coords[1]}"
            params["radius"] = "25000"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    data = res.json()
                    results = []
                    for item in data.get("results", []):
                        # Strict City Matching Check
                        formatted_addr = item.get("formatted_address", "")
                        if city.lower() not in formatted_addr.lower() and country.lower() not in formatted_addr.lower():
                            continue

                        results.append({
                            "google_place_id": item.get("place_id"),
                            "company_name": item.get("name"),
                            "address": formatted_addr,
                            "latitude": item.get("geometry", {}).get("location", {}).get("lat"),
                            "longitude": item.get("geometry", {}).get("location", {}).get("lng"),
                            "google_rating": item.get("rating", 0.0),
                            "reviews_count": item.get("user_ratings_total", 0),
                            "primary_category": keyword.title(),
                            "city": city,
                            "country": country,
                            "google_maps_url": f"https://www.google.com/maps/place/?q=place_id:{item.get('place_id')}",
                        })
                        if len(results) >= limit:
                            break
                    return results
        except Exception:
            pass
        return []

    @classmethod
    async def _fetch_overpass_osm(
        cls, keyword: str, city: str, country: str, country_cfg: dict, limit: int
    ) -> List[Dict[str, Any]]:
        url = "https://overpass-api.de/api/interpreter"
        query = f"""
        [out:json][timeout:15];
        area["name"="{city}"]->.searchArea;
        (
          node["name"](area.searchArea);
          way["name"](area.searchArea);
        );
        out body {limit * 2};
        """
        results = []
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.post(url, data={"data": query})
                if res.status_code == 200:
                    for el in res.json().get("elements", []):
                        tags = el.get("tags", {})
                        name = tags.get("name")
                        if not name:
                            continue
                        results.append({
                            "google_place_id": f"osm_{el.get('id')}",
                            "company_name": name,
                            "address": f"{tags.get('addr:street', '')} {city}, {country}".strip(),
                            "website": tags.get("website"),
                            "phone": tags.get("phone"),
                            "city": city,
                            "country": country,
                            "primary_category": keyword.title(),
                            "google_rating": 0.0,
                            "reviews_count": 0,
                        })
                        if len(results) >= limit:
                            break
        except Exception:
            pass
        return results

    @classmethod
    async def _enrich_place_entity(
        cls, client: httpx.AsyncClient, place: Dict[str, Any], country_cfg: dict
    ) -> Dict[str, Any]:
        # Step A: Fetch Live Details from Place Details API
        if not place["google_place_id"].startswith("osm_"):
            place = await cls._fetch_google_place_details(client, place)

        website = place.get("website")
        phone = place.get("phone")

        # Step B: Live Email Discovery (Hunter.io API -> Web Crawl)
        verified_email = None
        email_status = "NOT_FOUND"

        if website:
            verified_email = await cls._discover_hunter_email(client, website)
            if not verified_email:
                verified_email = await cls._crawl_website_email(client, website)

            if verified_email:
                email_status = await cls._verify_email_mx(verified_email)
            else:
                email_status = "NOT_FOUND"

        # Step C: Live SEO & Technical Audit
        seo_audit = await cls._audit_website_seo(client, website) if website else {"seo_score": 0, "ssl": False}

        place["verified_email"] = verified_email
        place["email_status"] = email_status
        place["seo_score"] = seo_audit.get("seo_score", 0)
        place["seo_audit_details"] = seo_audit
        place["lead_score"] = cls._compute_lead_score(place, seo_audit)

        return place

    @classmethod
    async def _fetch_google_place_details(cls, client: httpx.AsyncClient, place: dict) -> dict:
        if not getattr(settings, "GOOGLE_MAPS_API_KEY", None):
            return place

        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place["google_place_id"],
            "fields": "formatted_phone_number,international_phone_number,website,opening_hours,business_status,url",
            "key": settings.GOOGLE_MAPS_API_KEY,
        }
        try:
            res = await client.get(url, params=params)
            if res.status_code == 200:
                result = res.json().get("result", {})
                place["website"] = result.get("website") or place.get("website")
                place["phone"] = result.get("international_phone_number") or result.get("formatted_phone_number") or place.get("phone")
                place["business_status"] = result.get("business_status", "OPERATIONAL")
                place["google_maps_url"] = result.get("url") or place.get("google_maps_url")
                place["opening_hours"] = result.get("opening_hours")
        except Exception:
            pass
        return place

    @classmethod
    async def _discover_hunter_email(cls, client: httpx.AsyncClient, website: str) -> Optional[str]:
        api_key = getattr(settings, "HUNTER_IO_API_KEY", None)
        if not api_key:
            return None
        domain = urllib.parse.urlparse(website).netloc.replace("www.", "")
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={api_key}"
        try:
            res = await client.get(url)
            if res.status_code == 200:
                emails = res.json().get("data", {}).get("emails", [])
                if emails:
                    return emails[0].get("value")
        except Exception:
            pass
        return None

    @classmethod
    async def _crawl_website_email(cls, client: httpx.AsyncClient, website: str) -> Optional[str]:
        try:
            res = await client.get(website, timeout=5.0)
            if res.status_code == 200:
                emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", res.text)
                clean_emails = [
                    e for e in emails 
                    if not any(x in e.lower() for x in ["png", "jpg", "svg", "wixpress", "sentry"])
                ]
                if clean_emails:
                    return clean_emails[0]
        except Exception:
            pass
        return None

    @classmethod
    async def _verify_email_mx(cls, email: str) -> str:
        domain = email.split("@")[-1]
        try:
            proc = await asyncio.create_subprocess_exec(
                "nslookup", "-type=MX", domain,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await proc.communicate()
            if "mail exchanger" in stdout.decode().lower():
                return "VERIFIED"
        except Exception:
            pass
        return "RISKY"

    @classmethod
    async def _audit_website_seo(cls, client: httpx.AsyncClient, website: str) -> dict:
        audit = {"ssl": website.startswith("https"), "has_title": False, "has_meta": False, "seo_score": 0}
        try:
            res = await client.get(website, timeout=5.0)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                audit["has_title"] = bool(soup.find("title"))
                audit["has_meta"] = bool(soup.find("meta", attrs={"name": "description"}))
                
                score = 30
                if audit["ssl"]: score += 30
                if audit["has_title"]: score += 20
                if audit["has_meta"]: score += 20
                audit["seo_score"] = score
        except Exception:
            audit["seo_score"] = 20 if audit["ssl"] else 0
        return audit

    @staticmethod
    def _compute_lead_score(place: dict, seo_audit: dict) -> int:
        score = 0
        if place.get("website"): score += 25
        if place.get("verified_email"): score += 35
        if place.get("phone"): score += 15
        if place.get("google_rating", 0) >= 4.0: score += 15
        if seo_audit.get("seo_score", 0) >= 50: score += 10
        return min(score, 100)

    @staticmethod
    def _deduplicate(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        deduped = []
        for r in records:
            key = r.get("google_place_id") or r.get("website") or r.get("company_name", "").lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(r)
        return deduped
