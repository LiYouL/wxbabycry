# 智能育儿助手 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a WeChat Mini Program backend (FastAPI) + frontend for baby cry recognition, AI parenting advice, white noise, growth records, and vaccine reminders.

**Architecture:** FastAPI backend with SQLAlchemy async ORM + PostgreSQL, serving a native WeChat Mini Program frontend. Cry recognition uses librosa MFCC extraction → CNN classifier → Claude API for advice. White noise audio served as static files. All deployed on Tencent Cloud.

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy (async), PostgreSQL, Redis, librosa, pydub, PyTorch, anthropic SDK, WeChat Mini Program (native)

---

## Phase 1: Project Foundation

### Task 1: Project Scaffolding & Dependencies

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`

- [ ] **Step 1: Create requirements.txt**

```bash
mkdir -p backend/app backend/models backend/data
```

```txt
# backend/requirements.txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy[asyncio]==2.0.36
asyncpg==0.30.0
alembic==1.14.0
pydantic==2.10.3
pydantic-settings==2.7.0
python-jose[cryptography]==3.3.0
httpx==0.28.1
python-multipart==0.0.18
redis==5.2.1
librosa==0.10.2
pydub==0.25.1
torch==2.5.1
anthropic==0.42.0
aiofiles==24.1.0
```

- [ ] **Step 2: Install dependencies**

```bash
cd backend && pip install -r requirements.txt
```

- [ ] **Step 3: Create config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/babycry"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 30  # 30 days
    anthropic_api_key: str = ""
    audio_upload_dir: str = "./uploads/audio"
    noise_audio_dir: str = "./data/noise"
    min_record_seconds: int = 6
    max_record_seconds: int = 30
    model_path: str = "./models/cry_classifier.onnx"

    class Config:
        env_file = ".env"


settings = Settings()
```

- [ ] **Step 4: Create main.py (app entry point)**

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from app.config import settings

app = FastAPI(title="Baby Cry Recognition API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.audio_upload_dir, exist_ok=True)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run and verify**

```bash
cd backend && uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/api/health` — expected: `{"status":"ok"}`

- [ ] **Step 6: Commit**

```bash
git add backend/requirements.txt backend/app/__init__.py backend/app/main.py backend/app/config.py
git commit -m "feat: project scaffolding with FastAPI entry point and config"
```

---

### Task 2: Database Setup & All ORM Models

**Files:**
- Create: `backend/app/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/baby.py`
- Create: `backend/app/models/feeding.py`
- Create: `backend/app/models/sleep.py`
- Create: `backend/app/models/diaper.py`
- Create: `backend/app/models/vaccine.py`
- Create: `backend/app/models/cry_record.py`

- [ ] **Step 1: Create database.py**

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 2: Create user model**

```python
# backend/app/models/user.py
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
```

- [ ] **Step 3: Create baby model**

```python
# backend/app/models/baby.py
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
    feed_type = Column(String(16), default="")  # 母乳/配方奶/混合
    avatar_url = Column(String(512), default="")

    user = relationship("User", back_populates="babies")
    feedings = relationship("Feeding", back_populates="baby")
    sleeps = relationship("Sleep", back_populates="baby")
    diapers = relationship("Diaper", back_populates="baby")
    vaccines = relationship("Vaccine", back_populates="baby")
    cry_records = relationship("CryRecord", back_populates="baby")
```

- [ ] **Step 4: Create feeding model**

```python
# backend/app/models/feeding.py
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
    amount = Column(Integer, default=0)  # ml
    side = Column(String(8), default="")  # 左/右/瓶喂
    note = Column(String(256), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="feedings")
```

- [ ] **Step 5: Create sleep model**

```python
# backend/app/models/sleep.py
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
```

- [ ] **Step 6: Create diaper model**

```python
# backend/app/models/diaper.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Diaper(Base):
    __tablename__ = "diapers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    baby_id = Column(Integer, ForeignKey("babies.id"), nullable=False)
    time = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    type = Column(String(16), default="")  # 小便/大便/都有
    color = Column(String(16), default="")
    note = Column(String(256), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="diapers")
```

- [ ] **Step 7: Create vaccine model**

```python
# backend/app/models/vaccine.py
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
    status = Column(String(16), default="未接种")  # 未接种/已接种
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="vaccines")
```

- [ ] **Step 8: Create cry_record model**

```python
# backend/app/models/cry_record.py
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
    secondary_result = Column(Text, default="[]")  # JSON string
    audio_url = Column(String(512), default="")
    advice = Column(Text, default="{}")  # JSON string
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    baby = relationship("Baby", back_populates="cry_records")
```

- [ ] **Step 9: Create models __init__.py**

```python
# backend/app/models/__init__.py
from app.database import Base
from app.models.user import User
from app.models.baby import Baby
from app.models.feeding import Feeding
from app.models.sleep import Sleep
from app.models.diaper import Diaper
from app.models.vaccine import Vaccine
from app.models.cry_record import CryRecord

__all__ = ["Base", "User", "Baby", "Feeding", "Sleep", "Diaper", "Vaccine", "CryRecord"]
```

- [ ] **Step 10: Wire models into main.py and create tables**

```python
# Add to backend/app/main.py after app creation:
from app.database import engine, Base
from app.models import *  # noqa: ensure all models loaded

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
```

- [ ] **Step 11: Verify tables create on startup**

```bash
cd backend && python -c "import asyncio; from app.database import engine, Base; from app.models import *; asyncio.run(engine.begin().__aenter__()).run_sync(Base.metadata.create_all); print('OK')"
```

- [ ] **Step 12: Commit**

```bash
git add backend/app/database.py backend/app/models/
git commit -m "feat: add database setup and all ORM models"
```

---

### Task 3: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/baby.py`
- Create: `backend/app/schemas/records.py`
- Create: `backend/app/schemas/vaccine.py`
- Create: `backend/app/schemas/cry.py`

- [ ] **Step 1: Create user schema**

```python
# backend/app/schemas/user.py
from pydantic import BaseModel
from datetime import datetime


class UserLogin(BaseModel):
    code: str  # WeChat login code


class UserResponse(BaseModel):
    id: int
    openid: str
    nickname: str
    avatar_url: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Create baby schema**

```python
# backend/app/schemas/baby.py
from pydantic import BaseModel
from datetime import date
from typing import Optional


class BabyCreate(BaseModel):
    nickname: str = ""
    birthday: Optional[date] = None
    gender: str = ""
    feed_type: str = ""


class BabyUpdate(BabyCreate):
    avatar_url: str = ""


class BabyResponse(BaseModel):
    id: int
    user_id: int
    nickname: str
    birthday: Optional[date] = None
    gender: str
    feed_type: str
    avatar_url: str

    class Config:
        from_attributes = True
```

- [ ] **Step 3: Create records schema**

```python
# backend/app/schemas/records.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FeedingCreate(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    amount: int = 0
    side: str = ""
    note: str = ""


class FeedingResponse(BaseModel):
    id: int
    baby_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    amount: int
    side: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class SleepCreate(BaseModel):
    start_time: datetime
    end_time: Optional[datetime] = None
    quality: str = ""
    note: str = ""


class SleepResponse(BaseModel):
    id: int
    baby_id: int
    start_time: datetime
    end_time: Optional[datetime] = None
    quality: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True


class DiaperCreate(BaseModel):
    time: datetime
    type: str = ""
    color: str = ""
    note: str = ""


class DiaperResponse(BaseModel):
    id: int
    baby_id: int
    time: datetime
    type: str
    color: str
    note: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 4: Create vaccine schema**

```python
# backend/app/schemas/vaccine.py
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class VaccineCreate(BaseModel):
    name: str
    scheduled_date: date


class VaccineStatusUpdate(BaseModel):
    status: str  # 未接种/已接种


class VaccineResponse(BaseModel):
    id: int
    baby_id: int
    name: str
    scheduled_date: date
    status: str
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 5: Create cry schema**

```python
# backend/app/schemas/cry.py
from pydantic import BaseModel
from typing import Optional


class SecondaryType(BaseModel):
    type: str
    confidence: float


class CryAdvice(BaseModel):
    cause: str = ""
    solutions: list[str] = []
    soothing_tips: list[str] = []
    warnings: list[str] = []


class CryRecognizeResponse(BaseModel):
    cry_type: str
    confidence: float
    secondary_types: list[SecondaryType] = []
    advice: CryAdvice = CryAdvice()
```

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for all API endpoints"
```

---

## Phase 2: Core Services

### Task 4: Audio Processor Service

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/audio_processor.py`

- [ ] **Step 1: Create audio_processor.py**

```python
# backend/app/services/audio_processor.py
import librosa
import numpy as np
from pydub import AudioSegment
import io
from app.config import settings


class AudioProcessError(Exception):
    pass


def convert_to_wav(audio_bytes: bytes, original_format: str = "mp3") -> bytes:
    """Convert uploaded audio to WAV format."""
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=original_format)
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    buf.seek(0)
    return buf.read()


