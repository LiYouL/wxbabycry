# backend/app/api/user.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserResponse
from app.config import settings
from jose import jwt
import httpx
from typing import Optional

router = APIRouter(prefix="/api/user", tags=["user"])


async def get_wechat_openid(code: str) -> Optional[str]:
    """Exchange WeChat code for openid. MVP: accept code directly."""
    return code


def create_token(openid: str, user_id: int) -> str:
    return jwt.encode(
        {"sub": openid, "user_id": user_id},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )


@router.post("/login", response_model=dict)
async def login(body: UserLogin, db: AsyncSession = Depends(get_db)):
    openid = await get_wechat_openid(body.code)
    if not openid:
        raise HTTPException(status_code=400, detail="微信登录失败")

    result = await db.execute(select(User).where(User.openid == openid))
    user = result.scalar_one_or_none()

    if not user:
        user = User(openid=openid)
        db.add(user)
        await db.commit()
        await db.refresh(user)

    token = create_token(openid, user.id)
    return {"token": token, "user": UserResponse.model_validate(user)}
