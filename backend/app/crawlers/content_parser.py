import re
from typing import List, Optional, Set
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import nltk
import jieba
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
    """Content parser for cleaning, deduplication, and categorization (Chinese/English support)"""

    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))

        # Add Chinese stop words (simplified list)
        self.cn_stop_words = {
            '的', '了', '和', '是', '就', '都', '而', '及', '与', '着',
            '或', '一个', '没有', '我们', '你们', '他们', '它', '这', '那'
        }

        # AI/Technology related keywords (English & Chinese)
        self.ai_keywords = {
            # English
            'artificial intelligence', 'machine learning', 'deep learning', 'neural network',
            'chatgpt', 'gpt', 'llm', 'large language model', 'nlp', 'natural language processing',
            'computer vision', 'robotics', 'automation', 'ai ethics', 'generative ai',
            'openai', 'anthropic', 'google ai', 'microsoft ai', 'meta ai', 'mistral',

            # Chinese
            '人工智能', '机器学习', '深度学习', '神经网络', '大模型', '语言模型',
            '生成式', '自然语言处理', '计算机视觉', '机器人', '自动驾驶', '算法',
            '算力', '显卡', '英伟达', '智谱', '文心一言', '通义千问', 'kimi'
        }

        self.tech_keywords = {
            # English
            'startup', 'venture capital', 'unicorn', 'ipo', 'funding', 'valuation',
            'software', 'hardware', 'semiconductor', 'chip', 'processor', 'cloud',
            'programming', 'developer', 'coding', 'saas', 'paas', 'iaas',

            # Chinese
            '创业', '融资', '独角兽', '上市', '估值', '软件', '硬件', '芯片',
            '半导体', '处理器', '云服务', '云计算', '程序员', '开发', '代码',
            '开源', '架构', '前端', '后端', '全栈', 'SaaS', '互联网', '科技'
        }

    def clean_text(self, text: str) -> str:
        """
        Clean text content by removing extra whitespace, special characters
        """
        if not text:
            return ""

        # Remove HTML entities
        text = re.sub(r'&[a-z]+;', '', text)

        # Remove HTML tags (simple version)
        text = re.sub(r'<[^>]+>', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove special characters at start/end
        text = text.strip()

        return text

    def remove_duplicates(self, articles: List[dict]) -> List[dict]:
        """
        Remove duplicate articles based on title similarity and GUID
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
        if not title:
            return ""
        title = title.lower().strip()
        # Remove punctuation for both English and Chinese
        title = re.sub(r'[^\w\s\u4e00-\u9fa5]', '', title)
        title = re.sub(r'\s+', ' ', title)
        return title

    def extract_tags(self, title: str, content: str) -> List[str]:
        """
        Extract tags from content using keyword matching (Chinese & English)
        """
        text = f"{title} {content}".lower()
        tags = []

        # Check AI keywords
        for keyword in self.ai_keywords:
            if keyword.lower() in text:
                tags.append('AI')
                break # Found one is enough for the category tag

        # Check tech keywords
        for keyword in self.tech_keywords:
            if keyword.lower() in text:
                if 'Tech' not in tags:
                    tags.append('Tech')
                break

        # Extract named entities
        entities = self._extract_entities(text)
        tags.extend(entities)

        return list(set(tags))

    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential named entities (company names, etc.)"""
        entities = []

        # Common tech company patterns
        company_patterns = [
            r'\b(Google|Alphabet|Microsoft|Amazon|Apple|Meta|Facebook|Twitter|X|Tesla|SpaceX|Netflix|Uber|Lyft|Airbnb|Stripe|Salesforce|Oracle|IBM|Intel|AMD|NVIDIA)\b',
            r'(字节跳动|腾讯|阿里|百度|华为|小米|京东|美团|滴滴|网易)'
        ]

        for pattern in company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

        return list(set(entities))[:5]  # Limit to top 5 unique

    def categorize_article(self, title: str, content: str, category_keywords: dict) -> Optional[str]:
        """
        Automatically categorize article based on content
        """
        text = f"{title} {content}".lower()

        best_category = None
        best_score = 0

        # Also use internal keywords for default categories if provided map is empty or simple
        internal_mapping = {
            'AI': self.ai_keywords,
            'Technology': self.tech_keywords
        }

        # Merge provided keywords with internal ones
        check_map = category_keywords.copy()
        for cat, keys in internal_mapping.items():
            if cat in check_map:
                # Assuming check_map[cat] is a list, we add our set to it for checking
                # But actually we just want to iterate over both
                pass
            else:
                check_map[cat] = keys

        for category, keywords in check_map.items():
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
        """
        if not text1 or not text2:
            return False

        # Use jieba for Chinese tokenization
        words1 = set(jieba.cut(text1.lower()))
        words2 = set(jieba.cut(text2.lower()))

        # Filter out stop words and single characters
        words1 = {w for w in words1 if w.strip() and w not in self.stop_words and w not in self.cn_stop_words}
        words2 = {w for w in words2 if w.strip() and w not in self.stop_words and w not in self.cn_stop_words}

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
        Create a simple summary
        """
        if not content:
            return ""

        # Remove HTML
        clean_content = self.clean_text(content)

        # Simple sentence splitting handling Chinese and English punctuation
        # Split by period, question mark, exclamation point, or Chinese equivalents
        sentences = re.split(r'[.!?。！？]+', clean_content)
        sentences = [s.strip() for s in sentences if s.strip()]

        summary = '。'.join(sentences[:max_sentences])
        if summary and not summary.endswith(('。', '.', '!', '?')):
            summary += '...'

        return summary