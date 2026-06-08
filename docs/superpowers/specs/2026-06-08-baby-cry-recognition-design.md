# 智能育儿助手 — 设计文档

**日期:** 2026-06-08
**范围:** 婴儿哭声识别 + AI 育儿建议 + 白噪音 + 成长记录 + 疫苗提醒

---

## 1. 概述

开发一个微信小程序，核心功能是利用 CNN 模型识别婴儿哭声含义，并通过 Claude API 生成个性化育儿建议。同时提供白噪音、喂养/睡眠/大小便记录、疫苗提醒等辅助功能。

### 关键决策

| 维度 | 决策 |
|------|------|
| 后端 | Python FastAPI + PostgreSQL + Redis |
| 前端 | 原生微信小程序 |
| 部署 | 腾讯云（微信小程序云服务器） |
| 哭声识别 | librosa MFCC 提取 → CNN 分类 → Claude 生成建议 |
| 录音 | 微信小程序实时录音，6-30 秒 |
| 结果展示 | 置信度降序排列：主类别 + 辅助类别 + 分点建议 |
| CNN MVP | 占位模型先跑通全流程，后续替换真实模型 |
| 宝宝信息 | 可跳过，给通用建议；设置后更精准 |

---

## 2. 系统架构

```
┌──────────────────────┐     ┌──────────────────────────────────────┐
│   微信小程序前端       │     │           FastAPI 后端 (腾讯云)        │
│                      │     │                                      │
│  [首页] [识别] [记录] │     │  POST /api/cry/recognize  ← 哭声识别  │
│  [我的]              │     │  GET  /api/noise/*        ← 白噪音    │
│                      │     │  POST /api/records/*      ← 喂养等记录 │
│  喂养计时器 录音页面   │     │  GET  /api/vaccine/*      ← 疫苗提醒  │
│  睡眠记录  结果展示   │     │  POST /api/baby           ← 宝宝信息  │
│  大小便    白噪音列表 │     │  POST /api/user/login     ← 微信登录  │
│  疫苗列表            │     │                                      │
│                      │     │  ┌───────────┐ ┌──────────────────┐  │
│                      │     │  │ CNN 分类器  │ │  Claude API      │  │
│                      │     │  │ (哭声识别)  │ │  (育儿建议生成)   │  │
│                      │     │  └───────────┘ └──────────────────┘  │
└──────────────────────┘     └──────────────────────────────────────┘
```

---

## 3. 哭声识别数据流

```
小程序录音 → FastAPI 接收音频 → librosa 预处理
  → MFCC 特征提取 → CNN 分类预测 → 分类结果 (类别+置信度)
  → Claude API 生成建议 → JSON 结果返回前端展示
```

### 音频预处理

- 重采样至 16kHz 单声道
- 静音裁剪（去除前后空白）
- 录音时长限制：最低 6 秒，最长 30 秒
- 提取 40 维 MFCC 特征矩阵

### CNN 分类器

- 输入：MFCC 特征矩阵
- 结构：3-4 层卷积 + 最大池化 + FC + softmax
- 输出：7 类概率分布（饥饿、尿布不适、疲倦、疼痛、需要安抚、出牙、其他）
- MVP 阶段：随机权重占位模型，跑通全流程后替换

### 识别类别

1. 饥饿 (Hunger)
2. 尿布湿了/不适 (Diaper Change/Discomfort)
3. 疲倦/想睡觉 (Tired/Sleepy)
4. 疼痛/不适 (Pain/Colic)
5. 需要安抚/抱抱 (Needs Comfort/Cuddle)
6. 出牙 (Teething)
7. 其他/未知 (Other/Unknown)

### Claude 提示词结构

- 系统角色：育儿专家
- 上下文输入：哭声类别 + 置信度 + 宝宝月龄/喂养方式
- 输出格式：原因解释 + 解决方案（列表）+ 安抚技巧（列表）+ 注意事项

---

## 4. API 端点设计

### 哭声识别

```
POST /api/cry/recognize
  Request:  multipart/form-data { audio: file, baby_id?: int }
  Response: {
    "cry_type": "饥饿",
    "confidence": 0.87,
    "secondary_types": [
      {"type": "疲倦", "confidence": 0.23},
      {"type": "不适", "confidence": 0.12}
    ],
    "advice": {
      "cause": "宝宝可能因为饥饿而哭闹...",
      "solutions": ["立即喂奶", "观察吸吮是否有力"],
      "soothing_tips": ["轻轻摇晃", "播放白噪音"],
      "warnings": ["如持续哭闹超过30分钟建议就医"]
    }
  }
```

### 白噪音

```
GET  /api/noise/list              → 白噪音列表
GET  /api/noise/{id}/stream       → 音频流
```

### 成长记录

```
POST /api/records/feeding         → 添加喂养记录
GET  /api/records/feeding/list    → 喂养记录列表
POST /api/records/diaper          → 添加大小便记录
GET  /api/records/diaper/list     → 大小便记录列表
POST /api/records/sleep           → 添加睡眠记录
GET  /api/records/sleep/list      → 睡眠记录列表
```

### 疫苗提醒

```
GET  /api/vaccine/list            → 疫苗计划列表
PUT  /api/vaccine/{id}/status     → 更新疫苗状态
```

### 用户 & 宝宝

