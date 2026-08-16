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

        # Extract post images and captions (alt text = post caption on Instagram)
        post_image_urls = []
        post_captions = []
        try:
            imgs = page.query_selector_all("img")
            for img in imgs:
                src = img.get_attribute("src") or ""
                alt = (img.get_attribute("alt") or "").strip()
                # Skip profile photo and highlight covers (alt starts with "Фото профиля")
                if alt.startswith("Фото профиля") or not src:
                    continue
                if "cdninstagram.com" in src or "fbcdn.net" in src:
                    if src not in post_image_urls:
                        post_image_urls.append(src)
                    if alt and alt not in post_captions:
                        post_captions.append(alt)
                if len(post_image_urls) >= 3:
                    break
        except Exception:
            pass

        browser.close()

    profile = _parse_instagram_text(text, url)
    profile["post_image_urls"] = post_image_urls
    profile["post_captions"] = post_captions
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


def analyze_with_claude(profile: dict, lang: str = "ru") -> dict:
    import anthropic

    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY не найден в .env")

    client = anthropic.Anthropic(api_key=api_key)

    captions_str = "; ".join(profile.get("post_captions", []))
    profile_text = (
        f"Name: {profile.get('name', '')}\n"
        f"Username: @{profile.get('username', '')}\n"
        f"Bio: {profile.get('bio', '')}\n"
        f"Highlights: {', '.join(profile.get('highlights', []))}\n"
        f"Recent post captions: {captions_str}\n"
        f"Followers: {profile.get('followers', 0)}"
    )

    # Build message content — prepend post images if available, track count
    content: list = []
    images_loaded = 0
    for img_url in profile.get("post_image_urls", [])[:2]:
        img_data = _fetch_image_b64(img_url)
        if img_data:
            data, mt = img_data
            content.append({
                "type": "image",
                "source": {"type": "base64", "media_type": mt, "data": data},
            })
            images_loaded += 1

    # Ask for post_descriptions only when images actually loaded (avoids hallucinations)
    out_lang = "Russian" if lang == "ru" else "English"
    notes_example = '"бергамот", "белый мускус", "пион"' if lang == "ru" \
        else '"bergamot", "white musk", "peony"'
    desc_field = (
        f',\n  "post_descriptions": array of 1 short {out_lang} sentence per loaded image '
        '— what you actually see (outfit, setting, mood). Only describe what is visible.'
        if images_loaded > 0 else ""
    )

    prompt = f"""You are a perfume expert. Analyze this Instagram profile{"and the post images above" if images_loaded > 0 else ""} to determine the person's fragrance personality.

Profile:
{profile_text}

Return ONLY valid JSON with these exact fields. Always pick the closest matching value — never return "unknown" or "unable to determine":
{{
  "age_group": one of exactly: "teen", "young_adult", "adult", "mature",
  "aesthetic": one of exactly: "clean_minimal", "dark_moody", "boho", "glam_luxury", "sporty_fresh", "artistic", "preppy",
  "lifestyles": array of 1-3 items from exactly: ["fashion", "sport", "travel", "home_cozy", "food", "art_culture", "professional", "outdoor"],
  "dominant_vibe": one of exactly: "fresh", "warm_cozy", "sweet", "woody", "floral", "oriental", "clean",
  "notes_hint": array of 3-5 specific fragrance notes in {out_lang} (e.g. {notes_example}),
  "reasoning": one sentence in {out_lang} explaining the fragrance choice{desc_field}
}}"""

    content.append({"type": "text", "text": prompt})

    last_err: Exception | None = None
    for attempt in range(2):
        try:
            msg = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=700,
                messages=[{"role": "user", "content": content}],
            )
            raw = (msg.content[0].text or "").strip()
            if not raw:
                last_err = ValueError("Claude вернул пустой ответ")
                continue
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if not m:
                last_err = ValueError(f"Нет JSON в ответе Claude: {raw[:120]}")
                continue
            result = json.loads(m.group(0))
            result.setdefault("post_descriptions", [])
            return result
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            last_err = e
            continue

    raise ValueError(f"Не удалось получить анализ после 2 попыток — попробуй ещё раз ({last_err})")


