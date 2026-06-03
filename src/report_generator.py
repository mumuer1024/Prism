#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report Generator - 报告生成模块
负责将情报数据转换为 Markdown 报告

v2.1 改造：优先读取用户传入的 Key（USER_* 环境变量），回退到全局 .env
"""

import os
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def get_user_llm_config():
    """
    获取 LLM 配置（优先用户传入，回退全局 .env）
    
    Returns:
        dict: LLM 配置字典
    """
    return {
        'api_key': os.getenv("USER_LLM_API_KEY") or os.getenv("LLM_API_KEY", ""),
        'base_url': os.getenv("USER_LLM_BASE_URL") or os.getenv("LLM_BASE_URL", ""),
        'model': os.getenv("USER_LLM_MODEL") or os.getenv("LLM_MODEL", ""),
        'api_format': os.getenv("USER_LLM_API_FORMAT") or os.getenv("LLM_API_FORMAT", "openai"),
    }


def get_user_translator_config():
    """
    获取翻译模型配置（优先用户传入，回退全局 .env）
    
    Returns:
        dict: 翻译配置字典
    """
    return {
        'api_key': os.getenv("USER_TRANSLATOR_API_KEY") or os.getenv("TRANSLATOR_API_KEY", ""),
        'base_url': os.getenv("USER_TRANSLATOR_BASE_URL") or os.getenv("TRANSLATOR_BASE_URL", ""),
        'model': os.getenv("USER_TRANSLATOR_MODEL") or os.getenv("TRANSLATOR_MODEL", ""),
    }


# Import rate limit delay from centralized config
try:
    from config import GEMINI_RATE_LIMIT_DELAY
except ImportError:
    try:
        from src.config import GEMINI_RATE_LIMIT_DELAY
    except ImportError:
        GEMINI_RATE_LIMIT_DELAY = 1.5

# --- LLM Client for AI Analysis ---
try:
    from llm_client import chat
    LLM_CLIENT_AVAILABLE = True
except ImportError:
    try:
        from src.llm_client import chat
        LLM_CLIENT_AVAILABLE = True
    except ImportError:
        LLM_CLIENT_AVAILABLE = False
        logger.info("LLM client not available, AI analysis will be skipped.")

# --- Default Prompts ---
try:
    from defaults.prompts import get_default_prompt
except ImportError:
    from src.defaults.prompts import get_default_prompt

# --- Gemini Translator ---
try:
    from utils.gemini_translator import translate_to_chinese, summarize_blog_article
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- Jina Reader (Full Content Fetcher) ---
try:
    from utils.jina_reader import fetch_full_content
    JINA_AVAILABLE = True
except ImportError:
    JINA_AVAILABLE = False
    logger.info("Jina Reader not available, using RSS description only.")

if not GEMINI_AVAILABLE:
    logger.info("Gemini translator not available, using English summaries.")
    def translate_to_chinese(text, max_chars=100):
        return text[:max_chars] + "..." if len(text) > max_chars else text

    def summarize_blog_article(content, mode="brief"):
        return ""


def generate_report(intel: dict, date_str: str, user_prompt: str = None) -> str:
    """
    Generate magazine-style markdown report.

    Args:
        intel: 情报数据字典
        date_str: 日期字符串
        user_prompt: 用户自定义 Prompt（可选），用于生成报告风格说明
    """
    lines = [
        f"# 🌐 全球情报日报 (Global Intel Briefing)",
        f"**日期:** {date_str}",
        f"**生成时间:** {datetime.now().strftime('%H:%M')}",
        f"**数据源:** HN, GitHub, 36Kr, WallStreetCN, V2EX, PH, ArXiv, X, DailyHot",
        "",
        "---",
        ""
    ]

# --- Tech Trends ---
    lines.append("## 🛠️ 技术趋势 (Tech Trends)")
    lines.append("> Hacker News + GitHub Trending\n")

    if intel.get("tech_trends"):
        for i, item in enumerate(intel["tech_trends"][:10], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")
            time_str = item.get("time", "")
            cat = item.get("category", "")

            # 生成简介：使用标题翻译作为简介
            brief = ""
            if GEMINI_AVAILABLE and title:
                brief = translate_to_chinese(title, max_chars=80)
                time.sleep(GEMINI_RATE_LIMIT_DELAY)

            lines.append(f"### {i}. [{title}]({url})")
            if brief:
                lines.append(f"> ⚡ {brief}")
            lines.append(f"📍 {cat} | 🔥 {heat} | 🕒 {time_str}")
            lines.append("")
    else:
        lines.append("*暂无数据*\n")

# --- Capital Flow ---
    lines.append("## 💰 资本动向 (Capital Flow)")
    lines.append("> 36Kr + 华尔街见闻（AI/科技领域精选）\n")

    if intel.get("capital_flow"):
        for i, item in enumerate(intel["capital_flow"][:10], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            time_str = item.get("time", "")
            cat = item.get("category", "")

            # 生成简介：使用标题翻译作为简介
            brief = ""
            if GEMINI_AVAILABLE and title:
                brief = translate_to_chinese(title, max_chars=80)
                time.sleep(GEMINI_RATE_LIMIT_DELAY)

            lines.append(f"### {i}. [{title}]({url})")
            if brief:
                lines.append(f"> ⚡ {brief}")
            lines.append(f"📍 {cat} | 🕒 {time_str}")
            lines.append("")
    else:
        lines.append("*暂无数据*\n")

    # --- Research (ArXiv) ---
    lines.append("## 📚 学术前沿 (Research)")
    lines.append("> ArXiv AI/ML Papers\n")

    if intel.get("research"):
        for i, item in enumerate(intel["research"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            authors = item.get("authors", "")
            time_str = item.get("time", "")
            summary = item.get("summary", "").replace("\n", " ")

            brief_cn = translate_to_chinese(summary[:200], max_chars=80) if summary else ""
            if GEMINI_AVAILABLE and summary:
                time.sleep(GEMINI_RATE_LIMIT_DELAY)
            detail_cn = translate_to_chinese(summary, max_chars=2000) if summary else ""

            lines.append(f"### {i}. [{title}]({url})")
            if brief_cn:
                lines.append(f"> ⚡ {brief_cn}")

            lines.append(f"👤 {authors} | 📅 {time_str}")

            if detail_cn:
                lines.append("")
                lines.append(f"**详情:** {detail_cn}")

            lines.append("")
    else:
        lines.append("*暂无数据*\n")

    # --- Product Gems ---
    lines.append("## 💎 产品精选 (Product Gems)")
    lines.append("> Product Hunt Today\n")

    if intel.get("product_gems"):
        for i, item in enumerate(intel["product_gems"][:8], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")
            tagline = item.get("tagline", "")
            grok_review = item.get("grok_review")

            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"> {tagline}")
            lines.append(f"🔥 {heat}")
            lines.append("")

            if grok_review:
                lines.append(f"> **🦅 Grok 舆情核查**: {grok_review}")
                lines.append("")
    else:
        lines.append("*暂无数据 (Product Hunt API 可能需要配置)*\n")

    # --- Social (X/Twitter) ---
    lines.append("## 🐦 社交热议 (Social)")
    lines.append("> X (Twitter) - AI/Tech Discussions\n")

    if intel.get("social"):
        for item in intel["social"]:
            if item.get("type") == "markdown_report":
                lines.append(f"> 来源: {item.get('source', 'X')}\n")
                lines.append(item.get("content", "*无内容*"))
                lines.append("")
            else:
                title = item.get("title", "")
                url = item.get("url", "#")
                author = item.get("author", "")
                heat = item.get("heat", "")

                lines.append(f"### {author}")
                lines.append(f"> {title}")
                lines.append(f"❤️ {heat} | 🔗 [Link]({url})")
                lines.append("")
    else:
        lines.append("*暂无数据 (需要配置 XAI_API_KEY)*\n")

    # --- Community ---
    lines.append("## 🗣️ 社区热点 (Community)")
    lines.append("> V2EX 热门\n")

    if intel.get("community"):
        for i, item in enumerate(intel["community"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            heat = item.get("heat", "")

            lines.append(f"### {i}. [{title}]({url})")
            lines.append(f"💬 {heat}")
            lines.append("")
    else:
        lines.append("*暂无数据*\n")

    # --- DailyHot 热榜速递 ---
    lines.append("## 🔥 热榜速递 (Hot News)")
    lines.append("> DailyHotApi 聚合热榜\n")

    if intel.get("dailyhot"):
        # 按来源分组
        source_groups = {}
        for item in intel["dailyhot"]:
            source = item.get("source", "未知")
            if source not in source_groups:
                source_groups[source] = []
            source_groups[source].append(item)

        # 每个来源显示前3条
        for source, items in source_groups.items():
            lines.append(f"### 📰 {source}")
            for item in items[:3]:
                title = item.get("title", "Untitled")
                url = item.get("url", "#")
                hot = item.get("hot", 0)
                
                # 格式化热度
                if hot >= 100000000:
                    hot_str = f"{hot/100000000:.1f}亿"
                elif hot >= 10000:
                    hot_str = f"{hot/10000:.0f}万"
                else:
                    hot_str = str(hot) if hot > 0 else ""
                
                hot_display = f" 🔥{hot_str}" if hot_str else ""
                lines.append(f"- [{title}]({url}){hot_display}")
            lines.append("")
    else:
        lines.append("*暂无热榜数据 (DailyHotApi 不可用或未配置)*\n")

    # --- Insights (HN Top Blogs) ---
    lines.append("## 💡 深度洞察 (Insights)")
    lines.append("> HN Top Blogs - 精选技术博客\n")

    if intel.get("insights"):
        for i, item in enumerate(intel["insights"][:5], 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "#")
            author = item.get("author", "")
            time_str = item.get("time", "")
            rss_content = item.get("content", "").replace("\n", " ")

            # Jina full-content analysis
            source_text = ""
            if JINA_AVAILABLE and url and url.startswith("http"):
                logger.info(f"[Insights {i}] Fetching full content via Jina...")
                full_content = fetch_full_content(url)
                if full_content and len(full_content) > 200:
                    source_text = full_content
                    logger.info(f"[Insights {i}] Using Jina full content ({len(source_text)} chars)")

            if not source_text and rss_content:
                source_text = rss_content
                logger.debug(f"[Insights {i}] Fallback to RSS content ({len(source_text)} chars)")

            brief_cn = ""
            detail_cn = ""
            if source_text and GEMINI_AVAILABLE:
                brief_cn = summarize_blog_article(source_text, mode="brief")
                time.sleep(GEMINI_RATE_LIMIT_DELAY)
                detail_cn = summarize_blog_article(source_text, mode="detail")

            lines.append(f"### {i}. [{title}]({url})")
            if brief_cn:
                lines.append(f"> ⚡ {brief_cn}")

            lines.append(f"📍 {author}{' | 📅 ' + time_str if time_str else ''}")

            if detail_cn:
                lines.append("")
                lines.append(f"**详情:** {detail_cn}")

            lines.append("")
    else:
        lines.append("*暂无数据 (HN Blogs 传感器不可用)*\n")

    lines.append("---")
    lines.append("")
    lines.append("> 🤖 **本文由 AI 生成，仅供参考。** 内容可能存在偏差，不代表原文观点，不构成任何投资或决策建议。")
    lines.append("")
    lines.append("*报告由 Unified Intelligence Engine V2 自动生成*")

    # === AI 深度分析层 ===
    # 如果 user_prompt 不为空，调用 LLM 生成个性化洞察
    if user_prompt:
        logger.info("开始生成 AI 深度分析...")
        ai_analysis = _generate_ai_analysis(user_prompt, "\n".join(lines))
        if ai_analysis:
            lines.append("")
            lines.append("---")
            lines.append("")
            lines.append("## 🔍 个性化洞察")
            lines.append("> 基于您的关注点生成的深度分析\n")
            lines.append(ai_analysis)
            logger.info("AI 深度分析生成完成")

    return "\n".join(lines)


def _generate_ai_analysis(user_prompt: str, report_content: str) -> str:
    """
    调用 LLM 生成基于用户自定义 Prompt 的深度分析

    Args:
        user_prompt: 用户自定义的分析指令
        report_content: 当前报告的完整内容

    Returns:
        AI 生成的深度分析内容，失败时返回空字符串
    """
    if not LLM_CLIENT_AVAILABLE:
        logger.warning("LLM 客户端不可用，跳过 AI 分析")
        return ""

    # 优先读取用户传入的 LLM 配置
    llm_config = get_user_llm_config()
    if not llm_config['api_key']:
        logger.warning("LLM API Key 未配置，跳过 AI 分析")
        return ""

    # 获取默认分析 prompt（作为 system prompt 的补充）
    default_analysis_prompt = get_default_prompt("mission_analysis") or ""

    # 构建完整 prompt
    system_prompt = f"""你是一位资深的商业分析师和技术情报专家。

{default_analysis_prompt}

用户的个性化分析需求：
{user_prompt}"""

    user_message = f"""以下是今日情报日报的完整内容，请根据系统指令和您的个性化需求进行分析：

{report_content}"""

    try:
        logger.info(f"调用 LLM 生成深度分析: model={llm_config['model']}")
        result = chat(
            prompt=user_message,
            system=system_prompt,
            base_url=llm_config['base_url'],
            api_key=llm_config['api_key'],
            model=llm_config['model'],
            api_format=llm_config['api_format'],
            temperature=0.7,
            max_tokens=2048,
            timeout=180,  # 3分钟超时
        )
        if result:
            logger.info(f"AI 分析生成成功，长度: {len(result)}")
            return result
        else:
            logger.warning("LLM 返回空结果")
            return ""
    except Exception as e:
        logger.error(f"AI 分析生成失败: {e}")
        return ""


__all__ = ['generate_report']
