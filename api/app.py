"""RedFlag API.  Run locally:  uvicorn app:app --reload"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from redflag_core import load_model, scan

MODEL_DIR = Path(__file__).parent / "model"

# Local dev origins are always allowed. In production set ALLOWED_ORIGINS to your frontend URL(s),
# comma-separated, e.g. https://yourname.github.io,https://redflag.vercel.app
LOCAL_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5500",
                 "http://127.0.0.1:5500", "http://localhost:8000", "http://127.0.0.1:8000"]
EXTRA = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.vec, app.state.clf = load_model(MODEL_DIR)   # loaded once at startup
    yield


app = FastAPI(title="RedFlag", version="1.0.0", lifespan=lifespan,
              description="Awareness aid: scam-likelihood for a pasted SMS plus source-backed safety tips.")

app.add_middleware(CORSMiddleware, allow_origins=LOCAL_ORIGINS + EXTRA, allow_credentials=False,
                   allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])


class ScanRequest(BaseModel):
    message: str = Field(..., max_length=1000, description="The SMS text to check")

    @field_validator("message")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message must not be empty")
        return v


class AdviceItem(BaseModel):
    tip: str
    source: str
    source_short: str
    url: str
    retrieved: str
    quotes: list[str]


class ScanResponse(BaseModel):
    verdict: str
    confidence_score: float = Field(description="Estimated probability that the message is a scam (0 to 1)")
    summary: str
    safety_advice: str
    advice_items: list[AdviceItem]
    disclaimer: str


@app.post("/api/scan", response_model=ScanResponse)
def api_scan(req: ScanRequest):
    # Plain `def`, so FastAPI runs it in a worker thread. The message is never logged or stored.
    return scan(req.message, app.state.vec, app.state.clf)


@app.get("/api/health")
def health():
    return {"status": "ok", "model_loaded": True}
