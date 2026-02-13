# AI News Aggregator

一个自动聚合 AI 与科技领域新闻的 Web 应用。通过 RSS 源自动抓取内容，利用 DeepSeek API 生成中文摘要，并提供分类、筛选、收藏等阅读管理功能。

## Features

- **RSS 源管理** — 添加、编辑、删除 RSS 订阅源
- **定时自动抓取** — Celery Beat 每 5 分钟自动拉取新内容，每 24 小时清理过期内容
- **AI 中文摘要** — 基于 DeepSeek API（`deepseek-chat` 模型）自动生成中文新闻摘要
- **三层内容过滤** — 财经黑名单 → 关键词相关性匹配 → 宽泛源/专业源分级信任
- **自动分类** — 根据标题和正文关键词自动匹配 7 大技术分类
- **网页正文回退** — 当 RSS 源不提供正文时，自动抓取原始网页提取全文（html2text）
- **智能去重** — 基于 GUID 和标题相似度去重
- **搜索与筛选** — 全文搜索 + 分类/来源/已读/未读/收藏状态多维筛选
- **阅读管理** — 已读标记、收藏夹、阅读历史
- **暗色模式** — 跟随系统偏好自动切换
- **响应式设计** — 桌面端与移动端适配

## Tech Stack

| 层 | 技术 |
|----|------|
| **后端框架** | FastAPI (Python 3.11) |
| **数据库** | PostgreSQL 15 + SQLAlchemy 2.0 ORM |
| **缓存/队列** | Redis 7 + Celery 5.3 |
| **AI 摘要** | DeepSeek API (httpx) |
| **RSS 解析** | feedparser + requests + html2text |
| **数据验证** | Pydantic 2.5 + pydantic-settings |
| **前端** | Vanilla JavaScript + CSS (Jinja2 模板) |
| **部署** | Docker Compose (5 services) |

## Project Structure

```
ai-news-aggregator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/            # API 路由 (categories, sources, content)
│   │   │   ├── schemas.py         # Pydantic 请求/响应 Schema
│   │   │   └── deps.py            # FastAPI 依赖注入 (get_db, get_redis)
│   │   ├── core/
│   │   │   ├── config.py          # 全局配置 (pydantic-settings)
│   │   │   ├── database.py        # SQLAlchemy engine & SessionLocal
│   │   │   └── redis_client.py    # Redis 客户端
│   │   ├── models/
│   │   │   └── rss_models.py      # ORM 模型 (RSSSource, Content, Category...)
│   │   ├── services/
│   │   │   ├── rss_service.py     # RSS 源管理 + 全量抓取
│   │   │   ├── content_service.py # 内容管理 + 三层过滤
│   │   │   ├── category_service.py# 分类管理
│   │   │   └── summary_service.py # DeepSeek AI 摘要生成
│   │   ├── crawlers/
│   │   │   ├── rss_crawler.py     # RSS 抓取 + 网页正文回退
│   │   │   └── content_parser.py  # 内容清洗、分类、去重、黑名单
│   │   ├── main.py                # FastAPI 入口 (lifespan 启动)
│   │   ├── celery_app.py          # Celery 配置 + Beat 调度
│   │   └── tasks.py               # 异步任务 (抓取/清理/摘要生成)
│   ├── tests/                     # 单元测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── static/
│   │   ├── css/style.css          # 样式 (含暗色模式)
│   │   └── js/app.js              # 前端交互逻辑
│   └── templates/
│       └── index.html             # 主页模板
├── docs/
│   └── agent.md                   # 技术架构与业务设计文档
├── docker-compose.yml             # Docker Compose (开发环境)
├── docker-compose.prod.yml        # Docker Compose (生产环境)
├── render.yaml                    # Render Blueprint 部署配置
├── build.sh                       # Render 构建脚本
├── .env.example                   # 环境变量模板
└── README.md
```

## Architecture

### 内容处理流程

```
RSS Feed → fetch_feed() → parse_entry()
                              │
                              ├─ 正文不足 100 字? → fetch_article_content(url) 网页回退
                              │
                              └─ entry_data → create_or_update_content()
                                                │
                                                ├─ 1) 财经黑名单过滤 (is_financial_noise)
                                                ├─ 2) 关键词相关性匹配 (categorize_article)
                                                ├─ 3) 宽泛源额外检查 / 专业源信任放行
                                                │
                                                └─ DeepSeek API → 中文摘要 → 存入 PostgreSQL
```

### Docker Services

| Service | Container | Port Mapping |
|---------|-----------|-------------|
| PostgreSQL 15 | `ai_news_postgres` | `5433:5432` |
| Redis 7 | `ai_news_redis` | `6380:6379` |
| FastAPI Backend | `ai_news_backend` | `8001:8000` |
| Celery Worker | `ai_news_celery_worker` | — |
| Celery Beat | `ai_news_celery_beat` | — |

