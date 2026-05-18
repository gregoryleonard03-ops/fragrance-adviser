"""
Matcher using fragrances_db.json (76k combined database).
Used by both Sephora and Parfbar versions.
"""
import json
from pathlib import Path

_DB = None
_PARFBAR = None  # key: lower(brand)+lower(name)

DATA_DIR = Path(__file__).parent / "data"


def _load_db() -> list[dict]:
    global _DB
    if _DB is None:
        _DB = json.loads((DATA_DIR / "fragrances_db.json").read_text())
    return _DB


def _parfbar_key(brand: str, name: str) -> str:
    brand_l = brand.lower().strip()
    name_l = name.lower().strip()
    # parfbar often includes brand in name: "Amouage Interlude" → strip it
    if name_l.startswith(brand_l):
        name_l = name_l[len(brand_l):].strip()
    return (brand_l + name_l).replace(" ", "")


def _load_parfbar() -> dict[str, dict]:
    global _PARFBAR
    if _PARFBAR is None:
        parfbar_path = DATA_DIR / "fragrances_parfbar.json"
        if parfbar_path.exists():
            items = json.loads(parfbar_path.read_text())
            _PARFBAR = {}
            for item in items:
                key = _parfbar_key(item.get("brand", ""), item.get("name", ""))
                _PARFBAR[key] = item
        else:
            _PARFBAR = {}
    return _PARFBAR


# ── Keyword maps ────────────────────────────────────────────────────────────

NOTE_KEYWORDS: dict[str, list[str]] = {
    "citrus":   ["bergamot", "lemon", "grapefruit", "lime", "orange", "mandarin", "yuzu"],
    "rose":     ["rose", "peony", "geranium", "damascus"],
    "oud":      ["oud", "agarwood", "incense", "frankincense", "myrrh"],
    "vanilla":  ["vanilla", "tonka", "benzoin", "heliotrope", "coumarin"],
    "vetiver":  ["vetiver", "oakmoss", "patchouli", "moss"],
    "amber":    ["amber", "ambergris", "labdanum", "resin"],
    "fruits":   ["apple", "peach", "cherry", "blackcurrant", "pear", "plum", "raspberry"],
    "marine":   ["sea", "aquatic", "seaweed", "ozone", "salt", "ocean"],
}

VIBE_ACCORDS: dict[str, list[str]] = {
    "forest": ["Woody", "Green", "Mossy", "Earthy", "Forest"],
    "beach":  ["Marine", "Aquatic", "Fresh", "Ozonic", "Sea"],
    "fruits": ["Fruity", "Sweet", "Tropical"],
    "night":  ["Oriental", "Amber", "Musky", "Warm", "Dark"],
    "east":   ["Spicy", "Oud", "Incense", "Balsamic", "Resinous"],
    "snow":   ["Powdery", "White Floral", "Fresh", "Clean", "Iris"],
}

SEASON_ACCORDS: dict[str, list[str]] = {
    "summer": ["Fresh", "Citrus", "Aquatic", "Light"],
    "spring": ["Floral", "Green", "Fruity", "Fresh"],
    "winter": ["Warm", "Amber", "Spicy", "Gourmand", "Balsamic"],
    "autumn": ["Woody", "Warm", "Spicy", "Earthy"],
}

BRANCH_ACCORDS: dict[str, list[str]] = {
    "fresh_clean":    ["Fresh", "Citrus", "Aquatic", "Green", "Ozonic", "Clean"],
    "warm_cozy":      ["Warm", "Gourmand", "Vanilla", "Amber", "Balsamic", "Sweet"],
    "dark_sexy":      ["Leather", "Tobacco", "Smoky", "Spicy", "Dark", "Animalistic"],
    "elegant_luxury": ["Floral", "Powdery", "Woody", "Iris", "Rose", "Aldehyde"],
    "artistic_niche": ["Aromatic", "Earthy", "Incense", "Metallic", "Animalic", "Herbal"],
    "soft_skin":      ["Musky", "Powdery", "Clean", "White Floral", "Soft", "Soapy"],
}

GENDER_MAP = {
    "self":        None,
    "unisex":      None,
    "gift_male":   "men",
    "gift_female": "women",
}


def _parse_notes(text: str) -> list[str]:
    return [t.strip().lower() for t in text.split(",") if t.strip()]


