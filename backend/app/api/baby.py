# backend/app/api/baby.py
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.baby import Baby
from app.schemas.baby import BabyCreate, BabyUpdate, BabyResponse

router = APIRouter(prefix="/api/baby", tags=["baby"])


async def _get_first_user(db: AsyncSession):
    """MVP: Get the first user (simplified auth until WeChat login is fully wired)."""
    from app.models.user import User

    result = await db.execute(select(User).limit(1))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="请先登录")
    return user


@router.post("", response_model=BabyResponse)
async def create_baby(
    body: BabyCreate,
    db: AsyncSession = Depends(get_db),
):
    user = await _get_first_user(db)

    baby = Baby(user_id=user.id, **body.model_dump())
    db.add(baby)
    await db.commit()
    await db.refresh(baby)
    return BabyResponse.model_validate(baby)


@router.get("", response_model=List[BabyResponse])
async def list_babies(db: AsyncSession = Depends(get_db)):
    user = await _get_first_user(db)

    result = await db.execute(
        select(Baby).where(Baby.user_id == user.id).order_by(Baby.id)
    )
    babies = result.scalars().all()
    return [BabyResponse.model_validate(b) for b in babies]


@router.put("/{baby_id}", response_model=BabyResponse)
async def update_baby(
    baby_id: int,
    body: BabyUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Baby).where(Baby.id == baby_id))
    baby = result.scalar_one_or_none()
    if not baby:
        raise HTTPException(status_code=404, detail="宝宝不存在")

    for key, val in body.model_dump(exclude_unset=True).items():
        setattr(baby, key, val)
    await db.commit()
    await db.refresh(baby)
    return BabyResponse.model_validate(baby)
