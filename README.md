# AI News Aggregator

AI News Aggregator is a web application that automatically aggregates AI and technology news from multiple RSS sources, categorizes content, and provides a clean interface for reading and discovery.

## Features

- **RSS Source Management**: Add, edit, and delete RSS feed sources
- **Automatic Content Fetching**: Scheduled tasks fetch new content periodically
- **Content Categorization**: Automatic categorization with custom categories
- **Deduplication**: Smart duplicate detection to avoid repeated articles
- **Search & Filter**: Full-text search with category and source filters
- **Reading History**: Track what you've read
- **Bookmarks**: Save interesting articles for later
- **Responsive Design**: Works on desktop and mobile devices

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache/Queue**: Redis + Celery
- **Crawling**: feedparser + requests
- **Frontend**: Vanilla JavaScript + CSS

## Project Structure

```
ai-news-aggregator/
├── backend/
│   ├── app/
│   │   ├── api/              # API routes and schemas
│   │   ├── core/             # Configuration (database, Redis)
│   │   ├── models/           # SQLAlchemy models
│   │   ├── services/         # Business logic
│   │   ├── utils/            # Helper functions
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── celery_app.py     # Celery configuration
│   │   └── tasks.py          # Celery tasks
│   ├── crawlers/
│   │   ├── rss_crawler.py    # RSS feed fetcher
│   │   ├── content_parser.py # Content processing
│   │   └── scheduler.py      # Task scheduler
│   ├── tests/                # Unit tests
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── static/
│   │   ├── css/              # Stylesheets
│   │   └── js/               # JavaScript
│   └── templates/            # HTML templates
├── docker-compose.yml
└── README.md
```

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
cd /users/jason/claude-project/ai-news-aggregator
```

2. Start all services:
```bash
docker-compose up -d
```

3. The application will be available at:
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs
   - Interactive API: http://localhost:8000/api/redoc

### Manual Installation

1. Install PostgreSQL and Redis

2. Create a virtual environment and install dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
export DATABASE_URL="postgresql://postgres:password@localhost:5432/ai_news_db"
export REDIS_URL="redis://localhost:6379/0"
```

4. Run the application:
```bash
uvicorn app.main:app --reload
```

## Usage

### Adding RSS Sources

1. Click the "Add RSS Source" button on the home page
2. Enter the RSS feed URL and a name
3. Select a category (optional)
4. Click "Add Source"

### Fetching Content

- Content is automatically fetched every 5 minutes via Celery
- Click the refresh button to manually trigger fetching

### Managing Content

- Click any article to read it
- Use the bookmark button to save articles
- Filter by category, source, or read status
- Search for specific articles

## API Endpoints

### Categories
- `GET /api/categories/` - List all categories
- `POST /api/categories/` - Create category
- `GET /api/categories/{id}` - Get category details
- `PUT /api/categories/{id}` - Update category
- `DELETE /api/categories/{id}` - Delete category

### RSS Sources
- `GET /api/sources/` - List all sources
- `POST /api/sources/` - Create source
- `GET /api/sources/{id}` - Get source details
- `PUT /api/sources/{id}` - Update source
- `DELETE /api/sources/{id}` - Delete source
- `POST /api/sources/{id}/fetch` - Fetch content from source
- `GET /api/sources/{id}/stats` - Get source statistics

### Content
- `GET /api/content/` - List articles (with pagination and filters)
- `GET /api/content/{id}` - Get article details
- `POST /api/content/{id}/mark-read` - Mark as read
- `POST /api/content/{id}/mark-unread` - Mark as unread
- `POST /api/content/{id}/bookmark` - Toggle bookmark
- `POST /api/content/fetch-all` - Fetch from all sources

## Running Tests

```bash
cd backend
pytest tests/
```

## Configuration

Edit `app/core/config.py` to customize:
- Database connection
- Redis connection
- Celery settings
- Fetch intervals
- CORS origins

## Default Categories

The application initializes with these categories:
- AI (Purple)
- Technology (Blue)
- Business (Green)
- Science (Violet)
- Internet (Orange)

## Sample RSS Sources

Here are some popular RSS feeds to add:

| Source | URL | Category |
|--------|-----|----------|
| OpenAI Blog | https://openai.com/blog/rss.xml | AI |
| TechCrunch AI | https://techcrunch.com/category/artificial-intelligence/feed/ | AI |
| MIT Technology Review | https://www.technologyreview.com/feed/ | Technology |
| The Verge | https://www.theverge.com/rss/index.xml | Technology |
| Wired | https://www.wired.com/feed/ | Technology |
| Ars Technica | https://feeds.arstechnica.com/arstechnica/index | Technology |

## License

MIT License