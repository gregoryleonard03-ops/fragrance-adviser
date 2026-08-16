"""
Matcher using fragrances_db.json (76k combined database).
Used by both Sephora and Parfbar versions.
"""
import json
import re
from pathlib import Path

_DB = None
_DB_LOOKUP = None   # key → db item, for O(1) catalog lookup
_PARFBAR = None
_PROFUMUM = None
_GENERIC = None
_BIBLIOTEKA_LIST = None
_SCENTRIQUE = None

DATA_DIR = Path(__file__).parent / "data"

BUDGET_RANGES = {
    "parfbar": {
        "budget_1": (0,     2500),
        "budget_2": (2500,  4000),
        "budget_3": (4000,  6000),
        "budget_4": (6000,  float("inf")),
    },
    "profumum": {
        "budget_1": (0,     15000),
        "budget_2": (15000, 30000),
        "budget_3": (30000, 50000),
        "budget_4": (50000, float("inf")),
    },
    "generic": {
        "budget_1": (0,     15000),
        "budget_2": (15000, 30000),
        "budget_3": (30000, 50000),
        "budget_4": (50000, float("inf")),
    },
    # USD, full-bottle price; samples ($4–15) are shown alongside, not filtered.
    # Tiers ≈ catalog quartiles: p25=$195, median=$240, p75=$345
    "scentrique": {
        "budget_1": (0,     200),
        "budget_2": (200,   300),
        "budget_3": (300,   400),
        "budget_4": (400,   float("inf")),
    },
}


def _price_ok(price, price_filters: list) -> bool:
    """True if price falls within any selected budget range, or no filter is active."""
    if not price_filters or price is None:
        return True
    return any(lo <= price < hi for lo, hi in price_filters)


def _load_db() -> list[dict]:
    global _DB
    if _DB is None:
        _DB = json.loads((DATA_DIR / "fragrances_db.json").read_text())
    return _DB


def _load_db_lookup() -> dict:
    global _DB_LOOKUP
    if _DB_LOOKUP is None:
        db = _load_db()
        _DB_LOOKUP = {}
        for item in db:
            key = _parfbar_key(item.get("brand", ""), item.get("name", ""))
            _DB_LOOKUP[key] = item
    return _DB_LOOKUP


def _parfbar_key(brand: str, name: str) -> str:
    brand_l = brand.lower().strip()
    name_l = name.lower().strip()
    if name_l.startswith(brand_l):
        name_l = name_l[len(brand_l):].strip()
    return (brand_l + name_l).replace(" ", "")


def _load_parfbar() -> dict:
    global _PARFBAR
    if _PARFBAR is None:
        path = DATA_DIR / "fragrances_parfbar.json"
        if path.exists():
            items = json.loads(path.read_text())
            _PARFBAR = {}
            for item in items:
                key = _parfbar_key(item.get("brand", ""), item.get("name", ""))
                _PARFBAR[key] = item
        else:
            _PARFBAR = {}
    return _PARFBAR


def _load_profumum() -> dict:
    global _PROFUMUM
    if _PROFUMUM is None:
        path = DATA_DIR / "fragrances_profumum.json"
        if path.exists():
            items = json.loads(path.read_text())
            _PROFUMUM = {}
            for item in items:
                key = _parfbar_key(item.get("brand", ""), item.get("name", ""))
                _PROFUMUM[key] = item
        else:
            _PROFUMUM = {}
    return _PROFUMUM


def _load_scentrique() -> dict:
    global _SCENTRIQUE
    if _SCENTRIQUE is None:
        path = DATA_DIR / "fragrances_scentrique.json"
        if path.exists():
            items = json.loads(path.read_text())
            _SCENTRIQUE = {}
            for item in items:
                key = _parfbar_key(item.get("brand", ""), item.get("name", ""))
                _SCENTRIQUE[key] = item
        else:
            _SCENTRIQUE = {}
    return _SCENTRIQUE


def _load_generic() -> dict:
    """Merged Profumum + Parfbar. Profumum has priority (correct prices).
    Parfbar prices × 10: catalog stores 5ml decant price, full bottle ≈ 50ml = ×10."""
    global _GENERIC
    if _GENERIC is None:
        profumum = _load_profumum()
        parfbar  = _load_parfbar()
        _GENERIC = dict(profumum)
        for key, item in parfbar.items():
            if key not in _GENERIC:
                item_copy = dict(item)
                if item_copy.get("price"):
                    item_copy["price"] = item_copy["price"] * 10
                _GENERIC[key] = item_copy
    return _GENERIC


# ── Keyword maps ────────────────────────────────────────────────────────────

NOTE_KEYWORDS: dict[str, list[str]] = {
    "citrus":   ["bergamot", "lemon", "grapefruit", "lime", "orange", "mandarin", "yuzu",
                 "бергамот", "лимон", "грейпфрут", "апельсин", "мандарин"],
    "rose":     ["rose", "peony", "geranium", "damascus", "jasmine", "tuberose",
                 "роза", "жасмин", "пион", "тубероза", "герань"],
    "oud":      ["oud", "agarwood", "incense", "frankincense", "myrrh", "olibanum",
                 "уд", "ладан", "олибанум"],
    "vanilla":  ["vanilla", "tonka", "benzoin", "heliotrope", "coumarin",
                 "ваниль", "бобы тонка", "тонка", "бензоин"],
    "vetiver":  ["vetiver", "oakmoss", "patchouli", "moss",
                 "ветивер", "пачули", "дубовый мох"],
    "amber":    ["amber", "ambergris", "labdanum", "resin", "ambroxan",
                 "амбра", "серая амбра", "лабданум", "амброксан"],
    "fruits":   ["apple", "peach", "cherry", "blackcurrant", "pear", "plum", "raspberry",
                 "персик", "груша", "черная смородина", "малина", "вишня"],
    "marine":   ["sea", "aquatic", "seaweed", "ozone", "salt", "ocean",
                 "морской", "морская соль", "океан"],
    "spicy":    ["pepper", "cinnamon", "cardamom", "saffron", "ginger", "clove", "nutmeg",
                 "шафран", "розовый перец", "кардамон", "корица", "имбирь", "перец", "гвоздика"],
    "woody":    ["cedar", "sandalwood", "guaiac", "vetiver", "oud",
                 "кедр", "сандал", "гваяк", "сандалвуд"],
    "leather":  ["leather", "suede", "birch",
                 "кожа", "замша", "берёза"],
    "tobacco":  ["tobacco", "rum", "whiskey",
                 "табак", "ром", "виски"],
    "musk":     ["musk", "ambroxan", "cashmeran",
                 "мускус", "кашмеран", "кашемировое дерево"],
}

