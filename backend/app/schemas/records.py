# backend/app/schemas/records.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FeedingCreate(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    amount: int = 0
    side: str = ""
    note: str = ""


class FeedingResponse(BaseModel):
    id: int
    baby_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    amount: int
    side: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class SleepCreate(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    quality: str = ""
    note: str = ""


class SleepResponse(BaseModel):
    id: int
    baby_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    quality: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class DiaperCreate(BaseModel):
    time: datetime
    type: str = ""
    color: str = ""
    note: str = ""


class DiaperResponse(BaseModel):
    id: int
    baby_id: int
    time: datetime
    type: str
    color: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True
