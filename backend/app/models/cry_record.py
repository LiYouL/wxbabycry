from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class CryRecord(Base):
    __tablename__ = "cry_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=True)
    cry_type = Column(String(32), nullable=False)
    confidence = Column(Float, default=0.0)
    secondary_result = Column(Text, default="[]")
    audio_url = Column(String(512), default="")
    advice = Column(Text, default="{}")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="cry_records")