OCCASION_ACCORDS: dict[str, list[str]] = {
    "daily":         ["Fresh", "Clean", "Citrus", "Aromatic"],
    "office":        ["Fresh", "Powdery", "Clean", "Woody"],
    "work":          ["Fresh", "Powdery", "Clean", "Woody"],
    "date":          ["Oriental", "Amber", "Floral", "Musky"],
    "romantic":      ["Oriental", "Amber", "Floral", "Musky"],
    "party":         ["Spicy", "Oriental", "Fruity", "Smoky"],
    "night_city":    ["Oriental", "Smoky", "Spicy", "Leathery"],
    "summer_night":  ["Aquatic", "Citrus", "Amber", "Musky"],
    "summer_trip":   ["Aquatic", "Citrus", "Fresh", "Marine"],
    "autumn_winter": ["Warm", "Spicy", "Woody", "Amber"],
    "cozy_evening":  ["Vanilla", "Warm", "Gourmand", "Amber"],
    "special":       ["Oriental", "Floral", "Amber", "Spicy"],
    "evening":       ["Oriental", "Amber", "Spicy", "Floral"],
    "sport":         ["Fresh", "Citrus", "Aquatic", "Aromatic"],
    "restaurants":   ["Floral", "Woody", "Spicy", "Musky"],
    "travel":        ["Fresh", "Citrus", "Woody", "Clean"],
    "collection":    ["Resinous", "Incense", "Earthy", "Smoky"],
    "impress":       ["Resinous", "Incense", "Spicy", "Leathery"],
    "connoisseurs":  ["Incense", "Earthy", "Oud", "Resinous"],
    "bed_scent":     ["Musky", "Vanilla", "Powdery", "Soft"],
    "just_because":  ["Musky", "Clean", "Fresh", "Citrus"],
}

VIBE_ACCORDS: dict[str, list[str]] = {
    "forest": ["Woody", "Green", "Earthy", "Herbal"],
    "beach":  ["Marine", "Aquatic", "Fresh", "Sea"],
    "fruits": ["Fruity", "Sweet", "Tropical"],
    "night":  ["Oriental", "Amber", "Musky", "Warm"],
    "east":   ["Spicy", "Oud", "Incense", "Balsamic", "Resinous"],
    "snow":   ["Powdery", "White Floral", "Fresh", "Clean", "Iris"],
}

BRANCH_VIBE_ACCORDS: dict[str, list[str]] = {
    # fresh_clean vibes
    "luxury_hotel":          ["Fresh", "Powdery", "Clean", "Citrus"],
    "summer_europe":         ["Citrus", "Fresh", "Aquatic", "Fruity"],
    "sporty_expensive":      ["Fresh", "Citrus", "Aromatic", "Woody"],
    "scandinavian_minimal":  ["Fresh", "Clean", "Woody", "Green"],
    "rich_clean_person":     ["Powdery", "Clean", "Musky", "Fresh"],
    # warm_cozy vibes
    "sunday_morning":        ["Vanilla", "Sweet", "Gourmand", "Warm"],
    "autumn_coffee":         ["Spicy", "Warm", "Gourmand", "Balsamic"],
    "cashmere_fireplace":    ["Warm", "Vanilla", "Amber", "Sweet"],
    "warm_skin_sun":         ["Amber", "Musky", "Sweet", "Vanilla"],
    "nordic_cabin":          ["Woody", "Spicy", "Balsamic", "Warm"],
    # dark_sexy vibes
    "mafia_luxury":          ["Leather", "Tobacco", "Spicy", "Resinous"],
    "dangerous":             ["Spicy", "Smoky", "Leather", "Oriental"],
    "night_out":             ["Oriental", "Spicy", "Smoky", "Leathery"],
    "dominant":              ["Leather", "Animal", "Smoky"],
    "dark_elegance":         ["Leather", "Floral", "Powdery", "Smoky"],
    # elegant_luxury vibes
    "expensive_calm":        ["Powdery", "Floral", "Woody", "Fresh"],
    "clean_status":          ["Fresh", "Powdery", "Woody", "Clean"],
    "wealth_no_logos":       ["Powdery", "Iris", "Woody", "Musky"],
    "luxury_traveler":       ["Woody", "Floral", "Fresh", "Spicy"],
    "business_class":        ["Fresh", "Aromatic", "Woody", "Spicy"],
    # artistic_niche vibes
    "art_gallery":           ["Earthy", "Incense", "Resinous", "Smoky"],
    "desert_midnight":       ["Resinous", "Spicy", "Oriental", "Smoky"],
    "rain_hot_pavement":     ["Earthy", "Aquatic", "Aromatic", "Green"],
    "avantgarde":            ["Animal", "Incense", "Earthy"],
    "intellectual":          ["Aromatic", "Earthy", "Woody", "Clean"],
    # soft_skin vibes
    "second_skin":           ["Musky", "Clean", "Powdery", "Soft"],
    "just_showered":         ["Clean", "Fresh", "Musky", "Soapy"],
    "intimate_close":        ["Musky", "Vanilla", "Amber", "Powdery"],
    "clean_luxury":          ["Powdery", "Clean", "Musky", "White Floral"],
    "invisible_memo":        ["Musky", "Powdery", "Soft", "Clean"],
}

