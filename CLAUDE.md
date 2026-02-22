# AI News Aggregator 项目指南

## 项目概述

**项目目标**：一个自动聚合 AI 与科技领域新闻的 Web 应用，通过 RSS 源自动抓取内容，利用 MiniMax API 生成中文摘要，并提供分类、筛选、收藏等阅读管理功能。

**目标用户**：AI 和科技从业者、爱好者，需要跟踪 AI/科技动态的开发者。

## 技术架构

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.11) |
| 数据库 | PostgreSQL (Supabase) + SQLAlchemy 2.0 ORM |
| 缓存/队列 | Redis 7 (Render) + Celery 5.3 |
| AI 摘要 | MiniMax API (MiniMax-M2.5 模型) |
| RSS 解析 | feedparser + requests + html2text |
| 前端 | Vanilla JavaScript + CSS + Jinja2 模板 |
| 部署 | Docker Compose (本地), Render (生产) |
| 定时任务 | GitHub Actions |

## 服务架构

```
┌─────────────────────────────────────────────────────────────┐
│                        GitHub Actions                        │
│  (每 10 分钟触发: fetch-all + generate-summaries)         │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     Render (Web Service)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  FastAPI    │  │   Celery    │  │    Redis (Cache)   │ │
│  │  Backend    │  │   Worker    │  │    (Key-Value)     │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘ │
│         │                 │                                   │
│         └────────┬────────┘                                   │
│                  ▼                                            │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Supabase (PostgreSQL)                      ││
│  │   - content (文章)                                      ││
│  │   - rss_sources (RSS 源)                                ││
│  │   - categories (分类)                                   ││
│  │   - reading_history (阅读历史)                          ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## 核心业务逻辑

### 内容处理流程
```
RSS Feed → fetch_feed() → parse_entry()
                      │
                      ├─ 正文不足 500 字? → fetch_article_content(url) 网页回退
                      │
                      └─ entry_data → create_or_update_content()
                                        │
                                        ├─ 1) 关键词相关性匹配 (categorize_article)
                                        │
                                        └─ MiniMax API → 中文摘要 → 存入 PostgreSQL
```

### 内容过滤
1. **关键词相关性匹配** - 根据标题和正文关键词自动匹配分类
2. **分类过滤** - 只保留 AI、科技相关分类

### 自动分类 (9 大分类)
- 人工智能 - AI 产品发布、API 更新、AI 应用案例
- 科技前沿 - 科技行业综合资讯、硬件与平台动态
- 科学探索 - 科学研究、学术进展
- AI - AI 专题
- Technology - 技术综合
- Developer - 编程语言、框架更新、开发工具、开源项目
- Cloud & DevOps - 云服务、容器化、CI/CD、基础设施
- Cybersecurity - 安全漏洞通告、安全实践、数据隐私
- Startup & Product - 创业融资、新产品发布、产品设计

## 定时任务

### GitHub Actions (免费方案)
- **频率**: 每 10 分钟执行一次
- **触发内容**:
  1. `POST /api/content/fetch-all` - 抓取所有 RSS 源新文章
  2. `POST /api/content/generate-summaries` - 生成 AI 摘要
- **配置**: GitHub Secrets 中需设置 `API_BASE_URL`

### 内容清理
- **频率**: 每天一次 (Celery Beat)
- **策略**: 删除超过 7 天的非书签文章

## 项目结构

```
ai-news-aggregator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── categories.py  # 分类管理 API
│   │   │   │   ├── content.py     # 内容管理 API
│   │   │   │   ├── sources.py     # RSS 源管理 API
│   │   │   │   └── cron.py        # 定时任务 API
│   │   │   ├── schemas.py         # Pydantic Schema
│   │   │   └── deps.py            # FastAPI 依赖注入
│   │   ├── core/
│   │   │   ├── config.py          # 全局配置 (pydantic-settings)
│   │   │   ├── database.py        # SQLAlchemy SessionLocal
│   │   │   └── redis_client.py    # Redis 客户端
│   │   ├── models/
│   │   │   └── rss_models.py      # ORM 模型
│   │   ├── services/
│   │   │   ├── rss_service.py     # RSS 源管理 + 抓取
│   │   │   ├── content_service.py # 内容管理 + 过滤
│   │   │   ├── category_service.py# 分类管理
│   │   │   └── summary_service.py # MiniMax AI 摘要
│   │   ├── crawlers/
│   │   │   ├── rss_crawler.py    # RSS 抓取 + 网页回退
│   │   │   └── content_parser.py  # 内容清洗/分类/去重
│   │   ├── main.py                # FastAPI 入口
│   │   ├── celery_app.py          # Celery 配置
│   │   └── tasks.py               # Celery 任务
│   ├── tests/                     # 单元测试
│   └── requirements.txt
├── frontend/
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/
│       └── index.html
├── .github/
│   └── workflows/
│       └── scheduled-fetch.yml    # GitHub Actions 定时任务
├── docker-compose.yml             # 本地开发配置
├── render.yaml                   # Render 部署配置
└── CLAUDE.md                     # 本文件
```

## 常用命令

```bash
# 启动服务 (端口 8001)
docker-compose up -d

# 重新构建
docker-compose up -d --build

# 查看日志
docker-compose logs -f backend
docker-compose logs -f celery_worker

# 运行测试
docker-compose exec backend pytest tests/

# 数据库操作
docker-compose exec postgres psql -U postgres -d ai_news_db

# 手动触发 RSS 抓取
curl -X POST "http://localhost:8001/api/content/fetch-all"

# 手动触发摘要生成
curl -X POST "http://localhost:8001/api/content/generate-summaries"
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 (Supabase) | - |
| `REDIS_URL` | Redis 连接字符串 | redis://redis:6379/0 |
| `CELERY_BROKER_URL` | Celery 消息队列 | redis://redis:6379/1 |
| `CELERY_RESULT_BACKEND` | Celery 结果存储 | redis://redis:6379/2 |
| `MINIMAX_API_KEY` | MiniMax API Key (AI 摘要必需) | "" |
| `MINIMAX_MODEL` | MiniMax 模型 | MiniMax-M2.5 |
| `CONTENT_MIN_DATE` | 文章最早日期 | 2026-02-10 |

## RSS 订阅源 (12 个)

| 源 | 分类 |
|----|------|
| 机器之心 | AI/科技 |
| 新智元 | AI/科技 |
| AI 科技评论 | AI/科技 |
| OpenAI Blog | AI |
| Hugging Face Blog | AI/开源 |
| Google AI Blog | AI |
| Sebastian Raschka AI | AI/研究 |
| MIT Tech Review AI | AI |
| TechCrunch AI | AI/科技 |
| InfoQ 推荐 | 技术 |
| 美团技术团队 | 技术 |

## 部署说明

### 本地开发
```bash
docker-compose up -d
# 访问 http://localhost:8001
```

### 生产部署 (Render)
1. 创建 Supabase PostgreSQL 数据库
2. 在 Render Dashboard 创建 Blueprint，选择 `render.yaml`
3. 配置环境变量：
   - `DATABASE_URL`: Supabase 连接字符串
   - `MINIMAX_API_KEY`: MiniMax API Key
4. 配置 GitHub Actions Secrets：
   - `API_BASE_URL`: Render 部署 URL
5. 定时任务自动通过 GitHub Actions 每 10 分钟执行

## 代码规范

- **Python**: 遵循 PEP 8，使用类型提示
- **Imports**: 分组排序 (标准库 > 第三方 > 本地模块)
- **语言**: 代码注释英文，内容数据中文
- **错误处理**: 使用 logging 记录，返回适当的 HTTP 状态码
