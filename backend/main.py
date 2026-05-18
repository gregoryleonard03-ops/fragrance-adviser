"""
Local FastAPI server for Fragrance Adviser.
Start: uvicorn main:app --reload --port 8000
"""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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


class Answers(BaseModel):
    gender: str = ""
    budget: str = ""
    occasion: str = ""
    season: str = ""
    notes: list[str] = []
    longevity: str = ""
    sillage: str = ""
    brands: list[str] = []
    vibe: str = ""
    style: str = ""


@app.get("/")
def index():
    return FileResponse(str(FRONTEND / "index.html"))


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/recommend")
def get_recommendations(answers: Answers):
    try:
        results = recommend_from_db(answers.model_dump(), store="sephora", top_n=5)
        return {"recommendations": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