SUB_TYPE_ACCORDS: dict[str, list[str]] = {
    # fresh_clean sub_types
    "marine":        ["Marine", "Aquatic"],
    "citrus":        ["Citrus", "Fresh"],
    "clean":         ["Clean", "Powdery", "Musky"],
    "green":         ["Green", "Aromatic"],
    "metallic":      ["Fresh", "Aquatic"],
    # warm_cozy sub_types
    "vanilla_cream": ["Vanilla", "Sweet", "Gourmand"],
    "spices_warm":   ["Spicy", "Warm", "Balsamic"],
    "wood_resin":    ["Woody", "Resinous", "Balsamic"],
    "gourmand":      ["Gourmand", "Sweet", "Vanilla"],
    "soft_musk_warm":["Musky", "Powdery", "Vanilla"],
    # dark_sexy sub_types
    "leather":       ["Leathery", "Animal"],
    "tobacco":       ["Tobacco", "Smoky"],
    "smoke":         ["Smoky", "Resinous", "Incense"],
    "alcohol":       ["Tobacco", "Spicy", "Warm"],
    "spices_dark":   ["Spicy", "Resinous", "Oriental"],
    # elegant_luxury sub_types
    "old_money":     ["Powdery", "Floral", "Woody"],
    "quiet_luxury":  ["Powdery", "Woody", "Clean"],
    "ceo":           ["Aromatic", "Woody", "Fresh"],
    "european":      ["Floral", "Powdery", "Citrus"],
    "hotel":         ["Fresh", "Clean", "Floral"],
    # artistic_niche sub_types
    "unusual":       ["Earthy", "Aromatic", "Incense"],
    "narrative":     ["Incense", "Resinous", "Earthy"],
    "rarity":        ["Incense", "Animal", "Smoky"],
    "bold":          ["Animal", "Smoky", "Resinous"],
    "unexpected":    ["Earthy", "Aquatic", "Aromatic"],
    # soft_skin sub_types
    "clean_musk":    ["Musky", "Clean", "Powdery"],
    "powdery":       ["Powdery", "White Floral"],
    "milky":         ["Vanilla", "Sweet", "Musky"],
    "barely_there":  ["Musky", "Clean"],
    "warm_skin":     ["Musky", "Amber", "Vanilla"],
}

SEASON_ACCORDS: dict[str, list[str]] = {
    "summer": ["Fresh", "Citrus", "Aquatic", "Light"],
    "spring": ["Floral", "Green", "Fruity", "Fresh"],
    "winter": ["Warm", "Amber", "Spicy", "Gourmand", "Balsamic"],
    "autumn": ["Woody", "Warm", "Spicy", "Earthy"],
}

BRANCH_ACCORDS: dict[str, list[str]] = {
    "fresh_clean":    ["Fresh", "Citrus", "Aquatic", "Green", "Clean"],
    "warm_cozy":      ["Warm", "Gourmand", "Vanilla", "Amber", "Balsamic", "Sweet"],
    "dark_sexy":      ["Leather", "Tobacco", "Smoky", "Spicy", "Animal"],
    "elegant_luxury": ["Floral", "Powdery", "Woody", "Iris", "Rose"],
    "artistic_niche": ["Aromatic", "Earthy", "Incense", "Animal", "Herbal"],
    "soft_skin":      ["Musky", "Powdery", "Clean", "White Floral", "Soapy"],
}

# Scentrique (Shopify) tags → accords. Tags carry olfactory families and notes;
# this lets catalog items score even without a match in the 76k DB.
TAG_ACCORDS: dict[str, list[str]] = {
    "floral":          ["Floral"],
    "white florals":   ["White Floral", "Floral"],
    "rose":            ["Rose", "Floral"],
    "jasmine":         ["White Floral", "Floral"],
    "tuberose":        ["White Floral", "Floral"],
    "neroli":          ["Citrus", "White Floral"],
    "iris":            ["Iris", "Powdery"],
    "fruity":          ["Fruity", "Sweet"],
    "citrus":          ["Citrus", "Fresh"],
    "aquatic":         ["Aquatic", "Marine", "Fresh"],
    "green":           ["Green"],
    "fig":             ["Green", "Woody"],
    "tea":             ["Aromatic", "Green"],
    "lavender":        ["Aromatic", "Herbal"],
    "oud & woody":     ["Oud", "Woody"],
    "sandalwood":      ["Woody"],
    "cedarwood":       ["Woody"],
    "vetiver":         ["Woody", "Green", "Earthy"],
    "patchouli":       ["Earthy", "Woody"],
    "amber":           ["Amber", "Warm", "Oriental"],
    "incense":         ["Incense", "Resinous", "Smoky"],
    "leather":         ["Leather", "Leathery"],
    "tobacco":         ["Tobacco", "Smoky"],
    "tobacco & smoky": ["Tobacco", "Smoky"],
    "liquor":          ["Warm", "Spicy"],
    "spicy":           ["Spicy"],
    "musk":            ["Musky"],
    "gourmand":        ["Gourmand", "Sweet"],
    "vanilla":         ["Vanilla", "Sweet"],
    "tonka bean":      ["Vanilla", "Sweet", "Warm"],
    "chocolate":       ["Gourmand", "Sweet"],
    "coffee":          ["Gourmand", "Warm"],
    "almond":          ["Gourmand", "Sweet"],
    "coconut":         ["Gourmand", "Sweet", "Tropical"],
}


def _tag_accords(catalog_item: dict) -> list[str]:
    """Accords derived from a catalog item's own tags/product_type (lowercased)."""
    tags = list(catalog_item.get("tags") or [])
    if catalog_item.get("product_type"):
        tags.append(catalog_item["product_type"])
    out = []
    for t in tags:
        out += TAG_ACCORDS.get(t.lower().strip(), [])
    return [a.lower() for a in out]


GENDER_MAP = {
    "self":        None,
    "unisex":      None,
    "gift_male":   "men",
    "gift_female": "women",
}


# ── Gift mode normalization ───────────────────────────────────────────────────

GIFT_VIBE_TO_BRANCH: dict[str, str] = {
    "dark_sexy":      "dark_sexy",
    "elegant_luxury": "elegant_luxury",
    "warm_cozy":      "warm_cozy",
    "fresh_clean":    "fresh_clean",
    "artistic_niche": "artistic_niche",
    "soft_skin":      "soft_skin",
    "soft_sexy":      "dark_sexy",
    "rich_minimal":   "elegant_luxury",
}

