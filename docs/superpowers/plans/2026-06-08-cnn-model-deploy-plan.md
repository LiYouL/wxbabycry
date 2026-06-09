# CNN哭声识别模型 + 腾讯云部署 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 训练真实CNN模型替换placeholder随机分类器，并准备腾讯云部署配置

**Architecture:** librosa MFCC特征提取 → PyTorch CNN分类 → ONNX导出 → ONNX Runtime推理替换random预测。Docker Compose管理FastAPI+PostgreSQL+Nginx三容器部署

**Tech Stack:** Python 3.8, PyTorch, librosa, ONNX Runtime, Docker Compose, FastAPI, PostgreSQL

---

## Phase 1: 数据集准备 & 模型训练

### Task 1: 安装训练依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加训练依赖到requirements.txt**

```
torch>=1.10.0
torchaudio>=0.10.0
onnx>=1.12.0
onnxruntime>=1.12.0
soundfile>=0.10.0
audiomentations>=0.27.0
scikit-learn>=0.24.0
```

- [ ] **Step 2: 安装**

```bash
cd backend && pip install torch torchaudio onnx onnxruntime soundfile audiomentations scikit-learn
```

---

### Task 2: 数据集下载脚本

**Files:**
- Create: `backend/scripts/download_data.py`

- [ ] **Step 1: 写下载脚本**

```python
# backend/scripts/download_data.py
"""Download donateacry-corpus dataset from public source."""
import os
import urllib.request
import zipfile
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cry_dataset")
DONATEACRY_URL = "https://raw.githubusercontent.com/gveres/donateacry-corpus/master/donateacry_corpus.zip"

def download():
    os.makedirs(DATA_DIR, exist_ok=True)
    zip_path = os.path.join(DATA_DIR, "donateacry.zip")
    
    print(f"Downloading donateacry-corpus from {DONATEACRY_URL}...")
    try:
        urllib.request.urlretrieve(DONATEACRY_URL, zip_path)
    except Exception:
        print("GitHub download failed. Trying alternative source...")
        # Fallback: try kaggle or other mirror
        print("Please manually download from:")
        print("  https://github.com/gveres/donateacry-corpus")
        print(f"  and extract to {DATA_DIR}")
        print("Expected structure: data/cry_dataset/donateacry_corpus/<audio_files>")
        sys.exit(1)
    
    print("Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(DATA_DIR)
    
    os.remove(zip_path)
    print(f"Dataset extracted to {DATA_DIR}")

if __name__ == "__main__":
    download()
```

- [ ] **Step 2: 运行下载**

```bash
cd backend && python scripts/download_data.py
```

---

### Task 3: 数据增强模块

**Files:**
- Create: `backend/scripts/augment.py`

- [ ] **Step 1: 写增强模块**

```python
# backend/scripts/augment.py
"""Audio augmentation for baby cry training data."""
import numpy as np
import librosa
import soundfile as sf
from audiomentations import Compose, AddBackgroundNoise, RoomSimulator
from audiomentations import Gain, TimeStretch, PitchShift, FrequencyMask

SR = 16000

def create_augment_pipeline():
    return Compose([
        AddBackgroundNoise(
            sounds_path=None,  # Will use synthetic noise if no noise dataset
            min_snr_in_db=5,
            max_snr_in_db=20,
            p=0.5,
        ),
        RoomSimulator(
            min_target_rt60=0.1,
            max_target_rt60=0.6,
            p=0.4,
        ),
        Gain(
            min_gain_in_db=-10,
            max_gain_in_db=10,
            p=0.5,
        ),
        FrequencyMask(
            min_frequency_band=0.1,
            max_frequency_band=0.3,
            p=0.3,
        ),
        TimeStretch(
            min_rate=0.9,
            max_rate=1.1,
            p=0.5,
        ),
        PitchShift(
            min_semitones=-2,
            max_semitones=2,
            p=0.5,
        ),
    ])

def augment_sample(y, sr=SR16000, n_variants=3):
    """Generate n_variants augmented versions of one audio sample."""
    pipeline = create_augment_pipeline()
    variants = []
    for _ in range(n_variants):
        augmented = pipeline(samples=y, sample_rate=sr)
        variants.append(augmented)
    return variants

def add_synthetic_noise(y, noise_level=0.01):
    """Add simple white/gaussian noise as fallback."""
    noise = np.random.randn(len(y)) * noise_level * np.max(np.abs(y))
    return y + noise

def add_babble_noise(y, sr=SR16000):
    """Add low-frequency rumble simulating household noise."""
    t = np.arange(len(y)) / sr
    rumble = 0.01 * np.sin(2 * np.pi * 60 * t) + 0.005 * np.sin(2 * np.pi * 120 * t)
    return y + rumble
```

