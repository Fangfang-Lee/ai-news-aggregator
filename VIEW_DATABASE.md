# 查看 Docker 中的数据库数据

## 数据库连接信息
- **容器名**: `ai_news_postgres`
- **数据库名**: `ai_news_db`
- **用户名**: `postgres`
- **密码**: `password`
- **端口**: `5432` (已映射到本地)

---

## 方法 1: 使用 docker exec 进入容器（最简单）

### 进入 PostgreSQL 容器并连接数据库：
```bash
docker exec -it ai_news_postgres psql -U postgres -d ai_news_db
```

### 常用 SQL 命令：

#### 查看所有表：
```sql
\dt
```

#### 查看表结构：
```sql
\d categories
\d rss_sources
\d content
```

#### 查看数据：

**查看所有分类：**
```sql
SELECT * FROM categories;
```

**查看所有 RSS 源：**
```sql
SELECT id, name, url, is_active, last_fetched FROM rss_sources;
```

**查看文章数量：**
```sql
SELECT COUNT(*) FROM content;
```

**查看最新的 10 篇文章：**
```sql
SELECT id, title, published_date, rss_source_id 
FROM content 
ORDER BY published_date DESC 
LIMIT 10;
```

**查看文章详情（包含分类）：**
```sql
SELECT 
    c.id,
    c.title,
    c.summary,
    c.link,
    c.published_date,
    rs.name as source_name,
    cat.name as category_name
FROM content c
LEFT JOIN rss_sources rs ON c.rss_source_id = rs.id
LEFT JOIN content_category cc ON c.id = cc.content_id
LEFT JOIN categories cat ON cc.category_id = cat.id
ORDER BY c.published_date DESC
LIMIT 20;
```

**统计每个 RSS 源的文章数量：**
```sql
SELECT 
    rs.name,
    COUNT(c.id) as article_count,
    MAX(c.published_date) as latest_article
FROM rss_sources rs
LEFT JOIN content c ON rs.id = c.rss_source_id
GROUP BY rs.id, rs.name
ORDER BY article_count DESC;
```

#### 退出 psql：
```sql
\q
```

---

## 方法 2: 使用本地 psql 客户端（如果已安装）

如果你本地安装了 PostgreSQL 客户端，可以直接连接：

```bash
psql -h localhost -p 5432 -U postgres -d ai_news_db
```

输入密码：`password`

---

## 方法 3: 使用图形化工具

### 使用 pgAdmin 或 DBeaver：

**连接信息：**
- **Host**: `localhost`
- **Port**: `5432`
- **Database**: `ai_news_db`
- **Username**: `postgres`
- **Password**: `password`

---

## 方法 4: 使用 Python 脚本查看（在容器内）

```bash
# 进入后端容器
docker exec -it ai_news_backend bash

# 运行 Python 交互式 shell
python3

# 在 Python 中：
from app.core.database import SessionLocal
from app.models.rss_models import Content, RSSSource, Category

db = SessionLocal()

# 查看文章数量
print(f"文章总数: {db.query(Content).count()}")

# 查看所有 RSS 源
sources = db.query(RSSSource).all()
for s in sources:
    print(f"{s.name}: {s.url}")

# 查看最新文章
articles = db.query(Content).order_by(Content.published_date.desc()).limit(10).all()
for a in articles:
    print(f"{a.title[:50]}... - {a.published_date}")

db.close()
```

---

## 快速查看命令（一行）

### 查看文章总数：
```bash
docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "SELECT COUNT(*) FROM content;"
```

### 查看所有 RSS 源：
```bash
docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "SELECT id, name, url, is_active FROM rss_sources;"
```

### 查看最新 5 篇文章标题：
```bash
docker exec ai_news_postgres psql -U postgres -d ai_news_db -c "SELECT title, published_date FROM content ORDER BY published_date DESC LIMIT 5;"
```

---

## 数据库表结构

主要表：
- `categories` - 分类表
- `rss_sources` - RSS 源表
- `content` - 文章内容表
- `content_category` - 文章和分类的关联表
- `reading_history` - 阅读历史表