GIFT_STYLE_TO_SUBTYPE: dict[str, str] = {
    "minimal":  "quiet_luxury",
    "luxury":   "old_money",
    "creative": "unusual",
    "classic":  "european",
    "trendy":   "ceo",
    "casual":   "clean",
    "clean":    "clean_musk",
}

GIFT_EFFECT_TO_OCCASION: dict[str, str] = {
    "complimentary": "daily",
    "sexy":          "date",
    "status":        "restaurants",
    "cozy":          "cozy_evening",
    "memorable":     "special",
}

GIFT_PRIORITY_TO_OCCASION: dict[str, str] = {
    "everyone":    "daily",
    "expensive":   "restaurants",
    "unusual":     "special",
    "wearable":    "daily",
    "compliments": "daily",
    "niche_feel":  "impress",
    "mass_plus":   "daily",
}

GIFT_BOLDNESS_TO_VIBE: dict[str, list[str]] = {
    "safe":           ["fresh_clean", "elegant_luxury"],
    "niche_wearable": [],
    "unusual":        ["artistic_niche"],
    "rare":           ["artistic_niche"],
}


def _normalize_gift_answers(answers: dict) -> dict:
    """Remap gift-mode fields to standard scoring fields. No-op if gift_type is empty."""
    if not answers.get("gift_type"):
        return answers

    norm = dict(answers)

    gift_vibes = answers.get("gift_vibe") or []
    if isinstance(gift_vibes, str):
        gift_vibes = [gift_vibes]
    boldness_vibes = GIFT_BOLDNESS_TO_VIBE.get(answers.get("gift_boldness", ""), [])

    if gift_vibes:
        mapped = [GIFT_VIBE_TO_BRANCH.get(v, v) for v in gift_vibes]
        norm["branch"] = mapped[0]
        norm["vibe"] = mapped[1:] + boldness_vibes
    elif boldness_vibes:
        norm["vibe"] = boldness_vibes

    gift_styles = answers.get("gift_style") or []
    if isinstance(gift_styles, str):
        gift_styles = [gift_styles]
    norm["sub_type"] = [GIFT_STYLE_TO_SUBTYPE.get(s, s) for s in gift_styles]

    effects = answers.get("gift_effect") or []
    if isinstance(effects, str):
        effects = [effects]
    priorities = answers.get("gift_priority") or []
    if isinstance(priorities, str):
        priorities = [priorities]
    occ = [GIFT_EFFECT_TO_OCCASION[e] for e in effects if e in GIFT_EFFECT_TO_OCCASION]
    occ += [GIFT_PRIORITY_TO_OCCASION[p] for p in priorities if p in GIFT_PRIORITY_TO_OCCASION]
    if occ:
        norm["occasion"] = occ

    gift_intensity = answers.get("gift_intensity") or []
    if gift_intensity:
        norm["intensity"] = gift_intensity

    return norm


def _parse_notes(text: str) -> list[str]:
    return [t.strip().lower() for t in text.split(",") if t.strip()]


def _score_notes(all_notes: str, selected_notes: list[str]) -> int:
    score = 0
    for note_key in selected_notes:
        for kw in NOTE_KEYWORDS.get(note_key, []):
            if kw in all_notes:
                score += 3
    return score


def _score_accords(item_accords: list[str], accord_list: list[str], pts: int) -> int:
    score = 0
    for accord in accord_list:
        if accord.lower() in item_accords:
            score += pts
    return score


def _score(item: dict, answers: dict) -> int:
    """Score a DB item against quiz answers."""
    score = 0
    item_accords = [a.lower() for a in (item.get("accords") or [])]
    all_notes = " ".join([
        item.get("top_notes", ""),
        item.get("middle_notes", ""),
        item.get("base_notes", ""),
    ]).lower()

    # Notes match
    selected_notes = answers.get("notes") or []
    if isinstance(selected_notes, str):
        selected_notes = [selected_notes]
    score += _score_notes(all_notes, selected_notes)

    # Vibe → accords (VIBE_ACCORDS for sephora vibes, BRANCH_VIBE_ACCORDS for parfbar/profumum)
    vibe_raw = answers.get("vibe")
    vibes = vibe_raw if isinstance(vibe_raw, list) else ([vibe_raw] if vibe_raw else [])
    for vibe in vibes:
        accords = VIBE_ACCORDS.get(vibe) or BRANCH_VIBE_ACCORDS.get(vibe) or []
        score += _score_accords(item_accords, accords, 4)

    # Branch → accords (parfbar/profumum)
    branch = answers.get("branch")
    if branch:
        score += _score_accords(item_accords, BRANCH_ACCORDS.get(branch, []), 4)
        sub_raw = answers.get("sub_type")
        sub_types = sub_raw if isinstance(sub_raw, list) else ([sub_raw] if sub_raw else [])
        for sub_type in sub_types:
            score += _score_accords(item_accords, SUB_TYPE_ACCORDS.get(sub_type, []), 3)

    # Season → accords
    season_raw = answers.get("season")
    seasons = season_raw if isinstance(season_raw, list) else ([season_raw] if season_raw else [])
    for season in seasons:
        score += _score_accords(item_accords, SEASON_ACCORDS.get(season, []), 2)

    # Brand bonus
    brands = answers.get("brands") or []
    if isinstance(brands, str):
        brands = [brands]
    item_brand = (item.get("brand") or "").lower()
    if any(b.lower() in item_brand or item_brand in b.lower() for b in brands):
        score += 5

    return score