---

### Task 4: 训练脚本

**Files:**
- Create: `backend/scripts/train.py`

- [ ] **Step 1: 写训练脚本**

```python
# backend/scripts/train.py
"""Train CNN classifier on baby cry MFCC features and export to ONNX."""
import os
import sys
import json
import numpy as np
import librosa
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scripts.augment import augment_sample, add_synthetic_noise, add_babble_noise

# Config
SR = 16000
N_MFCC = 40
TIME_FRAMES = 128  # Fixed length for CNN input
BATCH_SIZE = 32
EPOCHS = 50
LR = 0.001
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cry_dataset", "donateacry_corpus")
MODEL_OUT = os.path.join(os.path.dirname(__file__), "..", "models", "cry_classifier.onnx")
MODEL_PT = os.path.join(os.path.dirname(__file__), "..", "models", "cry_classifier.pt")

# Mapping from donateacry labels to our 7 classes
LABEL_MAP = {
    "hunger": 0,
    "pain": 3,
    "discomfort": 1,
    "tired": 2,
    "burping": 4,
}
OUR_CLASSES = ["hunger", "diaper", "tired", "pain", "comfort", "teething", "other"]


class CryCNN(nn.Module):
    def __init__(self, n_classes=7):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
        )
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(128, 128), nn.ReLU(), nn.Dropout(0.5),
            nn.Linear(128, n_classes),
        )

    def forward(self, x):
        x = self.conv(x)
        return self.fc(x)


def extract_mfcc(filepath, sr=SR, n_mfcc=N_MFCC, time_frames=TIME_FRAMES):
    """Load audio and extract MFCC, pad/truncate to fixed length."""
    y, _ = librosa.load(filepath, sr=sr, mono=True)
    y, _ = librosa.effects.trim(y, top_db=20)
    if len(y) < sr * 1.5:
        return None  # Too short
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
    if mfcc.shape[1] < time_frames:
        mfcc = np.pad(mfcc, ((0, 0), (0, time_frames - mfcc.shape[1])))
    else:
        mfcc = mfcc[:, :time_frames]
    return mfcc


def load_data(data_dir):
    """Load all audio files with labels, return X (MFCC) and y (labels)."""
    X, y_labels = [], []
    
    for label_name, label_id in LABEL_MAP.items():
        folder = os.path.join(data_dir, label_name)
        if not os.path.isdir(folder):
            print(f"  Skipping missing folder: {folder}")
            continue
        for fname in os.listdir(folder):
            if fname.endswith((".wav", ".mp3", ".m4a", ".ogg")):
                filepath = os.path.join(folder, fname)
                mfcc = extract_mfcc(filepath)
                if mfcc is not None:
                    X.append(mfcc)
                    y_labels.append(label_id)
    
    return np.array(X), np.array(y_labels)


def augment_data(X, y, factor=3):
    """Apply time-domain augmentation and re-extract MFCC."""
    X_aug, y_aug = [], []
    for i in range(len(X)):
        X_aug.append(X[i])
        y_aug.append(y[i])
        # Generate augmented variants from MFCC (approximate via noise injection)
        for _ in range(factor - 1):
            noise = np.random.normal(0, 0.05, X[i].shape).astype(np.float32)
            X_aug.append(X[i] + noise)
            y_aug.append(y[i])
    return np.array(X_aug, dtype=np.float32), np.array(y_aug)


def train_model(X, y):
    """Train CNN and export to ONNX."""
    n_classes = len(OUR_CLASSES)
    n_samples = len(X)
    
    # One-hot encode
    y_onehot = np.zeros((n_samples, n_classes))
    y_onehot[np.arange(n_samples), y] = 1
    
    # Train/val split
    X_tr, X_val, y_tr, y_val = train_test_split(
        X, y_onehot, test_size=0.2, stratify=y, random_state=42
    )
    
    # Augment training data
    X_tr, y_tr = augment_data(X_tr, np.argmax(y_tr, axis=1), factor=3)
    
    # Class weights for imbalance
    y_int = np.argmax(y_tr, axis=1)
    class_counts = np.bincount(y_int, minlength=n_classes)
    class_weights = torch.tensor(
        max(class_counts) / (class_counts + 1), dtype=torch.float32
    )
    
    # Prepare DataLoaders
    train_ds = TensorDataset(
        torch.tensor(X_tr).unsqueeze(1),
        torch.tensor(y_tr, dtype=torch.float32),
    )
    val_ds = TensorDataset(
        torch.tensor(X_val, dtype=torch.float32).unsqueeze(1),
        torch.tensor(y_val, dtype=torch.float32),
    )
    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)
    
    # Model, loss, optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    model = CryCNN(n_classes=n_classes).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))
    optimizer = optim.Adam(model.parameters(), lr=LR)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
    
    best_val_loss = float("inf")
    patience_counter = 0
    
    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0
        for xb, yb in train_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        model.eval()
        val_loss, correct, total = 0, 0, 0
        with torch.no_grad():
            for xb, yb in val_loader:
                xb, yb = xb.to(device), yb.to(device)
                out = model(xb)
                val_loss += criterion(out, yb).item()
                pred = out.argmax(dim=1)
                correct += (pred == yb.argmax(dim=1)).sum().item()
                total += yb.size(0)
        
        val_loss /= len(val_loader)
        val_acc = correct / total
        print(f"Epoch {epoch+1}/{EPOCHS} | train_loss: {train_loss/len(train_loader):.4f} | val_loss: {val_loss:.4f} | val_acc: {val_acc:.4f}")
        
        scheduler.step(val_loss)
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            torch.save(model.state_dict(), MODEL_PT)
        else:
            patience_counter += 1
            if patience_counter >= 10:
                print("Early stopping")
                break
    
    # Load best model
    model.load_state_dict(torch.load(MODEL_PT))
    
    # Export to ONNX
    model.eval()
    dummy = torch.randn(1, 1, N_MFCC, TIME_FRAMES).to(device)
    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    
    torch.onnx.export(
        model, dummy, MODEL_OUT,
        input_names=["mfcc"],
        output_names=["probs"],
        dynamic_axes={"mfcc": {0: "batch"}},
        opset_version=14,
    )
    print(f"Model exported to {MODEL_OUT}")
    
    # Also export label mapping
    label_map_path = os.path.join(os.path.dirname(MODEL_OUT), "labels.json")
    with open(label_map_path, "w") as f:
        json.dump(OUR_CLASSES, f, ensure_ascii=False)
    
    return model


if __name__ == "__main__":
    print("Loading data...")
    X, y = load_data(DATA_DIR)
    print(f"Loaded {len(X)} samples, {len(set(y))} classes")
    print(f"Class distribution: {dict(zip(*np.unique(y, return_counts=True)))}")
    
    print("Training...")
    train_model(X, y)
    print("Done! Model saved to models/cry_classifier.onnx")
```

