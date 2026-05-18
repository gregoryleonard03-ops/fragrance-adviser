"""
One-time script: slim fragrances_combined.json down to fields needed for matching.
Run: python3 backend/tools/slim_db.py
Output: backend/data/fragrances_db.json
"""
import json
from pathlib import Path

SRC = Path.home() / "Downloads" / "fragrances_combined.json"
DST = Path(__file__).parent.parent / "data" / "fragrances_db.json"

print(f"Loading {SRC} ...")
raw = json.loads(SRC.read_text())
print(f"Total records: {len(raw)}")

slim = []
for item in raw:
    has_notes = any([
        item.get("top_notes"),
        item.get("middle_notes"),
        item.get("base_notes"),
        item.get("accords"),
    ])
    if not has_notes:
        continue
    slim.append({
        "name":         item.get("name", ""),
        "brand":        item.get("brand", ""),
        "gender":       item.get("gender"),
        "accords":      item.get("accords") or [],
        "top_notes":    item.get("top_notes") or "",
        "middle_notes": item.get("middle_notes") or "",
        "base_notes":   item.get("base_notes") or "",
    })

print(f"After filter: {len(slim)} records")
DST.write_text(json.dumps(slim, ensure_ascii=False))
size_mb = DST.stat().st_size / 1024 / 1024
print(f"Saved to {DST} ({size_mb:.1f} MB)")
