import re
import feedparser
import requests
import html2text
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RSSCrawler:
    """RSS feed crawler for fetching news articles"""

    DEFAULT_USER_AGENT = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/131.0.0.0 Safari/537.36'
    )

    def __init__(self, timeout: int = 30, user_agent: Optional[str] = None):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or self.DEFAULT_USER_AGENT,
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        })
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
        published_parsed = entry.get('published_parsed')
        updated_parsed = entry.get('updated_parsed')
        if published_parsed:
            try:
                published_date = datetime(*published_parsed[:6])
            except (TypeError, ValueError):
                pass
        elif updated_parsed:
            try:
                published_date = datetime(*updated_parsed[:6])
            except (TypeError, ValueError):
                pass

        # Get GUID (unique identifier)
        guid = entry.get('id') or entry.get('link') or str(hash(entry.get('title', '')))

        # Get summary/content
        summary = entry.get('summary')
        content = None
        entry_content = entry.get('content')
        if entry_content:
            content = entry_content[0].get('value', '') if isinstance(entry_content, list) else entry_content

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

        # Fallback: if RSS didn't provide content, fetch the article page
        if (not content_text or len(content_text.strip()) < 100) and entry.get('link'):
            try:
                fetched = self.fetch_article_content(entry['link'])
                if fetched and len(fetched) > len(content_text or ''):
                    content_text = fetched
                    if not html_content:
                        html_content = content_text
                    logger.info(f"Fetched full article content from {entry['link'][:60]} ({len(fetched)} chars)")
            except Exception as e:
                logger.debug(f"Could not fetch article content from {entry.get('link')}: {e}")

        # Extract image URL
        image_url = None
        enclosures = entry.get('enclosures')
        if enclosures:
            for enclosure in enclosures:
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
        return re.sub(r'<.*?>', '', text).strip()

    def _extract_first_image(self, html: str) -> Optional[str]:
        """Extract first image URL from HTML"""
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

    def fetch_article_content(self, url: str, max_length: int = 8000) -> Optional[str]:
        """
        Fetch article page and extract main text content.
        Used as fallback when RSS feed doesn't provide content.

        Args:
            url: Article URL
            max_length: Maximum characters to extract

        Returns:
            Extracted text content or None
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            # Only process HTML pages
            content_type = response.headers.get('content-type', '')
            if 'html' not in content_type.lower():
                return None

            html = response.text

            # Use html2text to extract readable text
            converter = html2text.HTML2Text()
            converter.ignore_links = True
            converter.ignore_images = True
            converter.ignore_emphasis = True
            converter.body_width = 0
            converter.skip_internal_links = True

            text = converter.handle(html).strip()

            # Basic cleanup: remove very short lines (nav, footer debris)
            lines = text.split('\n')
            meaningful_lines = [
                line.strip() for line in lines
                if len(line.strip()) > 15  # skip short navigation/menu items
            ]
            text = '\n'.join(meaningful_lines)

            if len(text) > max_length:
                text = text[:max_length] + '...'

            return text if len(text) > 100 else None

        except requests.exceptions.Timeout:
            logger.debug(f"Timeout fetching article: {url}")
        except requests.exceptions.RequestException as e:
            logger.debug(f"Error fetching article: {url} - {e}")
        except Exception as e:
            logger.debug(f"Unexpected error fetching article: {url} - {e}")

        return None

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