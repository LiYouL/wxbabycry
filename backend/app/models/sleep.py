from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Sleep(Base):
    __tablename__ = "sleeps"

    id = Column(Integer, primary_key=True, autoincrement=True)
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=False)
    start_time = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    quality = Column(String(16), default="")
    note = Column(String(256), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="sleeps")
