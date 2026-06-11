# backend/app/api/cry.py
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.baby import Baby
from app.models.cry_record import CryRecord
from app.services.ai_client import generate_advice
from app.schemas.cry import CryRecognizeResponse, SecondaryType, CryAdvice
from app.config import settings
import json
import logging
import os
import uuid
from typing import Optional

router = APIRouter(prefix="/api/cry", tags=["cry"])
logger = logging.getLogger(__name__)


def _get_audio_processor():
    from app.services.audio_processor import process_audio, AudioProcessError

    return process_audio, AudioProcessError


def _get_classifier():
    from app.services.cry_classifier import classifier

    return classifier


@router.post("/recognize", response_model=CryRecognizeResponse)
async def recognize_cry(
    audio: UploadFile = File(...),
    baby_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    # 1. Read and validate audio
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="未收到音频数据")

    # 2. Process audio → MFCC
    process_audio, audio_process_error = _get_audio_processor()
    try:
        mfcc = process_audio(audio_bytes, audio.filename or "recording.mp3")
    except audio_process_error as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        logger.exception("Failed to process uploaded cry audio")
        raise HTTPException(status_code=400, detail="音频格式无法识别，请重新录制后再试")

    # 3. CNN classification
    predictions = _get_classifier().predict(mfcc)

    primary = predictions[0]
    secondary = [
        SecondaryType(type=p["type"], confidence=p["confidence"])
        for p in predictions[1:]
    ]

    # 4. Get baby info if available
    baby_info = None
    if baby_id:
        try:
            result = await db.execute(select(Baby).where(Baby.id == baby_id))
            baby = result.scalar_one_or_none()
            if baby:
                baby_info = {
                    "nickname": baby.nickname,
                    "birthday": str(baby.birthday) if baby.birthday else None,
                    "feed_type": baby.feed_type,
                }
        except Exception:
            logger.exception("Failed to load baby info, continuing without profile")
            try:
                await db.rollback()
            except Exception:
                logger.exception("Failed to rollback baby info transaction")

    # 5. Generate advice via Claude
    advice = await generate_advice(primary["type"], primary["confidence"], baby_info)

    response = CryRecognizeResponse(
        cry_type=primary["type"],
        confidence=primary["confidence"],
        secondary_types=secondary,
        advice=advice,
    )

    if not settings.persist_cry_records:
        return response

    # 6. Save recognition record. Storage/DB failures should not block the user
    # from seeing the recognition result.
    try:
        os.makedirs(settings.audio_upload_dir, exist_ok=True)
        audio_filename = f"{uuid.uuid4()}.wav"
        audio_path = os.path.join(settings.audio_upload_dir, audio_filename)
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)

        record = CryRecord(
            baby_id=baby_id,
            cry_type=primary["type"],
            confidence=primary["confidence"],
            secondary_result=json.dumps(
                [{"type": s.type, "confidence": s.confidence} for s in secondary],
                ensure_ascii=False,
            ),
            audio_url=audio_path,
            advice=advice.model_dump_json(),
        )
        db.add(record)
        await db.commit()
    except Exception:
        logger.exception("Failed to save cry recognition record")
        try:
            await db.rollback()
        except Exception:
            logger.exception("Failed to rollback cry recognition transaction")

    return response