# RU + EN keys merged: the LLM answers in the profile language (lang param),
# and lookup works either way — no silent misses when the language switches
_NOTES_REVERSE: dict[str, str] = {
    "бергамот": "citrus", "лимон": "citrus", "грейпфрут": "citrus",
    "апельсин": "citrus", "мандарин": "citrus", "юзу": "citrus", "цитрус": "citrus",
    "bergamot": "citrus", "lemon": "citrus", "grapefruit": "citrus",
    "orange": "citrus", "mandarin": "citrus", "yuzu": "citrus", "citrus": "citrus",
    "роза": "rose", "жасмин": "rose", "пион": "rose", "тубероза": "rose",
    "нероли": "rose", "флоральные ноты": "rose",
    "rose": "rose", "jasmine": "rose", "peony": "rose", "tuberose": "rose",
    "neroli": "rose", "floral notes": "rose",
    "уд": "oud", "ладан": "oud", "мирра": "oud",
    "oud": "oud", "incense": "oud", "myrrh": "oud", "frankincense": "oud", "agarwood": "oud",
    "ваниль": "vanilla", "бобы тонка": "vanilla", "тонка": "vanilla",
    "vanilla": "vanilla", "tonka bean": "vanilla", "tonka": "vanilla",
    "ветивер": "vetiver", "пачули": "vetiver",
    "vetiver": "vetiver", "patchouli": "vetiver", "oakmoss": "vetiver",
    "амбра": "amber", "серая амбра": "amber", "амброксан": "amber",
    "amber": "amber", "ambergris": "amber", "ambroxan": "amber", "labdanum": "amber",
    "персик": "fruits", "груша": "fruits", "малина": "fruits", "вишня": "fruits",
    "peach": "fruits", "pear": "fruits", "raspberry": "fruits", "cherry": "fruits",
    "apple": "fruits", "plum": "fruits", "blackcurrant": "fruits",
    "морской": "marine", "морская соль": "marine", "океан": "marine",
    "marine": "marine", "sea salt": "marine", "ocean": "marine", "aquatic": "marine",
    "шафран": "spicy", "перец": "spicy", "розовый перец": "spicy",
    "кардамон": "spicy", "корица": "spicy", "имбирь": "spicy",
    "saffron": "spicy", "pepper": "spicy", "pink pepper": "spicy",
    "cardamom": "spicy", "cinnamon": "spicy", "ginger": "spicy",
    "кедр": "woody", "сандал": "woody", "сандалвуд": "woody", "сандаловое дерево": "woody",
    "cedar": "woody", "cedarwood": "woody", "sandalwood": "woody",
    "кожа": "leather", "замша": "leather",
    "leather": "leather", "suede": "leather",
    "табак": "tobacco",
    "tobacco": "tobacco",
    "мускус": "musk", "белый мускус": "musk", "зелёный чай": "musk",
    "musk": "musk", "white musk": "musk", "green tea": "musk",
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
    vibes += [v for v in _AESTHETIC_VIBES.get(analysis.get("aesthetic", ""), [])
              if v not in vibes]

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


# How many IG-derived vibes survive the merge with quiz answers. social_to_answers
# returns up to 4, a quiz gives 1-2 — unclamped, IG would shout the quiz down.
# ponytail: calibrated by eye on 2; retune on live /match runs with real profiles.
IG_MAX_VIBES = 2


def merge_answers(quiz: dict, ig: dict) -> dict:
    """Combine quiz + Instagram answers for one scoring pass.
    Lists → union (quiz values first), strings → quiz wins if non-empty."""
    ig = dict(ig or {})
    if ig.get("vibe"):
        ig["vibe"] = ig["vibe"][:IG_MAX_VIBES]
    merged = dict(ig)
    for k, v in (quiz or {}).items():
        if isinstance(v, list):
            base = [x for x in v]
            for x in (ig.get(k) or []):
                if x not in base:
                    base.append(x)
            merged[k] = base
        elif v:
            merged[k] = v
    return merged


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

_ACCORD_DESC_EN: dict[str, str] = {
    "citrus":    "citrusy and light",
    "fresh":     "fresh and clean",
    "clean":     "clean, almost invisible",
    "aquatic":   "marine and refreshing",
    "aromatic":  "aromatic and confident",
    "powdery":   "soft and powdery",
    "floral":    "floral and refined",
    "woody":     "woody and understated",
    "musky":     "musky and magnetic",
    "amber":     "warm and sensual",
    "warm":      "enveloping and cozy",
    "spicy":     "spicy and memorable",
    "oriental":  "oriental and deep",
    "vanilla":   "sweet and enveloping",
    "green":     "green and alive",
    "leathery":  "leathery and bold",
    "gourmand":  "gourmand and seductive",
}

_LIFESTYLE_CONTEXT_EN: dict[str, str] = {
    "professional": "made for a confident business presence",
    "travel":       "a companion for every trip",
    "fashion":      "underlines a personal sense of style",
    "sport":        "energizing and effortless",
    "home_cozy":    "brings warmth and comfort",
    "art_culture":  "for a creative, open-minded person",
    "food":         "sensual — for special evenings",
    "outdoor":      "breathes in the open air",
}


def _fallback_reason(analysis: dict, rec: dict, lang: str = "ru") -> str:
    accords = [a.lower() for a in (rec.get("accords") or [])]
    lifestyles = analysis.get("lifestyles", [])
    priority = ["citrus", "fresh", "clean", "aquatic", "aromatic", "floral",
                "powdery", "woody", "musky", "amber", "warm", "spicy", "vanilla",
                "oriental", "green", "leathery", "gourmand"]
    key = next((a for a in priority if a in accords), accords[0] if accords else "")
    if lang == "en":
        desc = _ACCORD_DESC_EN.get(key, "a refined fragrance")
        context = _LIFESTYLE_CONTEXT_EN.get(lifestyles[0] if lifestyles else "", "for any occasion")
    else:
        desc = _ACCORD_DESC.get(key, "изысканный аромат")
        context = _LIFESTYLE_CONTEXT.get(lifestyles[0] if lifestyles else "", "к любому поводу")
    return f"{desc[0].upper()}{desc[1:]} — {context}."


def generate_reasons(analysis: dict, recs: list[dict], post_captions: list[str] | None = None,
                     lang: str = "ru") -> list[str]:
    """One Claude call → unique personalized reason for each fragrance."""
    import anthropic

    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return [_fallback_reason(analysis, r, lang) for r in recs]

    captions = post_captions or []

    frags = "\n".join([
        f"{i+1}. {r['brand']} — {r['name']} ({', '.join((r.get('accords') or [])[:3])})"
        for i, r in enumerate(recs)
    ])

    if lang == "en":
        post_ctx = ("Post captions: " + "; ".join(captions) + ".") if captions else ""
        prompt = (
            f"You are a perfume expert. For each fragrance write a unique one-sentence "
            f"explanation in English — why it suits this specific person.\n\n"
            f"Profile: {analysis.get('aesthetic')} style, {analysis.get('dominant_vibe')} vibe, "
            f"lifestyle: {', '.join(analysis.get('lifestyles', []))}.\n"
            f"{post_ctx}\n\n"
            f"Fragrances:\n{frags}\n\n"
            f"Return ONLY a JSON array of {len(recs)} strings: [\"reason1\", \"reason2\", ...]\n"
            f"Each reason must be unique. Mention concrete details from the posts or lifestyle."
        )
    else:
        post_ctx = ("Подписи к постам: " + "; ".join(captions) + ".") if captions else ""
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
        raw = (msg.content[0].text or "").strip()
        m = re.search(r"\[.*\]", raw, re.DOTALL)
        if m:
            reasons = json.loads(m.group(0))
            if isinstance(reasons, list) and len(reasons) == len(recs):
                return reasons
    except Exception:
        pass

    return [_fallback_reason(analysis, r, lang) for r in recs]


def generate_profile_and_reasons(analysis: dict, quiz_answers: dict, recs: list[dict],
                                 post_captions: list[str] | None = None) -> dict:
    """One Claude call → scent-profile card (headline + summary) and a unique
    reason per fragrance. English only — used by /match. Works with or without
    IG analysis; falls back to templates without an API key."""
    import anthropic

    _load_env()
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    def fallback():
        branch = (quiz_answers or {}).get("branch", "")
        headline = {
            "fresh_clean": "The Fresh Minimalist", "warm_cozy": "The Warm Soul",
            "dark_sexy": "The Night Presence", "elegant_luxury": "The Quiet Luxe",
            "artistic_niche": "The Original", "soft_skin": "The Second Skin",
        }.get(branch, "Your Scent Profile")
        return {
            "headline": headline,
            "summary": "Matched from your quiz answers across scent direction, "
                       "favorite notes and the moments you dress for.",
            "reasons": [_fallback_reason(analysis or {}, r, "en") for r in recs],
        }

    if not api_key:
        return fallback()

    ig_ctx = ""
    if analysis:
        ig_ctx = (
            f"From their Instagram: {analysis.get('aesthetic')} aesthetic, "
            f"{analysis.get('dominant_vibe')} vibe, lifestyle: {', '.join(analysis.get('lifestyles', []))}. "
            f"Analysis note: {analysis.get('reasoning', '')}\n"
        )
        if post_captions:
            ig_ctx += "Post captions: " + "; ".join(post_captions) + ".\n"

    frags = "\n".join([
        f"{i+1}. {r['brand']} — {r['name']} ({', '.join((r.get('accords') or [])[:3])})"
        for i, r in enumerate(recs)
    ])

    prompt = (
        f"You are a perfume expert writing a personal scent profile for a client.\n\n"
        f"{ig_ctx}"
        f"From their quiz: scent direction '{quiz_answers.get('branch', '')}', "
        f"vibes {quiz_answers.get('vibe', [])}, favorite notes {quiz_answers.get('notes', [])}, "
        f"occasions {quiz_answers.get('occasion', [])}.\n\n"
        f"Their matched fragrances:\n{frags}\n\n"
        f"Return ONLY valid JSON:\n"
        f'{{"headline": "a 2-4 word archetype name for this person (e.g. \'The Midnight Minimalist\')",\n'
        f' "summary": "2 sentences in English: who this person is scent-wise and why these picks fit; '
        f'mention a concrete detail from their Instagram if provided",\n'
        f' "reasons": [{len(recs)} unique one-sentence explanations, one per fragrance in order]}}'
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (msg.content[0].text or "").strip()
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            if (isinstance(data.get("reasons"), list) and len(data["reasons"]) == len(recs)
                    and data.get("headline") and data.get("summary")):
                return data
    except Exception:
        pass
    return fallback()


_VIBE_TO_BMOOD: dict[str, str] = {
    "fresh":     "fresh_energy",
    "clean":     "fresh_energy",
    "warm_cozy": "warm_cozy",
    "sweet":     "gourmand_joy",
    "floral":    "tender",
    "oriental":  "seduction",
    "woody":     "warm_cozy",
}

_VIBE_TO_BFAMILIES: dict[str, list[str]] = {
    "fresh":     ["aquatic", "citrus", "green"],
    "clean":     ["aquatic", "citrus"],
    "warm_cozy": ["woody", "gourmand"],
    "sweet":     ["gourmand", "floral"],
    "floral":    ["floral"],
    "oriental":  ["tobacco", "woody"],
    "woody":     ["woody"],
}

_LIFESTYLE_TO_BOCCASION: dict[str, str] = {
    "professional": "office",
    "travel":       "daily",
    "fashion":      "special",
    "sport":        "daily",
    "home_cozy":    "daily",
    "art_culture":  "special",
    "outdoor":      "daily",
    "food":         "daily",
}


def social_to_biblioteka_answers(analysis: dict) -> dict:
    vibe = analysis.get("dominant_vibe", "")
    aesthetic = analysis.get("aesthetic", "")
    lifestyles = analysis.get("lifestyles", [])

    b_mood = _VIBE_TO_BMOOD.get(vibe, "fresh_energy")
    if aesthetic == "dark_moody" and b_mood == "fresh_energy":
        b_mood = "mystery"

    b_families = list(_VIBE_TO_BFAMILIES.get(vibe, ["aquatic"]))

    b_occasion = _LIFESTYLE_TO_BOCCASION.get(lifestyles[0] if lifestyles else "", "daily")

    return {
        "b_mood":      b_mood,
        "b_occasion":  b_occasion,
        "b_families":  b_families,
        "b_sweetness": "",
        "b_freshness": "",
        "b_brightness": "",
        "b_format":    "",
    }


def analyze_instagram(url: str) -> dict:
    from matcher_db import recommend_from_db, pick_biblioteka_box

    profile = fetch_instagram_profile(url)
    analysis = analyze_with_claude(profile)

    # Parfbar recommendations
    answers = social_to_answers(analysis)
    recs = recommend_from_db(answers, store="parfbar", top_n=5)
    reasons = generate_reasons(analysis, recs, post_captions=profile.get("post_captions", []))
    for rec, reason in zip(recs, reasons):
        rec["reason"] = reason

    # Biblioteka recommendations
    bib_answers = social_to_biblioteka_answers(analysis)
    bib_recs = recommend_from_db(bib_answers, store="biblioteka", top_n=3)
    bib_box = pick_biblioteka_box(bib_answers)
    bib_reasons = generate_reasons(analysis, bib_recs, post_captions=profile.get("post_captions", []))
    for rec, reason in zip(bib_recs, bib_reasons):
        rec["reason"] = reason

    return {
        "profile": profile,
        "analysis": analysis,
        "answers": answers,
        "recommendations": recs,
        "biblioteka": {
            "fragrances": bib_recs,
            "box": bib_box,
        },
        "success": True,
    }


def analyze_instagram_light(url: str, lang: str = "en") -> dict:
    """Profile → analysis → answers, no recommendations. Used by /match,
    where scoring happens later in /api/recommend/combined."""
    profile = fetch_instagram_profile(url)
    # Login-wall / nonexistent / empty profile: the scraper "succeeds" on the
    # error page (its text lands in bio!) and the LLM hallucinates an aesthetic
    # out of nothing. Real signal = followers/posts/captions/highlights, not bio.
    if not (profile.get("followers") or profile.get("posts")
            or profile.get("post_captions") or profile.get("highlights")):
        return {"success": False, "error": "profile unavailable or empty"}
    analysis = analyze_with_claude(profile, lang=lang)
    return {
        "analysis": analysis,
        "answers": social_to_answers(analysis),
        "post_captions": profile.get("post_captions", []),
        "username": profile.get("username", ""),
        "success": True,
    }


if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.instagram.com/anastaasia.sh/"
    result = analyze_instagram(url)
    print(json.dumps(result, ensure_ascii=False, indent=2))