- [ ] **Step 2: 运行训练**

```bash
cd backend && python scripts/train.py
```

---

### Task 5: 替换 placeholder 分类器

**Files:**
- Modify: `backend/app/services/cry_classifier.py`

- [ ] **Step 1: 用ONNX Runtime替换随机预测**

```python
# backend/app/services/cry_classifier.py
import os
import json
import numpy as np
import onnxruntime as ort
from app.config import settings

CRY_TYPES = ["饥饿", "尿布不适", "疲倦", "疼痛", "需要安抚", "出牙", "其他"]


class CryClassifier:
    def __init__(self, model_path: str = ""):
        model_path = model_path or settings.model_path
        self._labels = CRY_TYPES
        
        if os.path.exists(model_path):
            self._session = ort.InferenceSession(model_path)
            self._ready = True
            # Load label mapping if available
            label_map_path = os.path.join(os.path.dirname(model_path), "labels.json")
            if os.path.exists(label_map_path):
                with open(label_map_path, "r") as f:
                    mapped = json.load(f)
                    if len(mapped) == len(self._labels):
                        self._labels = mapped
        else:
            self._session = None
            self._ready = False

    def predict(self, mfcc: np.ndarray) -> list[dict]:
        if not self._ready:
            return self._random_predict(len(self._labels))
        
        # Prepare input: (1, 1, n_mfcc, time_frames)
        if mfcc.shape[1] < 128:
            mfcc = np.pad(mfcc, ((0, 0), (0, 128 - mfcc.shape[1])))
        else:
            mfcc = mfcc[:, :128]
        
        inp = mfcc[np.newaxis, np.newaxis, :, :].astype(np.float32)
        out = self._session.run(None, {"mfcc": inp})[0][0]
        
        # Softmax
        probs = np.exp(out - out.max()) / np.exp(out - out.max()).sum()
        
        results = [
            {"type": self._labels[i], "confidence": round(float(probs[i]), 4)}
            for i in range(min(len(self._labels), len(probs)))
        ]
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results

    def _random_predict(self, n) -> list[dict]:
        raw = np.random.dirichlet(np.ones(n) * 0.5)
        boost_idx = np.random.randint(0, n)
        raw[boost_idx] *= 3
        probs = raw / raw.sum()
        results = [
            {"type": self._labels[i], "confidence": round(float(probs[i]), 4)}
            for i in range(n)
        ]
        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results


classifier = CryClassifier()
```