def _score_catalog_item(catalog_item: dict, db_item, answers: dict):
    """Score a catalog item. Returns (total_score, breakdown_dict) tuple."""
    bd_branch   = {"score": 0, "max_possible": 0, "matched_accords": []}
    bd_notes    = {"score": 0, "max_possible": 0, "matched_keywords": []}
    bd_vibe     = {"score": 0, "max_possible": 0, "vibe_values": [], "matched_accords": []}
    bd_sub_type = {"score": 0, "max_possible": 0, "sub_type_values": [], "matched_accords": []}
    bd_season   = {"score": 0, "max_possible": 0, "matched_accords": []}
    bd_occasion = {"score": 0, "max_possible": 0, "occasion_values": [], "matched_accords": []}

    item_accords = [a.lower() for a in (db_item.get("accords") or [])] if db_item else []
    item_accords += _tag_accords(catalog_item)
    db_notes_str = ""
    if db_item:
        db_notes_str = " ".join([
            db_item.get("top_notes", ""),
            db_item.get("middle_notes", ""),
            db_item.get("base_notes", ""),
        ])
    catalog_notes = " ".join([
        catalog_item.get("top_notes", ""),
        catalog_item.get("middle_notes", ""),
        catalog_item.get("base_notes", ""),
    ])
    # tags often carry note names (Jasmine, Sandalwood, Tonka Bean…) — let
    # NOTE_KEYWORDS match against them too
    tags_text = " ".join(catalog_item.get("tags") or [])
    all_notes = (db_notes_str + " " + catalog_notes + " " + tags_text).lower()

    # Notes match (EN + RU)
    selected_notes = answers.get("notes") or []
    if isinstance(selected_notes, str):
        selected_notes = [selected_notes]
    for note_key in selected_notes:
        bd_notes["max_possible"] += 3
        matched_any = False
        for kw in NOTE_KEYWORDS.get(note_key, []):
            if kw in all_notes:
                if kw not in bd_notes["matched_keywords"]:
                    bd_notes["matched_keywords"].append(kw)
                matched_any = True
        if matched_any:
            bd_notes["score"] += 3

    # Vibe → accords
    vibe_raw = answers.get("vibe")
    vibes = vibe_raw if isinstance(vibe_raw, list) else ([vibe_raw] if vibe_raw else [])
    bd_vibe["vibe_values"] = vibes
    for vibe in vibes:
        accords = VIBE_ACCORDS.get(vibe) or BRANCH_VIBE_ACCORDS.get(vibe) or []
        bd_vibe["max_possible"] += len(accords) * 4
        for accord in accords:
            if accord.lower() in item_accords:
                bd_vibe["score"] += 4
                if accord not in bd_vibe["matched_accords"]:
                    bd_vibe["matched_accords"].append(accord)

    # Branch → accords
    branch = answers.get("branch")
    if branch:
        branch_accords = BRANCH_ACCORDS.get(branch, [])
        bd_branch["max_possible"] = len(branch_accords) * 4
        for accord in branch_accords:
            if accord.lower() in item_accords:
                bd_branch["score"] += 4
                bd_branch["matched_accords"].append(accord)

        sub_raw = answers.get("sub_type")
        sub_types = sub_raw if isinstance(sub_raw, list) else ([sub_raw] if sub_raw else [])
        bd_sub_type["sub_type_values"] = sub_types
        for sub_type in sub_types:
            st_accords = SUB_TYPE_ACCORDS.get(sub_type, [])
            bd_sub_type["max_possible"] += len(st_accords) * 3
            for accord in st_accords:
                if accord.lower() in item_accords:
                    bd_sub_type["score"] += 3
                    if accord not in bd_sub_type["matched_accords"]:
                        bd_sub_type["matched_accords"].append(accord)

    # Season → accords
    season_raw = answers.get("season")
    seasons = season_raw if isinstance(season_raw, list) else ([season_raw] if season_raw else [])
    for season in seasons:
        s_accords = SEASON_ACCORDS.get(season, [])
        bd_season["max_possible"] += len(s_accords) * 2
        for accord in s_accords:
            if accord.lower() in item_accords:
                bd_season["score"] += 2
                if accord not in bd_season["matched_accords"]:
                    bd_season["matched_accords"].append(accord)

    # Occasion → accords
    occasion_raw = answers.get("occasion")
    occasions = occasion_raw if isinstance(occasion_raw, list) else ([occasion_raw] if occasion_raw else [])
    bd_occasion["occasion_values"] = occasions
    for occ in occasions:
        occ_accords = OCCASION_ACCORDS.get(occ, [])
        bd_occasion["max_possible"] += len(occ_accords) * 2
        for accord in occ_accords:
            if accord.lower() in item_accords:
                bd_occasion["score"] += 2
                if accord not in bd_occasion["matched_accords"]:
                    bd_occasion["matched_accords"].append(accord)

    total = (bd_branch["score"] + bd_notes["score"] + bd_vibe["score"] +
             bd_sub_type["score"] + bd_season["score"] + bd_occasion["score"])

    if not db_item and total == 0:
        total = -1

    breakdown = {
        "total":    total,
        "branch":   bd_branch,
        "notes":    bd_notes,
        "vibe":     bd_vibe,
        "sub_type": bd_sub_type,
        "season":   bd_season,
        "occasion": bd_occasion,
    }
    return total, breakdown


