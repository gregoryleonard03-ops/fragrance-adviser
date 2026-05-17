"""
Local fragrance matcher — no external APIs.
Scores each fragrance against user quiz answers and returns top 5.
"""

import json
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "fragrances.json"

# Keywords mapped to quiz answer keys
NOTE_KEYWORDS = {
    "citrus":  ["bergamot", "lemon", "grapefruit", "lime", "orange", "mandarin", "citrus", "neroli"],
    "rose":    ["rose", "jasmine", "peony", "lily", "floral", "violet", "iris", "tuberose", "magnolia"],
    "oud":     ["oud", "agarwood", "sandalwood", "cedar", "wood", "vetiver", "patchouli", "guaiac"],
    "vanilla": ["vanilla", "tonka", "benzoin", "gourmand", "praline", "caramel", "sweet"],
    "vetiver": ["vetiver", "patchouli", "earth", "mossy", "oakmoss", "green", "fougere"],
    "amber":   ["amber", "musk", "animalic", "castoreum", "labdanum", "resin", "balsam"],
    "fruits":  ["peach", "pear", "apple", "berry", "strawberry", "raspberry", "mango", "fruit", "tropical"],
    "marine":  ["marine", "aquatic", "sea", "ocean", "salt", "ozonic", "water", "fresh"],
}

VIBE_KEYWORDS = {
    "forest":  ["wood", "cedar", "pine", "vetiver", "green", "fern", "moss", "earthy", "forest"],
    "beach":   ["marine", "aquatic", "solar", "coconut", "salt", "sea", "fresh", "ozonic"],
    "fruits":  ["fruit", "peach", "pear", "berry", "tropical", "mango", "juicy", "sweet"],
    "night":   ["dark", "intense", "sensual", "night", "mysterious", "smoky", "leather", "oud"],
    "east":    ["oriental", "spice", "oud", "incense", "amber", "saffron", "resin", "warm"],
    "snow":    ["clean", "powdery", "fresh", "soft", "light", "transparent", "iris", "white"],
}

SEASON_KEYWORDS = {
    "summer": ["fresh", "light", "citrus", "aquatic", "clean", "airy", "fruity", "green"],
    "spring": ["floral", "fresh", "light", "green", "dewy", "bright", "citrus", "rose"],
    "winter": ["warm", "rich", "heavy", "spicy", "oriental", "deep", "cozy", "balsam", "resin"],
}

OCCASION_KEYWORDS = {
    "daily":    ["fresh", "clean", "light", "casual", "easy", "versatile", "everyday"],
    "office":   ["clean", "professional", "subtle", "fresh", "light", "inoffensive", "soft"],
    "romantic": ["sensual", "seductive", "warm", "intimate", "floral", "musky", "intense"],
    "event":    ["bold", "luxurious", "opulent", "intense", "statement", "unique", "complex"],
}

GENDER_KEYWORDS = {
    "male":   ["masculine", "woody", "aromatic", "leather", "fougere", "fresh", "spicy"],
    "female": ["feminine", "floral", "sweet", "soft", "powdery", "fruity", "rose"],
    "unisex": ["unisex", "gender-neutral", "androgynous", "clean", "fresh", "woody"],
}

LONGEVITY_KEYWORDS = {
    "light":  ["eau de cologne", "edc", "light", "fresh", "airy"],
    "medium": ["eau de toilette", "edt"],
    "strong": ["eau de parfum", "edp", "parfum", "extrait", "intense", "rich"],
}

TOP_BRANDS = [
    "Chanel", "Dior", "Yves Saint Laurent", "YSL", "Tom Ford",
    "Byredo", "Jo Malone", "Maison Margiela", "Hermès", "Hermes",
    "Gucci", "Versace", "Armani", "Giorgio Armani", "Prada",
    "Marc Jacobs", "Valentino", "Burberry", "Coach", "Viktor&Rolf",
]


def _score_text(text: str, keywords: list[str]) -> int:
    text_lower = text.lower()
    return sum(2 if kw in text_lower else 0 for kw in keywords)


