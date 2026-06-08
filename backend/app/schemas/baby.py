# backend/app/schemas/baby.py
from pydantic import BaseModel
from datetime import date
from typing import Optional


class BabyCreate(BaseModel):
    nickname: str = ""
    birthday: Optional[date] = None
    gender: str = ""
    feed_type: str = ""


class BabyUpdate(BabyCreate):
    avatar_url: str = ""


class BabyResponse(BaseModel):
    id: int
    user_id: int
    nickname: str
    birthday: Optional[date] = None
    gender: str
    feed_type: str
    avatar_url: str

    class Config:
        from_attributes = True
