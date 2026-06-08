from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Feeding(Base):
    __tablename__ = "feedings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=False)
    start_time = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    amount = Column(Integer, default=0)
    side = Column(String(8), default="")
    note = Column(String(256), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="feedings")
