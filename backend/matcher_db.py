"""
Matcher using fragrances_db.json (76k combined database).
Used by both Sephora and Parfbar versions.
"""
import json
from pathlib import Path

_DB = None
_DB_LOOKUP = None   # key → db item, for O(1) catalog lookup
_PARFBAR = None
_PROFUMUM = None

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

GENDER_MAP = {
    "self":        None,
    "unisex":      None,
    "gift_male":   "men",
    "gift_female": "women",
}


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
    all_notes = (db_notes_str + " " + catalog_notes).lower()

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
        parts.append(f"Ноты: {', '.join(matched_notes[:3])}.")

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
            parts.append(f"Вайб: {', '.join(matched_accords[:2])}.")
            break

    if not parts and item.get("accords"):
        parts.append(f"Аккорды: {', '.join(item['accords'][:3])}.")
    elif not parts and catalog_item:
        # For items without DB data, use catalog notes snippet
        top = catalog_item.get("top_notes", "")
        if top:
            parts.append(f"Ноты: {top[:40]}.")

    brands = answers.get("brands") or []
    if any(b.lower() in (item.get("brand") or catalog_item.get("brand") if catalog_item else "").lower()
           for b in brands):
        parts.append("Твой бренд.")

    store_label = {
        "sephora": "Найти на Sephora",
        "parfbar": "Купить на Parfbar",
        "profumum": "Купить на Profumum.ru",
    }
    parts.append(store_label.get(store, "Найти в магазине") + ".")
    return " ".join(parts[:3])


def recommend_from_db(answers: dict, store: str = "sephora", top_n: int = 5) -> list[dict]:
    if store in ("parfbar", "profumum"):
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
    catalog = _load_parfbar() if store == "parfbar" else _load_profumum()
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
            "image_url":    catalog_item.get("image_url", ""),
            "url":          url,
            "score":        s,
            "accords":      (db_item.get("accords") or []) if db_item else [],
            "reason":       reason,
            "score_details": breakdown,
        })

        if len(results) == top_n:
            break

    return results


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