def validate_duration(y: np.ndarray, sr: int) -> None:
    """Check audio meets min/max duration requirements."""
    duration = len(y) / sr
    if duration < settings.min_record_seconds:
        raise AudioProcessError(
            f"录音时长不足 {settings.min_record_seconds} 秒，请重新录制"
        )
    if duration > settings.max_record_seconds:
        y = y[: int(sr * settings.max_record_seconds)]


def has_audio(y: np.ndarray, sr: int) -> bool:
    """Check if audio has meaningful content (not silence)."""
    rms = librosa.feature.rms(y=y)
    return float(np.mean(rms)) > 0.005


def extract_mfcc(y: np.ndarray, sr: int, n_mfcc: int = 40) -> np.ndarray:
    """Extract MFCC features from audio."""
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    return mfcc  # shape: (n_mfcc, time_frames)


def process_audio(audio_bytes: bytes, filename: str = "recording.mp3") -> np.ndarray:
    """Full audio preprocessing pipeline. Returns MFCC feature matrix."""
    fmt = filename.rsplit(".", 1)[-1] if "." in filename else "mp3"
    wav_bytes = convert_to_wav(audio_bytes, fmt)

    y, sr = librosa.load(io.BytesIO(wav_bytes), sr=16000, mono=True)

    validate_duration(y, sr)

    if not has_audio(y, sr):
        raise AudioProcessError("未检测到有效声音，请靠近婴儿重新录音")

    y, _ = librosa.effects.trim(y, top_db=20)

    mfcc = extract_mfcc(y, sr)
    return mfcc
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/__init__.py backend/app/services/audio_processor.py
git commit -m "feat: add audio preprocessing service (librosa MFCC extraction)"
```

---

### Task 5: CNN Classifier (Placeholder)

**Files:**
- Create: `backend/app/services/cry_classifier.py`

- [ ] **Step 1: Create cry_classifier.py**

```python
# backend/app/services/cry_classifier.py
import numpy as np

CRY_TYPES = [
    "饥饿",
    "尿布不适",
    "疲倦",
    "疼痛",
    "需要安抚",
    "出牙",
    "其他",
]


class CryClassifier:
    """Placeholder CNN classifier for baby cry recognition.

    MVP: Returns random predictions with controlled confidence.
    Will be replaced with a real PyTorch/ONNX model.
    """

    def __init__(self, model_path: str = ""):
        self._labels = CRY_TYPES

    def predict(self, mfcc: np.ndarray) -> list[dict]:
        """Predict cry types from MFCC features.

        Args:
            mfcc: MFCC feature matrix (n_mfcc, time_frames)

        Returns:
            Sorted list of {type, confidence} descending by confidence.
        """
        n = len(self._labels)
        raw = np.random.dirichlet(np.ones(n) * 0.5)
        # Boost one random label for more realistic distribution
        boost_idx = np.random.randint(0, n)
        raw[boost_idx] *= 3
        probs = raw / raw.sum()

        results = [
            {"type": self._labels[i], "confidence": round(float(probs[i]), 4)}
            for i in range(n)
        ]
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results


# Singleton
classifier = CryClassifier()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/cry_classifier.py
git commit -m "feat: add placeholder CNN cry classifier"
```

---

### Task 6: Claude API Client

**Files:**
- Create: `backend/app/services/ai_client.py`

- [ ] **Step 1: Create ai_client.py**

```python
# backend/app/services/ai_client.py
from anthropic import AsyncAnthropic
from app.config import settings
from app.schemas.cry import CryAdvice

SYSTEM_PROMPT = """你是一位经验丰富的育儿专家，擅长帮助新手父母理解婴儿的需求。

根据哭声识别结果，你需要：
1. 用温暖亲切的语气解释婴儿可能的状况
2. 提供具体可操作的解决方案
3. 给出安抚建议
4. 必要时提醒家长关注其他症状

请用中文回复。"""


def build_prompt(cry_type: str, confidence: float, baby_info: dict | None) -> str:
    """Build the Claude prompt with cry recognition context."""
    info_parts = [f"哭声识别结果：{cry_type}（置信度 {confidence:.0%}）"]

    if baby_info:
        if baby_info.get("nickname"):
            info_parts.append(f"宝宝昵称：{baby_info['nickname']}")
        if baby_info.get("feed_type"):
            info_parts.append(f"喂养方式：{baby_info['feed_type']}")
        if baby_info.get("birthday"):
            info_parts.append(f"出生日期：{baby_info['birthday']}")

    context = "\n".join(info_parts)

    return f"""请根据以下信息提供育儿建议：

{context}

请按以下格式回复（严格 JSON 格式）：
{{
  "cause": "哭声原因解释（1-2句）",
  "solutions": ["解决方案1", "解决方案2"],
  "soothing_tips": ["安抚技巧1", "安抚技巧2"],
  "warnings": ["注意事项（如需要）"]
}}"""


async def generate_advice(
    cry_type: str, confidence: float, baby_info: dict | None = None
) -> CryAdvice:
    """Generate parenting advice using Claude API."""
    prompt = build_prompt(cry_type, confidence, baby_info)

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        import json

        text = response.content[0].text
        data = json.loads(text)
        return CryAdvice(**data)
    except Exception:
        return _fallback_advice(cry_type)


