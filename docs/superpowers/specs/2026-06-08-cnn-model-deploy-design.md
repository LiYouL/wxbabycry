# CNN哭声识别模型 + 腾讯云部署 — 设计文档

**日期:** 2026-06-08
**范围:** 真实CNN模型训练替换占位 + 腾讯云服务器部署上线

---

## 1. 模型训练方案

### 1.1 数据集

- **主数据集**: donateacry-corpus，400+标注婴儿哭声样本
- **5个原始类别**: hunger / pain / discomfort / tired / burping
- **映射到7个系统类别**: 饥饿、疼痛、尿布不适、疲倦、需要安抚、出牙、其他

### 1.2 数据增强（针对真实录音噪声）

| 增强 | 模拟场景 | 方法 |
|------|---------|------|
| 背景噪声 | 电视、风扇、车流、人声 | ESC-50噪声叠加，SNR 5-20dB |
| 房间混响 | 卧室/客厅 | 脉冲响应卷积 |
| 音量变化 | 手机距离 | ±10dB随机增益 |
| 频率掩码 | 被子/隔门 | 随机频段衰减 |
| 时间拉伸 | 月龄差异 | 0.9x-1.1x |
| 音高偏移 | 不同宝宝 | ±2半音 |

原始400条 → 增强后2000+条

### 1.3 模型架构

```
MFCC(40×T) → Conv2D(32,3×3) → BN → ReLU → MaxPool(2,2)
→ Conv2D(64,3×3) → BN → ReLU → MaxPool(2,2)
→ Conv2D(128,3×3) → BN → ReLU → GlobalAvgPool
→ Dense(128) → ReLU → Dropout(0.5) → Softmax(7)
```

- 输入: 40×128 MFCC (固定长度，短截长补)
- 参数量: ~300K, ONNX约200KB
- CPU推理: <10ms

### 1.4 训练配置

- 优化器: Adam (lr=0.001)
- 损失: CrossEntropy
- Batch size: 32
- Epochs: 50, early stop patience=10
- Split: 80/20 train/val

### 1.5 代码改动

- 添加 `backend/scripts/train.py` — 训练脚本
- `cry_classifier.py` — ONNX Runtime替换random预测
- `cry.py` / `ai_client.py` — 无需修改

---

## 2. 腾讯云部署

### 2.1 服务器

- 轻量应用服务器 2核4G 60GB SSD
- Ubuntu 22.04
- 月费 ~¥70

### 2.2 架构

```
用户 → Nginx(HTTPS) → uvicorn(FastAPI)
                          ↓
              PostgreSQL │ Redis │ 本地文件存储(音频)
```

### 2.3 Docker Compose

```yaml
services:
  backend:   # FastAPI + ONNX推理
  postgres:  # PostgreSQL 16
  nginx:     # 反向代理 + Let's Encrypt
```

### 2.4 上线步骤

1. 购买轻量服务器
2. 安装Docker + Docker Compose
3. 推送代码+模型文件
4. docker compose up -d
5. 微信小程序后台配置request合法域名
6. 配置SSL证书

---

## 3. 实施顺序

1. 下载donateacry-corpus数据集
2. 编写数据增强+训练脚本
3. 本地GPU训练CNN
4. 导出ONNX模型
5. 替换cry_classifier.py
6. 本地验证端到端
7. 购买服务器并部署
