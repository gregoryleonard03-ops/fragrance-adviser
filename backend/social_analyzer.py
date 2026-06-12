"""
Instagram profile → fragrance personality analyzer.
Fetches public profile with Playwright, analyzes with Claude API (incl. Vision).
"""
from __future__ import annotations

import base64
import json
import os
import re
import time
from pathlib import Path


def _load_env():
    for env_path in [Path(__file__).parent / ".env", Path(__file__).parent.parent / ".env"]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def _fetch_image_b64(url: str) -> tuple[str, str] | None:
    """Download image, return (base64_data, media_type) or None on failure."""
    try:
        import requests
        r = requests.get(url, timeout=5, headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.instagram.com/",
        })
        if r.status_code == 200:
            mt = r.headers.get("content-type", "image/jpeg").split(";")[0]
            return base64.b64encode(r.content).decode(), mt
    except Exception:
        pass
    return None


def fetch_instagram_profile(url: str) -> dict:
    from playwright.sync_api import sync_playwright

    url = url.split("?")[0].rstrip("/") + "/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            locale="ru-RU",
        )
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=20000)
        except Exception:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
        time.sleep(2)

        text = page.inner_text("body")

        # Extract post image URLs from the grid (skip tiny avatar thumbnails)
        post_image_urls = []
        try:
            imgs = page.query_selector_all("img[srcset]")
            for img in imgs:
                src = img.get_attribute("src") or ""
                if (
                    "fbcdn.net" in src
                    and "s150x150" not in src
                    and "s320x320" not in src
                    and "p320x320" not in src
                    and src not in post_image_urls
                ):
                    post_image_urls.append(src)
                if len(post_image_urls) >= 3:
                    break
        except Exception:
            pass

        browser.close()

    profile = _parse_instagram_text(text, url)
    profile["post_image_urls"] = post_image_urls
    return profile


def _parse_instagram_text(text: str, url: str) -> dict:
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    username = re.search(r"instagram\.com/([^/?]+)", url)
    username = username.group(1) if username else ""

    name = ""
    bio_lines = []
    highlights = []
    followers = posts = 0

    skip = {
        # English
        "Log In", "Sign Up", "Meta", "About", "Blog", "Jobs", "Help",
        "API", "Privacy", "Terms", "Locations", "Popular", "Contact",
        "Threads", "Instagram Lite", "Meta AI", "Meta Verified",
        # Russian login-wall strings
        "Войти", "Войдите", "Вход", "Зарегистрироваться", "Регистрация",
        "Ещё", "ещё", "Подписаться", "Сообщение", "Электронная почта",
        "Забыли пароль?", "или", "Войдите с помощью Facebook",
    }

    for line in lines:
        if re.match(r"^\d[\d,\.]*\s+(posts?|публикац)", line, re.I):
            m = re.search(r"([\d,]+)", line)
            if m:
                posts = int(m.group(1).replace(",", ""))
        elif re.match(r"^\d[\d,\.]*\s+(followers?|подписчик)", line, re.I):
            m = re.search(r"([\d,]+)", line)
            if m:
                followers = int(m.group(1).replace(",", ""))

    for line in lines:
        if line in skip or line.lower() == username.lower():
            continue
        if re.match(r"^\d", line):
            continue
        if len(line) > 2 and not line.startswith("http"):
            name = line
            break

    name_found = False
    for line in lines:
        if line == name:
            name_found = True
            continue
        if not name_found:
            continue
        if len(line) <= 20 and not re.search(r"[.!?]", line) and not re.match(r"^\d", line):
            if line not in skip and not line.startswith("http"):
                highlights.append(line)
        elif 20 < len(line) < 200:
            if line not in skip and not line.startswith("http"):
                bio_lines.append(line)
        if line in ("Meta", "About"):
            break

    return {
        "name": name,
        "username": username,
        "bio": " ".join(bio_lines[:5]),
        "highlights": [h for h in highlights[:15] if len(h) >= 1],
        "followers": followers,
        "posts": posts,
    }


