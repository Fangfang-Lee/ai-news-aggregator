# AI News Aggregator - Agent Context

> 本文档为 AI 编码助手提供项目全貌，同时也作为开发者的技术与业务参考。

---

## 1. 项目概述与约束

### 项目定位

面向**应用层开发工程师**的中文科技早报聚合器。用户每天早上打开，快速浏览 AI、科技、互联网、开发者工具等领域的核心资讯。

### 核心约束

- **中文优先**：RSS 源以中文信息源为主，AI 摘要使用中文生成
- **应用层视角**：关注技术如何用，而非底层原理和学术论文
- **单用户模式**：当前无用户认证系统，所有数据面向单一用户
- **轻量部署**：支持 Docker 一键启动，也支持 Render.com 云部署

### 编码规范

- **后端**：Python 3.10+，FastAPI 异步风格，类型注解完整
- **命名**：Python 使用 snake_case，API 路径使用 kebab-case（如 `/mark-read`）
- **分层架构**：Route → Service → Model，路由层不写业务逻辑
- **错误处理**：Service 层抛异常，Route 层捕获并返回 HTTP 错误
- **前端**：Vanilla JS（无框架），单页应用，中文界面
- **日志**：使用 Python logging 模块，按模块命名 logger

---

## 2. 技术架构

### 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| Web 框架 | FastAPI | 异步 API + 静态文件服务 + Jinja2 模板 |
| ORM | SQLAlchemy 2.0 | 声明式模型，`from_attributes` 模式 |
| 数据库 | PostgreSQL 15 | 主数据存储 |
| 缓存/消息 | Redis 7 | Celery Broker (db1) + Result Backend (db2) |
| 任务队列 | Celery | Worker + Beat 定时调度 |
| RSS 解析 | feedparser + requests | 抓取并解析 RSS 订阅源 |
| 内容处理 | html2text + NLTK | HTML 转文本、去重、关键词提取 |
| AI 摘要 | DeepSeek API (httpx) | 中文文章摘要生成 |
| 前端 | Vanilla JS + CSS | 无框架，单页应用 |

### 系统架构

```
用户浏览器
    │
    ▼
FastAPI (端口 8000)
    ├── GET /              → Jinja2 渲染 index.html
    ├── GET /static/*      → 静态文件（CSS/JS）
    ├── GET /api/*         → REST API
    └── GET /docs          → Swagger 文档
    │
    ▼
Service 层（业务逻辑）
    │
    ├── SQLAlchemy ──→ PostgreSQL (端口 5432)
    └── Redis Client ──→ Redis (端口 6379)

Celery Worker（后台任务）
    ├── 每 5 分钟：抓取所有活跃 RSS 源
    └── 每 24 小时：清理过期内容（保留书签）

Celery Beat（定时调度器）
    └── 触发 Worker 任务
```

### 数据流

```
RSS 源 URL
    │
    ▼
RSSCrawler.fetch_feed()       ← feedparser 解析 XML
    │
    ▼
RSSCrawler.parse_entry()      ← 提取标题/摘要/链接/图片/日期
    │
    ▼
ContentParser                  ← 去重（GUID + 标题归一化）
    │                           ← 关键词分类
    │                           ← 文本清洗
    ▼
ContentService.create_or_update_content()  ← 存入 PostgreSQL
    │
    ▼
SummaryService.generate_summary()  ← DeepSeek API 生成中文摘要（可选）
    │
    ▼
前端展示 ← API 分页查询 + 筛选
```

### 数据模型

```
RSSSource (rss_sources)
  ├── id, name, url, description
  ├── category_id → FK(categories)
  ├── is_active, last_fetched
  └── has_many: Content

Category (categories)
  ├── id, name, description, color
  ├── has_many: RSSSource
  └── many_to_many: Content (via content_category)

Content (content)
  ├── id, title, summary, content_html, content_text
  ├── link, image_url, author, published_date
  ├── guid (unique), source_url
  ├── rss_source_id → FK(rss_sources)
  ├── is_read, is_bookmarked
  └── many_to_many: Category (via content_category)

ReadingHistory (reading_history)
  ├── id, content_id → FK(content)
  └── read_at, read_duration

UserSettings (user_settings)
  ├── id, theme, articles_per_page
  └── auto_refresh, refresh_interval
```

**关键关系**：
- RSSSource → Category：多对一（每个源属于一个分类）
- Content ↔ Category：多对多（通过 `content_category` 关联表）
- Content → RSSSource：多对一（每篇文章来自一个源）

### 目录结构