def _score(item: dict, answers: dict) -> int:
    score = 0
    item_accords = [a.lower() for a in (item.get("accords") or [])]
    all_notes = " ".join([
        item.get("top_notes", ""),
        item.get("middle_notes", ""),
        item.get("base_notes", ""),
    ]).lower()

    # ── Notes match ──────────────────────────────────────────
    selected_notes = answers.get("notes") or []
    if isinstance(selected_notes, str):
        selected_notes = [selected_notes]
    for note_key in selected_notes:
        for kw in NOTE_KEYWORDS.get(note_key, []):
            if kw in all_notes:
                score += 3

    # ── Vibe → accords ──────────────────────────────────────
    vibe = answers.get("vibe")
    if vibe:
        for accord in VIBE_ACCORDS.get(vibe, []):
            if accord.lower() in item_accords:
                score += 4

    # ── Branch → accords (Parfbar) ──────────────────────────
    branch = answers.get("branch")
    if branch:
        for accord in BRANCH_ACCORDS.get(branch, []):
            if accord.lower() in item_accords:
                score += 4
        sub_type = answers.get("sub_type")
        if sub_type:
            for accord in BRANCH_ACCORDS.get(sub_type, []):
                if accord.lower() in item_accords:
                    score += 3

    # ── Season → accords ────────────────────────────────────
    season = answers.get("season")
    if season:
        for accord in SEASON_ACCORDS.get(season, []):
            if accord.lower() in item_accords:
                score += 2

    # ── Brand bonus ─────────────────────────────────────────
    brands = answers.get("brands") or []
    if isinstance(brands, str):
        brands = [brands]
    item_brand = (item.get("brand") or "").lower()
    if any(b.lower() in item_brand or item_brand in b.lower() for b in brands):
        score += 5

    return score


def _build_reason(item: dict, answers: dict, store: str) -> str:
    parts = []
    accords = item.get("accords") or []
    if accords:
        parts.append(f"Аккорды: {', '.join(accords[:3])}.")
    vibe = answers.get("vibe") or answers.get("branch")
    if vibe:
        parts.append(f"Подходит под настроение «{vibe}».")
    if store == "parfbar":
        parts.append("Можно купить на Parfbar.")
    else:
        parts.append("Найти на Sephora.")
    return " ".join(parts)


def recommend_from_db(answers: dict, store: str = "sephora", top_n: int = 5) -> list[dict]:
    db = _load_db()

    # Gender filter
    gender_filter = GENDER_MAP.get(answers.get("gender", "self"))
    if gender_filter:
        candidates = [f for f in db if f.get("gender") in (gender_filter, "unisex", None)]
    else:
        candidates = db

    # Pre-load parfbar catalog for bonus scoring
    parfbar_lookup = _load_parfbar() if store == "parfbar" else {}

    # Score
    scored = []
    for item in candidates:
        s = _score(item, answers)
        if s > 0:
            # Bonus: item is available in parfbar catalog → prioritise it
            if parfbar_lookup and _parfbar_key(item.get("brand",""), item.get("name","")) in parfbar_lookup:
                s += 15
            scored.append((s, item))

    scored.sort(key=lambda x: -x[0])
    top50 = scored[:50]
    results = []
    seen = set()

    for s, item in top50:
        name = item.get("name", "")
        brand = item.get("brand", "")
        key = f"{brand}|{name}".lower()
        if key in seen:
            continue
        seen.add(key)

        q = f"{brand}+{name}".replace(" ", "+")
        price = None
        url = ""

        if store == "parfbar":
            lookup_key = _parfbar_key(brand, name)
            parfbar_item = parfbar_lookup.get(lookup_key)
            if parfbar_item:
                price = parfbar_item.get("price")
                url = parfbar_item.get("url", f"https://parfbar.com/?s={q}")
            else:
                url = f"https://parfbar.com/?s={q}"
        else:
            url = f"https://www.sephora.com/search?keyword={q}"

        results.append({
            "name":      name,
            "brand":     brand,
            "price":     price,
            "image_url": "",
            "url":       url,
            "score":     s,
            "accords":   item.get("accords") or [],
            "reason":    _build_reason(item, answers, store),
        })

        if len(results) == top_n:
            break

    return results


if __name__ == "__main__":
    test = {"gender": "self", "notes": ["oud", "amber"], "vibe": "night", "season": "winter"}
    recs = recommend_from_db(test, store="sephora")
    for r in recs:
        print(f"{r['score']:3d}  {r['brand']} — {r['name']}")
        print(f"       {r['reason']}")