def _build_reason(item: dict, answers: dict, store: str, catalog_item=None) -> str:
    en = store == "scentrique"
    lbl_notes, lbl_vibe, lbl_accords, lbl_brand = (
        ("Notes: ", "Vibe: ", "Accords: ", "Your brand.") if en
        else ("Ноты: ", "Вайб: ", "Аккорды: ", "Твой бренд.")
    )
    parts = []

    db_notes = " ".join([
        item.get("top_notes", ""),
        item.get("middle_notes", ""),
        item.get("base_notes", ""),
    ])
    catalog_notes = ""
    if catalog_item:
        catalog_notes = " ".join([
            catalog_item.get("top_notes", ""),
            catalog_item.get("middle_notes", ""),
            catalog_item.get("base_notes", ""),
        ])
    all_notes = (db_notes + " " + catalog_notes).lower()

    selected_notes = answers.get("notes") or []
    if isinstance(selected_notes, str):
        selected_notes = [selected_notes]
    matched_notes = [kw for nk in selected_notes
                     for kw in NOTE_KEYWORDS.get(nk, []) if kw in all_notes]
    if matched_notes:
        parts.append(f"{lbl_notes}{', '.join(matched_notes[:3])}.")

    item_accords = [a.lower() for a in (item.get("accords") or [])]

    # Try vibe first, then branch
    vibe_raw = answers.get("vibe") or []
    vibes = vibe_raw if isinstance(vibe_raw, list) else ([vibe_raw] if vibe_raw else [])
    branch = answers.get("branch")
    check_keys = vibes + ([branch] if branch else [])

    for key in check_keys:
        accords = (VIBE_ACCORDS.get(key) or BRANCH_VIBE_ACCORDS.get(key)
                   or BRANCH_ACCORDS.get(key) or [])
        matched_accords = [a for a in accords if a.lower() in item_accords]
        if matched_accords:
            parts.append(f"{lbl_vibe}{', '.join(matched_accords[:2])}.")
            break

    if not parts and item.get("accords"):
        parts.append(f"{lbl_accords}{', '.join(item['accords'][:3])}.")
    elif not parts and catalog_item:
        # For items without DB data, use catalog notes snippet (or scent tags for scentrique)
        service = {"for him", "for her", "unisex", "spring/summer", "fall/winter"}
        brand_l = (catalog_item.get("brand") or "").lower()
        scent_tags = [t for t in (catalog_item.get("tags") or [])
                      if t.lower() not in service
                      and not (brand_l and brand_l.split()[0] in t.lower())]
        top = catalog_item.get("top_notes", "") or ", ".join(scent_tags[:3])
        if top:
            parts.append(f"{lbl_notes}{top[:40]}.")

    brands = answers.get("brands") or []
    if any(b.lower() in (item.get("brand") or catalog_item.get("brand") if catalog_item else "").lower()
           for b in brands):
        parts.append(lbl_brand)

    store_label = {
        "sephora": "Найти на Sephora",
        "parfbar": "Купить на Parfbar",
        "profumum": "Купить на Profumum.ru",
        "scentrique": "Available at Scentrique",
    }
    parts.append(store_label.get(store, "Найти в магазине") + ".")
    return " ".join(parts[:3])


def recommend_from_db(answers: dict, store: str = "sephora", top_n: int = 5) -> list[dict]:
    if store == "biblioteka":
        return _recommend_biblioteka(answers, top_n)
    if store in ("parfbar", "profumum", "generic", "scentrique"):
        return _recommend_catalog(answers, store, top_n)

    db = _load_db()

    gender_filter = GENDER_MAP.get(answers.get("gender", "self"))
    if gender_filter:
        candidates = [f for f in db if f.get("gender") in (gender_filter, "unisex", None)]
    else:
        candidates = db

    scored = []
    for item in candidates:
        s = _score(item, answers)
        if s > 0:
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

        q = (brand + " " + name).replace(" ", "+")
        url = f"https://www.sephora.com/search?keyword={q}"

        results.append({
            "name":      name,
            "brand":     brand,
            "price":     None,
            "image_url": "",
            "url":       url,
            "score":     s,
            "accords":   item.get("accords") or [],
            "reason":    _build_reason(item, answers, store),
        })

        if len(results) == top_n:
            break

    return results


def _recommend_catalog(answers: dict, store: str, top_n: int) -> list[dict]:
    """Hybrid scoring: iterate over CATALOG items, enrich with DB data when available."""
    answers = _normalize_gift_answers(answers)
    if store == "parfbar":
        catalog = _load_parfbar()
    elif store == "generic":
        catalog = _load_generic()
    elif store == "scentrique":
        catalog = _load_scentrique()
    else:
        catalog = _load_profumum()
    db_lookup = _load_db_lookup()

    # Build price filter from selected budget tiers
    budget_vals = answers.get("budget", [])
    if isinstance(budget_vals, str):
        budget_vals = [budget_vals]
    store_ranges = BUDGET_RANGES.get(store, {})
    price_filters = [store_ranges[b] for b in budget_vals if b in store_ranges]

    scored = []
    for key, catalog_item in catalog.items():
        db_item = db_lookup.get(key)
        s, breakdown = _score_catalog_item(catalog_item, db_item, answers)
        scored.append((s, breakdown, catalog_item, db_item))

    scored.sort(key=lambda x: -x[0])

    results = []
    seen = set()

    for s, breakdown, catalog_item, db_item in scored:
        if s <= 0:
            continue

        price = catalog_item.get("price")
        if not _price_ok(price, price_filters):
            continue

        name = catalog_item.get("name", "")
        brand = catalog_item.get("brand", "")
        key = f"{brand}|{name}".lower()
        if key in seen:
            continue
        seen.add(key)

        url = catalog_item.get("url", "")
        if not url:
            q = (brand + " " + name).replace(" ", "+")
            url = f"https://parfbar.com/?s={q}" if store == "parfbar" else f"https://profumum.ru/catalog/?q={q}"

        # For reason: use db_item if available, else empty dict
        source_item = db_item if db_item else {}
        reason = _build_reason(source_item, answers, store, catalog_item)

        results.append({
            "name":         name,
            "brand":        brand,
            "price":        price,
            "sample_price": catalog_item.get("sample_price"),
            "sample_size":  catalog_item.get("sample_size"),
            "image_url":    catalog_item.get("image_url", ""),
            "url":          url,
            "score":        s,
            "accords":      (db_item.get("accords") or []) if db_item else [],
            "reason":       reason,
            "score_details": breakdown,
        })

        if len(results) == top_n:
            break

    # Fallback: if scoring found nothing (all scores ≤ 0), return top-N by budget only
    if not results:
        for s, breakdown, catalog_item, db_item in scored:
            price = catalog_item.get("price")
            if not _price_ok(price, price_filters):
                continue
            name = catalog_item.get("name", "")
            brand = catalog_item.get("brand", "")
            dedup_key = f"{brand}|{name}".lower()
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            url = catalog_item.get("url", "")
            if not url:
                q = (brand + " " + name).replace(" ", "+")
                url = f"https://parfbar.com/?s={q}" if store == "parfbar" else f"https://profumum.ru/catalog/?q={q}"
            source_item = db_item if db_item else {}
            reason = _build_reason(source_item, answers, store, catalog_item)
            results.append({
                "name": name, "brand": brand, "price": price,
                "sample_price": catalog_item.get("sample_price"),
                "sample_size": catalog_item.get("sample_size"),
                "image_url": catalog_item.get("image_url", ""),
                "url": url, "score": s,
                "accords": (db_item.get("accords") or []) if db_item else [],
                "reason": reason, "score_details": breakdown,
            })
            if len(results) == top_n:
                break

    return results


