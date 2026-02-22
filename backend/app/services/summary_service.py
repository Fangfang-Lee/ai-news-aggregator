import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating article summaries using MiniMax API"""

    def __init__(self):
        self.api_key = settings.MINIMAX_API_KEY
        self.base_url = "https://api.minimax.chat/v1"
        self.model = settings.MINIMAX_MODEL

    def generate_summary(self, content: str, max_length: int = 500) -> Optional[str]:
        """
        Generate a summary of article content using MiniMax API

        Args:
            content: Article content to summarize
            max_length: Maximum length of summary in characters

        Returns:
            Generated summary or None if failed
        """
        if not self.api_key:
            logger.warning("MiniMax API key not configured")
            return None

        if not content or len(content.strip()) < 50:
            return content[:max_length] if content else None

        # Use larger input length to capture more content for better summarization
        max_input_length = 8000
        if len(content) > max_input_length:
            # Take from beginning AND end to capture full story
            content = content[:5000] + "\n\n...[文章内容较长，以上为前半部分]...\n\n" + content[-3000:]

        system_prompt = """你是一个专业的新闻摘要助手。请仔细阅读下面的新闻文章，然后生成一个简洁的中文摘要。

要求：
1. 如果原文是英文，先完整翻译成中文
2. 认真阅读全文，找出文章的核心观点、主要事件和关键结论
3. 摘要长度严格控制在最多300字，越简短越好
4. 绝对禁止任何介绍性语句，如"本文介绍了"、"作者是"、"文章指出"、"文章介绍"、"作者分享了"等，直接陈述核心内容
5. 使用简洁、清晰的中文，越简短越好
6. 不要编造信息，只基于原文内容总结
7. 直接输出摘要，不要添加任何前缀、后缀或评论
8. 确保每个句子都是完整的，不要在句子中间断开"""

        user_prompt = f"新闻文章内容：\n\n{content}\n\n请为这篇文章生成一个中文摘要（300字以内）。绝对禁止使用\"本文介绍了\"、\"作者是\"、\"文章介绍\"、\"作者分享了\"等任何介绍性语句开头，直接陈述核心内容："

        try:
            with httpx.Client(timeout=90.0) as client:
                response = client.post(
                    f"{self.base_url}/text/chatcompletion_v2",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": 350,  # Limit output to ~300 Chinese characters
                        "temperature": 0.5
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data["choices"][0]["message"]["content"].strip()

                    # Clean up any prefix/suffix
                    summary = summary.replace("摘要：", "").replace("摘要:", "").replace("Summary:", "").strip()
                    # Remove quotes if present
                    summary = summary.strip('"\'""')

                    # Remove introductory phrases
                    intro_patterns = [
                        "本文介绍了", "本文", "作者是", "作者在", "作者分享了",
                        "文章指出", "文章介绍", "文章介绍了", "文章分享", "本文指出", "本文分享",
                        "作者担任", "作者发现", "该文介绍", "本文探讨", "文章探讨",
                        "该文章", "该文", "该篇", "作者构建", "作者部署", "作者设计",
                        "作者提出", "作者创建", "作者开发", "作者使用", "作者采用",
                        "在Cisco", "在某", "在此", "从中", "Cisco担任", "作者认为",
                        "这是一篇", "这是一", "这是", "一篇关于", "一篇", "介绍使用",
                        "关于使用", "在AI"
                    ]
                    for pattern in intro_patterns:
                        if summary.startswith(pattern):
                            summary = summary[len(pattern):].strip()
                            # Also remove common leading phrases after these
                            if summary.startswith("的"):
                                summary = summary[1:].strip()
                            if summary.startswith("是"):
                                summary = summary[1:].strip()
                            if summary.startswith("了"):
                                summary = summary[1:].strip()
                            if summary.startswith("构") and len(summary) > 1 and summary[1] in "建了":
                                summary = summary[2:].strip()
                            # Also remove "一年"、"两年" etc after removing "Cisco担任"
                            if summary.startswith("一年") or summary.startswith("两年") or summary.startswith("多年"):
                                summary = summary[2:].strip()

                    # Also handle cases like "在xxx构建了xxx"
                    if summary.startswith("在") and len(summary) > 3:
                        # Find first occurrence of a verb after "在xxx"
                        for verb in ["构建", "部署", "设计", "开发", "创建", "搭建"]:
                            idx = summary.find(verb)
                            if idx > 0 and idx < 10:  # verb should appear early
                                summary = summary[idx + len(verb):].strip()
                                if summary.startswith("了"):
                                    summary = summary[1:].strip()
                                break

                    # Ensure summary ends with complete sentence (not truncated)
                    # Check if the summary ends mid-sentence
                    if summary and summary[-1] not in '。！？.!?,;；':
                        # Find the last complete sentence
                        last_punctuation = max(
                            summary.rfind('。'),
                            summary.rfind('！'),
                            summary.rfind('？'),
                            summary.rfind('.'),
                            summary.rfind('!'),
                            summary.rfind('?')
                        )
                        if last_punctuation > len(summary) * 0.5:  # At least 50% through
                            summary = summary[:last_punctuation + 1]

                    logger.info(f"Generated summary via MiniMax ({len(summary)} chars)")
                    return summary
                else:
                    logger.error(f"MiniMax API error: {response.status_code} - {response.text}")
                    return None

        except Exception as e:
            logger.error(f"MiniMax API error: {e}")
            return None

    def get_dynamic_length(self, content: str) -> int:
        """Dynamically determine summary length based on content"""
        if not content:
            return 400

        content_length = len(content)

        if content_length < 500:
            return 300
        elif content_length < 2000:
            return 350
        elif content_length < 5000:
            return 450
        else:
            return 500  # Maximum for longer articles
