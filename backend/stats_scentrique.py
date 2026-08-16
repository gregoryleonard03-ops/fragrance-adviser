"""Stage 0A acceptance: catalog stats + 3 sample recommendation runs."""
import json
from pathlib import Path

import matcher_db

items = json.loads((Path(__file__).parent / "data" / "fragrances_scentrique.json").read_text())

print(f"products: {len(items)}")
print(f"with price+url: {sum(1 for x in items if x['price'] and x['url'])}")
print(f"with scent tags: {sum(1 for x in items if x['tags'])}")
print(f"with notes (top/mid/base): {sum(1 for x in items if x['top_notes'] or x['middle_notes'] or x['base_notes'])}")
print(f"with description: {sum(1 for x in items if x['description'])}")
print(f"with sample variant: {sum(1 for x in items if x['sample_price'] is not None)}")
print(f"with image: {sum(1 for x in items if x['image_url'])}")
print(f"matched in 76k DB: {sum(1 for x in items if matcher_db._load_db_lookup().get(matcher_db._parfbar_key(x['brand'], x['name'])))}")

prices = sorted(x["price"] for x in items if x["price"])
n = len(prices)
print(f"\nfull-bottle price: min={prices[0]}, p25={prices[n//4]}, median={prices[n//2]}, "
      f"p75={prices[3*n//4]}, max={prices[-1]}")
brands = {}
for x in items:
    brands[x["brand"]] = brands.get(x["brand"], 0) + 1
print("brands:", dict(sorted(brands.items(), key=lambda kv: -kv[1])))

TESTS = [
    ("dark & seductive, evening", {
        "branch": "dark_sexy", "sub_type": ["leather"], "vibe": ["night_out"],
        "notes": ["oud", "tobacco"], "season": ["winter"], "occasion": ["date"], "budget": []}),
    ("fresh & clean, office", {
        "branch": "fresh_clean", "sub_type": ["citrus"], "vibe": ["luxury_hotel"],
        "notes": ["citrus", "marine"], "season": ["summer"], "occasion": ["office"], "budget": []}),
    ("warm gourmand, cozy", {
        "branch": "warm_cozy", "sub_type": ["vanilla_cream"], "vibe": ["cashmere_fireplace"],
        "notes": ["vanilla", "amber"], "season": ["autumn"], "occasion": ["cozy_evening"], "budget": []}),
]

for label, answers in TESTS:
    print(f"\n=== {label} ===")
    for r in matcher_db.recommend_from_db(answers, store="scentrique"):
        sample = f" (sample {r['sample_size']} ${r['sample_price']})" if r["sample_price"] else ""
        print(f"  {r['score']:3}  {r['brand']} — {r['name']}  ${r['price']}{sample}")