# ── Biblioteka ароматов (собственный бренд, своя система выдачи) ───────────────
# Их товаров нет в Sephora DB, поэтому скоринг идёт по полям нашего каталога:
# family + 4 характеристики (longevity/brightness/sweetness/freshness) + настроение
# (ключевые слова в описании/нотах). Образные ответы квиза маппятся сюда.

_LEVEL_ORDER = {"low": 0, "medium": 1, "high": 2}

# Настроение из их подборок → ключевые слова в описании/нотах (рус)
BIBLIOTEKA_MOOD_KEYWORDS: dict[str, list[str]] = {
    "fresh_energy": ["озон", "вода", "водян", "мят", "цитрус", "лимон", "бергамот",
                     "свеж", "бодр", "утро", "лёд", "лед", "морск", "акватик", "трав",
                     "бриз", "ветивер", "зелен", "зелён"],
    "warm_cozy":    ["тепл", "уют", "камин", "кашемир", "дерев", "ваниль", "янтар",
                     "амбр", "сандал", "смол", "балз", "плед", "какао", "кедр", "орех"],
    "seduction":    ["соблазн", "страст", "кожа", "мускус", "шлейф", "ночь", "чёрн",
                     "черн", "табак", "афродизиак", "чувствен", "поцелуй", "обнаж"],
    "mystery":      ["туман", "замок", "мистик", "дым", "ладан", "землист", "тёмн",
                     "темн", "призрак", "тайн", "камен", "сталь", "метал", "ведьм", "ночн"],
    "tender":       ["нежн", "пудр", "мускус", "чист", "молочн", "цвет", "лёгк",
                     "легк", "мыльн", "пион", "ирис", "хлопок", "кожа младенц"],
    "gourmand_joy": ["карамель", "ваниль", "крем", "сладк", "десерт", "груш",
                     "шоколад", "сахар", "брюле", "печень", "мёд", "мед", "ягод", "сдоб",
                     "морожен", "фисташк", "пломбир", "орех", "фундук", "ирис"],
}

BIBLIOTEKA_OCCASION_KEYWORDS: dict[str, list[str]] = {
    "daily":   ["повседневн", "каждый", "везде", "всегда", "универсальн", "лёгк"],
    "evening": ["вечер", "ночной", "романтик", "свидани", "соблазн", "притяжени"],
    "office":  ["офис", "работ", "деловой", "сдержанн", "строг", "ненавязчив"],
    "special": ["особый", "праздник", "торжество", "запомн", "незабываем", "восхищает"],
}

# Семейство нот → ключевые слова (fallback, если поле family пустое или не совпало)
BIBLIOTEKA_FAMILY_KEYWORDS: dict[str, list[str]] = {
    "floral":   ["цвет", "роза", "жасмин", "пион", "ирис", "черёмух", "черемух",
                 "ландыш", "фиалк", "флёрдоранж", "тубероз"],
    "gourmand": ["ваниль", "карамель", "крем", "шоколад", "сахар", "десерт", "брюле",
                 "мёд", "мед", "груш", "ягод", "печень", "сдоб", "какао"],
    "woody":    ["дерев", "сандал", "кедр", "пачул", "ветивер", "смол", "древес", "гваяк"],
    "aquatic":  ["вода", "водян", "морск", "озон", "акватик", "солён", "солен", "бриз", "океан"],
    "green":    ["трав", "зелён", "зелен", "лист", "мят", "мох", "лужай"],
    "citrus":   ["цитрус", "лимон", "бергамот", "апельсин", "грейпфрут", "мандарин", "лайм"],
    "mineral":  ["минерал", "камен", "сталь", "метал", "земл", "порох", "туман", "озон"],
    "tobacco":  ["табак", "кожа", "ром", "виски", "дым", "замш"],
}


def _load_biblioteka_list() -> list[dict]:
    global _BIBLIOTEKA_LIST
    if _BIBLIOTEKA_LIST is None:
        path = DATA_DIR / "fragrances_biblioteka.json"
        if path.exists():
            _BIBLIOTEKA_LIST = json.loads(path.read_text())
        else:
            _BIBLIOTEKA_LIST = []
    return _BIBLIOTEKA_LIST


def _score_biblioteka_item(item: dict, answers: dict) -> tuple[int, dict]:
    score = 0
    matched = {"families": [], "axes": [], "mood": []}
    text = (item.get("description", "") + " " + item.get("notes", "")).lower()

    # Семейства нот (multi)
    fams = answers.get("b_families") or []
    if isinstance(fams, str):
        fams = [fams]
    item_family = (item.get("family") or "").lower()
    for f in fams:
        if item_family and item_family == f:
            score += 5
            if f not in matched["families"]:
                matched["families"].append(f)
        else:
            for kw in BIBLIOTEKA_FAMILY_KEYWORDS.get(f, []):
                if kw in text:
                    score += 1
                    if f not in matched["families"]:
                        matched["families"].append(f)
                    break

    # Характеристики: точное совпадение +3, соседний уровень +1
    for axis, akey in [("sweetness", "b_sweetness"), ("freshness", "b_freshness"),
                       ("brightness", "b_brightness")]:
        want = answers.get(akey)
        have = (item.get(axis) or "").lower()
        if want in _LEVEL_ORDER and have in _LEVEL_ORDER:
            d = abs(_LEVEL_ORDER[want] - _LEVEL_ORDER[have])
            if d == 0:
                score += 3
                matched["axes"].append(axis)
            elif d == 1:
                score += 1

    # Настроение → ключевые слова (макс 3 совпадения, чтобы не перевешивать)
    mood = answers.get("b_mood", "")
    mood_hits = 0
    for kw in BIBLIOTEKA_MOOD_KEYWORDS.get(mood, []):
        if kw in text and mood_hits < 3:
            score += 2
            mood_hits += 1
            matched["mood"].append(kw)

    # Повод → ключевые слова (макс 3 совпадения)
    occasion = answers.get("b_occasion", "")
    occ_hits = 0
    matched["occasion"] = []
    for kw in BIBLIOTEKA_OCCASION_KEYWORDS.get(occasion, []):
        if kw in text and occ_hits < 3:
            score += 2
            occ_hits += 1
            matched["occasion"].append(kw)

    return score, matched