def _fallback_advice(cry_type: str) -> CryAdvice:
    """Fallback advice when Claude API is unavailable."""
    fallbacks = {
        "饥饿": CryAdvice(
            cause="宝宝可能因为饥饿而哭闹",
            solutions=["尝试给宝宝喂奶", "观察宝宝是否有觅食反射（转头、张嘴）"],
            soothing_tips=["喂奶时保持安静环境", "喂完后轻拍背部帮助排气"],
            warnings=["如持续拒绝进食，请咨询医生"],
        ),
        "尿布不适": CryAdvice(
            cause="宝宝可能因为尿布湿了或不舒适而哭闹",
            solutions=["检查并及时更换尿布", "清洁并保持臀部干燥"],
            soothing_tips=["更换尿布时用温水清洗", "涂抹护臀霜预防红臀"],
            warnings=["如出现严重红疹请就医"],
        ),
        "疲倦": CryAdvice(
            cause="宝宝可能感到疲倦，需要睡觉",
            solutions=["创造一个安静、昏暗的睡眠环境", "尝试包裹襁褓增加安全感"],
            soothing_tips=["播放白噪音帮助入睡", "轻轻摇晃或轻拍宝宝"],
            warnings=["如长时间无法入睡，请观察是否有其他不适"],
        ),
        "疼痛": CryAdvice(
            cause="宝宝可能因腹痛、胀气等不适而哭闹",
            solutions=["检查宝宝腹部是否胀硬", "尝试顺时针轻揉宝宝腹部"],
            soothing_tips=["飞机抱姿势可缓解胀气", "温水浴可帮助放松"],
            warnings=["如持续哭闹超过30分钟，建议及时就医"],
        ),
        "需要安抚": CryAdvice(
            cause="宝宝需要安抚和关注，可能感到孤单或不安",
            solutions=["抱起宝宝轻轻安抚", "对宝宝说话或唱歌"],
            soothing_tips=["用温柔的声音和宝宝交流", "轻轻抚摸宝宝的背部"],
            warnings=["观察宝宝是否有其他不适症状，不要长时间让宝宝独自哭闹"],
        ),
        "出牙": CryAdvice(
            cause="宝宝可能正在出牙，牙龈不适导致哭闹",
            solutions=["用干净的手指轻轻按摩宝宝牙龈", "提供安全的牙胶给宝宝咬"],
            soothing_tips=["可以冷藏牙胶（不要冷冻）缓解不适", "保持宝宝口腔清洁"],
            warnings=["如伴随发烧超过38°C请就医"],
        ),
        "其他": CryAdvice(
            cause="宝宝的哭声原因不太明确",
            solutions=["逐一检查：是否饿了、尿布湿了、困了、太热/太冷"],
            soothing_tips=["抱抱宝宝，让宝宝感受到安全感", "带宝宝到不同环境走走"],
            warnings=["如果宝宝持续哭闹且无法安抚，建议咨询儿科医生"],
        ),
    }
    return fallbacks.get(cry_type, fallbacks["其他"])
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/ai_client.py
git commit -m "feat: add Claude API client with fallback advice"
```

---

## Phase 3: API Routes

### Task 7: User & Baby API

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/user.py`
- Create: `backend/app/api/baby.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create user API**

```python
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

router = APIRouter(prefix="/api/user", tags=["user"])


async def get_wechat_openid(code: str) -> str | None:
    """Exchange WeChat code for openid. Requires WeChat appid/secret in production."""
    # MVP: accept a mock code for development, or direct openid
    # In production, call WeChat API:
    # https://api.weixin.qq.com/sns/jscode2session?appid=APPID&secret=SECRET&js_code=CODE&grant_type=authorization_code
    return code  # MVP placeholder


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
```

- [ ] **Step 2: Create baby API**

```python
# backend/app/api/baby.py
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


@router.get("", response_model=list[BabyResponse])
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
```

- [ ] **Step 3: Register routes in main.py**

```python
# Add to backend/app/main.py after middleware setup:
from app.api.user import router as user_router
from app.api.baby import router as baby_router

app.include_router(user_router)
app.include_router(baby_router)
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/__init__.py backend/app/api/user.py backend/app/api/baby.py
git commit -m "feat: add user login and baby profile API endpoints"
```

---

### Task 8: Cry Recognition API

**Files:**
- Create: `backend/app/api/cry.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create cry recognition endpoint**

```python
# backend/app/api/cry.py
from fastapi import APIRouter, UploadFile, File, Depends, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.baby import Baby
from app.models.cry_record import CryRecord
from app.services.audio_processor import process_audio, AudioProcessError
from app.services.cry_classifier import classifier
from app.services.ai_client import generate_advice
from app.schemas.cry import CryRecognizeResponse, SecondaryType, CryAdvice
from app.config import settings
import os
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/api/cry", tags=["cry"])


@router.post("/recognize", response_model=CryRecognizeResponse)
async def recognize_cry(
    audio: UploadFile = File(...),
    baby_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
):
    # 1. Read and validate audio
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="未收到音频数据")

    # 2. Process audio → MFCC
    try:
        mfcc = process_audio(audio_bytes, audio.filename or "recording.mp3")
    except AudioProcessError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. CNN classification
    predictions = classifier.predict(mfcc)

    primary = predictions[0]
    secondary = [
        SecondaryType(type=p["type"], confidence=p["confidence"])
        for p in predictions[1:]
    ]

    # 4. Get baby info if available
    baby_info = None
    if baby_id:
        result = await db.execute(select(Baby).where(Baby.id == baby_id))
        baby = result.scalar_one_or_none()
        if baby:
            baby_info = {
                "nickname": baby.nickname,
                "birthday": str(baby.birthday) if baby.birthday else None,
                "feed_type": baby.feed_type,
            }

    # 5. Generate advice via Claude
    advice = await generate_advice(primary["type"], primary["confidence"], baby_info)

    # 6. Save recognition record
    audio_filename = f"{uuid.uuid4()}.wav"
    audio_path = os.path.join(settings.audio_upload_dir, audio_filename)
    with open(audio_path, "wb") as f:
        f.write(audio_bytes)

    record = CryRecord(
        baby_id=baby_id,
        cry_type=primary["type"],
        confidence=primary["confidence"],
        secondary_result=str(
            [{"type": s.type, "confidence": s.confidence} for s in secondary]
        ),
        audio_url=audio_path,
        advice=advice.model_dump_json(),
    )
    db.add(record)
    await db.commit()

    return CryRecognizeResponse(
        cry_type=primary["type"],
        confidence=primary["confidence"],
        secondary_types=secondary,
        advice=advice,
    )
```

- [ ] **Step 2: Register in main.py**

```python
# Add to backend/app/main.py:
from app.api.cry import router as cry_router

app.include_router(cry_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/cry.py
git commit -m "feat: add cry recognition API endpoint with full pipeline"
```

---

### Task 9: Growth Records API (Feeding, Sleep, Diaper)

**Files:**
- Create: `backend/app/api/records.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create records API**

```python
# backend/app/api/records.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.database import get_db
from app.models.feeding import Feeding
from app.models.sleep import Sleep
from app.models.diaper import Diaper
from app.schemas.records import (
    FeedingCreate, FeedingResponse,
    SleepCreate, SleepResponse,
    DiaperCreate, DiaperResponse,
)

router = APIRouter(prefix="/api/records", tags=["records"])


# ── Feeding ──