### 定时任务 (Celery Beat)

| 任务 | 周期 | 说明 |
|------|------|------|
| `fetch_all_sources` | 每 5 分钟 | 抓取所有活跃 RSS 源的新内容 |
| `cleanup_old_content` | 每 24 小时 | 清理过期内容（已收藏的保留） |

## Quick Start

### Docker 部署（推荐）

```bash
# 1. 克隆仓库
git clone git@github.com:Fangfang-Lee/ai-news-aggregator.git
cd ai-news-aggregator

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 DEEPSEEK_API_KEY

# 3. 启动所有服务
docker-compose up -d

# 4. 访问应用
# Web 界面: http://localhost:8001
# API 文档: http://localhost:8001/docs
```

### 手动安装

```bash
# 前提：已安装 PostgreSQL 和 Redis

# 1. 创建虚拟环境并安装依赖
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env

# 3. 启动 FastAPI
uvicorn app.main:app --reload --port 8001

# 4. 启动 Celery（新终端）
celery -A app.celery_app worker --loglevel=info
celery -A app.celery_app beat --loglevel=info
```

## Environment Variables

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql://postgres:password@localhost:5432/ai_news_db` |
| `REDIS_URL` | Redis 连接字符串 | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery Broker URL | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery Result Backend URL | `redis://localhost:6379/2` |
| `DEEPSEEK_API_KEY` | DeepSeek API Key（AI 摘要必需） | `""` |
| `CORS_ORIGINS` | 允许的 CORS 来源（JSON 列表） | `["http://localhost:8001", "http://127.0.0.1:8001"]` |
| `RSS_FETCH_INTERVAL` | RSS 抓取间隔（秒） | `300` |
| `CONTENT_MIN_DATE` | 文章最早日期（早于此日期的文章将被跳过） | `2026-02-10` |

## API Endpoints

### Categories — 分类管理

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/categories/` | 获取所有分类 |
| POST | `/api/categories/` | 创建分类 |
| GET | `/api/categories/{id}` | 获取分类详情 |
| PUT | `/api/categories/{id}` | 更新分类 |
| DELETE | `/api/categories/{id}` | 删除分类 |

### Sources — RSS 源管理

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/sources/` | 获取所有源（支持分类筛选、分页） |
| POST | `/api/sources/` | 创建新源 |
| GET | `/api/sources/{id}` | 获取源详情 |
| PUT | `/api/sources/{id}` | 更新源 |
| DELETE | `/api/sources/{id}` | 删除源 |
| POST | `/api/sources/{id}/fetch` | 手动触发抓取 |
| GET | `/api/sources/{id}/stats` | 获取源统计信息 |

### Content — 内容管理

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/content/` | 获取文章列表（分页 + 分类/来源/已读/收藏/搜索筛选） |
| GET | `/api/content/{id}` | 获取文章详情 |
| POST | `/api/content/{id}/mark-read` | 标记已读 |
| POST | `/api/content/{id}/mark-unread` | 标记未读 |
| POST | `/api/content/{id}/bookmark` | 切换收藏状态 |
| POST | `/api/content/fetch-all` | 全量抓取所有活跃源 |
| POST | `/api/content/generate-summaries` | 触发 AI 摘要批量生成 |
| GET | `/api/content/categories/{id}` | 按分类获取文章 |

## Default Categories

| 分类 | 说明 | 色标 |
|------|------|------|
| AI | AI 产品发布、API 更新、AI 应用案例 | `#6366f1` Indigo |
| Technology | 科技行业综合资讯、硬件与平台动态 | `#3b82f6` Blue |
| Internet | 互联网行业新闻、大厂动态、行业趋势 | `#f97316` Orange |
| Developer | 编程语言、框架更新、开发工具、开源项目 | `#14b8a6` Teal |
| Cloud & DevOps | 云服务、容器化、CI/CD、基础设施 | `#06b6d4` Cyan |
| Cybersecurity | 安全漏洞通告、安全实践、数据隐私 | `#ef4444` Red |
| Startup & Product | 创业融资、新产品发布、产品设计 | `#eab308` Amber |

## Default RSS Sources

初始安装时自动配置以下 15 个 RSS 源：

### AI — 人工智能（10 源）

