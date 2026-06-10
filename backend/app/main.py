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
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass  # Allow server to start without database for development

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.audio_upload_dir, exist_ok=True)
os.makedirs(settings.noise_audio_dir, exist_ok=True)


from app.api.user import router as user_router
from app.api.baby import router as baby_router
from app.api.cry import router as cry_router
from app.api.records import router as records_router
from app.api.vaccine import router as vaccine_router
from app.api.noise import router as noise_router

app.include_router(user_router)
app.include_router(baby_router)
app.include_router(cry_router)
app.include_router(records_router)
app.include_router(vaccine_router)
app.include_router(noise_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/health/model")
async def model_health():
    from app.services.cry_classifier import classifier

    return {"status": "ok", "model": classifier.status()}