@router.post("/feeding", response_model=FeedingResponse)
async def create_feeding(
    body: FeedingCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Feeding(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return FeedingResponse.model_validate(record)


@router.get("/feeding/list", response_model=list[FeedingResponse])
async def list_feedings(
    baby_id: int = Query(...),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Feeding)
        .where(Feeding.baby_id == baby_id)
        .order_by(desc(Feeding.start_time))
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()
    return [FeedingResponse.model_validate(r) for r in records]


# ── Sleep ──

@router.post("/sleep", response_model=SleepResponse)
async def create_sleep(
    body: SleepCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Sleep(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return SleepResponse.model_validate(record)


@router.get("/sleep/list", response_model=list[SleepResponse])
async def list_sleeps(
    baby_id: int = Query(...),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Sleep)
        .where(Sleep.baby_id == baby_id)
        .order_by(desc(Sleep.start_time))
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()
    return [SleepResponse.model_validate(r) for r in records]


# ── Diaper ──

@router.post("/diaper", response_model=DiaperResponse)
async def create_diaper(
    body: DiaperCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Diaper(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return DiaperResponse.model_validate(record)


@router.get("/diaper/list", response_model=list[DiaperResponse])
async def list_diapers(
    baby_id: int = Query(...),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Diaper)
        .where(Diaper.baby_id == baby_id)
        .order_by(desc(Diaper.time))
        .limit(limit)
        .offset(offset)
    )
    records = result.scalars().all()
    return [DiaperResponse.model_validate(r) for r in records]
```

- [ ] **Step 2: Register in main.py**

```python
# Add to backend/app/main.py:
from app.api.records import router as records_router

app.include_router(records_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/records.py
git commit -m "feat: add feeding, sleep, and diaper record APIs"
```

---

### Task 10: Vaccine API

**Files:**
- Create: `backend/app/api/vaccine.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create vaccine API**

```python
# backend/app/api/vaccine.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timezone
from app.database import get_db
from app.models.vaccine import Vaccine
from app.schemas.vaccine import VaccineCreate, VaccineStatusUpdate, VaccineResponse

router = APIRouter(prefix="/api/vaccine", tags=["vaccine"])


@router.post("", response_model=VaccineResponse)
async def create_vaccine(
    body: VaccineCreate,
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    record = Vaccine(baby_id=baby_id, **body.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return VaccineResponse.model_validate(record)


@router.get("/list", response_model=list[VaccineResponse])
async def list_vaccines(
    baby_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Vaccine)
        .where(Vaccine.baby_id == baby_id)
        .order_by(desc(Vaccine.scheduled_date))
    )
    records = result.scalars().all()
    return [VaccineResponse.model_validate(r) for r in records]


@router.put("/{vaccine_id}/status", response_model=VaccineResponse)
async def update_vaccine_status(
    vaccine_id: int,
    body: VaccineStatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Vaccine).where(Vaccine.id == vaccine_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="疫苗记录不存在")

    record.status = body.status
    if body.status == "已接种":
        record.completed_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(record)
    return VaccineResponse.model_validate(record)
```

- [ ] **Step 2: Register in main.py**

```python
# Add to backend/app/main.py:
from app.api.vaccine import router as vaccine_router

app.include_router(vaccine_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/vaccine.py
git commit -m "feat: add vaccine reminder API endpoints"
```

---

### Task 11: White Noise API

**Files:**
- Create: `backend/app/api/noise.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Create noise API**

```python
# backend/app/api/noise.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import settings
import os
import json

router = APIRouter(prefix="/api/noise", tags=["noise"])


# Inline noise metadata (MVP: no database table for noise)
# Audio files go in settings.noise_audio_dir
NOISE_LIST = [
    {"id": 1, "name": "吹风机", "icon": "💨", "category": "白噪音", "file": "hair_dryer.mp3"},
    {"id": 2, "name": "虫鸣", "icon": "🦗", "category": "白噪音", "file": "insects.mp3"},
    {"id": 3, "name": "鸟鸣", "icon": "🐦", "category": "白噪音", "file": "birds.mp3"},
    {"id": 4, "name": "电视白噪音", "icon": "📺", "category": "白噪音", "file": "tv_static.mp3"},
    {"id": 5, "name": "风声", "icon": "🌬️", "category": "白噪音", "file": "wind.mp3"},
    {"id": 6, "name": "心跳", "icon": "💓", "category": "白噪音", "file": "heartbeat.mp3"},
    {"id": 7, "name": "雨声", "icon": "🌧️", "category": "白噪音", "file": "rain.mp3"},
    {"id": 8, "name": "海浪", "icon": "🌊", "category": "白噪音", "file": "ocean.mp3"},
]


@router.get("/list")
async def list_noise():
    """Return white noise list. Filters out items whose file doesn't exist."""
    available = []
    for item in NOISE_LIST:
        path = os.path.join(settings.noise_audio_dir, item["file"])
        if os.path.exists(path):
            available.append(item)
    return {"items": available, "categories": ["全部", "白噪音"]}


@router.get("/{noise_id}/stream")
async def stream_noise(noise_id: int):
    """Stream a white noise audio file."""
    for item in NOISE_LIST:
        if item["id"] == noise_id:
            path = os.path.join(settings.noise_audio_dir, item["file"])
            if not os.path.exists(path):
                raise HTTPException(status_code=404, detail="音频文件不存在")
            return FileResponse(path, media_type="audio/mpeg")
    raise HTTPException(status_code=404, detail="白噪音不存在")
```

- [ ] **Step 2: Register in main.py**

```python
# Add to backend/app/main.py:
from app.api.noise import router as noise_router

app.include_router(noise_router)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/noise.py
git commit -m "feat: add white noise list and stream API"
```

---

### Task 12: Wire Up main.py & End-to-End Test

**Files:**
- Modify: `backend/app/main.py`

- [ ] **Step 1: Final main.py**

Read the current `backend/app/main.py` and ensure all routers are registered. The file should now look like:

```python
# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa

app = FastAPI(title="Baby Cry Recognition API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.audio_upload_dir, exist_ok=True)
os.makedirs(settings.noise_audio_dir, exist_ok=True)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Register routers
from app.api.user import router as user_router
from app.api.baby import router as baby_router
from app.api.cry import router as cry_router
from app.api.records import router as records_router
from app.api.vaccine import router as vaccine_router
from app.api.noise import router as noise_router

app.include_router(user_router)
app.include_router(baby_router)
app.include_router(cry_router)
app.include_router(records_router)
app.include_router(vaccine_router)
app.include_router(noise_router)
```

- [ ] **Step 2: Start server and run smoke tests**

```bash
# Terminal 1: Start server
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2: Run smoke tests
# Health check
curl http://localhost:8000/api/health

# Login
curl -X POST http://localhost:8000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"code": "test_openid_123"}'

# Create baby
curl -X POST http://localhost:8000/api/baby \
  -H "Content-Type: application/json" \
  -d '{"nickname": "宝宝测试", "birthday": "2026-01-01", "gender": "男", "feed_type": "母乳"}'

# Cry recognition (with a test audio file)
curl -X POST http://localhost:8000/api/cry/recognize \
  -F "audio=@test_recording.mp3" \
  -F "baby_id=1"

# Get noise list
curl http://localhost:8000/api/noise/list

# Create feeding record
curl -X POST "http://localhost:8000/api/records/feeding?baby_id=1" \
  -H "Content-Type: application/json" \
  -d '{"start_time": "2026-06-08T10:00:00", "amount": 120, "side": "左"}'

# Get feeding list
curl "http://localhost:8000/api/records/feeding/list?baby_id=1"

# Create vaccine
curl -X POST "http://localhost:8000/api/vaccine?baby_id=1" \
  -H "Content-Type: application/json" \
  -d '{"name": "脊灰疫苗", "scheduled_date": "2026-07-01"}'

# Get vaccine list
curl "http://localhost:8000/api/vaccine/list?baby_id=1"
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: wire all API routers into main app"
```

---

## Phase 4: WeChat Mini Program Frontend

### Task 13: Mini Program Project Setup

**Files:**
- Create: `miniapp/app.js`
- Create: `miniapp/app.json`
- Create: `miniapp/app.wxss`
- Create: `miniapp/project.config.json`
- Create: `miniapp/utils/api.js`

- [ ] **Step 1: Create app.js**

```javascript
// miniapp/app.js
App({
  globalData: {
    apiBase: 'http://localhost:8000/api',  // Change to Tencent Cloud URL in production
    token: '',
    babyId: null,
    babyInfo: null,
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
    }
  },
});
```

- [ ] **Step 2: Create app.json (page registration)**

```json
{
  "pages": [
    "pages/home/home",
    "pages/recognize/recognize",
    "pages/result/result",
    "pages/noise/noise",
    "pages/records/records",
    "pages/records/add/add",
    "pages/vaccine/vaccine",
    "pages/profile/profile",
    "pages/baby/edit/edit"
  ],
  "window": {
    "backgroundTextStyle": "light",
    "navigationBarBackgroundColor": "#FFB6C1",
    "navigationBarTitleText": "育儿助手",
    "navigationBarTextStyle": "black"
  },
  "tabBar": {
    "color": "#999",
    "selectedColor": "#FF69B4",
    "list": [
      {
        "pagePath": "pages/home/home",
        "text": "首页",
        "iconPath": "images/home.png",
        "selectedIconPath": "images/home-active.png"
      },
      {
        "pagePath": "pages/recognize/recognize",
        "text": "识别",
        "iconPath": "images/recognize.png",
        "selectedIconPath": "images/recognize-active.png"
      },
      {
        "pagePath": "pages/records/records",
        "text": "记录",
        "iconPath": "images/records.png",
        "selectedIconPath": "images/records-active.png"
      },
      {
        "pagePath": "pages/profile/profile",
        "text": "我的",
        "iconPath": "images/profile.png",
        "selectedIconPath": "images/profile-active.png"
      }
    ]
  },
  "requiredPrivateInfos": ["getLocation"],
  "permission": {
    "scope.record": {
      "desc": "用于录制婴儿哭声进行识别"
    }
  }
}
```

- [ ] **Step 3: Create app.wxss**

```css
/* miniapp/app.wxss */
page {
  background-color: #FFF8F0;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif;
  color: #333;
}

.container {
  padding: 20rpx 30rpx;
}

.btn-primary {
  background: linear-gradient(135deg, #FFB6C1, #FF69B4);
  color: #fff;
  border-radius: 50rpx;
  border: none;
  padding: 20rpx 60rpx;
  font-size: 32rpx;
}

.btn-secondary {
  background: #fff;
  color: #FF69B4;
  border: 2rpx solid #FF69B4;
  border-radius: 50rpx;
  padding: 16rpx 50rpx;
  font-size: 28rpx;
}

.card {
  background: #fff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.05);
}
```

- [ ] **Step 4: Create API utility**

```javascript
// miniapp/utils/api.js
const app = getApp();

function request(method, path, data = {}, options = {}) {
  return new Promise((resolve, reject) => {
    const header = {
      'Content-Type': 'application/json',
    };
    if (app.globalData.token) {
      header['Authorization'] = `Bearer ${app.globalData.token}`;
    }

    wx.request({
      url: `${app.globalData.apiBase}${path}`,
      method,
      header,
      data,
      ...options,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(res.data);
        }
      },
      fail(err) {
        wx.showToast({ title: '网络请求失败', icon: 'none' });
        reject(err);
      },
    });
  });
}

function uploadFile(path, filePath, formData = {}) {
  return new Promise((resolve, reject) => {
    const header = {};
    if (app.globalData.token) {
      header['Authorization'] = `Bearer ${app.globalData.token}`;
    }

    wx.uploadFile({
      url: `${app.globalData.apiBase}${path}`,
      filePath,
      name: 'audio',
      header,
      formData,
      success(res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(res.data));
        } else {
          reject(JSON.parse(res.data));
        }
      },
      fail(err) {
        wx.showToast({ title: '上传失败', icon: 'none' });
        reject(err);
      },
    });
  });
}

module.exports = {
  get: (path, data) => request('GET', path, data),
  post: (path, data) => request('POST', path, data),
  put: (path, data) => request('PUT', path, data),
  uploadFile,
};
```

- [ ] **Step 5: Commit**

```bash
git add miniapp/
git commit -m "feat: init WeChat Mini Program project structure"
```

---

### Task 14: Cry Recognition Pages (Record + Result)

**Files:**
- Create: `miniapp/pages/recognize/recognize.js`
- Create: `miniapp/pages/recognize/recognize.wxml`
- Create: `miniapp/pages/recognize/recognize.wxss`
- Create: `miniapp/pages/result/result.js`
- Create: `miniapp/pages/result/result.wxml`
- Create: `miniapp/pages/result/result.wxss`

- [ ] **Step 1: Create recognize.js (recording logic)**

```javascript
// miniapp/pages/recognize/recognize.js
const api = require('../../utils/api');
const app = getApp();
const recorderManager = wx.getRecorderManager();

Page({
  data: {
    isRecording: false,
    recordTime: 0,
    canStop: false,  // Disable stop before 6s
    timer: null,
  },

  onLoad() {
    recorderManager.onStop((res) => this.onRecordStop(res));
  },

  startRecord() {
    this.setData({ isRecording: true, recordTime: 0, canStop: false });

    recorderManager.start({
      duration: 30000,       // Max 30s
      sampleRate: 16000,
      numberOfChannels: 1,
      encodeBitRate: 48000,
      format: 'mp3',
    });

    this.data.timer = setInterval(() => {
      const t = this.data.recordTime + 1;
      this.setData({
        recordTime: t,
        canStop: t >= 6,
      });
      if (t >= 30) {
        this.stopRecord();
      }
    }, 1000);
  },

  stopRecord() {
    if (!this.data.canStop) {
      wx.showToast({ title: `请至少录制6秒`, icon: 'none' });
      return;
    }
    clearInterval(this.data.timer);
    recorderManager.stop();
    this.setData({ isRecording: false });
  },

  async onRecordStop(res) {
    wx.showLoading({ title: '识别中...' });

    try {
      const formData = {};
      if (app.globalData.babyId) {
        formData.baby_id = String(app.globalData.babyId);
      }

      const result = await api.uploadFile(
        '/cry/recognize',
        res.tempFilePath,
        formData
      );

      wx.hideLoading();
      wx.navigateTo({
        url: '/pages/result/result',
        success: (page) => {
          page.setData({ result });
        },
      });
    } catch (err) {
      wx.hideLoading();
      wx.showToast({ title: '识别失败，请重试', icon: 'none' });
    }
  },

  onUnload() {
    if (this.data.timer) clearInterval(this.data.timer);
  },
});
```

- [ ] **Step 2: Create recognize.wxml**

```xml
<!-- miniapp/pages/recognize/recognize.wxml -->
<view class="container">
  <view class="header">
    <text class="baby-name">{{babyName || '宝宝'}}</text>
  </view>

  <view class="cry-animation">
    <image class="cry-img {{isRecording ? 'shake' : ''}}"
           src="/images/crying-baby.png"
           mode="aspectFit" />
  </view>

  <view class="record-section">
    <view wx:if="{{!isRecording}}" class="status-text">
      请靠近婴儿头部，点击开始录音
    </view>
    <view wx:else class="status-text recording">
      正在录制... {{recordTime}}s
    </view>

    <view wx:if="{{isRecording}}" class="waveform">
      <view wx:for="{{[1,2,3,4,5,6,7,8,9,10]}}" wx:key="index"
            class="wave-bar" style="animation-delay: {{index * 0.08}}s" />
    </view>

    <view class="record-btn {{isRecording ? 'recording' : ''}}"
          bindtap="{{isRecording ? 'stopRecord' : 'startRecord'}}">
      <text>{{isRecording ? '⏹' : '🎤'}}</text>
    </view>

    <view class="hint">
      {{isRecording ? '点击停止录音' : '最少录制6秒，最长30秒'}}
    </view>
  </view>
</view>
```

- [ ] **Step 3: Create recognize.wxss**

```css
/* miniapp/pages/recognize/recognize.wxss */
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 60rpx;
  min-height: 100vh;
}

.cry-animation {
  margin: 40rpx 0;
}

.cry-img {
  width: 240rpx;
  height: 240rpx;
  border-radius: 50%;
}

.shake {
  animation: shake 0.5s infinite;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4rpx); }
  75% { transform: translateX(4rpx); }
}

