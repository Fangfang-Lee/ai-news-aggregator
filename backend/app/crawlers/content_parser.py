import re
from typing import List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class ContentParser:
    """Content parser for cleaning, deduplication, and categorization"""

    def __init__(self):
        # Category keywords (Chinese + English)
        self.category_keywords = {
            'AI': {
                '人工智能', 'AI', '机器学习', '深度学习', '大模型', '大语言模型',
                'LLM', 'GPT', 'ChatGPT', '智能体', 'Agent', '提示工程',
                'prompt', 'AIGC', '生成式', 'Copilot', '通义', '文心',
                'Claude', 'Gemini', 'DeepSeek', '自然语言处理', 'NLP',
                '计算机视觉', '语音识别', 'AI应用', '人机交互',
                'OpenAI', 'Anthropic', '百川', '智谱', 'Midjourney',
                'Stable Diffusion', 'Sora', '多模态', 'RAG',
                # English AI terms for international sources
                'machine learning', 'deep learning', 'neural network',
                'transformer', 'diffusion', 'fine-tuning', 'fine tuning',
                'inference', 'training', 'model', 'embedding',
                'tokenizer', 'benchmark', 'dataset', 'pretrain',
                'reinforcement learning', 'RLHF', 'distillation',
                'reasoning', 'LLM', 'language model', 'vision model',
                'multimodal', 'text-to-image', 'text-to-video',
                'speech recognition', 'computer vision', 'OCR',
                'Hugging Face', 'llama', 'Mistral', 'Qwen',
                'open-source', 'weights', 'checkpoint',
                'GPU', 'CUDA', 'TPU', 'tensor',
            },
            'Technology': {
                '科技', '技术', '芯片', '半导体', '处理器', '手机',
                '智能硬件', '5G', '6G', '物联网', 'IoT', '元宇宙',
                '区块链', '量子计算', '新能源', '电动车', '自动驾驶',
                '可穿戴', 'VR', 'AR', '混合现实', '折叠屏',
                'Apple', 'Google', 'Microsoft', 'Samsung', 'Intel', 'AMD',
                'NVIDIA', 'TSMC', '台积电', '高通', 'Qualcomm',
            },
            'Internet': {
                '互联网', '电商', '社交', '短视频', '直播', '流量',
                '用户增长', '平台', '生态', '数字化', '在线',
                '阿里', '腾讯', '百度', '字节跳动', '抖音', 'TikTok',
                '美团', '京东', '拼多多', '小红书', '快手', 'B站',
                '哔哩哔哩', '微信', '支付宝', '网易', '滴滴',
                '大厂', '裁员', '组织架构', '业务调整',
            },
            'Developer': {
                '开发者', '编程', '代码', '开源', 'GitHub', 'Git',
                '框架', 'API', 'SDK', '前端', '后端', '全栈',
                'Python', 'JavaScript', 'TypeScript', 'Rust', 'Go', 'Java',
                'React', 'Vue', 'Node.js', 'Docker', 'Kubernetes',
                'VS Code', 'IDE', '效率工具', '技术栈', '架构',
                '微服务', '数据库', 'Redis', 'PostgreSQL', 'MySQL',
                '版本发布', '技术周刊', '最佳实践', '设计模式',
                # English dev terms
                'developer', 'programming', 'open source', 'framework',
                'library', 'CLI', 'runtime', 'compiler', 'debugging',
                'refactoring', 'tooling', 'package', 'release',
                'Swift', 'Kotlin', 'C++', 'WebAssembly', 'WASM',
            },
            'Cloud & DevOps': {
                '云计算', '云服务', '云原生', 'AWS', 'Azure', 'GCP',
                '阿里云', '腾讯云', '华为云', 'DevOps', 'CI/CD',
                '容器', '容器化', 'K8s', 'Kubernetes', 'Docker',
                '微服务', 'Serverless', '无服务器', '基础设施',
                '运维', 'SRE', '监控', '可观测性', '服务网格',
                'Terraform', 'Ansible', 'Jenkins', 'GitOps',
            },
            'Cybersecurity': {
                '安全', '漏洞', '网络安全', '信息安全', '数据泄露',
                '黑客', '攻击', '勒索', '病毒', '木马', '钓鱼',
                '加密', '隐私', '数据保护', 'GDPR', '等保',
                'CVE', '零日', '渗透', '防火墙', 'WAF',
                '安全审计', '风险评估', '应急响应', '威胁情报',
            },
            'Startup & Product': {
                '创业', '融资', 'VC', '风投', '天使轮',
                'A轮', 'B轮', '独角兽',
                '产品', '用户体验', 'UX', 'UI', '交互设计',
                '增长黑客', '商业模式', 'SaaS', 'ToB', 'ToC',
                '产品经理', '需求分析', '用户画像', 'MVP',
                'AI产品', '产品设计', '功能迭代',
            },
        }

        # Negative keywords: financial/stock content that should be filtered out
        # If title contains any of these AND no core tech term, article is skipped
        self.blacklist_keywords = {
            # 股市术语
            '分红', 'ETF', '股价', '股票', '市盈率', '涨停', '跌停',
            '基金净值', '债券', '期货', '外汇汇率', '大盘', '牛市', '熊市',
            '个股', '仓位', '持仓', '减持', '增持', 'A股', '港股', '美股',
            '券商', '散户', '抄底', '割肉', '套牢', '解套',
            '股息', '市值蒸发', '跌幅', '涨幅', '估值',
            # 理财/投资分析
            '每股收益', '营业利润', '盈利超预期', '财报', '季报',
            '分析师评级', '目标价', '买入评级',
            # 非科技行业
            '冲刺港股', '冲刺IPO',
        }

        # Chinese and global tech company names for entity extraction
        self.company_patterns = [
            # Chinese tech companies
            r'\b(阿里巴巴|腾讯|百度|字节跳动|华为|小米|美团|京东|拼多多|网易|快手|哔哩哔哩)\b',
            # Global tech companies
            r'\b(Google|Alphabet|Microsoft|Amazon|Apple|Meta|Tesla|SpaceX|Netflix|OpenAI|Anthropic|NVIDIA)\b',
        ]

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
        # Remove punctuation (both Chinese and English)
        title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title)
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

        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    if category not in tags:
                        tags.append(category)
                    break  # Found match for this category, move on

        # Extract company entities
        entities = self._extract_entities(f"{title} {content}")
        tags.extend(entities)

        return list(set(tags))

    def _extract_entities(self, text: str) -> List[str]:
        """Extract potential named entities (company names, etc.)"""
        entities = []

        for pattern in self.company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            entities.extend(matches)

        return list(set(entities))[:3]  # Limit to top 3 unique

    def is_financial_noise(self, title: str) -> bool:
        """
        Check if an article title indicates pure financial/stock content
        that is not relevant to tech/AI readers.

        Args:
            title: Article title

        Returns:
            True if the article appears to be irrelevant financial content
        """
        if not title:
            return False

        for keyword in self.blacklist_keywords:
            if keyword in title:
                # Double check: if the title also contains core tech keywords, keep it
                # e.g. "AI概念股涨停" should still pass
                core_tech_terms = {'AI', '人工智能', '芯片', '半导体', '科技', '互联网',
                                   '大模型', '机器人', '自动驾驶', '算力', '数据中心',
                                   '云计算', 'SaaS', '开源'}
                for tech_term in core_tech_terms:
                    if tech_term in title:
                        return False  # Has tech relevance, keep it
                return True  # Pure financial, filter out

        return False

    def categorize_article(self, title: str, content: str) -> Optional[str]:
        """
        Automatically categorize article based on content

        Args:
            title: Article title
            content: Article content

        Returns:
            Category name with highest match score or None
        """
        text = f"{title} {content}"

        best_category = None
        best_score = 0

        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                # Case-insensitive match for English, direct match for Chinese
                if keyword.lower() in text.lower():
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

        # Simple character overlap similarity (works for both Chinese and English)
        chars1 = set(text1)
        chars2 = set(text2)

        if not chars1 or not chars2:
            return False

        intersection = chars1 & chars2
        union = chars1 | chars2

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

        # Split by Chinese and English sentence delimiters
        sentences = re.split(r'[.!?。！？]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        return '。'.join(sentences[:max_sentences])
