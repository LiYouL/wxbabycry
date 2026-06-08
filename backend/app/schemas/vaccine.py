# backend/app/schemas/vaccine.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class VaccineCreate(BaseModel):
    name: str
    scheduled_date: date


class VaccineStatusUpdate(BaseModel):
    status: str


class VaccineResponse(BaseModel):
    id: int
    baby_id: int
    name: str
    scheduled_date: date
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