.record-section {
  text-align: center;
  margin-top: 40rpx;
}

.status-text {
  font-size: 28rpx;
  color: #999;
  margin-bottom: 30rpx;
}

.status-text.recording {
  color: #FF6B6B;
}

.waveform {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  height: 60rpx;
  gap: 6rpx;
  margin-bottom: 30rpx;
}

.wave-bar {
  width: 8rpx;
  background: linear-gradient(to top, #FFB6C1, #FF69B4);
  border-radius: 4rpx;
  animation: waveHeight 0.8s ease-in-out infinite alternate;
}

@keyframes waveHeight {
  0% { height: 10rpx; }
  100% { height: 50rpx; }
}

.record-btn {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #FFB6C1, #FF69B4);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 48rpx;
  margin: 0 auto;
  box-shadow: 0 8rpx 24rpx rgba(255,105,180,0.3);
}

.record-btn.recording {
  background: linear-gradient(135deg, #FF6B6B, #FF4444);
  animation: pulse 1.2s infinite;
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255,68,68,0.4); }
  50% { box-shadow: 0 0 0 20rpx rgba(255,68,68,0); }
}

.hint {
  font-size: 22rpx;
  color: #bbb;
  margin-top: 20rpx;
}
```

- [ ] **Step 4: Create result.js**

```javascript
// miniapp/pages/result/result.js
Page({
  data: {
    result: null,
  },

  onLoad(options) {
    // Result data is set via navigateTo from recognize page
  },

  goBack() {
    wx.navigateBack();
  },

  retryRecord() {
    wx.navigateBack();
  },
});
```

- [ ] **Step 5: Create result.wxml**

```xml
<!-- miniapp/pages/result/result.wxml -->
<view class="container" wx:if="{{result}}">
  <view class="result-card">
    <view class="main-type">
      <text class="type-emoji">{{result.cry_type === '饥饿' ? '🍼' : result.cry_type === '尿布不适' ? '👶' : result.cry_type === '疲倦' ? '😴' : result.cry_type === '疼痛' ? '😣' : result.cry_type === '需要安抚' ? '🤗' : result.cry_type === '出牙' ? '🦷' : '❓'}}</text>
      <text class="type-label">{{result.cry_type}}</text>
      <text class="confidence">{{result.confidence * 100}}% 置信度</text>
    </view>

    <view class="secondary-types" wx:if="{{result.secondary_types.length > 0}}">
      <text class="section-title">其他可能</text>
      <view class="type-tags">
        <view class="tag" wx:for="{{result.secondary_types}}" wx:key="type">
          {{item.type}} {{item.confidence * 100}}%
        </view>
      </view>
    </view>
  </view>

  <view class="advice-card">
    <view class="advice-section" wx:if="{{result.advice.cause}}">
      <text class="section-title">📋 原因分析</text>
      <text class="advice-text">{{result.advice.cause}}</text>
    </view>

    <view class="advice-section" wx:if="{{result.advice.solutions.length > 0}}">
      <text class="section-title">✅ 建议方案</text>
      <view class="advice-item" wx:for="{{result.advice.solutions}}" wx:key="*this">
        <text>• {{item}}</text>
      </view>
    </view>

    <view class="advice-section" wx:if="{{result.advice.soothing_tips.length > 0}}">
      <text class="section-title">🤗 安抚技巧</text>
      <view class="advice-item" wx:for="{{result.advice.soothing_tips}}" wx:key="*this">
        <text>• {{item}}</text>
      </view>
    </view>

    <view class="advice-section warning" wx:if="{{result.advice.warnings.length > 0}}">
      <text class="section-title">⚠️ 注意事项</text>
      <view class="advice-item" wx:for="{{result.advice.warnings}}" wx:key="*this">
        <text>• {{item}}</text>
      </view>
    </view>
  </view>

  <view class="actions">
    <button class="btn-primary" bindtap="retryRecord">🔄 重新录音</button>
  </view>
