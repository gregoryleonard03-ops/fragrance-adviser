# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**Aroma Match** — AI-платформа персонального подбора парфюма. Продаётся владельцам нишевых магазинов (текущий клиент — Profumum.ru). Без внешних AI API — матчинг локальный по ключевым словам.

Главная страница (`/`) — бренд Aroma Match, две карточки: «Profumum — Квиз» (→ `/profumum`) и «О продукте» (→ `/pitch` — продающая презентация в виде scroll-snap HTML-слайдов).

Sephora и Parfbar остались как рабочие прототипы по прямым URL (`/sephora`, `/parfbar`), но **скрыты с главной** — на будущее, для тестов и потенциальной активации.

Брендинг: `frontend/assets/logo_am.png` (вариант лого №5 — AM с распылителем). Единый золотой акцент `--accent` через CSS-переменные: `#b89a6a` (тёмная тема), `#8a7045` (светлая). Тумблер темы ☀/☽ синхронизируется через `localStorage.parfindo-theme` на всех страницах. Внутри квиза Profumum остаётся локальный зелёный `#4a9e6a` — не трогаем.

## Running the project

```bash
# 1. Install dependencies (once)
pip3 install -r backend/requirements.txt
python3 -m playwright install chromium  # only needed for scraper

# 2. Start the server
cd backend
python3 -m uvicorn main:app --port 8000 --reload

# 3. Share publicly (new terminal tab)
cloudflared tunnel --url http://localhost:8000 --no-autoupdate
# or
ssh -R 80:localhost:8000 serveo.net
```

Open: http://localhost:8000

## Architecture

```
backend/
  main.py          — FastAPI: serves frontend + POST /api/recommend
  matcher.py       — local scoring engine (no API calls)
  scraper.py       — one-time Playwright scraper to build fragrances.json
  data/
    fragrances.json — fragrance catalog (35 entries, manually curated)

frontend/           — vanilla JS, no build step
  index.html        — Aroma Match home: 2 cards + theme toggle + logo
  assets/
    logo_am.png     — AM logo (transparent PNG, used everywhere)
  pitch/            — sales presentation (11 slides, scroll-snap)
    index.html
    style.css
    app.js
  profumum/         — main customer quiz (RU, 7 questions)
  sephora/          — hidden prototype (EN, 10 questions) — direct URL only
  parfbar/          — hidden prototype (RU, 7 questions) — direct URL only
```

Routes in `backend/main.py`:
- `/` → home
- `/pitch` → presentation page
- `/pitch/aroma-match.pdf` → original PDF download
- `/profumum`, `/sephora`, `/parfbar` → quiz pages
- `/api/recommend/{profumum|sephora|parfbar}` → matching API

Static files are served via FastAPI at `/static/*` — HTML references them as `/static/assets/logo_am.png`, `/static/pitch/style.css` etc. (absolute paths).

## How matching works

`matcher.py` scores each fragrance against quiz answers:
- **Budget** → hard filter by price range
- **Notes / Vibe / Season / Occasion** → keyword match against `description` + `notes` fields, weighted scores
- **Brand preference** → +5 bonus if brand matches
- **Niche vs bestseller** → +3 bonus based on `TOP_BRANDS` list

Test matcher standalone:
```bash
cd backend && python3 matcher.py
```

## Adding fragrances

Edit `backend/data/fragrances.json`. Each entry:
```json
{
  "id": "P123456",
  "name": "Fragrance Name",
  "brand": "Brand",
  "price": 150,
  "description": "English description with notes mentioned naturally",
  "notes": ["bergamot", "sandalwood", "vanilla"],
  "url": "https://www.sephora.com/search?keyword=Brand+Name",
  "image_url": ""
}
```

Matching quality depends entirely on keywords in `description` and `notes`. Richer descriptions = better matches.

## Scraping real Sephora data

`scraper.py` uses Playwright (headless=False) to avoid Cloudflare blocks:
```bash
cd backend && python3 scraper.py
```
Writes ~120 products to `data/fragrances.json`. Takes 10–15 min. Sephora has anti-bot protection — slow delays (2–4s) are intentional.

## Quiz flow

`QUESTIONS` array in `app.js` defines all 10 questions. Each question has `id`, `multi` (bool), `cols` (grid columns), and `options`. Single-select questions auto-advance after 350ms. Brand question (id: `brands`) is always skippable. Answer keys map directly to `Answers` pydantic model in `main.py`.

## Port conflicts

```bash
lsof -ti:8000 | xargs kill -9
```
