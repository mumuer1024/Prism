# -*- coding: utf-8 -*-
"""
监控 API 路由

提供错误追踪、API 监控和告警的管理接口
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.auth.dependencies import get_current_user, get_admin_user
from src.database.models import User
from src.monitoring.error_tracker import ErrorTracker
from src.monitoring.api_monitor import APIStatsService
from src.monitoring.alert_service import AlertService

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# 错误追踪 API
# ============================================================================

@router.get("/errors", summary="获取错误列表")
def get_errors(
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    severity: Optional[str] = Query(None, description="严重程度"),
    category: Optional[str] = Query(None, description="分类"),
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取错误列表（管理员）"""
    tracker = ErrorTracker(db)
    errors, total = tracker.get_errors(
        is_resolved=is_resolved,
        severity=severity,
        category=category,
        hours=hours,
        skip=skip,
        limit=limit,
    )
    
    return {
        "errors": [e.to_dict() for e in errors],
        "total": total,
    }


@router.get("/errors/stats", summary="获取错误统计")
def get_error_stats(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取错误统计（管理员）"""
    tracker = ErrorTracker(db)
    stats = tracker.get_error_stats(hours=hours)
    return stats


@router.post("/errors/{error_id}/resolve", summary="标记错误为已解决")
def resolve_error(
    error_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """标记错误为已解决（管理员）"""
    tracker = ErrorTracker(db)
    success = tracker.resolve_error(error_id, resolved_by=current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="错误记录不存在")
    
    return {"success": True, "message": "已标记为已解决"}


# ============================================================================
# API 监控 API
# ============================================================================

@router.get("/api-stats", summary="获取 API 统计")
def get_api_stats(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取 API 统计（管理员）"""
    service = APIStatsService(db)
    stats = service.get_stats(hours=hours)
    return stats


@router.get("/api-stats/slow-requests", summary="获取慢请求列表")
def get_slow_requests(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    threshold_ms: float = Query(3000, ge=100, description="慢请求阈值（毫秒）"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取慢请求列表（管理员）"""
    service = APIStatsService(db)
    logs, total = service.get_slow_requests(
        hours=hours,
        threshold_ms=threshold_ms,
        skip=skip,
        limit=limit,
    )
    
    return {
        "logs": [log.to_dict() for log in logs],
        "total": total,
    }


# ============================================================================
# 告警 API
# ============================================================================

@router.get("/alerts", summary="获取告警列表")
def get_alerts(
    is_resolved: Optional[bool] = Query(None, description="是否已解决"),
    alert_level: Optional[str] = Query(None, description="告警级别"),
    alert_type: Optional[str] = Query(None, description="告警类型"),
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取告警列表（管理员）"""
    service = AlertService(db)
    alerts, total = service.get_alerts(
        is_resolved=is_resolved,
        alert_level=alert_level,
        alert_type=alert_type,
        hours=hours,
        skip=skip,
        limit=limit,
    )
    
    return {
        "alerts": [a.to_dict() for a in alerts],
        "total": total,
    }


@router.get("/alerts/stats", summary="获取告警统计")
def get_alert_stats(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取告警统计（管理员）"""
    service = AlertService(db)
    stats = service.get_alert_stats(hours=hours)
    return stats


@router.post("/alerts/check", summary="手动检查告警规则")
def check_alerts(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """手动检查告警规则（管理员）"""
    service = AlertService(db)
    alerts = service.check_all_rules()
    
    return {
        "triggered": len(alerts),
        "alerts": alerts,
    }


@router.post("/alerts/{alert_id}/acknowledge", summary="确认告警")
def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """确认告警（管理员）"""
    service = AlertService(db)
    success = service.acknowledge_alert(alert_id, acknowledged_by=current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="告警记录不存在")
    
    return {"success": True, "message": "已确认告警"}


@router.post("/alerts/{alert_id}/resolve", summary="解决告警")
def resolve_alert(
    alert_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """解决告警（管理员）"""
    service = AlertService(db)
    success = service.resolve_alert(alert_id, resolved_by=current_user.id)
    
    if not success:
        raise HTTPException(status_code=404, detail="告警记录不存在")
    
    return {"success": True, "message": "已解决告警"}


# ============================================================================
# 综合监控面板 API
# ============================================================================

@router.get("/dashboard", summary="获取监控面板数据")
def get_dashboard(
    hours: int = Query(24, ge=1, le=168, description="时间范围（小时）"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """获取监控面板数据（管理员）"""
    # 获取各类统计
    error_tracker = ErrorTracker(db)
    api_service = APIStatsService(db)
    alert_service = AlertService(db)
    
    error_stats = error_tracker.get_error_stats(hours=hours)
    api_stats = api_service.get_stats(hours=hours)
    alert_stats = alert_service.get_alert_stats(hours=hours)
    
    # 获取最近的未解决告警
    recent_alerts, _ = alert_service.get_alerts(
        is_resolved=False,
        limit=5,
    )
    
    # 获取最近的未解决错误
    recent_errors, _ = error_tracker.get_errors(
        is_resolved=False,
        limit=5,
    )
    
    return {
        "error_stats": error_stats,
        "api_stats": api_stats,
        "alert_stats": alert_stats,
        "recent_alerts": [a.to_dict() for a in recent_alerts],
        "recent_errors": [e.to_dict() for e in recent_errors],
        "hours": hours,
    }