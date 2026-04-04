# -*- coding: utf-8 -*-
"""
监控模块

提供错误追踪、API 监控和告警功能
"""

from src.monitoring.error_tracker import (
    ErrorRecord,
    ErrorTracker,
    track_error,
)

from src.monitoring.api_monitor import (
    APIRequestLog,
    APIMonitorMiddleware,
    APIStatsService,
)

from src.monitoring.alert_service import (
    AlertRecord,
    AlertService,
    AlertRule,
    ErrorRateAlertRule,
    SlowRequestAlertRule,
    APIErrorAlertRule,
    log_notifier,
    webhook_notifier,
)

__all__ = [
    # 错误追踪
    "ErrorRecord",
    "ErrorTracker",
    "track_error",
    # API 监控
    "APIRequestLog",
    "APIMonitorMiddleware",
    "APIStatsService",
    # 告警
    "AlertRecord",
    "AlertService",
    "AlertRule",
    "ErrorRateAlertRule",
    "SlowRequestAlertRule",
    "APIErrorAlertRule",
    "log_notifier",
    "webhook_notifier",
]