- [ ] **Step 2: 验证接口兼容**

```bash
cd backend && python -c "
from app.services.cry_classifier import classifier
import numpy as np
mfcc = np.random.randn(40, 200).astype(np.float32)
result = classifier.predict(mfcc)
print('Predict OK:', len(result), 'classes')
print('Top result:', result[0])
"
```

---

## Phase 2: 腾讯云部署配置

### Task 6: Dockerfile

**Files:**
- Create: `backend/Dockerfile`

- [ ] **Step 1: 写Dockerfile**

```dockerfile
FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads/audio data/noise models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

---

### Task 7: Docker Compose

**Files:**
- Create: `backend/docker-compose.yml`

- [ ] **Step 1: 写docker-compose.yml**

```yaml
version: "3.9"

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:${DB_PASSWORD:-postgres}@postgres:5432/babycry
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET:-change-me-in-production}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - AUDIO_UPLOAD_DIR=/app/uploads/audio
      - NOISE_AUDIO_DIR=/app/data/noise
      - MODEL_PATH=/app/models/cry_classifier.onnx
    volumes:
      - ./models:/app/models
      - ./data/noise:/app/data/noise
      - uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_started
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${DB_PASSWORD:-postgres}
      - POSTGRES_DB=babycry
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d babycry"]
      interval: 5s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  pgdata:
  uploads:
```

---

### Task 8: Nginx 配置

**Files:**
- Create: `backend/nginx.conf`

- [ ] **Step 1: 写nginx.conf**

```nginx
events { worker_connections 1024; }

http {
    server {
        listen 80;
        server_name _;

        client_max_body_size 10m;

        location / {
            proxy_pass http://backend:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

        location /static/ {
            alias /app/static/;
        }
    }
}
```

---

### Task 9: .env 生产环境模板

**Files:**
- Modify: `backend/.env.example`

- [ ] **Step 1: 更新.env.example**

```
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:your-db-password@localhost:5432/babycry

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=change-this-to-a-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=43200

# Anthropic API
ANTHROPIC_API_KEY=sk-ant-your-key

# 文件路径
AUDIO_UPLOAD_DIR=./uploads/audio
NOISE_AUDIO_DIR=./data/noise
MODEL_PATH=./models/cry_classifier.onnx

# 录音限制
MIN_RECORD_SECONDS=6
MAX_RECORD_SECONDS=30
```

---

### Task 10: 部署文档

**Files:**
- Create: `backend/DEPLOY.md`

- [ ] **Step 1: 写部署文档**

```markdown
# 腾讯云部署指南

## 1. 服务器准备

购买腾讯云轻量应用服务器 2核4G，Ubuntu 22.04。

```bash
# SSH登录
ssh root@<your-server-ip>

# 安装Docker
curl -fsSL https://get.docker.com | sh

# 安装Docker Compose
apt install docker-compose -y
```

## 2. 上传代码

```bash
# 本地打包
cd backend
tar czf deploy.tar.gz \
  app/ models/ data/noise/ \
  Dockerfile docker-compose.yml nginx.conf requirements.txt

# 上传到服务器
scp deploy.tar.gz root@<ip>:/root/

# 服务器上解压
ssh root@<ip>
tar xzf deploy.tar.gz -C /opt/babycry/
cd /opt/babycry
```

## 3. 配置环境变量

```bash
cd /opt/babycry
cp .env.example .env
# 编辑.env,填入真实的数据库密码、JWT密钥、Anthropic API Key
nano .env
```

## 4. 启动

```bash
docker-compose up -d
```

## 5. 微信小程序配置

在微信公众平台 → 开发 → 开发管理 → 服务器域名：
- request合法域名: `https://<your-domain>`

## 6. SSL证书

腾讯云控制台申请免费SSL证书，下载Nginx格式，放入 `ssl/` 目录。
```

---

### Task 11: Commit

- [ ] **Step 1: 提交所有改动**

```bash
git add backend/scripts/ backend/models/ backend/app/services/cry_classifier.py
git add backend/Dockerfile backend/docker-compose.yml backend/nginx.conf backend/DEPLOY.md
git add backend/requirements.txt backend/.env.example
git commit -m "feat: CNN training pipeline + Tencent Cloud deploy configs"
```