```
POST /api/user/login              → 微信登录
POST /api/baby                    → 创建/更新宝宝信息
GET  /api/baby                    → 获取宝宝信息
```

---

## 5. 数据模型

### user 用户
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| openid | varchar(64) unique | 微信 openid |
| nickname | varchar(64) | |
| avatar_url | varchar(512) | |
| created_at | datetime | |

### baby 宝宝信息
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| user_id | int FK | |
| nickname | varchar(32) | |
| birthday | date | |
| gender | varchar(4) | |
| feed_type | varchar(16) | 母乳/配方奶/混合 |
| avatar_url | varchar(512) | |

### feeding 喂养
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| baby_id | int FK | |
| start_time | datetime | |
| end_time | datetime | |
| amount | int | ml |
| side | varchar(8) | 左/右/瓶喂 |
| note | varchar(256) | |

### sleep 睡眠
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| baby_id | int FK | |
| start_time | datetime | |
| end_time | datetime | |
| quality | varchar(16) | |
| note | varchar(256) | |

### diaper 大小便
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| baby_id | int FK | |
| time | datetime | |
| type | varchar(16) | 小便/大便/都有 |
| color | varchar(16) | |
| note | varchar(256) | |

### vaccine 疫苗
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| baby_id | int FK | |
| name | varchar(64) | |
| scheduled_date | date | |
| status | varchar(16) | 未接种/已接种 |
| completed_at | datetime | |

### cry_record 哭声识别记录
| 字段 | 类型 | 说明 |
|------|------|------|
| id | int PK | |
| baby_id | int FK (nullable) | |
| cry_type | varchar(32) | 主要类别 |
| confidence | float | 置信度 |
| secondary_result | text (JSON) | 辅助类别列表 |
| audio_url | varchar(512) | 音频存储路径 |
| advice | text (JSON) | Claude 建议 |
| created_at | datetime | |

---

## 6. 技术选型

### 后端
| 组件 | 选型 |
|------|------|
| 框架 | FastAPI + uvicorn |
| ORM | SQLAlchemy (async) |
| 数据库 | PostgreSQL |
| 缓存 | Redis (会话/限流) |
| 音频处理 | librosa + pydub |
| CNN 推理 | PyTorch → ONNX 导出 |
| AI SDK | anthropic (Claude API) |
| 文件存储 | 本地 → 后续腾讯云 COS |
| 认证 | 微信 openid + JWT |

### 前端 (微信小程序)
| 组件 | 选型 |
|------|------|
| 框架 | 原生微信小程序 |
| 录音 | wx.getRecorderManager |
| 音频播放 | wx.createInnerAudioContext |
| 网络请求 | wx.request |
| 本地存储 | wx.setStorageSync |

### 项目结构
```
backend/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── config.py             # 配置
│   ├── api/                  # 路由模块
│   │   ├── cry.py            # 哭声识别
│   │   ├── records.py        # 喂养/睡眠/大小便
│   │   ├── vaccine.py        # 疫苗
│   │   ├── noise.py          # 白噪音
│   │   ├── baby.py           # 宝宝信息
│   │   └── user.py           # 登录/用户
│   ├── models/               # SQLAlchemy ORM
│   ├── services/
│   │   ├── cry_classifier.py # CNN 分类器
│   │   ├── audio_processor.py# 音频预处理
│   │   └── ai_client.py     # Claude API
│   ├── schemas/              # Pydantic 模型
│   └── utils/
├── models/                   # CNN 权重
├── data/                     # 白噪音音频
├── requirements.txt
└── alembic/
```

---

## 7. 前端页面流程

### 识别流程（三个核心页面）

1. **录音待机页** — 婴儿动画 + "请靠近婴儿头部，点击开始录音" + 录音按钮 + "最少录制 6 秒"
2. **录音中** — 波形动画 + 计时显示 + "点击停止录音" + 最长 30 秒自动停止
3. **结果展示页** — 主类别（大字）+ 置信度 + 辅助类别标签（置信度降序）+ 原因解释 + 分点建议 + 安抚技巧 + 注意事项 + "重新录音"按钮

### 其他页面

- **白噪音列表** — 分类 Tab + 列表（图标/名称/试听按钮/循环切换）+ 底部播放控制条
- **成长记录** — 喂养计时器、睡眠记录、大小便记录、记录列表（时间倒序）
- **疫苗提醒** — 疫苗计划列表 + 已接种/未接种状态 + 完成按钮

---

## 8. 错误处理

| 场景 | 处理策略 |
|------|---------|
| 录音不足 6 秒 | 前端阻止提交，提示最少录制 6 秒 |
| 录音超过 30 秒 | 前端自动截断/停止 |
| 音频质量差/无声音 | 后端检测后返回提示重新录音 |
| CNN 分类置信度过低 | Claude 提示用户结合实际情况判断 |
| Claude API 超时/失败 | 重试 2 次，失败后返回基础建议文本 |
| 网络中断 | 前端本地缓存录音，恢复后重新上传 |
| 未设置宝宝信息 | 跳过个性化参数，生成通用建议 |

---

## 9. 后续迭代

- 收集用户反馈数据，训练真实 CNN 模型替换占位
- 不同月龄婴儿哭声差异优化
- 育儿知识问答（Claude 对话机器人）
- 成长日志 AI 分析
- 微信服务通知推送
- 音频文件迁移至腾讯云 COS
