from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import re


def truncate_text(text: str, max_length: int = 200) -> str:
    """
    Truncate text to max_length, adding ellipsis if needed

    Args:
        text: Text to truncate
        max_length: Maximum length

    Returns:
        Truncated text
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def format_date(date: Optional[datetime]) -> str:
    """
    Format datetime for display

    Args:
        date: Datetime to format

    Returns:
        Formatted date string
    """
    if not date:
        return "Unknown"

    now = datetime.utcnow()
    diff = now - date

    if diff < timedelta(minutes=1):
        return "Just now"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes}m ago"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        return f"{hours}h ago"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"{days}d ago"
    else:
        return date.strftime("%b %d, %Y")


def generate_slug(text: str) -> str:
    """
    Generate URL-friendly slug from text

    Args:
        text: Text to slugify

    Returns:
        Slug string
    """
    # Convert to lowercase
    slug = text.lower()

    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)

    # Remove leading/trailing hyphens
    slug = slug.strip('-')

    return slug


def compute_hash(content: str) -> str:
    """
    Compute MD5 hash of content

    Args:
        content: Content to hash

    Returns:
        Hash string
    """
    return hashlib.md5(content.encode()).hexdigest()


def sanitize_html(html: str) -> str:
    """
    Basic HTML sanitization

    Args:
        html: HTML string

    Returns:
        Sanitized HTML
    """
    if not html:
        return ""

    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove style tags
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)

    # Remove comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    return html


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL

    Args:
        url: URL string

    Returns:
        Domain or None
    """
    if not url:
        return None

    import urllib.parse
    parsed = urllib.parse.urlparse(url)
    return parsed.netloc


def parse_user_agent(user_agent: str) -> Dict[str, Any]:
    """
    Parse user agent string for basic device info

    Args:
        user_agent: User agent string

    Returns:
        Dict with device info
    """
    info = {
        'is_mobile': False,
        'is_tablet': False,
        'is_desktop': True,
        'browser': 'Unknown',
        'os': 'Unknown'
    }

    ua_lower = user_agent.lower()

    if 'mobile' in ua_lower or 'android' in ua_lower:
        info['is_mobile'] = True
        info['is_desktop'] = False

    if 'ipad' in ua_lower or 'tablet' in ua_lower:
        info['is_tablet'] = True
        info['is_mobile'] = False
        info['is_desktop'] = False

    # Simple browser detection
    if 'chrome' in ua_lower:
        info['browser'] = 'Chrome'
    elif 'firefox' in ua_lower:
        info['browser'] = 'Firefox'
    elif 'safari' in ua_lower:
        info['browser'] = 'Safari'
    elif 'edge' in ua_lower:
        info['browser'] = 'Edge'

    # Simple OS detection
    if 'windows' in ua_lower:
        info['os'] = 'Windows'
    elif 'mac os' in ua_lower or 'macos' in ua_lower:
        info['os'] = 'macOS'
    elif 'linux' in ua_lower:
        info['os'] = 'Linux'
    elif 'android' in ua_lower:
        info['os'] = 'Android'
    elif 'ios' in ua_lower or 'iphone' in ua_lower:
        info['os'] = 'iOS'

    return info