</view>
```

- [ ] **Step 6: Create result.wxss**

```css
/* miniapp/pages/result/result.wxss */
.result-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 40rpx;
  margin: 30rpx 0;
  text-align: center;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.main-type {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.type-emoji { font-size: 80rpx; margin-bottom: 12rpx; }
.type-label { font-size: 44rpx; font-weight: 700; color: #e91e63; }
.confidence { font-size: 26rpx; color: #999; margin-top: 8rpx; }

.secondary-types { margin-top: 30rpx; }
.section-title { font-size: 26rpx; color: #999; margin-bottom: 12rpx; display: block; }
.type-tags { display: flex; flex-wrap: wrap; gap: 12rpx; justify-content: center; }
.tag {
  background: #F3E5F5;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
  font-size: 24rpx;
  color: #7B1FA2;
}

.advice-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 30rpx;
  margin-bottom: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0,0,0,0.05);
}

.advice-section { margin-bottom: 24rpx; }
.advice-section:last-child { margin-bottom: 0; }
.advice-text { font-size: 28rpx; color: #555; line-height: 1.6; }
.advice-item { font-size: 26rpx; color: #555; line-height: 1.8; padding-left: 10rpx; }

.warning { background: #FFF3E0; padding: 16rpx 20rpx; border-radius: 12rpx; }

.actions {
  text-align: center;
  margin: 30rpx 0 40rpx;
}
```

- [ ] **Step 7: Commit**

```bash
git add miniapp/pages/recognize/ miniapp/pages/result/
git commit -m "feat: add cry recording and result display pages"
```

---

### Task 15: White Noise Page

**Files:**
- Create: `miniapp/pages/noise/noise.js`
- Create: `miniapp/pages/noise/noise.wxml`
- Create: `miniapp/pages/noise/noise.wxss`

- [ ] **Step 1: Create noise.js**

```javascript
// miniapp/pages/noise/noise.js
const api = require('../../utils/api');
const app = getApp();
const audioCtx = wx.createInnerAudioContext();

Page({
  data: {
    items: [],
    categories: [],
    activeCategory: '全部',
    currentTrack: null,
    isPlaying: false,
    isLoop: false,
  },

  onLoad() { this.loadList(); },

  async loadList() {
    try {
      const res = await api.get('/noise/list');
      this.setData({ items: res.items, categories: res.categories });
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  switchCategory(e) {
    this.setData({ activeCategory: e.currentTarget.dataset.cat });
  },

  togglePlay(e) {
    const item = e.currentTarget.dataset.item;
    if (this.data.currentTrack && this.data.currentTrack.id === item.id) {
      this._togglePauseResume();
    } else {
      this._playNew(item);
    }
  },

  _playNew(item) {
    audioCtx.src = `${app.globalData.apiBase}/noise/${item.id}/stream`;
    audioCtx.loop = this.data.isLoop;
    audioCtx.play();
    this.setData({ currentTrack: item, isPlaying: true });
  },

  _togglePauseResume() {
    if (this.data.isPlaying) {
      audioCtx.pause();
    } else {
      audioCtx.play();
    }
    this.setData({ isPlaying: !this.data.isPlaying });
  },

  toggleLoop() {
    const loop = !this.data.isLoop;
    audioCtx.loop = loop;
    this.setData({ isLoop: loop });
  },

  onUnload() { audioCtx.destroy(); },
});
```

- [ ] **Step 2: Create noise.wxml**

```xml
<!-- miniapp/pages/noise/noise.wxml -->
<view class="container">
  <view class="header-desc">
    播放白噪音有助于宝宝放松和入睡，建议在安静环境中播放，不超过30分钟。
  </view>

  <scroll-view class="tabs" scroll-x>
    <view class="tab {{activeCategory === cat ? 'active' : ''}}"
          wx:for="{{categories}}" wx:key="*this"
          data-cat="{{item}}" bindtap="switchCategory">
      {{item}}
    </view>
  </scroll-view>

  <view class="noise-list">
    <view class="noise-item" wx:for="{{items}}" wx:key="id">
      <view class="noise-icon">{{item.icon}}</view>
      <view class="noise-name">{{item.name}}</view>
      <view class="noise-actions">
        <view class="noise-btn" data-item="{{item}}" bindtap="togglePlay">
          {{currentTrack && currentTrack.id === item.id && isPlaying ? '⏸' : '▶️'}}
        </view>
        <view class="noise-btn {{isLoop ? 'active' : ''}}" bindtap="toggleLoop">🔁</view>
      </view>
    </view>
  </view>

  <view class="player-bar" wx:if="{{currentTrack}}">
    <text class="playing-name">{{currentTrack.name}}</text>
    <view class="player-controls">
      <view class="ctrl-btn" bindtap="togglePlay">
        {{isPlaying ? '⏸' : '▶️'}}
      </view>
      <view class="ctrl-btn {{isLoop ? 'active' : ''}}" bindtap="toggleLoop">🔁</view>
    </view>
  </view>
</view>
```

- [ ] **Step 3: Create noise.wxss**

```css
/* miniapp/pages/noise/noise.wxss */
.header-desc {
  font-size: 24rpx; color: #999; margin-bottom: 20rpx; line-height: 1.6;
}
.tabs {
  display: flex; white-space: nowrap; margin-bottom: 20rpx;
}
.tab {
  display: inline-block; padding: 12rpx 28rpx; font-size: 26rpx; color: #666;
  border-radius: 30rpx; margin-right: 16rpx;
}
.tab.active { background: #FFB6C1; color: #fff; }
.noise-item {
  display: flex; align-items: center; background: #fff; border-radius: 16rpx;
  padding: 24rpx; margin-bottom: 16rpx;
}
.noise-icon { font-size: 44rpx; margin-right: 20rpx; }
.noise-name { flex: 1; font-size: 28rpx; }
.noise-actions { display: flex; gap: 16rpx; }
.noise-btn { font-size: 36rpx; padding: 8rpx; }
.noise-btn.active { color: #FF69B4; }
.player-bar {
  position: fixed; bottom: 0; left: 0; right: 0; background: #fff;
  padding: 20rpx 30rpx; display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 -4rpx 16rpx rgba(0,0,0,0.05);
}
.playing-name { font-size: 26rpx; color: #333; }
.player-controls { display: flex; gap: 24rpx; }
.ctrl-btn { font-size: 40rpx; }
.ctrl-btn.active { color: #FF69B4; }
```

- [ ] **Step 4: Commit**

```bash
git add miniapp/pages/noise/
git commit -m "feat: add white noise player page"
```

---

### Task 16: Records, Vaccine & Profile Pages

**Files:**
- Create: `miniapp/pages/records/records.js`, `.wxml`, `.wxss`
- Create: `miniapp/pages/records/add/add.js`, `.wxml`, `.wxss`
- Create: `miniapp/pages/vaccine/vaccine.js`, `.wxml`, `.wxss`
- Create: `miniapp/pages/profile/profile.js`, `.wxml`, `.wxss`
- Create: `miniapp/pages/baby/edit/edit.js`, `.wxml`, `.wxss`
- Create: `miniapp/pages/home/home.js`, `.wxml`, `.wxss`

- [ ] **Step 1: Create records list page**

```javascript
// miniapp/pages/records/records.js
const api = require('../../utils/api');
const app = getApp();

Page({
  data: {
    records: [],
    tab: 'feeding',  // feeding | sleep | diaper
    noMore: false,
  },

  onShow() { this.loadRecords(); },

  async loadRecords() {
    if (!app.globalData.babyId) return;
    const { tab } = this.data;
    const path = `/records/${tab}/list?baby_id=${app.globalData.babyId}`;
    try {
      const res = await api.get(path);
      this.setData({ records: res, noMore: res.length < 20 });
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  switchTab(e) { this.setData({ tab: e.currentTarget.dataset.tab }, () => this.loadRecords()); },
  goAdd() { wx.navigateTo({ url: `/pages/records/add/add?type=${this.data.tab}` }); },
});
```

```xml
<!-- miniapp/pages/records/records.wxml -->
<view class="container">
  <view class="tabs">
    <view class="tab {{tab === 'feeding' ? 'active' : ''}}" data-tab="feeding" bindtap="switchTab">喂养</view>
    <view class="tab {{tab === 'sleep' ? 'active' : ''}}" data-tab="sleep" bindtap="switchTab">睡眠</view>
    <view class="tab {{tab === 'diaper' ? 'active' : ''}}" data-tab="diaper" bindtap="switchTab">大小便</view>
  </view>

  <view class="record-list">
    <view class="record-item" wx:for="{{records}}" wx:key="id">
      <text>{{item.start_time || item.time}}</text>
      <text wx:if="{{tab === 'feeding'}}">{{item.amount}}ml {{item.side}}</text>
      <text wx:if="{{tab === 'sleep'}}">质量: {{item.quality || '未记录'}}</text>
      <text wx:if="{{tab === 'diaper'}}">{{item.type}} {{item.color}}</text>
    </view>
    <view class="no-more" wx:if="{{noMore}}">没有更多了</view>
  </view>

  <view class="add-btn" bindtap="goAdd">+ 添加记录</view>
</view>
```

- [ ] **Step 2: Create add record page**

```javascript
// miniapp/pages/records/add/add.js
const api = require('../../../utils/api');
const app = getApp();

Page({
  data: {
    type: 'feeding',
    startTime: '',
    endTime: '',
    amount: '',
    side: '',
    quality: '',
    diaperType: '',
    color: '',
    note: '',
  },

  onLoad(options) {
    this.setData({ type: options.type || 'feeding' });
  },

  onTimeChange(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [field]: e.detail.value });
  },

  onInputChange(e) {
    const { field } = e.currentTarget.dataset;
    this.setData({ [field]: e.detail.value });
  },

  async submit() {
    const { type } = this.data;
    const babyId = app.globalData.babyId;
    if (!babyId) { wx.showToast({ title: '请先设置宝宝信息', icon: 'none' }); return; }

    let path, body;
    if (type === 'feeding') {
      path = `/records/feeding?baby_id=${babyId}`;
      body = { start_time: this.data.startTime, end_time: this.data.endTime || null, amount: parseInt(this.data.amount) || 0, side: this.data.side, note: this.data.note };
    } else if (type === 'sleep') {
      path = `/records/sleep?baby_id=${babyId}`;
      body = { start_time: this.data.startTime, end_time: this.data.endTime || null, quality: this.data.quality, note: this.data.note };
    } else {
      path = `/records/diaper?baby_id=${babyId}`;
      body = { time: this.data.startTime, type: this.data.diaperType, color: this.data.color, note: this.data.note };
    }

    try {
      await api.post(path, body);
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1000);
    } catch (err) {
      wx.showToast({ title: '保存失败', icon: 'none' });
    }
  },
});
```

- [ ] **Step 3: Create vaccine page**

```javascript
// miniapp/pages/vaccine/vaccine.js
const api = require('../../utils/api');
const app = getApp();

Page({
  data: { vaccines: [] },

  onShow() { this.loadList(); },

  async loadList() {
    if (!app.globalData.babyId) return;
    try {
      const res = await api.get(`/vaccine/list?baby_id=${app.globalData.babyId}`);
      this.setData({ vaccines: res });
    } catch (err) {
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  async markComplete(e) {
    const { id } = e.currentTarget.dataset;
    try {
      await api.put(`/vaccine/${id}/status`, { status: '已接种' });
      wx.showToast({ title: '已标记完成', icon: 'success' });
      this.loadList();
    } catch (err) {
      wx.showToast({ title: '操作失败', icon: 'none' });
    }
  },
});
```

```xml
<!-- miniapp/pages/vaccine/vaccine.wxml -->
<view class="container">
  <view class="vaccine-item" wx:for="{{vaccines}}" wx:key="id">
    <view class="vaccine-info">
      <text class="vaccine-name">{{item.name}}</text>
      <text class="vaccine-date">计划: {{item.scheduled_date}}</text>
      <text class="vaccine-status {{item.status === '已接种' ? 'done' : ''}}">{{item.status}}</text>
    </view>
    <view class="vaccine-action" wx:if="{{item.status === '未接种'}}">
      <button class="btn-secondary" size="mini" data-id="{{item.id}}" bindtap="markComplete">完成</button>
    </view>
  </view>
</view>
```

- [ ] **Step 4: Create profile page**

```javascript
// miniapp/pages/profile/profile.js
const app = getApp();

Page({
  data: {
    babyInfo: null,
  },

  onShow() {
    this.setData({ babyInfo: app.globalData.babyInfo });
  },

  goEditBaby() {
    wx.navigateTo({ url: '/pages/baby/edit/edit' });
  },
  goVaccine() {
    wx.navigateTo({ url: '/pages/vaccine/vaccine' });
  },
  goNoise() {
    wx.navigateTo({ url: '/pages/noise/noise' });
  },
});
```

```xml
<!-- miniapp/pages/profile/profile.wxml -->
<view class="container">
  <view class="profile-header">
    <image class="avatar" src="{{babyInfo.avatar_url || '/images/default-avatar.png'}}" mode="aspectFill" />
    <text class="nickname">{{babyInfo.nickname || '未设置宝宝'}}</text>
    <text class="age" wx:if="{{babyInfo.birthday}}">月龄: {{babyInfo.birthday}}</text>
  </view>

  <view class="menu-list">
    <view class="menu-item" bindtap="goEditBaby">📝 宝宝信息设置</view>
    <view class="menu-item" bindtap="goVaccine">💉 疫苗提醒</view>
    <view class="menu-item" bindtap="goNoise">🎵 白噪音</view>
    <view class="menu-item">📊 成长分析</view>
    <view class="menu-item">📮 意见反馈</view>
    <view class="menu-item">📤 分享小程序</view>
  </view>
</view>
```

- [ ] **Step 5: Create baby edit page**

```javascript
// miniapp/pages/baby/edit/edit.js
const api = require('../../../utils/api');
const app = getApp();

Page({
  data: {
    nickname: '',
    birthday: '',
    gender: '',
    feedType: '',
  },

  onShow() {
    const b = app.globalData.babyInfo;
    if (b) this.setData({ nickname: b.nickname || '', birthday: b.birthday || '', gender: b.gender || '', feedType: b.feed_type || '' });
  },

  onInput(e) { const { field } = e.currentTarget.dataset; this.setData({ [field]: e.detail.value }); },

  async save() {
    const body = { nickname: this.data.nickname, birthday: this.data.birthday || null, gender: this.data.gender, feed_type: this.data.feedType };
    try {
      const res = await api.post('/baby', body);
      app.globalData.babyId = res.id;
      app.globalData.babyInfo = res;
      wx.showToast({ title: '保存成功', icon: 'success' });
      setTimeout(() => wx.navigateBack(), 1000);
    } catch (err) {
      wx.showToast({ title: '保存失败', icon: 'none' });
    }
  },
});
```

- [ ] **Step 6: Create home page**

```javascript
// miniapp/pages/home/home.js
const app = getApp();

Page({
  data: {
    babyInfo: null,
    dayCount: 0,
    greeting: '',
  },

  onShow() {
    const b = app.globalData.babyInfo;
    if (b) {
      this.setData({ babyInfo: b });
      if (b.birthday) {
        const days = Math.floor((Date.now() - new Date(b.birthday).getTime()) / 86400000);
        this.setData({ dayCount: days, greeting: `早上好！今天${b.nickname}已经${days}天啦！` });
      }
    }
  },

  goTo(e) {
    const { page } = e.currentTarget.dataset;
    wx.navigateTo({ url: page });
  },
});
```

```xml
<!-- miniapp/pages/home/home.wxml -->
<view class="container">
  <view class="greeting" wx:if="{{greeting}}">{{greeting}}</view>

  <view class="grid">
    <view class="grid-item" data-page="/pages/records/records" bindtap="goTo">
      <view class="grid-icon">📝</view>
      <text>成长记录</text>
    </view>
    <view class="grid-item" data-page="/pages/vaccine/vaccine" bindtap="goTo">
      <view class="grid-icon">💉</view>
      <text>疫苗提醒</text>
    </view>
    <view class="grid-item" data-page="/pages/noise/noise" bindtap="goTo">
      <view class="grid-icon">🎵</view>
      <text>白噪音</text>
    </view>
    <view class="grid-item" data-page="/pages/profile/profile" bindtap="goTo">
      <view class="grid-icon">👤</view>
      <text>我的</text>
    </view>
  </view>
</view>
```

- [ ] **Step 7: Commit**

```bash
git add miniapp/pages/records/ miniapp/pages/vaccine/ miniapp/pages/profile/ miniapp/pages/baby/ miniapp/pages/home/
git commit -m "feat: add records, vaccine, profile, baby edit, and home pages"
```

---

## Phase 5: Integration & Polish

### Task 17: Login Flow & Global State

**Files:**
- Modify: `miniapp/app.js`

- [ ] **Step 1: Update app.js with login flow**

```javascript
// miniapp/app.js
const api = require('./utils/api');

App({
  globalData: {
    apiBase: 'http://localhost:8000/api',
    token: '',
    babyId: null,
    babyInfo: null,
  },

  onLaunch() {
    const token = wx.getStorageSync('token');
    if (token) {
      this.globalData.token = token;
      this.loadBabyInfo();
    } else {
      this.login();
    }
  },

  async login() {
    try {
      const { code } = await wx.login();
      const res = await api.post('/user/login', { code });
      this.globalData.token = res.token;
      wx.setStorageSync('token', res.token);
      await this.loadBabyInfo();
    } catch (err) {
      console.error('Login failed:', err);
    }
  },

  async loadBabyInfo() {
    try {
      const babies = await api.get('/baby');
      if (babies.length > 0) {
        this.globalData.babyId = babies[0].id;
        this.globalData.babyInfo = babies[0];
      }
    } catch (err) {
      console.error('Load baby failed:', err);
    }
  },
});
```

- [ ] **Step 2: Commit**

```bash
git add miniapp/app.js
git commit -m "feat: add WeChat login flow and global state management"
```

---

### Task 18: Final Verification & .gitignore

**Files:**
- Create: `.gitignore`
- Create: `backend/.env.example`

- [ ] **Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
.venv/
venv/

# Environment
.env
backend/.env

# IDE
.vscode/
.idea/

# Superpowers
.superpowers/

# Uploads
backend/uploads/

# Models (large files)
backend/models/*.onnx
backend/models/*.pt
backend/models/*.pth

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create .env.example**

```bash
# backend/.env.example
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/babycry
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=change-me-in-production
ANTHROPIC_API_KEY=sk-ant-xxx
```

- [ ] **Step 3: Verify project structure**

```bash
# Expected structure:
# backend/
#   app/
#     main.py, config.py, database.py
#     api/      (user.py, baby.py, cry.py, records.py, vaccine.py, noise.py)
#     models/   (user.py, baby.py, feeding.py, sleep.py, diaper.py, vaccine.py, cry_record.py)
#     services/ (audio_processor.py, cry_classifier.py, ai_client.py)
#     schemas/  (user.py, baby.py, records.py, vaccine.py, cry.py)
#   models/     (empty - for CNN weights)
#   data/       (white noise audio files)
#   requirements.txt
# miniapp/
#   app.js, app.json, app.wxss
#   utils/api.js
#   pages/
#     home/ recognize/ result/ noise/
#     records/ vaccine/ profile/ baby/
```

- [ ] **Step 4: Final commit**

```bash
git add .gitignore backend/.env.example
git commit -m "chore: add .gitignore and env template"
```

---

## Summary

**Total: 18 tasks across 5 phases**

| Phase | Tasks | What it delivers |
|-------|-------|-----------------|
| 1. Foundation | 1-3 | FastAPI scaffold, DB models, Pydantic schemas |
| 2. Core Services | 4-6 | Audio processor, CNN classifier, Claude client |
| 3. API Routes | 7-12 | All REST endpoints wired up |
| 4. Frontend | 13-16 | WeChat Mini Program with all pages |
| 5. Polish | 17-18 | Login flow, global state, .gitignore |

**To run the backend:** `cd backend && uvicorn app.main:app --reload --port 8000`

**To test:** Open the mini program in WeChat DevTools, point API base to `http://localhost:8000/api`.
