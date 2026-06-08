# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa: ensure all models loaded

app = FastAPI(title="Baby Cry Recognition API", version="0.1.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.audio_upload_dir, exist_ok=True)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
