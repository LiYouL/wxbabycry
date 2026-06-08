# backend/app/schemas/cry.py
from pydantic import BaseModel
from typing import List, Optional


class SecondaryType(BaseModel):
    type: str
    confidence: float


class CryAdvice(BaseModel):
    cause: str = ""
    solutions: List[str] = []
    soothing_tips: List[str] = []
    warnings: List[str] = []


class CryRecognizeResponse(BaseModel):
    cry_type: str
    confidence: float
    secondary_types: List[SecondaryType] = []
    advice: CryAdvice = CryAdvice()
