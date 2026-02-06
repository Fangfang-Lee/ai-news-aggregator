# 手动启动项目指南

## 方式一：使用 Docker（推荐）

### 前提条件
1. 确保 Docker Desktop 已安装并正在运行
2. 在 macOS 上，打开"应用程序"文件夹，启动 Docker Desktop
3. 等待 Docker Desktop 完全启动（菜单栏图标显示为运行状态）

### 启动步骤
```bash
cd /Users/jason/cursor/ai-news-aggregator
docker-compose up -d
```

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
docker-compose logs -f
```

### 停止服务
```bash
docker-compose down
```

---

## 方式二：手动启动（不使用 Docker）

### 前提条件
1. Python 3.7+
2. PostgreSQL 已安装并运行
3. Redis 已安装并运行

### 启动步骤

1. **安装 PostgreSQL 和 Redis**（如果未安装）：
   ```bash
   # macOS 使用 Homebrew
   brew install postgresql redis
   
   # 启动 PostgreSQL
   brew services start postgresql
   
   # 启动 Redis
   brew services start redis
   ```

2. **创建数据库**：
   ```bash
   createdb ai_news_db
   ```

3. **设置 Python 虚拟环境**：
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **创建 .env 文件**（如果不存在）：
   ```bash
   cp .env.example .env
   ```

5. **启动 FastAPI 应用**：
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **在另一个终端启动 Celery Worker**：
   ```bash
   cd backend
   source venv/bin/activate
   celery -A app.celery_app worker --loglevel=info
   ```

7. **在第三个终端启动 Celery Beat**（定时任务）：
   ```bash
   cd backend
   source venv/bin/activate
   celery -A app.celery_app beat --loglevel=info
   ```

### 访问应用
- Web 界面: http://localhost:8000
- API 文档: http://localhost:8000/api/docs
