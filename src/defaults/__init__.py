# -*- coding: utf-8 -*-
"""
默认配置模块

提供各功能模块的默认 Prompt 和数据源配置
"""

from src.defaults.prompts import (
    DEFAULT_MISSION_PROMPT,
    DEFAULT_MISSION_ANALYSIS_PROMPT,
    DEFAULT_BOUNTY_KEYWORDS,
    DEFAULT_BOUNTY_ANALYSIS_PROMPT,
    DEFAULT_BOUNTY_REPORT_TEMPLATE,
    DEFAULT_ALPHA_PROMPT,
    DEFAULT_REVENUE_PROMPT,
    ALPHA_QUERIES,
    TOOL_TYPES,
    get_default_prompt,
    get_default_bounty_keywords,
    get_tool_display_name,
)

from src.defaults.sources import (
    DEFAULT_SOURCES,
    get_default_sources,
    get_source_by_key,
    get_official_sources,
)

__all__ = [
    # Prompts
    "DEFAULT_MISSION_PROMPT",
    "DEFAULT_MISSION_ANALYSIS_PROMPT",
    "DEFAULT_BOUNTY_KEYWORDS",
    "DEFAULT_BOUNTY_ANALYSIS_PROMPT",
    "DEFAULT_BOUNTY_REPORT_TEMPLATE",
    "DEFAULT_ALPHA_PROMPT",
    "DEFAULT_REVENUE_PROMPT",
    "ALPHA_QUERIES",
    "TOOL_TYPES",
    "get_default_prompt",
    "get_default_bounty_keywords",
    "get_tool_display_name",
    # Sources
    "DEFAULT_SOURCES",
    "get_default_sources",
    "get_source_by_key",
    "get_official_sources",
]