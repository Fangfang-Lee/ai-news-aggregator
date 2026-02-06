# Vercel 部署指南

## 前置准备

1. **Supabase 数据库**
   - 在 Supabase 创建项目
   - 获取数据库连接字符串（Settings -> Database -> Connection string）
   - 格式：`postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require`

2. **Redis（可选，用于缓存）**
   - 可以使用 Upstash Redis（免费）
   - 或使用其他 Redis 服务

## 部署步骤

### 1. 安装 Vercel CLI

```bash
npm i -g vercel
```

### 2. 登录 Vercel

```bash
vercel login
```

### 3. 配置环境变量

在 Vercel 项目设置中添加以下环境变量：

```bash
# 数据库（Supabase）
DATABASE_URL=postgresql://postgres:<PASSWORD>@db.<PROJECT_REF>.supabase.co:5432/postgres?sslmode=require
DATABASE_SSLMODE=require

# Redis（如果使用）
REDIS_URL=redis://<your-redis-url>
CELERY_BROKER_URL=redis://<your-redis-url>/1
CELERY_RESULT_BACKEND=redis://<your-redis-url>/2

# 安全密钥（用于 Cron 认证）
SECRET_KEY=your-random-secret-key-here

# DeepSeek API（可选，用于摘要生成）
DEEPSEEK_API_KEY=your-deepseek-api-key

# CORS
CORS_ORIGINS=["https://your-domain.vercel.app"]
```

### 4. 部署

```bash
vercel
```

首次部署会提示配置，选择：
- Set up and deploy? **Yes**
- Which scope? 选择你的账户
- Link to existing project? **No**
- Project name? 输入项目名称
- Directory? **./** (当前目录)

### 5. 生产环境部署

```bash
vercel --prod
```

## 重要说明

### Celery Worker 限制

Vercel 是无服务器环境，**不支持长期运行的 Celery Worker**。定时任务通过以下方式实现：

1. **Vercel Cron Jobs**：自动调用 `/api/cron/fetch-all` 和 `/api/cron/cleanup`
2. **手动触发**：通过 API 端点 `/api/content/fetch-all` 手动触发

### Cron 任务配置

Cron 任务在 `vercel.json` 中配置：
- `/api/cron/fetch-all`：每小时执行（抓取所有 RSS 源）
- `/api/cron/cleanup`：每天执行（清理旧内容）

Cron 任务需要认证，使用 `SECRET_KEY` 作为 Bearer token。

### 静态文件

静态文件位于 `frontend/static/`，通过 Vercel 自动处理。

### 数据库迁移

首次部署后，数据库表会自动创建（通过 `Base.metadata.create_all`）。

如果需要初始化默认数据，可以调用：
```bash
curl -X POST https://your-domain.vercel.app/api/content/fetch-all
```

## 故障排查

1. **数据库连接失败**
   - 检查 `DATABASE_URL` 是否正确
   - 确认 Supabase 允许外部连接
   - 检查 SSL 模式设置

2. **Cron 任务不执行**
   - 检查 Vercel Cron 配置
   - 确认 `SECRET_KEY` 已设置
   - 查看 Vercel 日志

3. **静态文件 404**
   - 确认 `frontend/static/` 目录存在
   - 检查路由配置

## 更新部署

```bash
vercel --prod
```

每次推送代码到 Git 后，Vercel 会自动部署（如果已连接 Git 仓库）。