def analyze_with_claude(profile: dict) -> dict:
    import anthropic

    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY не найден в .env")

    client = anthropic.Anthropic(api_key=api_key)

    profile_text = (
        f"Name: {profile.get('name', '')}\n"
        f"Username: @{profile.get('username', '')}\n"
        f"Bio: {profile.get('bio', '')}\n"
        f"Highlights: {', '.join(profile.get('highlights', []))}\n"
        f"Followers: {profile.get('followers', 0)}"
    )

    prompt = f"""You are a perfume expert. Analyze this Instagram profile (and post images if provided) to determine the person's fragrance personality.

Profile:
{profile_text}

Return ONLY valid JSON with these exact fields. Always pick the closest matching value — never return "unknown" or "unable to determine":
{{
  "age_group": one of exactly: "teen", "young_adult", "adult", "mature",
  "aesthetic": one of exactly: "clean_minimal", "dark_moody", "boho", "glam_luxury", "sporty_fresh", "artistic", "preppy",
  "lifestyles": array of 1-3 items from exactly: ["fashion", "sport", "travel", "home_cozy", "food", "art_culture", "professional", "outdoor"],
  "dominant_vibe": one of exactly: "fresh", "warm_cozy", "sweet", "woody", "floral", "oriental", "clean",
  "notes_hint": array of 3-5 specific fragrance notes in Russian (e.g. "бергамот", "белый мускус", "пион"),
  "reasoning": one sentence in Russian explaining the fragrance choice,
  "post_descriptions": array of 1-2 sentences in Russian describing each visible post image — empty array if no images
}}"""

    # Build message content — prepend post images if available
    content: list = []
    for img_url in profile.get("post_image_urls", [])[:2]:
        img_data = _fetch_image_b64(img_url)
        if img_data:
            data, mt = img_data
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mt, "data": data},
            })
    content.append({"type": "text", "text": prompt})

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        messages=[{"role": "user", "content": content}],
    )

    raw = msg.content[0].text.strip()
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        raw = m.group(0)
    result = json.loads(raw)
    result.setdefault("post_descriptions", [])
    return result


_NOTES_REVERSE: dict[str, str] = {
    "бергамот": "citrus", "лимон": "citrus", "грейпфрут": "citrus",
    "апельсин": "citrus", "мандарин": "citrus", "юзу": "citrus", "цитрус": "citrus",
    "роза": "rose", "жасмин": "rose", "пион": "rose", "тубероза": "rose",
    "нероли": "rose", "флоральные ноты": "rose",
    "уд": "oud", "ладан": "oud", "мирра": "oud",
    "ваниль": "vanilla", "бобы тонка": "vanilla", "тонка": "vanilla",
    "ветивер": "vetiver", "пачули": "vetiver",
    "амбра": "amber", "серая амбра": "amber", "амброксан": "amber",
    "персик": "fruits", "груша": "fruits", "малина": "fruits", "вишня": "fruits",
    "морской": "marine", "морская соль": "marine", "океан": "marine",
    "шафран": "spicy", "перец": "spicy", "розовый перец": "spicy",
    "кардамон": "spicy", "корица": "spicy", "имбирь": "spicy",
    "кедр": "woody", "сандал": "woody", "сандалвуд": "woody", "сандаловое дерево": "woody",
    "кожа": "leather", "замша": "leather",
    "табак": "tobacco",
    "мускус": "musk", "белый мускус": "musk", "зелёный чай": "musk",
}

_DOMINANT_VIBE_MAP: dict[str, list[str]] = {
    "fresh":     ["beach", "scandinavian_minimal"],
    "warm_cozy": ["night", "cashmere_fireplace"],
    "sweet":     ["fruits", "sunday_morning"],
    "woody":     ["forest", "nordic_cabin"],
    "floral":    ["snow", "expensive_calm"],
    "oriental":  ["east", "night_out"],
    "clean":     ["beach", "just_showered"],
}

_AESTHETIC_VIBES: dict[str, list[str]] = {
    "clean_minimal": ["scandinavian_minimal", "rich_clean_person"],
    "dark_moody":    ["dark_elegance", "dangerous"],
    "boho":          ["desert_midnight", "art_gallery"],
    "glam_luxury":   ["expensive_calm", "wealth_no_logos"],
    "sporty_fresh":  ["sporty_expensive"],
    "artistic":      ["art_gallery", "intellectual"],
    "preppy":        ["clean_status", "expensive_calm"],
}

_LIFESTYLE_OCCASION: dict[str, str] = {
    "professional": "office",
    "travel":       "travel",
    "fashion":      "special",
    "sport":        "sport",
    "home_cozy":    "cozy_evening",
    "art_culture":  "collection",
    "food":         "restaurants",
    "outdoor":      "travel",
}


def social_to_answers(analysis: dict) -> dict:
    vibes = list(_DOMINANT_VIBE_MAP.get(analysis.get("dominant_vibe", ""), []))
    vibes += _AESTHETIC_VIBES.get(analysis.get("aesthetic", ""), [])

    notes = []
    for note in analysis.get("notes_hint", []):
        key = _NOTES_REVERSE.get(note.lower())
        if key and key not in notes:
            notes.append(key)

    occasions = []
    for ls in analysis.get("lifestyles", []):
        occ = _LIFESTYLE_OCCASION.get(ls)
        if occ and occ not in occasions:
            occasions.append(occ)

    # Floral boost for young women (not dark aesthetic)
    if (
        analysis.get("age_group") in ("teen", "young_adult")
        and analysis.get("aesthetic") != "dark_moody"
    ):
        if "snow" not in vibes and "floral" not in vibes:
            vibes.append("snow")  # snow → White Floral, Powdery, Fresh, Iris
        if "rose" not in notes:
            notes.append("rose")

    return {
        "vibe":     vibes[:4],
        "notes":    notes,
        "occasion": occasions,
        "gender":   "",
        "budget":   [],
        "season":   [],
    }


