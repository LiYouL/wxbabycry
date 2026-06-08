from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(64), unique=True, nullable=False)
    nickname = Column(String(64), default="")
    avatar_url = Column(String(512), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    babies = relationship("Baby", back_populates="user")
