# backend/app/api/records.py
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.feeding import Feeding
from app.models.sleep import Sleep
from app.models.diaper import Diaper
from app.schemas.records import (
    FeedingCreate, FeedingResponse,
    SleepCreate, SleepResponse,
    DiaperCreate, DiaperResponse,
)

router = APIRouter(prefix="/api/records", tags=["records"])


# ── Feeding ──

@router.post("/feeding", response_model=FeedingResponse)
async def create_feeding(
    body: FeedingCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Feeding(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return FeedingResponse.model_validate(record)


@router.get("/feeding/list", response_model=List[FeedingResponse])
async def list_feedings(
    baby_id: int = Query(...),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Feeding)
        .where(Feeding.baby_id == baby_id)
        .order_by(desc(Feeding.start_time))
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()
    return [FeedingResponse.model_validate(r) for r in records]


# ── Sleep ──

@router.post("/sleep", response_model=SleepResponse)
async def create_sleep(
    body: SleepCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Sleep(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return SleepResponse.model_validate(record)


@router.get("/sleep/list", response_model=List[SleepResponse])
async def list_sleeps(
    baby_id: int = Query(...),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Sleep)
        .where(Sleep.baby_id == baby_id)
        .order_by(desc(Sleep.start_time))
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()
    return [SleepResponse.model_validate(r) for r in records]


# ── Diaper ──

@router.post("/diaper", response_model=DiaperResponse)
async def create_diaper(
    body: DiaperCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Diaper(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return DiaperResponse.model_validate(record)


@router.get("/diaper/list", response_model=List[DiaperResponse])
async def list_diapers(
    baby_id: int = Query(...),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Diaper)
        .where(Diaper.baby_id == baby_id)
        .order_by(desc(Diaper.time))
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()
    return [DiaperResponse.model_validate(r) for r in records]