_ACCORD_DESC: dict[str, str] = {
    "citrus":    "цитрусовый и лёгкий",
    "fresh":     "свежий и чистый",
    "clean":     "чистый, почти невидимый",
    "aquatic":   "морской, освежающий",
    "aromatic":  "ароматный и уверенный",
    "powdery":   "нежный и пудровый",
    "floral":    "цветочный и изысканный",
    "woody":     "древесный и сдержанный",
    "musky":     "мускусный и притягивающий",
    "amber":     "тёплый и чувственный",
    "warm":      "обволакивающий и уютный",
    "spicy":     "пряный и запоминающийся",
    "oriental":  "восточный и глубокий",
    "vanilla":   "сладкий и обволакивающий",
    "green":     "зелёный, живой",
    "leathery":  "кожаный и смелый",
    "gourmand":  "гурманский, соблазнительный",
}

_LIFESTYLE_CONTEXT: dict[str, str] = {
    "professional": "для уверенного делового образа",
    "travel":       "спутник в любом путешествии",
    "fashion":      "подчёркивает индивидуальный стиль",
    "sport":        "бодрит и не устаёт",
    "home_cozy":    "создаёт уют и тепло",
    "art_culture":  "для творческого и открытого человека",
    "food":         "чувственный — для особых вечеров",
    "outdoor":      "дышит на свежем воздухе",
}


def _fallback_reason(analysis: dict, rec: dict) -> str:
    accords = [a.lower() for a in (rec.get("accords") or [])]
    lifestyles = analysis.get("lifestyles", [])
    priority = ["citrus", "fresh", "clean", "aquatic", "aromatic", "floral",
                "powdery", "woody", "musky", "amber", "warm", "spicy", "vanilla",
                "oriental", "green", "leathery", "gourmand"]
    key = next((a for a in priority if a in accords), accords[0] if accords else "")
    desc = _ACCORD_DESC.get(key, "изысканный аромат")
    context = _LIFESTYLE_CONTEXT.get(lifestyles[0] if lifestyles else "", "к любому поводу")
    return f"{desc[0].upper()}{desc[1:]} — {context}."


def generate_reasons(analysis: dict, recs: list[dict]) -> list[str]:
    """One Claude call → unique personalized reason for each fragrance."""
    import anthropic

    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return [_fallback_reason(analysis, r) for r in recs]

    post_ctx = ""
    descs = analysis.get("post_descriptions", [])
    if descs:
        post_ctx = "Последние посты: " + "; ".join(descs) + "."

    frags = "\n".join([
        f"{i+1}. {r['brand']} — {r['name']} ({', '.join((r.get('accords') or [])[:3])})"
        for i, r in enumerate(recs)
    ])

    prompt = (
        f"Ты эксперт по парфюмерии. Напиши для каждого аромата уникальное объяснение "
        f"(1 предложение, по-русски) — почему он подходит именно этому человеку.\n\n"
        f"Профиль: {analysis.get('aesthetic')} стиль, {analysis.get('dominant_vibe')} вайб, "
        f"образ жизни: {', '.join(analysis.get('lifestyles', []))}.\n"
        f"{post_ctx}\n\n"
        f"Ароматы:\n{frags}\n\n"
        f"Верни ТОЛЬКО JSON массив из {len(recs)} строк: [\"причина1\", \"причина2\", ...]\n"
        f"Каждая причина уникальна. Упоминай конкретные детали из постов или образа жизни."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text.strip()
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            reasons = json.loads(m.group(0))
            if isinstance(reasons, list) and len(reasons) == len(recs):
                return reasons
    except Exception:
        pass

    return [_fallback_reason(analysis, r) for r in recs]


def analyze_instagram(url: str) -> dict:
    from matcher_db import recommend_from_db

    profile = fetch_instagram_profile(url)
    analysis = analyze_with_claude(profile)
    answers = social_to_answers(analysis)
    recs = recommend_from_db(answers, store="parfbar", top_n=5)
    reasons = generate_reasons(analysis, recs)
    for rec, reason in zip(recs, reasons):
        rec["reason"] = reason
    return {
        "profile": profile,
        "analysis": analysis,
        "recommendations": recs,
        "success": True,
    }


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.instagram.com/anastaasia.sh/"
    result = analyze_instagram(url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
