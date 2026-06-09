# 微信云托管部署指南

## 优势

- 免域名、免备案、免 SSL 配置
- 自动 HTTPS，直接绑定小程序
- 按量计费，测试阶段几乎免费
- 自动弹性伸缩

## 1. 开通云托管

打开 https://cloud.weixin.qq.com → 云托管 → 新建环境

- 环境名称：`babycry`
- 付费模式：按量计费
- 建议开启「数据库」→ MySQL（可选，月费约 ¥20）

## 2. 部署方式（二选一）

### 方式 A：从 GitHub 自动部署

1. 云托管 → 服务 → 新建服务
2. 选择「从 GitHub 导入」
3. 连接到你的仓库 `LiYouL/wxbabycry`
4. 构建目录：`backend/`
5. Dockerfile 路径：`backend/Dockerfile.wechat`
6. 服务端口：`8000`
7. 环境变量里填好 `ANTHROPIC_API_KEY`

### 方式 B：容器镜像手动部署

1. 云托管 → 服务 → 新建服务
2. 选择「从容器镜像」
3. Dockerfile 用 `backend/Dockerfile.wechat`
4. 服务端口：`8000`
5. 环境变量填：
   - `ANTHROPIC_API_KEY` = 你的 Claude API Key
   - `JWT_SECRET` = 随机字符串

## 3. 绑定小程序

1. 云托管 → 服务 → 你的服务 → 「绑定小程序」
2. 选择你的小程序 AppID
3. 系统自动生成 HTTPS 域名

## 4. 小程序配置

微信公众平台 → 开发 → 服务器域名：
- request合法域名：填入云托管自动生成的域名（如 `https://xxx.sh.run.tcloudbase.com`）

## 5. 成本预估

| 项目 | 费用 |
|------|------|
| 容器运行 | ~¥0.1/天（低频） |
| 外网流量 | 1GB 内免费 |
| 数据库（可选） | MySQL ¥20/月 |

测试阶段：每月不超过 ¥5

## 6. 环境变量说明

在云托管控制台「版本管理」→「环境变量」中设置：

```
ANTHROPIC_API_KEY=sk-ant-xxx
JWT_SECRET=your-random-string
DATABASE_URL=sqlite+aiosqlite:///./babycry.db
```

> SQLite 适合测试（数据存在容器内，重新部署会丢失）。生产环境建议开启云托管 MySQL 并改用对应 DATABASE_URL。
