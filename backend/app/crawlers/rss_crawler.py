import feedparser
import requests
from typing import List, Dict, Optional
from datetime import datetime
import logging
from urllib.parse import urljoin
import html2text

logger = logging.getLogger(__name__)


class RSSCrawler:
    """RSS feed crawler for fetching news articles"""

    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        self.timeout = timeout
        self.session = requests.Session()
        if user_agent:
            self.session.headers.update({'User-Agent': user_agent})
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0

    def fetch_feed(self, url: str) -> Optional[Dict]:
        """
        Fetch and parse RSS feed from URL

        Args:
            url: RSS feed URL

        Returns:
            Parsed feed data or None if failed
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()

            # Parse RSS feed
            feed = feedparser.parse(response.content)

            if feed.bozo:
                logger.warning(f"Feed parsing warning for {url}: {feed.bozo_exception}")

            return {
                'feed': feed.feed,
                'entries': feed.entries,
                'status': response.status_code
            }

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching RSS feed from {url}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching RSS feed from {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing feed {url}: {e}")

        return None

    def parse_entry(self, entry: Dict, source_url: str, category_id: Optional[int] = None) -> Dict:
        """
        Parse a single RSS entry into structured data

        Args:
            entry: RSS feed entry
            source_url: URL of the RSS source
            category_id: Category ID for the content

        Returns:
            Parsed content data
        """
        # Get published date
        published_date = None
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_date = datetime(*entry.published_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                published_date = datetime(*entry.updated_parsed[:6])
            except (TypeError, ValueError):
                pass

        # Get GUID (unique identifier)
        guid = entry.get('id') or entry.get('link') or str(hash(entry.get('title', '')))

        # Get summary/content
        summary = entry.get('summary')
        content = None
        if hasattr(entry, 'content') and entry.content:
            content = entry.content[0].get('value', '') if isinstance(entry.content, list) else entry.content

        # Convert HTML to plain text
        content_text = None
        html_content = content or summary
        if html_content:
            try:
                content_text = self.html_converter.handle(html_content)
                content_text = content_text.strip()
            except Exception as e:
                logger.warning(f"Error converting HTML to text: {e}")
                content_text = self._strip_html_tags(html_content)

        # Extract image URL
        image_url = None
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('image/'):
                    image_url = enclosure.get('href')
                    break
        elif summary and '<img' in summary:
            image_url = self._extract_first_image(summary)

        return {
            'title': entry.get('title', 'Untitled'),
            'summary': self._strip_html_tags(summary) if summary else None,
            'content_html': html_content,
            'content_text': content_text,
            'link': entry.get('link', ''),
            'image_url': image_url,
            'author': entry.get('author'),
            'published_date': published_date,
            'guid': guid,
            'source_url': source_url,
            'category_id': category_id
        }

    def _strip_html_tags(self, text: str) -> str:
        """Strip HTML tags from text"""
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()

    def _extract_first_image(self, html: str) -> Optional[str]:
        """Extract first image URL from HTML"""
        import re
        match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html)
        return match.group(1) if match else None

    def fetch_and_parse(self, url: str, category_id: Optional[int] = None) -> Optional[List[Dict]]:
        """
        Fetch RSS feed and parse all entries

        Args:
            url: RSS feed URL
            category_id: Category ID for the content

        Returns:
            List of parsed entries or None if failed
        """
        feed_data = self.fetch_feed(url)
        if not feed_data:
            return None

        entries = []
        for entry in feed_data['entries']:
            try:
                parsed = self.parse_entry(entry, url, category_id)
                entries.append(parsed)
            except Exception as e:
                logger.error(f"Error parsing entry: {e}")
                continue

        return entries

    def validate_feed_url(self, url: str) -> bool:
        """
        Validate if a URL is a valid RSS feed

        Args:
            url: URL to validate

        Returns:
            True if valid RSS feed, False otherwise
        """
        try:
            feed_data = self.fetch_feed(url)
            if feed_data and feed_data.get('entries'):
                return True
        except Exception:
            pass
        return False