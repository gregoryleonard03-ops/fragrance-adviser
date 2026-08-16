"""
One-time scraper: scentrique.us (Shopify) → data/fragrances_scentrique.json

Polite by design (cold-demo, no relationship with the store):
- sequential, 1.5s delay between network requests
- honest User-Agent
- disk cache: every response saved to data/scentrique_cache/, re-runs read from disk
- stops on 429/5xx instead of retrying

Notes (top/middle/base) are NOT available anywhere on the site (checked
body_html and rendered HTML — notes render via a JS widget from an external
app). Signal for matching = tags (families + notes + gender + season),
product_type, body_html description.

Usage: cd backend && python3 scrape_scentrique.py
"""
from __future__ import annotations

import json
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://www.scentrique.us"
UA = "AromaMatch-catalog-bot/1.0 (contact: gregoryleonard03@icloud.com)"
DELAY = 1.5

DATA_DIR = Path(__file__).parent / "data"
CACHE_DIR = DATA_DIR / "scentrique_cache"
OUT_PATH = DATA_DIR / "fragrances_scentrique.json"

# tags that are navigation/marketing, not scent signal — dropped from output
NOISE_TAGS = re.compile(
    r"^(all products|fragrances|best sellers|new arrivals?|gifts? .*|vday|"
    r"father's day.*|mother's day.*|.*promo.*|sale|discovery.*|sample.*)$",
    re.I,
)


def fetch(url: str, cache_name: str) -> str | None:
    """Fetch with disk cache. Returns text or None on 404. Exits on 429/5xx."""
    cache_file = CACHE_DIR / cache_name
    if cache_file.exists():
        return cache_file.read_text()
    time.sleep(DELAY)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            text = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"  404: {url}")
            return None
        print(f"STOP: HTTP {e.code} on {url} — not retrying (polite mode)")
        sys.exit(1)
    cache_file.write_text(text)
    return text


def get_handles() -> list[str]:
    index = fetch(BASE + "/sitemap.xml", "sitemap_index.xml")
    m = re.search(r"<loc>([^<]*sitemap_products_1\.xml[^<]*)</loc>", index)
    url = m.group(1).replace("&amp;", "&")
    sitemap = fetch(url, "sitemap_products.xml")
    handles = re.findall(r"<loc>%s/products/([^<]+)</loc>" % re.escape(BASE), sitemap)
    return sorted(set(handles))


def strip_html(html: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


# not wearable perfume → excluded from the quiz catalog
EXCLUDE_TAGS = {
    "candle", "candles & home scents", "reed diffuser",
    "body care", "body lotion", "gift boxes", "gift card",
    "discovery sets", "samples & discovery sets",
}


def parse_product(p: dict) -> dict | None:
    raw_tags = [t.strip() for t in p.get("tags", "").split(",")] \
        if isinstance(p.get("tags"), str) else list(p.get("tags") or [])
    haystack = {t.lower() for t in raw_tags} | {p.get("product_type", "").lower()}
    title_l = p["title"].lower()
    if haystack & EXCLUDE_TAGS or "discovery set" in title_l or "gift card" in title_l:
        return None

    variants = [
        {"title": v["title"], "price": float(v["price"])}
        for v in p.get("variants", [])
        if v.get("price")
    ]
    if not variants:
        return None

    def ml(v):
        m = re.search(r"([\d.]+)\s*ml", v["title"], re.I)
        return float(m.group(1)) if m else None

    variants = [v for v in variants if v["price"] > 0]
    if not variants:  # $0 = event tickets / placeholders
        return None
    sized = [(ml(v), v) for v in variants]
    full = max(sized, key=lambda x: (x[0] is not None, x[0] or 0, x[1]["price"]))[1]
    samples = [v for s, v in sized if s is not None and s <= 8]
    sample = min(samples, key=lambda v: v["price"]) if samples else None

    tags = [t.strip() for t in p.get("tags", "").split(",") if t.strip()] \
        if isinstance(p.get("tags"), str) else list(p.get("tags") or [])
    scent_tags = [t for t in tags if not NOISE_TAGS.match(t)]

    return {
        "name": re.sub(r"\s+by\s+.*$", "", p["title"], flags=re.I).strip() or p["title"],
        "brand": p.get("vendor", ""),
        "price": full["price"],
        "sample_price": sample["price"] if sample else None,
        "sample_size": sample["title"] if sample else None,
        "url": f"{BASE}/products/{p['handle']}",
        "image_url": (p.get("images") or [{}])[0].get("src", ""),
        "top_notes": "", "middle_notes": "", "base_notes": "",
        "description": strip_html(p.get("body_html", ""))[:1000],
        "tags": scent_tags,
        "product_type": p.get("product_type", ""),
    }


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    handles = get_handles()
    print(f"{len(handles)} handles in sitemap")

    items, skipped = [], []
    for i, h in enumerate(handles, 1):
        text = fetch(f"{BASE}/products/{h}.json", f"{h}.json")
        if text is None:
            skipped.append(h)
            continue
        try:
            product = json.loads(text)["product"]
        except (json.JSONDecodeError, KeyError):
            print(f"  bad JSON: {h}")
            skipped.append(h)
            continue
        item = parse_product(product)
        if item:
            items.append(item)
        else:
            skipped.append(h)
        if i % 50 == 0:
            print(f"  {i}/{len(handles)}")

    OUT_PATH.write_text(json.dumps(items, ensure_ascii=False, indent=1))
    print(f"\nwrote {len(items)} items → {OUT_PATH}")
    if skipped:
        print(f"skipped {len(skipped)}: {skipped[:10]}{'...' if len(skipped) > 10 else ''}")

    with_tags = sum(1 for x in items if x["tags"])
    with_sample = sum(1 for x in items if x["sample_price"] is not None)
    print(f"with scent tags: {with_tags}, with sample variant: {with_sample}")


if __name__ == "__main__":
    main()
