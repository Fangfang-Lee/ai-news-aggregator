import httpx
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SummaryService:
    """Service for generating article summaries using DeepSeek API"""

    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    async def generate_summary(self, content: str, max_length: int = 300) -> Optional[str]:
        """
        Generate a summary of article content using DeepSeek API

        Args:
            content: Article content to summarize
            max_length: Maximum length of summary in characters

        Returns:
            Generated summary or None if failed
        """
        if not self.api_key:
            logger.warning("DeepSeek API key not configured")
            return None

        if not content or len(content.strip()) < 50:
            # Content too short, just return truncated original
            return content[:max_length]

        # Truncate content if too long to save tokens
        max_input_length = 4000  # Limit input to save tokens
        if len(content) > max_input_length:
            content = content[:max_input_length] + "..."

        system_prompt = f"""你是一个新闻摘要助手。请用中文总结以下新闻内容。
要求：
1. 摘要长度控制在 {max_length // 2}-{max_length} 字
2. 突出新闻的核心信息和要点
3. 使用简洁清晰的语言
4. 不要编造信息，只基于原文总结
5. 直接输出摘要，不要加任何前缀或后缀"""

        user_prompt = f"新闻内容：\n\n{content}\n\n请生成中文摘要："

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "max_tokens": max_length,
                        "temperature": 0.7
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    summary = data["choices"][0]["message"]["content"].strip()
                    # Clean up any prefix/suffix
                    summary = summary.replace("摘要：", "").replace("Summary:", "").strip()
                    logger.info(f"Generated summary for article ({len(summary)} chars)")
                    return summary
                else:
                    error_data = response.json()
                    logger.error(f"DeepSeek API error: {response.status_code} - {error_data}")
                    return None

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return None

    async def get_dynamic_length(self, content: str) -> int:
        """
        Dynamically determine summary length based on content

        Args:
            content: Article content

        Returns:
            Recommended summary length
        """
        if not content:
            return 100

        content_length = len(content)

        if content_length < 500:
            return 100
        elif content_length < 1500:
            return 200
        elif content_length < 3000:
            return 250
        else:
            return 300  # Maximum length
