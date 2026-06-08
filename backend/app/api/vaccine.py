# backend/app/api/vaccine.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from app.database import get_db
from app.models.vaccine import Vaccine
from app.schemas.vaccine import VaccineCreate, VaccineStatusUpdate, VaccineResponse

router = APIRouter(prefix="/api/vaccine", tags=["vaccine"])


@router.post("", response_model=VaccineResponse)
async def create_vaccine(
    body: VaccineCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Vaccine(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return VaccineResponse.model_validate(record)


@router.get("/list", response_model=List[VaccineResponse])
async def list_vaccines(
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vaccine)
        .where(Vaccine.baby_id == baby_id)
        .order_by(desc(Vaccine.scheduled_date))
    )
    records = result.scalars().all()
    return [VaccineResponse.model_validate(r) for r in records]


@router.put("/{vaccine_id}/status", response_model=VaccineResponse)
async def update_vaccine_status(
    vaccine_id: int,
    body: VaccineStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Vaccine).where(Vaccine.id == vaccine_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="疫苗记录不存在")

    record.status = body.status
    if body.status == "已接种":
        record.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(record)
    return VaccineResponse.model_validate(record)
