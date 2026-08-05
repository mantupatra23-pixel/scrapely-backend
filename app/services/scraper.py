import asyncio
from typing import List, Dict, Any
from playwright.async_api import async_playwright
from app.config.settings import settings

class GoogleMapsScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape_leads(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        results = []
        async with async_playwright() as p:
            # Launch browser with stealth arguments
            browser = await p.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            search_url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
            await page.goto(search_url, timeout=60000)
            await page.wait_for_timeout(3000)

            # Scroll loop to load results
            listings_selector = 'a[href*="/maps/place/"]'
            scraped_count = 0

            while scraped_count < max_results:
                elements = await page.query_selector_all(listings_selector)
                if not elements:
                    break

                for el in elements[scraped_count:max_results]:
                    try:
                        parent = await el.evaluate_handle('node => node.closest("div.Nv2pk")')
                        
                        # Extract Name
                        title_el = await parent.query_selector('div.qBF1Pd')
                        name = await title_el.inner_text() if title_el else "N/A"

                        # Extract Rating & Reviews
                        rating_el = await parent.query_selector('span.MW43ne')
                        rating = float(await rating_el.inner_text()) if rating_el else None

                        # Extract Phone & Category
                        info_text = await parent.inner_text()
                        lines = [line.strip() for line in info_text.split('\n') if line.strip()]

                        results.append({
                            "company_name": name,
                            "rating": rating,
                            "category": query.split(" in ")[0] if " in " in query else "Business",
                            "city": query.split(" in ")[1] if " in " in query else "Unknown",
                            "address": lines[2] if len(lines) > 2 else None,
                            "phone": next((l for l in lines if l.startswith("+") or l.replace(" ", "").isdigit()), None),
                            "source": "google_maps"
                        })
                    except Exception as e:
                        continue

                scraped_count = len(results)
                if scraped_count >= max_results:
                    break

                # Scroll down
                await page.evaluate('document.querySelector("div[role=\'feed\']").scrollBy(0, 1000)')
                await page.wait_for_timeout(2000)

            await browser.close()
        return results
