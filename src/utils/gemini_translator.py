"""
Translator - 使用可配置的 LLM 端点翻译文本为中文
支持 OpenAI 兼容 / Gemini 原生 / Claude 原生 三种格式
原文件名保留为 gemini_translator.py 以兼容现有 import
"""
import sys
import time
import logging

logger = logging.getLogger(__name__)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from config import (
        TRANSLATOR_API_KEY, TRANSLATOR_BASE_URL, TRANSLATOR_MODEL,
        TRANSLATOR_API_FORMAT, GEMINI_TIMEOUT, GEMINI_MAX_RETRIES
    )
    from llm_client import chat
except ImportError:
    from src.config import (
        TRANSLATOR_API_KEY, TRANSLATOR_BASE_URL, TRANSLATOR_MODEL,
        TRANSLATOR_API_FORMAT, GEMINI_TIMEOUT, GEMINI_MAX_RETRIES
    )
    from src.llm_client import chat


def _translate(prompt: str, max_tokens: int = 1024) -> str:
    """内部翻译调用，带重试。"""
    if not TRANSLATOR_API_KEY:
        return ""

    for attempt in range(GEMINI_MAX_RETRIES):
        try:
            result = chat(
                prompt=prompt,
                base_url=TRANSLATOR_BASE_URL,
                api_key=TRANSLATOR_API_KEY,
                model=TRANSLATOR_MODEL,
                api_format=TRANSLATOR_API_FORMAT,
                temperature=0.3,
                max_tokens=max_tokens,
                timeout=GEMINI_TIMEOUT,
            )
            if result:
                return result
        except Exception as e:
            if attempt < GEMINI_MAX_RETRIES - 1:
                logger.warning(f"翻译失败 ({attempt + 1}/{GEMINI_MAX_RETRIES}): {e}")
                time.sleep(2 ** attempt)
                continue
            logger.error(f"翻译最终失败: {e}")

    return ""


def translate_to_chinese(text: str, max_chars: int = 100) -> str:
    if not TRANSLATOR_API_KEY:
        logger.warning("翻译 API Key 未配置，跳过翻译")
        return text[:max_chars] + "..." if len(text) > max_chars else text

    if not text or len(text) < 10:
        return text

    prompt = f"""请将以下学术论文摘要完整翻译成简体中文，要求：
1. 保持学术风格，用词精准
2. 完整翻译全部内容，不要省略任何信息
3. 只输出翻译结果，不要添加任何解释

原文：
{text}"""

    result = _translate(prompt, max_tokens=1024)
    if result:
        return result
    return text[:max_chars] + "..." if len(text) > max_chars else text


def translate_summary_pair(summary: str) -> tuple[str, str]:
    if not summary:
        return ("", "")
    brief_cn = translate_to_chinese(summary[:200], max_chars=80)
    detail_cn = translate_to_chinese(summary, max_chars=500)
    return (brief_cn, detail_cn)


def summarize_blog_article(content: str, mode: str = "brief") -> str:
    if not TRANSLATOR_API_KEY or not content or len(content) < 50:
        return ""

    if mode == "brief":
        prompt = f"""请阅读以下技术博客文章，用一句话中文概括核心观点（最多100字）。
要求：
- 直接说重点，不要"本文介绍了..."这种开头
- 忽略作者信息、日期、URL等元数据
- 突出技术洞察或实用价值

文章内容：
{content[:2000]}"""
        max_tokens = 256
    else:
        prompt = f"""请作为技术情报分析师，阅读以下博客文章并生成中文深度分析报告。

要求：
1. 忽略作者信息、URL、图片链接等元数据
2. 提取核心技术观点和实践经验
3. 用3-4个段落组织：背景、关键发现、技术细节、实用价值
4. 语言风格：专业但易懂，适合技术人士快速阅读
5. 总长度控制在300-500字

文章内容：
{content[:6000]}"""
        max_tokens = 1024

    return _translate(prompt, max_tokens=max_tokens)


if __name__ == "__main__":
    test_text = "Adapting large pretrained models to new tasks efficiently and continually is crucial for real-world deployment but remains challenging due to catastrophic forgetting."
    print("原文:", test_text)
    print("翻译:", translate_to_chinese(test_text, 80))
