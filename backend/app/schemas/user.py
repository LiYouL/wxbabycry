# backend/app/schemas/user.py
from pydantic import BaseModel
from datetime import datetime


class UserLogin(BaseModel):
    code: str


class UserResponse(BaseModel):
    id: int
    openid: str
    nickname: str
    avatar_url: str
    created_at: datetime

    class Config:
        from_attributes = True