| 源 | URL | 说明 |
|----|-----|------|
| 机器之心 | `plink.anyfeeder.com/weixin/almosthuman2014` | AI 领域专业媒体 |
| 新智元 | `plink.anyfeeder.com/weixin/AI_era` | AI 产业资讯与技术动态 |
| AI 科技评论 | `rsshub.rssforever.com/leiphone/category/ai` | 雷锋网 AI 频道，学术+产业 |
| OpenAI Blog | `openai.com/blog/rss.xml` | OpenAI 官方博客 |
| Hugging Face Blog | `huggingface.co/blog/feed.xml` | 开源 AI 生态系统 |
| Google AI Blog | `blog.google/technology/ai/rss/` | Google AI 研究动态 |
| Sebastian Raschka | `magazine.sebastianraschka.com/feed` | LLM 深度研究分析 |
| MIT Tech Review AI | `technologyreview.com/.../feed` | MIT 科技评论 AI 视角 |
| TechCrunch AI | `techcrunch.com/.../feed` | 硅谷 AI 新闻 |
| Towards Data Science | `towardsdatascience.com/feed` | AI/ML 实战技术文章 |

### Technology — 科技综合（2 源）

| 源 | URL | 说明 |
|----|-----|------|
| 虎嗅 | `huxiu.com/rss/0.xml` | 科技商业深度报道 |
| 腾讯科技 | `plink.anyfeeder.com/weixin/qqtech` | 科技产业资讯 |

### Developer — 开发者（2 源）

| 源 | URL | 说明 |
|----|-----|------|
| 阮一峰的网络日志 | `ruanyifeng.com/blog/atom.xml` | 技术博客，每周科技周刊 |
| InfoQ 推荐 | `plink.anyfeeder.com/infoq/recommend` | 软件开发技术前沿资讯 |

### Cloud & DevOps — 云计算（1 源）

| 源 | URL | 说明 |
|----|-----|------|
| 美团技术团队 | `tech.meituan.com/feed/` | 美团技术实践与架构分享 |

## Production Deployment (Render + Supabase)

### 架构概览

```
┌─────────────────┐       ┌──────────────────┐
│  Render          │       │   Supabase       │
│                  │       │                  │
│  ┌────────────┐  │       │  PostgreSQL 15   │
│  │ Web Service │──┼───────┤  (免费 500 MB)   │
│  │ (FastAPI)   │  │       │                  │
│  └────────────┘  │       └──────────────────┘
│        │         │
│  ┌────────────┐  │
│  │ Worker      │  │
│  │ (Celery +   │  │
│  │  Beat)      │  │
│  └─────┬──────┘  │
│        │         │
│  ┌────────────┐  │
│  │ Redis KVS  │  │
│  │ (25 MB)    │  │
│  └────────────┘  │
└─────────────────┘
```

### 费用

| 服务 | 方案 | 月费 |
|------|------|------|
| Render Web Service | Starter | $7 |
| Render Worker | Starter | $7 |
| Render Redis KVS | Free | $0 |
| Supabase PostgreSQL | Free (500 MB) | $0 |
| **合计** | | **~$14/月** |

### 部署步骤

#### 1. Supabase — 创建数据库

1. 登录 [Supabase Dashboard](https://supabase.com/dashboard)
2. 新建 Project → 选择 **Singapore** Region → 设置 DB 密码
3. 进入 **Settings → Database → Connection string → URI**
4. 复制连接字符串（格式：`postgresql://postgres.[ref]:[password]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres`）

#### 2. Render — Blueprint 部署

1. 将代码推送到 GitHub 仓库
2. 登录 [Render Dashboard](https://dashboard.render.com)
3. **New → Blueprint** → 连接 GitHub 仓库
4. Render 会自动读取 `render.yaml`，创建 3 个服务
5. 在 Dashboard 中手动填入环境变量：
   - `DATABASE_URL` → Supabase 连接字符串
   - `DEEPSEEK_API_KEY` → 你的 DeepSeek API Key
   - `CORS_ORIGINS` → `["https://你的域名.onrender.com"]`

#### 3. 验证部署

```bash
# 健康检查
curl https://ai-news-backend.onrender.com/health

# 手动触发抓取
curl -X POST https://ai-news-backend.onrender.com/api/content/fetch-all
```

### 免费部署方案 (仅 Web Service)

如果只想使用免费层，可以跳过 Worker 服务，改用外部 Cron 触发：

1. `render.yaml` 中将 Web Service 的 `plan` 改为 `free`，删除 Worker 服务
2. 注册 [cron-job.org](https://cron-job.org)（免费），添加定时任务：
   - **每 5 分钟**: `POST https://你的域名.onrender.com/api/content/fetch-all`
   - **每 24 小时**: 无需额外操作（旧内容会在数据库层面自然淘汰）
3. 限制：免费 Web Service 15 分钟无访问后休眠，首次访问冷启动约 30-60 秒

## Running Tests

```bash
cd backend
pytest tests/ -v
```

测试使用 SQLite 内存数据库，无需启动 PostgreSQL/Redis。

## Documentation

详细的技术架构、业务设计和 AI Agent 上下文请参考 [docs/agent.md](docs/agent.md)。

## License

MIT License