```
ai-news-aggregator/
├── backend/
│   └── app/
│       ├── api/
│       │   ├── routes/            # API 路由（sources/categories/content）
│       │   ├── schemas.py         # Pydantic 请求/响应模型
│       │   └── deps.py            # 依赖注入（数据库会话）
│       ├── core/
│       │   ├── config.py          # Settings（pydantic-settings，读 .env）
│       │   ├── database.py        # SQLAlchemy engine + SessionLocal
│       │   └── redis_client.py    # Redis 连接
│       ├── models/
│       │   └── rss_models.py      # 全部 SQLAlchemy 模型
│       ├── services/
│       │   ├── rss_service.py     # RSS 源增删改查 + 抓取
│       │   ├── content_service.py # 内容查询/标记已读/书签
│       │   ├── category_service.py# 分类管理 + 初始化默认分类
│       │   └── summary_service.py # DeepSeek API 摘要生成
│       ├── crawlers/
│       │   ├── rss_crawler.py     # RSS 抓取与解析（feedparser）
│       │   ├── content_parser.py  # 去重/分类/文本清洗（NLTK）
│       │   └── scheduler.py       # 任务调度器
│       ├── main.py                # FastAPI 应用入口
│       ├── celery_app.py          # Celery 配置 + Beat 调度
│       └── tasks.py               # Celery 任务定义
│   ├── tests/                     # pytest 测试（SQLite 内存数据库）
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── static/css/style.css       # 样式（支持深色模式）
│   ├── static/js/app.js           # NewsAggregator 类（单页应用）
│   └── templates/index.html       # Jinja2 主模板（中文界面）
├── docker-compose.yml             # 本地开发（Postgres + Redis + Backend + Celery）
├── docker-compose.supabase.yml    # Supabase 部署配置
├── render.yaml                    # Render.com 部署配置
├── .env.example                   # 环境变量模板
└── docs/
    └── agent.md                   # 本文档
```

### 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接 | `postgresql://postgres:password@localhost:5432/ai_news_db` |
| `REDIS_URL` | Redis 连接 | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery Broker | `redis://localhost:6379/1` |
| `CELERY_RESULT_BACKEND` | Celery 结果存储 | `redis://localhost:6379/2` |
| `SECRET_KEY` | 应用密钥 | （需修改） |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | （可选，空则跳过摘要） |
| `CORS_ORIGINS` | 允许的跨域来源 | `["http://localhost:8000"]` |
| `RSS_FETCH_INTERVAL` | 抓取间隔（秒） | `300` |
| `MAX_WORKERS` | 最大并发抓取数 | `5` |

---

## 3. 业务设计

### 分类体系（7 类）

| 分类 | 定位 | 颜色 |
|------|------|------|
| AI | AI 产品发布、API/SDK 更新、应用案例 | #6366f1 (Indigo) |
| Technology | 科技行业综合资讯、硬件与平台动态 | #3b82f6 (Blue) |
| Internet | 互联网行业新闻、大厂动态、行业趋势 | #f97316 (Orange) |
| Developer | 编程语言、框架、开发工具、开源项目 | #14b8a6 (Teal) |
| Cloud & DevOps | 云服务、容器化、CI/CD、基础设施 | #06b6d4 (Cyan) |
| Cybersecurity | 安全漏洞通告、安全实践、数据隐私 | #ef4444 (Red) |
| Startup & Product | 创业融资、新产品发布、产品设计 | #eab308 (Amber) |

### 内置 RSS 源（23 个中文源）

**AI**：机器之心、新智元、量子位
**Technology**：36氪、虎嗅、IT之家、爱范儿
**Internet**：极客公园、品玩、钛媒体、cnBeta
**Developer**：阮一峰、V2EX、InfoQ、HelloGitHub、少数派、开源中国
**Cloud & DevOps**：Readhub 开发者资讯、美团技术团队
**Cybersecurity**：FreeBuf、360 安全博客
**Startup & Product**：人人都是产品经理、猎云网、36氪快讯

### 核心业务流程

#### 内容抓取

1. Celery Beat 每 5 分钟触发 `fetch_all_sources` 任务
2. 遍历所有 `is_active=True` 的 RSS 源
3. `RSSCrawler` 请求 RSS XML 并用 feedparser 解析
4. `ContentParser` 按 GUID + 标题归一化去重
5. 新文章写入 `content` 表，关联 `rss_source_id` 和分类

#### 内容消费

1. 用户打开首页，前端调用 `GET /api/content/` 加载文章列表
2. 支持按分类、来源、已读/未读、书签状态筛选
3. 支持关键词搜索（标题和内容全文匹配）
4. 分页加载（默认每页 20 条）
5. 点击文章弹出详情弹窗，自动标记已读并记录阅读历史

#### 内容管理

- 手动添加/编辑/删除 RSS 源
- 手动触发单个源或全部源的抓取
- 书签收藏（受清理任务保护，不会被自动删除）
- 过期内容每 24 小时自动清理（默认 30 天，书签除外）

### AI 摘要策略

- 通过 DeepSeek API (`deepseek-chat` 模型) 生成中文摘要
- 输入截断：最多 4000 字符以节省 token
- 摘要长度动态调整：短文 100 字 → 长文 300 字
- API Key 未配置时自动跳过，不影响核心功能
- 摘要 prompt 要求：突出核心信息、简洁清晰、不编造内容

### 前端交互

- **单页应用**：`NewsAggregator` 类管理全部状态和交互
- **中文界面**：所有按钮、提示、空状态均为中文
- **深色模式**：基于 `prefers-color-scheme` 自动切换
- **响应式**：桌面端和移动端均可使用
- **搜索防抖**：输入搜索词后 debounce 300ms 再触发请求