def _biblioteka_reason(item: dict, matched: dict) -> str:
    parts = []
    descr = []
    if (item.get("sweetness") or "").lower() == "high":
        descr.append("сладкий")
    if (item.get("freshness") or "").lower() == "high":
        descr.append("свежий")
    elif (item.get("freshness") or "").lower() == "low":
        descr.append("тёплый")
    if (item.get("brightness") or "").lower() == "high":
        descr.append("яркий")
    elif (item.get("brightness") or "").lower() == "low":
        descr.append("тихий")
    if (item.get("longevity") or "").lower() == "high":
        descr.append("стойкий")
    if descr:
        s = ", ".join(descr[:3])
        return s[0].upper() + s[1:] + " — как ты и хотел."
    # если характеристики нейтральные — короткий намёк по нотам
    notes = item.get("notes", "")
    first_notes = [n.strip() for n in notes.split(",") if n.strip()][:2]
    if first_notes:
        return "В сердце — " + ", ".join(first_notes).lower() + "."
    return "Из коллекции «Библиотеки ароматов»."


def _format_biblioteka(item: dict, matched: dict, score: int) -> dict:
    return {
        "name":      item.get("name", ""),
        "brand":     item.get("brand", "Библиотека ароматов"),
        "price":     item.get("price"),
        "image_url": item.get("image_url", ""),
        "url":       item.get("url", ""),
        "score":     score,
        "notes":     item.get("notes", ""),
        "volumes":   item.get("volumes", ""),
        "reason":    _biblioteka_reason(item, matched),
    }


def _recommend_biblioteka(answers: dict, top_n: int = 3) -> list[dict]:
    items = _load_biblioteka_list()
    perfumes = [i for i in items if (i.get("type") or "perfume") != "box"]

    scored = []
    for it in perfumes:
        s, matched = _score_biblioteka_item(it, answers)
        scored.append((s, it, matched))
    scored.sort(key=lambda x: -x[0])

    results, seen = [], set()
    for s, it, matched in scored:
        if s <= 0:
            continue
        key = it.get("name", "").lower()
        if key in seen:
            continue
        seen.add(key)
        results.append(_format_biblioteka(it, matched, s))
        if len(results) == top_n:
            break

    # Fallback: если ничего не набрало баллов — отдать первые top_n
    if not results:
        for it in perfumes[:top_n]:
            results.append(_format_biblioteka(it, {"families": [], "axes": [], "mood": []}, 0))

    return results


def pick_biblioteka_box(answers: dict):
    """Подобрать готовый тематический бокс под настроение/семейства из квиза."""
    items = _load_biblioteka_list()
    boxes = [i for i in items if (i.get("type") or "perfume") == "box"]
    if not boxes:
        return None

    mood = answers.get("b_mood", "")
    fams = answers.get("b_families") or []
    if isinstance(fams, str):
        fams = [fams]
    kws = BIBLIOTEKA_MOOD_KEYWORDS.get(mood, [])

    # ключевые слова выбранных семейств — для матча, когда настроение не сработало
    fam_kws = [kw for f in fams for kw in BIBLIOTEKA_FAMILY_KEYWORDS.get(f, [])]

    def _item_count(b):
        mobj = re.search(r"\d+", b.get("volumes", ""))
        return int(mobj.group()) if mobj else 99

    best, best_key = boxes[0], (-1, 0)
    for b in boxes:
        # Только название+описание: у части боксов в notes склеены ноты всех
        # ароматов набора — этот «шум» иначе перебивает тематический матч.
        text = (b.get("name", "") + " " + b.get("description", "")).lower()
        # Совпадение поля family — доминирующий сигнал (точная тема набора).
        # Ключевые слова — лишь добивка с потолком.
        fam_field = 10 if (b.get("family") or "").lower() in fams else 0
        mood_hits = min(sum(1 for kw in kws if kw in text), 3)
        fam_kw_hits = min(sum(1 for kw in fam_kws if kw in text), 2)
        sc = fam_field + mood_hits + fam_kw_hits
        # Тай-брейк: при равном счёте берём меньший набор (он тематичнее
        # generic-боксов на 10 ароматов).
        key = (sc, -_item_count(b))
        if key > best_key:
            best_key, best = key, b

    return {
        "name":      best.get("name", ""),
        "price":     best.get("price"),
        "image_url": best.get("image_url", ""),
        "url":       best.get("url", ""),
        "description": best.get("description", ""),
    }


if __name__ == "__main__":
    print("=== Sephora: oud + night ===")
    test = {"gender": "self", "notes": ["oud", "amber"], "vibe": ["night"], "season": ["winter"]}
    recs = recommend_from_db(test, store="sephora")
    for r in recs:
        print(f"{r['score']:3d}  {r['brand']} — {r['name']}")
        print(f"       {r['reason']}")

    print("\n=== Parfbar: dark_sexy + leather + night_out ===")
    test2 = {"branch": "dark_sexy", "sub_type": ["leather", "tobacco"], "vibe": ["night_out"],
             "notes": ["leather", "tobacco"], "gender": "self"}
    recs2 = recommend_from_db(test2, store="parfbar")
    for r in recs2:
        print(f"{r['score']:3d}  {r['brand']} — {r['name']}")
        print(f"       {r['reason']}")

    print("\n=== Parfbar: fresh_clean + marine ===")
    test3 = {"branch": "fresh_clean", "sub_type": ["marine", "citrus"], "vibe": ["luxury_hotel"],
             "notes": ["citrus", "marine"], "gender": "self"}
    recs3 = recommend_from_db(test3, store="parfbar")
    for r in recs3:
        print(f"{r['score']:3d}  {r['brand']} — {r['name']}")
        print(f"       {r['reason']}")
