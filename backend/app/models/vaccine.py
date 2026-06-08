from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Vaccine(Base):
    __tablename__ = "vaccines"

    id = Column(Integer, primary_key=True, autoincrement=True)
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=False)
    name = Column(String(64), nullable=False)
    scheduled_date = Column(Date, nullable=False)
    status = Column(String(16), default="未接种")
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="vaccines")
