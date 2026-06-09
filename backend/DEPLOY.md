# 腾讯云部署指南

## 1. 服务器准备

购买腾讯云轻量应用服务器（2核4G，60GB SSD，Ubuntu 22.04）。

```bash
ssh root@<your-server-ip>

# 安装 Docker
curl -fsSL https://get.docker.com | sh

# 安装 Docker Compose
apt install docker-compose -y

# 验证
docker --version && docker-compose --version
```

## 2. 上传代码

```bash
# 本地打包
cd backend
tar czf deploy.tar.gz \
  app/ models/ data/noise/ scripts/ \
  Dockerfile docker-compose.yml nginx.conf requirements.txt \
  .env.example

# 上传
scp deploy.tar.gz root@<ip>:/root/

# 服务器解压
ssh root@<ip>
mkdir -p /opt/babycry
cd /opt/babycry
tar xzf /root/deploy.tar.gz
```

## 3. 配置环境变量

```bash
cd /opt/babycry
cp .env.example .env
nano .env
```

必填项：
- `DB_PASSWORD`: 数据库密码
- `JWT_SECRET`: 随机字符串（`openssl rand -hex 32`）
- `ANTHROPIC_API_KEY`: Claude API 密钥

## 4. 启动服务

```bash
docker-compose up -d
docker-compose ps  # 确认所有容器运行中
docker-compose logs backend  # 查看后端日志
```

## 5. 微信小程序配置

登录微信公众平台 → 开发 → 开发管理 → 服务器域名：
- request合法域名: `https://<your-domain>`

## 6. SSL 证书

腾讯云控制台 → SSL 证书 → 申请免费证书 → 下载 Nginx 格式：
```bash
mkdir -p ssl
# 上传证书文件到 ssl/ 目录
# 修改 nginx.conf 添加 443 端口和 SSL 配置
```

## 7. 常见问题

| 问题 | 解决 |
|------|------|
| backend 连不上 postgres | `docker-compose logs postgres` 检查是否就绪 |
| 录音上传失败 | 检查 `uploads/audio` 目录权限 |
| 模型未加载 | 确认 `models/cry_classifier.onnx` 存在 |
| 白噪音列表空 | 确认 `data/noise/` 下有 mp3 文件 |
