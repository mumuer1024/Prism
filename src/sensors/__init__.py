# -*- coding: utf-8 -*-
"""
数据源传感器模块

包含所有数据源采集器：
- V2EX 雷达（带镜像支持）
- 自定义数据源采集器
- 数据源健康检测
"""

from src.sensors.v2ex_radar import (
    V2EXRadar,
    MirrorTracker,
    MirrorStatus,
    MirrorStats,
    Lead,
    fetch_v2ex_leads,
    get_radar,
    V2EX_MIRROR_ENABLED,
)

from src.sensors.custom_source import (
    CustomSourceSensor,
    CustomSourceItem,
    fetch_custom_rss,
    fetch_custom_webpage,
    fetch_user_custom_sources,
    CUSTOM_SOURCE_ENABLED,
)

from src.sensors.source_health import (
    SourceHealthChecker,
    SourceHealthResult,
    HealthStatus,
    check_sources_health,
    check_single_source,
    create_health_router,
)

__all__ = [
    # V2EX 雷达
    "V2EXRadar",
    "MirrorTracker",
    "MirrorStatus",
    "MirrorStats",
    "Lead",
    "fetch_v2ex_leads",
    "get_radar",
    "V2EX_MIRROR_ENABLED",

    # 自定义数据源
    "CustomSourceSensor",
    "CustomSourceItem",
    "fetch_custom_rss",
    "fetch_custom_webpage",
    "fetch_user_custom_sources",
    "CUSTOM_SOURCE_ENABLED",

    # 健康检测
    "SourceHealthChecker",
    "SourceHealthResult",
    "HealthStatus",
    "check_sources_health",
    "check_single_source",
    "create_health_router",
]