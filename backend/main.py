"""
Fragrance Adviser — единый FastAPI сервер для всех 3 магазинов.
Start: uvicorn main:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from matcher_db import recommend_from_db

app = FastAPI(title="Fragrance Adviser")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND = Path(__file__).parent.parent / "frontend"
app.mount("/static", StaticFiles(directory=str(FRONTEND)), name="static")


# ── Общая модель ответов (все поля optional) ─────────────────────────────────
class Answers(BaseModel):
    # Sephora fields
    gender: str = ""
    budget: list[str] = []
    occasion: list[str] = []
    season: list[str] = []
    notes: list[str] = []
    longevity: list[str] = []
    sillage: list[str] = []
    brands: list[str] = []
    vibe: list[str] = []
    style: list[str] = []
    # Parfbar branching fields
    branch: str = ""
    sub_type: list[str] = []
    intensity: list[str] = []


NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}

# ── Страницы ─────────────────────────────────────────────────────────────────
@app.get("/")
def index():
    return FileResponse(str(FRONTEND / "index.html"), headers=NO_CACHE)

@app.get("/sephora")
def sephora_page():
    return FileResponse(str(FRONTEND / "sephora" / "index.html"), headers=NO_CACHE)

@app.get("/parfbar")
def parfbar_page():
    return FileResponse(str(FRONTEND / "parfbar" / "index.html"), headers=NO_CACHE)

@app.get("/profumum")
def profumum_page():
    return FileResponse(str(FRONTEND / "profumum" / "index.html"), headers=NO_CACHE)

@app.get("/pitch")
def pitch_page():
    return FileResponse(str(FRONTEND / "pitch" / "index.html"), headers=NO_CACHE)

@app.get("/pitch/aroma-match.pdf")
def pitch_pdf():
    return FileResponse(
        str(Path(__file__).parent.parent / "Aroma Match.pdf"),
        media_type="application/pdf",
        filename="Aroma Match.pdf",
    )


# ── Healthcheck ───────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok"}


# ── API endpoints ─────────────────────────────────────────────────────────────
@app.post("/api/recommend/sephora")
def recommend_sephora(answers: Answers):
    try:
        results = recommend_from_db(answers.model_dump(), store="sephora", top_n=5)
        return {"recommendations": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend/parfbar")
def recommend_parfbar(answers: Answers):
    try:
        results = recommend_from_db(answers.model_dump(), store="parfbar", top_n=5)
        return {"recommendations": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommend/profumum")
def recommend_profumum(answers: Answers):
    try:
        results = recommend_from_db(answers.model_dump(), store="profumum", top_n=5)
        return {"recommendations": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