def score_fragrance(fragrance: dict, answers: dict) -> tuple[int, list[str]]:
    score = 0
    matched_notes = []
    desc = fragrance.get("description", "").lower()
    notes = " ".join(fragrance.get("notes", [])).lower()
    combined = desc + " " + notes
    name_lower = fragrance.get("name", "").lower()

    # --- Budget filter (hard) ---
    price = fragrance.get("price", 0)
    budget = answers.get("budget", "")
    if budget == "$50-100" and price > 100:
        return -999, []
    if budget == "$100-200" and (price < 50 or price > 200):
        return -999, []
    if budget == "$200-300" and (price < 100 or price > 300):
        return -999, []
    if budget == "$300+" and price < 200:
        return -999, []

    # --- Brand match (bonus) ---
    frag_brand = fragrance.get("brand", "").lower()
    preferred_brands = answers.get("brands", [])
    for pb in preferred_brands:
        if pb.lower() in frag_brand or frag_brand in pb.lower():
            score += 5
            break

    # --- Notes preference ---
    selected_notes = answers.get("notes", [])
    for note_key in selected_notes:
        kws = NOTE_KEYWORDS.get(note_key, [])
        hits = [kw for kw in kws if kw in combined]
        if hits:
            score += 3 * len(hits)
            matched_notes.extend(hits[:2])

    # --- Vibe ---
    vibe = answers.get("vibe", "")
    if vibe:
        kws = VIBE_KEYWORDS.get(vibe, [])
        score += _score_text(combined, kws)

    # --- Season ---
    season = answers.get("season", "")
    if season:
        kws = SEASON_KEYWORDS.get(season, [])
        score += _score_text(combined, kws)

    # --- Occasion ---
    occasion = answers.get("occasion", "")
    if occasion:
        kws = OCCASION_KEYWORDS.get(occasion, [])
        score += _score_text(combined, kws)

    # --- Gender ---
    gender = answers.get("gender", "")
    if gender and gender != "self":
        target = "male" if gender == "gift_male" else "female" if gender == "gift_female" else "unisex"
        kws = GENDER_KEYWORDS.get(target, [])
        score += _score_text(combined, kws)

    # --- Longevity ---
    longevity = answers.get("longevity", "")
    if longevity:
        kws = LONGEVITY_KEYWORDS.get(longevity, [])
        score += _score_text(combined + " " + name_lower, kws)

    # --- Niche vs mainstream ---
    style = answers.get("style", "")
    is_top_brand = any(b.lower() in frag_brand for b in TOP_BRANDS)
    if style == "niche" and not is_top_brand:
        score += 3
    elif style == "bestseller" and is_top_brand:
        score += 3

    return score, list(set(matched_notes))


def build_reason(fragrance: dict, answers: dict, matched_notes: list[str]) -> str:
    parts = []

    if matched_notes:
        notes_str = ", ".join(matched_notes[:3])
        parts.append(f"Contains {notes_str} notes you love.")

    season_map = {"summer": "warm weather", "spring": "spring & autumn", "winter": "cold weather"}
    season = answers.get("season", "")
    if season and season in season_map:
        parts.append(f"Great for {season_map[season]}.")

    occasion_map = {
        "daily": "everyday wear",
        "office": "office",
        "romantic": "romantic evenings",
        "event": "special occasions",
    }
    occasion = answers.get("occasion", "")
    if occasion and occasion in occasion_map:
        parts.append(f"Perfect for {occasion_map[occasion]}.")

    if not parts:
        parts.append("A great match for your preferences.")

    price = fragrance.get("price", 0)
    if price:
        parts.append(f"${price:.0f} — fits your budget.")

    return " ".join(parts[:3])


def recommend(answers: dict, top_n: int = 5) -> list[dict]:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Fragrance data not found at {DATA_FILE}. Run scraper.py first.")

    with open(DATA_FILE, encoding="utf-8") as f:
        catalog = json.load(f)

    scored = []
    for frag in catalog:
        s, matched = score_fragrance(frag, answers)
        if s > -999:
            scored.append((s, matched, frag))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for s, matched, frag in scored[:top_n]:
        results.append({
            "id": frag.get("id", ""),
            "name": frag.get("name", ""),
            "brand": frag.get("brand", ""),
            "price": frag.get("price", 0),
            "image_url": frag.get("image_url", ""),
            "url": frag.get("url", ""),
            "score": s,
            "reason": build_reason(frag, answers, matched),
        })

    return results


# --- Quick test ---
if __name__ == "__main__":
    test_answers = {
        "gender": "self",
        "budget": "$100-200",
        "occasion": "romantic",
        "season": "winter",
        "notes": ["vanilla", "amber"],
        "longevity": "strong",
        "sillage": "medium",
        "brands": ["Tom Ford"],
        "vibe": "night",
        "style": "niche",
    }
    try:
        recs = recommend(test_answers)
        print(f"\nTop {len(recs)} recommendations:")
        for r in recs:
            print(f"  [{r['score']}] {r['brand']} — {r['name']} (${r['price']})")
            print(f"       {r['reason']}")
    except FileNotFoundError as e:
        print(f"[!] {e}")
        print("Run scraper.py first to build the catalog.")
