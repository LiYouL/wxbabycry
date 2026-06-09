# backend/app/api/noise.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import settings
import os

router = APIRouter(prefix="/api/noise", tags=["noise"])


NOISE_LIST = [
    {"id": 1, "name": "吹风机", "icon": "\U0001f4a8", "category": "白噪音", "file": "hair_dryer.mp3"},
    {"id": 2, "name": "虫鸣", "icon": "\U0001f997", "category": "白噪音", "file": "insects.mp3"},
    {"id": 3, "name": "鸟鸣", "icon": "\U0001f426", "category": "白噪音", "file": "birds.mp3"},
    {"id": 4, "name": "电视白噪音", "icon": "\U0001f4fa", "category": "白噪音", "file": "tv_static.mp3"},
    {"id": 5, "name": "风声", "icon": "\U0001f32c️", "category": "白噪音", "file": "wind.mp3"},
    {"id": 6, "name": "心跳", "icon": "\U0001f493", "category": "白噪音", "file": "heartbeat.mp3"},
    {"id": 7, "name": "雨声", "icon": "\U0001f327️", "category": "白噪音", "file": "rain.mp3"},
    {"id": 8, "name": "海浪", "icon": "\U0001f30a", "category": "白噪音", "file": "ocean.mp3"},
    {"id": 9, "name": "蚊子声", "icon": "\U0001f99f", "category": "白噪音", "file": "mosquito.mp3"},
    {"id": 10, "name": "洗衣机", "icon": "\U0001f9fa", "category": "白噪音", "file": "washer.mp3"},
]


@router.get("/list")
async def list_noise():
    available = []
    for item in NOISE_LIST:
        path = os.path.join(settings.noise_audio_dir, item["file"])
        if os.path.exists(path):
            available.append(item)
    return {"items": available, "categories": ["全部", "白噪音"]}


@router.get("/{noise_id}/stream")
async def stream_noise(noise_id: int):
    for item in NOISE_LIST:
        if item["id"] == noise_id:
            path = os.path.join(settings.noise_audio_dir, item["file"])
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="音频文件不存在")
            return FileResponse(path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="白噪音不存在")
