from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Baby(Base):
    __tablename__ = "babies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    nickname = Column(String(32), default="")
    birthday = Column(Date, nullable=True)
    gender = Column(String(4), default="")
    feed_type = Column(String(16), default="")
    avatar_url = Column(String(512), default="")

    user = relationship("User", back_populates="babies")
    feedings = relationship("Feeding", back_populates="baby")
    sleeps = relationship("Sleep", back_populates="baby")
    diapers = relationship("Diaper", back_populates="baby")
    vaccines = relationship("Vaccine", back_populates="baby")
    cry_records = relationship("CryRecord", back_populates="baby")
