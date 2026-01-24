import pytest
from datetime import datetime


class TestRSSCrawler:
    """Tests for RSS crawler functionality"""

    def test_init(self):
        """Test RSS crawler initialization"""
        from app.crawlers.rss_crawler import RSSCrawler
        crawler = RSSCrawler()
        assert crawler.timeout == 30
        assert crawler.session is not None

    def test_parse_entry_basic(self):
        """Test basic entry parsing"""
        from app.crawlers.rss_crawler import RSSCrawler

        crawler = RSSCrawler()
        entry = {
            'title': 'Test Article',
            'summary': 'This is a summary',
            'link': 'https://example.com/article',
            'published_parsed': (2024, 1, 15, 10, 30, 0, 0, 1, 0),
            'id': 'test-guid-123'
        }

        result = crawler.parse_entry(entry, 'https://example.com/feed')

        assert result['title'] == 'Test Article'
        assert result['link'] == 'https://example.com/article'
        assert result['guid'] == 'test-guid-123'
        assert result['published_date'] == datetime(2024, 1, 15, 10, 30, 0)

    def test_parse_entry_without_date(self):
        """Test entry parsing without published date"""
        from app.crawlers.rss_crawler import RSSCrawler

        crawler = RSSCrawler()
        entry = {
            'title': 'Test Article',
            'link': 'https://example.com/article',
        }

        result = crawler.parse_entry(entry, 'https://example.com/feed')

        assert result['title'] == 'Test Article'
        assert result['published_date'] is None

    def test_strip_html_tags(self):
        """Test HTML tag stripping"""
        from app.crawlers.rss_crawler import RSSCrawler

        crawler = RSSCrawler()
        html = "<p>This is <strong>bold</strong> text</p>"
        result = crawler._strip_html_tags(html)

        assert "This is bold text" in result
        assert "<p>" not in result
        assert "<strong>" not in result

    def test_extract_first_image(self):
        """Test extracting first image from HTML"""
        from app.crawlers.rss_crawler import RSSCrawler

        crawler = RSSCrawler()
        html = '<p>Some text</p><img src="https://example.com/image.jpg" alt="Image">'
        result = crawler._extract_first_image(html)

        assert result == "https://example.com/image.jpg"

    def test_extract_first_image_none(self):
        """Test extracting image when none exists"""
        from app.crawlers.rss_crawler import RSSCrawler

        crawler = RSSCrawler()
        html = '<p>Some text but no images</p>'
        result = crawler._extract_first_image(html)

        assert result is None


class TestContentParser:
    """Tests for content parser functionality"""

    def test_init(self):
        """Test content parser initialization"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        assert parser.lemmatizer is not None
        assert len(parser.ai_keywords) > 0

    def test_clean_text(self):
        """Test text cleaning"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        dirty_text = "  This   is  a  test  &nbsp;  text  "
        result = parser.clean_text(dirty_text)

        assert result == "This is a test text"

    def test_clean_text_empty(self):
        """Test cleaning empty text"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        result = parser.clean_text("")

        assert result == ""

    def test_clean_text_none(self):
        """Test cleaning None text"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        result = parser.clean_text(None)

        assert result == ""

    def test_normalize_title(self):
        """Test title normalization"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        title1 = "Test Article Title"
        title2 = "Test Article   Title!"
        title3 = "different title"

        norm1 = parser._normalize_title(title1)
        norm2 = parser._normalize_title(title2)
        norm3 = parser._normalize_title(title3)

        assert norm1 == norm2
        assert norm1 != norm3

    def test_remove_duplicates(self):
        """Test duplicate removal"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        articles = [
            {'title': 'Article 1', 'guid': 'guid-1'},
            {'title': 'Article 2', 'guid': 'guid-2'},
            {'title': 'Article 1', 'guid': 'guid-1'},  # Duplicate by guid
            {'title': 'Article 2', 'guid': 'guid-3'},  # Similar title, different guid
        ]

        result = parser.remove_duplicates(articles)

        assert len(result) == 3

    def test_extract_tags(self):
        """Test tag extraction"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        title = "OpenAI announces new GPT model"
        content = "This article discusses artificial intelligence and machine learning"

        tags = parser.extract_tags(title, content)

        assert len(tags) > 0
        assert 'AI' in tags

    def test_summarize_content(self):
        """Test content summarization"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        content = "First sentence. Second sentence. Third sentence. Fourth sentence. Fifth sentence."

        result = parser.summarize_content(content, max_sentences=3)

        assert len(result.split('.')) == 4  # 3 sentences + empty string after final dot

    def test_summarize_empty_content(self):
        """Test summarizing empty content"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        result = parser.summarize_content("")

        assert result == ""

    def test_is_duplicate_content_high_similarity(self):
        """Test duplicate detection with high similarity"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        text1 = "This is a test article about AI"
        text2 = "This is a test article about AI and machine learning"

        result = parser.is_duplicate_content(text1, text2, threshold=0.5)

        assert result is True

    def test_is_duplicate_content_low_similarity(self):
        """Test duplicate detection with low similarity"""
        from app.crawlers.content_parser import ContentParser

        parser = ContentParser()
        text1 = "This is about artificial intelligence"
        text2 = "That article is about cooking recipes"

        result = parser.is_duplicate_content(text1, text2, threshold=0.8)

        assert result is False