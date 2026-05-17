"""
Sephora fragrance scraper.
Run once: python3 scraper.py
Saves results to data/fragrances.json
"""

import asyncio
import json
import random
import re
import time
from pathlib import Path

from playwright.async_api import async_playwright

OUTPUT = Path(__file__).parent / "data" / "fragrances.json"
TARGET_COUNT = 120
CATEGORY_URL = "https://www.sephora.com/shop/fragrance"


async def scrape_product(page, url: str) -> dict | None:
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(1500, 2500))

        data = {}

        # Name
        name_el = await page.query_selector('h1[data-comp="DisplayName"]')
        if not name_el:
            name_el = await page.query_selector("h1.css-1g2jq23")
        data["name"] = (await name_el.inner_text()).strip() if name_el else ""

        # Brand
        brand_el = await page.query_selector('a[data-comp="BrandName"]')
        if not brand_el:
            brand_el = await page.query_selector("span.css-euydo4")
        data["brand"] = (await brand_el.inner_text()).strip() if brand_el else ""

        # Price
        price_el = await page.query_selector('[data-comp="Price"]')
        price_text = (await price_el.inner_text()).strip() if price_el else ""
        match = re.search(r"\$(\d+(?:\.\d+)?)", price_text)
        data["price"] = float(match.group(1)) if match else 0.0

        # Description
        desc_el = await page.query_selector('[data-comp="Content"] p')
        if not desc_el:
            desc_el = await page.query_selector(".css-pz6utb p")
        data["description"] = (await desc_el.inner_text()).strip() if desc_el else ""

        # Notes — try to extract from ingredients/about section
        notes_els = await page.query_selector_all('[data-comp="Ingredients"] li, .css-1iivs0v li')
        notes = [await el.inner_text() for el in notes_els[:12]]
        data["notes"] = [n.strip().lower() for n in notes if n.strip()]

        # If no structured notes, extract from description
        if not data["notes"] and data["description"]:
            note_section = re.findall(r"(?:notes? of|featuring|with)\s+([^.]+)", data["description"], re.IGNORECASE)
            if note_section:
                raw = note_section[0]
                data["notes"] = [n.strip().lower() for n in re.split(r",|and", raw) if n.strip()]

        # Image
        img_el = await page.query_selector('img[data-comp="Image"]')
        if not img_el:
            img_el = await page.query_selector(".css-1lmdzki img")
        data["image_url"] = await img_el.get_attribute("src") if img_el else ""

        data["url"] = url
        # Product ID from URL
        pid_match = re.search(r"-(P\d+)", url)
        data["id"] = pid_match.group(1) if pid_match else url.split("/")[-1]

        if data["name"] and data["brand"]:
            return data
    except Exception as e:
        print(f"  [!] Error scraping {url}: {e}")
    return None


async def get_product_urls(page) -> list[str]:
    """Scroll the category page and collect product links."""
    print(f"Opening {CATEGORY_URL} ...")
    await page.goto(CATEGORY_URL, wait_until="domcontentloaded", timeout=30000)
    await page.wait_for_timeout(3000)

    # Handle cookie/age banner if present
    for selector in ["button[data-at='age_gate_continue']", "button:has-text('Continue')", "#onetrust-accept-btn-handler"]:
        btn = await page.query_selector(selector)
        if btn:
            await btn.click()
            await page.wait_for_timeout(1000)
            break

    urls = set()
    scroll_attempts = 0
    max_scrolls = 40

    while len(urls) < TARGET_COUNT and scroll_attempts < max_scrolls:
        links = await page.query_selector_all('a[href*="/product/"]')
        for link in links:
            href = await link.get_attribute("href")
            if href and "/product/" in href and href not in urls:
                full = f"https://www.sephora.com{href}" if href.startswith("/") else href
                # Filter out non-fragrance or variant URLs
                if "?" not in full or "skuId" in full:
                    urls.add(full.split("?")[0])

        print(f"  Found {len(urls)} product URLs so far ...")

        # Scroll down
        await page.evaluate("window.scrollBy(0, 1200)")
        await page.wait_for_timeout(random.randint(1800, 3000))
        scroll_attempts += 1

    return list(urls)[:TARGET_COUNT]


async def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        page = await context.new_page()

        print("=== Step 1: Collecting product URLs ===")
        product_urls = await get_product_urls(page)
        print(f"Total URLs collected: {len(product_urls)}")

        print("\n=== Step 2: Scraping individual products ===")
        fragrances = []
        for i, url in enumerate(product_urls, 1):
            print(f"[{i}/{len(product_urls)}] {url}")
            result = await scrape_product(page, url)
            if result:
                fragrances.append(result)
                print(f"  ✓ {result['brand']} — {result['name']} (${result['price']})")
            await asyncio.sleep(random.uniform(2, 4))

        await browser.close()

    print(f"\n=== Done: {len(fragrances)} fragrances scraped ===")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(fragrances, f, ensure_ascii=False, indent=2)
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    asyncio.run(main())
