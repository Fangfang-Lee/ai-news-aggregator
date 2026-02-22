# AI News Aggregator 项目指南

## 项目概述

**项目目标**：一个自动聚合 AI 与科技领域新闻的 Web 应用，通过 RSS 源自动抓取内容，利用 DeepSeek API 生成中文摘要，并提供分类、筛选、收藏等阅读管理功能。

**目标用户**：AI 和科技从业者、爱好者，需要跟踪 AI/科技动态的开发者。

## 技术架构

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.11) |
| 数据库 | PostgreSQL 15 + SQLAlchemy 2.0 ORM |
| 缓存/队列 | Redis 7 + Celery 5.3 |
| AI 摘要 | DeepSeek API (deepseek-chat 模型) |
| RSS 解析 | feedparser + requests + html2text |
| 前端 | Vanilla JavaScript + CSS + Jinja2 模板 |
| 部署 | Docker Compose (本地), Render (生产) |

## 核心业务逻辑

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

### 三层内容过滤
1. **财经黑名单过滤** - 过滤纯股票、基金、理财等与科技无关的内容
2. **关键词相关性匹配** - 根据标题和正文关键词自动匹配 7 大分类
3. **分级信任机制** - 宽泛源额外检查，专业源直接放行

### 自动分类 (7 大分类)
- AI - AI 产品发布、API 更新、AI 应用案例
- Technology - 科技行业综合资讯、硬件与平台动态
- Internet - 互联网行业新闻、大厂动态、行业趋势
- Developer - 编程语言、框架更新、开发工具、开源项目
- Cloud & DevOps - 云服务、容器化、CI/CD、基础设施
- Cybersecurity - 安全漏洞通告、安全实践、数据隐私
- Startup & Product - 创业融资、新产品发布、产品设计

### 定时任务 (Celery Beat)
- `fetch_all_sources` - 每 5 分钟抓取所有活跃 RSS 源
- `cleanup_old_content` - 每 24 小时清理过期内容（收藏的保留）
- `generate_missing_summaries` - 生成 AI 摘要（需要 DEEPSEEK_API_KEY）

## 项目结构

```
ai-news-aggregator/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── categories.py  # 分类管理 API
│   │   │   │   ├── content.py     # 内容管理 API
│   │   │   │   └── sources.py     # RSS 源管理 API
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
│   │   │   └── summary_service.py # DeepSeek AI 摘要
│   │   ├── crawlers/
│   │   │   ├── rss_crawler.py    # RSS 抓取 + 网页回退
│   │   │   └── content_parser.py  # 内容清洗/分类/去重/黑名单
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
├── docker-compose.yml
├── render.yaml                    # Render 部署配置
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
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | PostgreSQL 连接字符串 | postgresql://postgres:password@postgres:5432/ai_news_db |
| `REDIS_URL` | Redis 连接字符串 | redis://redis:6379/0 |
| `DEEPSEEK_API_KEY` | DeepSeek API Key (AI 摘要必需) | "" |
| `CONTENT_MIN_DATE` | 文章最早日期 | 2026-02-10 |
| `RSS_FETCH_INTERVAL` | 抓取间隔(秒) | 300 |

## 代码规范

- **Python**: 遵循 PEP 8，使用类型提示
- **Imports**: 分组排序 (标准库 > 第三方 > 本地模块)
- **语言**: 代码注释英文，内容数据中文
- **错误处理**: 使用 logging 记录，返回适当的 HTTP 状态码
