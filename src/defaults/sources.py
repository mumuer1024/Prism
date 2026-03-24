# -*- coding: utf-8 -*-
"""
默认数据源配置

存储各功能模块的默认数据源配置
"""

from typing import List, Dict, Optional

# ============================================================================
# 默认数据源定义
# ============================================================================
DEFAULT_SOURCES = [
    # 情报日报数据源
    {
        "key": "hacker_news",
        "name": "Hacker News",
        "icon": "📰",
        "desc": "热门技术新闻和社区讨论",
        "source_type": "rss",
        "tool_type": "mission",
        "url": "https://hnrss.org/frontpage",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "github_trending",
        "name": "GitHub Trending",
        "icon": "⭐",
        "desc": "GitHub 每日热门仓库",
        "source_type": "webpage",
        "tool_type": "mission",
        "url": "https://github.com/trending",
        "requires_key": "GITHUB_TOKEN",
        "is_official": True,
    },
    {
        "key": "arxiv",
        "name": "ArXiv AI/ML",
        "icon": "📄",
        "desc": "最新 AI/ML 学术论文",
        "source_type": "rss",
        "tool_type": "mission",
        "url": "http://export.arxiv.org/api/query",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "producthunt",
        "name": "Product Hunt",
        "icon": "🚀",
        "desc": "每日新产品发布",
        "source_type": "api",
        "tool_type": "mission",
        "url": "https://api.producthunt.com/v2/api/graphql",
        "requires_key": "PRODUCTHUNT_TOKEN",
        "is_official": True,
    },
    {
        "key": "v2ex",
        "name": "V2EX",
        "icon": "💬",
        "desc": "创意工作者社区",
        "source_type": "rss",
        "tool_type": "mission",
        "url": "https://www.v2ex.com/index.xml",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "36kr",
        "name": "36氪",
        "icon": "🇨🇳",
        "desc": "中国科技创业媒体",
        "source_type": "rss",
        "tool_type": "mission",
        "url": "https://36kr.com/feed",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "wallstreet",
        "name": "华尔街见闻",
        "icon": "📈",
        "desc": "中国财经资讯",
        "source_type": "rss",
        "tool_type": "mission",
        "url": "https://wallstreetcn.com/news/global",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "x_grok",
        "name": "X/Twitter (Grok)",
        "icon": "🐦",
        "desc": "X 平台实时搜索（需 Grok）",
        "source_type": "api",
        "tool_type": "mission",
        "url": "https://api.x.ai/v1/chat/completions",
        "requires_key": "XAI_API_KEY",
        "is_official": True,
    },
    {
        "key": "hn_blogs",
        "name": "HN Top Blogs",
        "icon": "📝",
        "desc": "Hacker News 热门博客",
        "source_type": "rss",
        "tool_type": "mission",
        "url": "https://hnrss.org/blogs",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "xhs",
        "name": "小红书",
        "icon": "📕",
        "desc": "小红书热门话题与趋势",
        "source_type": "webpage",
        "tool_type": "mission",
        "url": "https://www.xiaohongshu.com",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "tavily",
        "name": "Tavily 搜索",
        "icon": "🔍",
        "desc": "AI 驱动的实时搜索",
        "source_type": "api",
        "tool_type": "mission",
        "url": "https://api.tavily.com/search",
        "requires_key": "TAVILY_TOKEN",
        "is_official": True,
    },
    # 赏金猎人数据源
    {
        "key": "v2ex_bounty",
        "name": "V2EX 急单",
        "icon": "💰",
        "desc": "V2EX 有偿/外包/急单",
        "source_type": "rss",
        "tool_type": "bounty",
        "url": "https://www.v2ex.com/index.xml",
        "requires_key": None,
        "is_official": True,
    },
    {
        "key": "chrome_store",
        "name": "Chrome 扩展商店",
        "icon": "🔌",
        "desc": "Chrome 扩展商店趋势",
        "source_type": "webpage",
        "tool_type": "bounty",
        "url": "https://chromewebstore.google.com",
        "requires_key": None,
        "is_official": True,
    },
    # Alpha 雷达数据源
    {
        "key": "x_grok_alpha",
        "name": "X/Twitter (Grok)",
        "icon": "🐦",
        "desc": "Web3/Solana 开源项目搜索",
        "source_type": "api",
        "tool_type": "alpha",
        "url": "https://api.x.ai/v1/chat/completions",
        "requires_key": "XAI_API_KEY",
        "is_official": True,
    },
]


def get_default_sources(tool_type: Optional[str] = None) -> List[Dict]:
    """
    获取默认数据源列表

    Args:
        tool_type: 可选，筛选指定工具类型的数据源

    Returns:
        数据源列表
    """
    if tool_type:
        return [s for s in DEFAULT_SOURCES if s["tool_type"] == tool_type]
    return DEFAULT_SOURCES.copy()


def get_source_by_key(key: str) -> Optional[Dict]:
    """
    根据 key 获取数据源配置

    Args:
        key: 数据源唯一标识

    Returns:
        数据源配置字典，未找到返回 None
    """
    for source in DEFAULT_SOURCES:
        if source["key"] == key:
            return source.copy()
    return None


def get_official_sources(tool_type: Optional[str] = None) -> List[Dict]:
    """
    获取官方预设数据源列表

    Args:
        tool_type: 可选，筛选指定工具类型的数据源

    Returns:
        官方数据源列表
    """
    sources = get_default_sources(tool_type)
    return [s for s in sources if s.get("is_official", False)]


def get_tool_types() -> List[str]:
    """
    获取所有工具类型列表

    Returns:
        工具类型列表
    """
    return list(set(s["tool_type"] for s in DEFAULT_SOURCES))