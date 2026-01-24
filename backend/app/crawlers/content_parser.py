import re
from typing import List, Optional, Set
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import logging

logger = logging.getLogger(__name__)

# Download NLTK data on first use
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class ContentParser:
    """Content parser for cleaning, deduplication, and categorization"""

    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

        # AI/Technology related keywords
        self.ai_keywords = {
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'chatgpt', 'gpt', 'llm', 'large language model', 'nlp', 'natural language processing',
            'computer vision', 'robotics', 'automation', 'ai ethics', 'generative ai',
            'openai', 'anthropic', 'google ai', 'microsoft ai', 'meta ai'
        }

        self.tech_keywords = {
            'startup', 'venture capital', 'unicorn', 'ipo', 'funding', 'valuation',
            'software', 'hardware', 'semiconductor', 'chip', 'processor', 'cloud',
            'programming', 'developer', 'coding', 'saas', 'paas', 'iaas'
        }

    def clean_text(self, text: str) -> str:
        """
        Clean text content by removing extra whitespace, special characters

        Args:
            text: Raw text content

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        # Remove HTML entities
        text = re.sub(r'&[a-z]+;', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters at start/end
        text = text.strip()

        return text

    def remove_duplicates(self, articles: List[dict]) -> List[dict]:
        """
        Remove duplicate articles based on title similarity and GUID

        Args:
            articles: List of article dictionaries

        Returns:
            List of unique articles
        """
        seen_guids: Set[str] = set()
        seen_titles: Set[str] = set()
        unique_articles = []

        for article in articles:
            guid = article.get('guid', '')
            title = self._normalize_title(article.get('title', ''))

            # Check for exact GUID match
            if guid and guid in seen_guids:
                continue

            # Check for similar title
            if title in seen_titles:
                continue

            unique_articles.append(article)
            if guid:
                seen_guids.add(guid)
            seen_titles.add(title)

        return unique_articles

    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        title = title.lower().strip()
        title = re.sub(r'[^\w\s]', '', title)
        title = re.sub(r'\s+', ' ', title)
        return title

    def extract_tags(self, title: str, content: str) -> List[str]:
        """
        Extract tags from content using keyword matching

        Args:
            title: Article title
            content: Article content

        Returns:
            List of extracted tags
        """
        text = f"{title} {content}".lower()
        tags = []

        # Check AI keywords
        for keyword in self.ai_keywords:
            if keyword.lower() in text:
                tags.append('AI')

        # Check tech keywords
        for keyword in self.tech_keywords:
            if keyword.lower() in text:
                if 'Tech' not in tags:
                    tags.append('Tech')

        # Extract named entities (simple version)
        entities = self._extract_entities(text)
        tags.extend(entities)

        return list(set(tags))

    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential named entities (company names, etc.)"""
        entities = []

        # Common tech company patterns
        company_patterns = [
            r'\b(Google|Alphabet|Microsoft|Amazon|Apple|Meta|Facebook|Twitter|X|Tesla|SpaceX|Netflix|Uber|Lyft|Airbnb|Stripe|Salesforce|Oracle|IBM|Intel|AMD|NVIDIA)\b'
        ]

        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

        return entities[:3]  # Limit to top 3

    def categorize_article(self, title: str, content: str, category_keywords: dict) -> Optional[str]:
        """
        Automatically categorize article based on content

        Args:
            title: Article title
            content: Article content
            category_keywords: Dict mapping category names to keyword lists

        Returns:
            Category name with highest match score or None
        """
        text = f"{title} {content}".lower()

        best_category = None
        best_score = 0

        for category, keywords in category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in text:
                    score += 1

            if score > best_score:
                best_score = score
                best_category = category

        return best_category if best_score > 0 else None

    def is_duplicate_content(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        Check if two texts are duplicates based on content similarity

        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold (0-1)

        Returns:
            True if texts are similar above threshold
        """
        if not text1 or not text2:
            return False

        # Simple word overlap similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        if not words1 or not words2:
            return False

        intersection = words1 & words2
        union = words1 | words2

        if not union:
            return False

        similarity = len(intersection) / len(union)
        return similarity >= threshold

    def summarize_content(self, content: str, max_sentences: int = 3) -> str:
        """
        Create a simple summary by taking the first N sentences

        Args:
            content: Article content
            max_sentences: Maximum sentences in summary

        Returns:
            Summary text
        """
        if not content:
            return ""

        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        return '. '.join(sentences[:max_sentences])