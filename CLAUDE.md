# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

AI-powered fragrance quiz that asks 10 questions and recommends 5 perfumes from Sephora. No external AI APIs — matching is done locally via keyword scoring. Built as a web prototype.

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

frontend/           — vanilla JS SPA, no build step
  index.html        — 4 screens: intro / quiz / loading / results
  app.js            — QUESTIONS array + quiz logic + fetch to /api/recommend
  style.css         — luxury fragrance aesthetic with Sephora red (#d4145a) accents
```

Static files are served via FastAPI at `/static/*` — HTML references them as `/static/style.css` and `/static/app.js` (absolute paths, not relative).

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
