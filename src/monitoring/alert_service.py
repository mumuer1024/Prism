# -*- coding: utf-8 -*-
"""
告警机制

支持多种告警渠道和告警规则
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index

logger = logging.getLogger(__name__)


# ============================================================================
# 告警记录模型
# ============================================================================

class AlertRecord(Base):
    """
    告警记录表

    存储所有告警事件
    """
    __tablename__ = "alert_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 告警信息
    alert_type = Column(String(50), nullable=False, index=True)  # 告警类型
    alert_level = Column(String(20), nullable=False, index=True)  # 告警级别: info, warning, critical
    title = Column(String(255), nullable=False)  # 告警标题
    message = Column(Text, nullable=False)  # 告警消息
    
    # 来源信息
    source = Column(String(100), nullable=True)  # 告警来源
    source_id = Column(Integer, nullable=True)  # 来源ID（如错误ID）
    
    # 状态
    is_acknowledged = Column(Boolean, default=False, nullable=False)  # 是否已确认
    acknowledged_at = Column(DateTime, nullable=True)  # 确认时间
    acknowledged_by = Column(Integer, nullable=True)  # 确认人
    
    is_resolved = Column(Boolean, default=False, nullable=False)  # 是否已解决
    resolved_at = Column(DateTime, nullable=True)  # 解决时间
    resolved_by = Column(Integer, nullable=True)  # 解决人
    
    # 通知状态
    notification_sent = Column(Boolean, default=False, nullable=False)  # 是否已发送通知
    notification_channels = Column(String(255), nullable=True)  # 通知渠道（逗号分隔）
    notification_error = Column(Text, nullable=True)  # 通知错误信息
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 额外数据
    extra_data = Column(Text, nullable=True)  # JSON 格式的额外数据

    __table_args__ = (
        Index("idx_alert_type_level", "alert_type", "alert_level"),
        Index("idx_alert_created_at", "created_at"),
        Index("idx_alert_resolved", "is_resolved"),
    )

    def __repr__(self):
        return f"<AlertRecord(id={self.id}, type='{self.alert_type}', level='{self.alert_level}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "alert_type": self.alert_type,
            "alert_level": self.alert_level,
            "title": self.title,
            "message": self.message,
            "source": self.source,
            "source_id": self.source_id,
            "is_acknowledged": self.is_acknowledged,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "is_resolved": self.is_resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "notification_sent": self.notification_sent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 告警规则
# ============================================================================

class AlertRule:
    """告警规则基类"""
    
    rule_type: str = "base"
    rule_name: str = "基础规则"
    
    def __init__(self, db: Session, config: Dict[str, Any] = None):
        self.db = db
        self.config = config or {}
    
    def check(self) -> Optional[Dict[str, Any]]:
        """
        检查是否触发告警
        
        Returns:
            如果触发告警，返回告警信息字典；否则返回 None
        """
        raise NotImplementedError
    
    def _create_alert(
        self,
        title: str,
        message: str,
        alert_level: str = "warning",
        source: str = None,
        source_id: int = None,
        extra_data: Dict = None,
    ) -> AlertRecord:
        """创建告警记录"""
        alert = AlertRecord(
            alert_type=self.rule_type,
            alert_level=alert_level,
            title=title,
            message=message,
            source=source or self.rule_type,
            source_id=source_id,
            extra_data=json.dumps(extra_data) if extra_data else None,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        logger.warning(f"告警触发: [{alert_level}] {title}")
        return alert


class ErrorRateAlertRule(AlertRule):
    """错误率告警规则"""
    
    rule_type = "error_rate"
    rule_name = "错误率告警"
    
    def __init__(self, db: Session, config: Dict[str, Any] = None):
        super().__init__(db, config)
        self.threshold = config.get("threshold", 10)  # 错误数量阈值
        self.window_minutes = config.get("window_minutes", 5)  # 时间窗口（分钟）
    
    def check(self) -> Optional[Dict[str, Any]]:
        """检查错误率"""
        from src.monitoring.error_tracker import ErrorRecord
        
        since = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        
        # 统计未解决的错误数量
        error_count = self.db.query(ErrorRecord).filter(
            ErrorRecord.created_at >= since,
            ErrorRecord.is_resolved == False
        ).count()
        
        if error_count >= self.threshold:
            return self._create_alert(
                title=f"错误率过高: {error_count} 个错误",
                message=f"在过去 {self.window_minutes} 分钟内检测到 {error_count} 个未解决的错误，超过阈值 {self.threshold}",
                alert_level="critical" if error_count >= self.threshold * 2 else "warning",
                extra_data={"error_count": error_count, "threshold": self.threshold},
            ).to_dict()
        
        return None


class SlowRequestAlertRule(AlertRule):
    """慢请求告警规则"""
    
    rule_type = "slow_request"
    rule_name = "慢请求告警"
    
    def __init__(self, db: Session, config: Dict[str, Any] = None):
        super().__init__(db, config)
        self.threshold = config.get("threshold", 5)  # 慢请求数量阈值
        self.response_time_threshold = config.get("response_time_threshold", 3000)  # 响应时间阈值（毫秒）
        self.window_minutes = config.get("window_minutes", 5)  # 时间窗口（分钟）
    
    def check(self) -> Optional[Dict[str, Any]]:
        """检查慢请求"""
        from src.monitoring.api_monitor import APIRequestLog
        
        since = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        
        # 统计慢请求数量
        slow_count = self.db.query(APIRequestLog).filter(
            APIRequestLog.created_at >= since,
            APIRequestLog.response_time_ms > self.response_time_threshold
        ).count()
        
        if slow_count >= self.threshold:
            return self._create_alert(
                title=f"慢请求过多: {slow_count} 个",
                message=f"在过去 {self.window_minutes} 分钟内检测到 {slow_count} 个慢请求（>{self.response_time_threshold}ms），超过阈值 {self.threshold}",
                alert_level="warning",
                extra_data={"slow_count": slow_count, "threshold": self.threshold},
            ).to_dict()
        
        return None


class APIErrorAlertRule(AlertRule):
    """API 错误告警规则"""
    
    rule_type = "api_error"
    rule_name = "API 错误告警"
    
    def __init__(self, db: Session, config: Dict[str, Any] = None):
        super().__init__(db, config)
        self.threshold = config.get("threshold", 10)  # 错误数量阈值
        self.window_minutes = config.get("window_minutes", 5)  # 时间窗口（分钟）
    
    def check(self) -> Optional[Dict[str, Any]]:
        """检查 API 错误"""
        from src.monitoring.api_monitor import APIRequestLog
        
        since = datetime.utcnow() - timedelta(minutes=self.window_minutes)
        
        # 统计 5xx 错误数量
        error_count = self.db.query(APIRequestLog).filter(
            APIRequestLog.created_at >= since,
            APIRequestLog.response_status >= 500
        ).count()
        
        if error_count >= self.threshold:
            return self._create_alert(
                title=f"API 错误过多: {error_count} 个 5xx 错误",
                message=f"在过去 {self.window_minutes} 分钟内检测到 {error_count} 个 5xx 错误，超过阈值 {self.threshold}",
                alert_level="critical",
                extra_data={"error_count": error_count, "threshold": self.threshold},
            ).to_dict()
        
        return None


# ============================================================================
# 告警服务
# ============================================================================

class AlertService:
    """告警服务"""
    
    # 内置规则
    BUILTIN_RULES = {
        "error_rate": ErrorRateAlertRule,
        "slow_request": SlowRequestAlertRule,
        "api_error": APIErrorAlertRule,
    }
    
    def __init__(self, db: Session):
        self.db = db
        self.rules: Dict[str, AlertRule] = {}
        self.notifiers: List[Callable] = []
        
        # 初始化默认规则
        self._init_default_rules()
    
    def _init_default_rules(self):
        """初始化默认规则"""
        for rule_type, rule_class in self.BUILTIN_RULES.items():
            self.rules[rule_type] = rule_class(self.db)
    
    def add_rule(self, rule_type: str, config: Dict[str, Any] = None):
        """添加或更新规则"""
        if rule_type in self.BUILTIN_RULES:
            self.rules[rule_type] = self.BUILTIN_RULES[rule_type](self.db, config)
        else:
            logger.warning(f"未知的告警规则类型: {rule_type}")
    
    def add_notifier(self, notifier: Callable):
        """添加通知器"""
        self.notifiers.append(notifier)
    
    def check_all_rules(self) -> List[Dict[str, Any]]:
        """
        检查所有规则
        
        Returns:
            触发的告警列表
        """
        alerts = []
        
        for rule_type, rule in self.rules.items():
            try:
                result = rule.check()
                if result:
                    alerts.append(result)
                    
                    # 发送通知
                    self._send_notification(result)
            except Exception as e:
                logger.error(f"检查规则 {rule_type} 失败: {e}")
        
        return alerts
    
    def _send_notification(self, alert: Dict[str, Any]):
        """发送通知"""
        for notifier in self.notifiers:
            try:
                notifier(alert)
            except Exception as e:
                logger.error(f"发送通知失败: {e}")
    
    def get_alerts(
        self,
        is_resolved: Optional[bool] = None,
        alert_level: Optional[str] = None,
        alert_type: Optional[str] = None,
        hours: int = 24,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """
        获取告警列表
        
        Args:
            is_resolved: 是否已解决
            alert_level: 告警级别
            alert_type: 告警类型
            hours: 时间范围（小时）
            skip: 跳过数量
            limit: 返回数量
        
        Returns:
            (alerts, total) 元组
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(AlertRecord).filter(
            AlertRecord.created_at >= since
        )
        
        if is_resolved is not None:
            query = query.filter(AlertRecord.is_resolved == is_resolved)
        
        if alert_level:
            query = query.filter(AlertRecord.alert_level == alert_level)
        
        if alert_type:
            query = query.filter(AlertRecord.alert_type == alert_type)
        
        query = query.order_by(desc(AlertRecord.created_at))
        total = query.count()
        alerts = query.offset(skip).limit(limit).all()
        
        return alerts, total
    
    def acknowledge_alert(self, alert_id: int, acknowledged_by: Optional[int] = None) -> bool:
        """确认告警"""
        alert = self.db.query(AlertRecord).filter(
            AlertRecord.id == alert_id
        ).first()
        
        if not alert:
            return False
        
        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        
        self.db.commit()
        return True
    
    def resolve_alert(self, alert_id: int, resolved_by: Optional[int] = None) -> bool:
        """解决告警"""
        alert = self.db.query(AlertRecord).filter(
            AlertRecord.id == alert_id
        ).first()
        
        if not alert:
            return False
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = resolved_by
        
        self.db.commit()
        return True
    
    def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """获取告警统计"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # 总告警数
        total = self.db.query(AlertRecord).filter(
            AlertRecord.created_at >= since
        ).count()
        
        # 未解决告警数
        unresolved = self.db.query(AlertRecord).filter(
            AlertRecord.created_at >= since,
            AlertRecord.is_resolved == False
        ).count()
        
        # 按级别分组
        by_level = {}
        for level in ["critical", "warning", "info"]:
            count = self.db.query(AlertRecord).filter(
                AlertRecord.created_at >= since,
                AlertRecord.alert_level == level
            ).count()
            by_level[level] = count
        
        # 按类型分组
        by_type = {}
        for alert_type in self.BUILTIN_RULES.keys():
            count = self.db.query(AlertRecord).filter(
                AlertRecord.created_at >= since,
                AlertRecord.alert_type == alert_type
            ).count()
            if count > 0:
                by_type[alert_type] = count
        
        return {
            "total": total,
            "unresolved": unresolved,
            "resolved": total - unresolved,
            "by_level": by_level,
            "by_type": by_type,
            "hours": hours,
        }


# ============================================================================
# 通知器
# ============================================================================

def log_notifier(alert: Dict[str, Any]):
    """日志通知器"""
    level = alert.get("alert_level", "warning")
    title = alert.get("title", "未知告警")
    message = alert.get("message", "")
    
    if level == "critical":
        logger.critical(f"[告警] {title}: {message}")
    elif level == "warning":
        logger.warning(f"[告警] {title}: {message}")
    else:
        logger.info(f"[告警] {title}: {message}")


def webhook_notifier(webhook_url: str):
    """Webhook 通知器工厂函数"""
    import requests
    
    def notifier(alert: Dict[str, Any]):
        try:
            payload = {
                "alert_type": alert.get("alert_type"),
                "alert_level": alert.get("alert_level"),
                "title": alert.get("title"),
                "message": alert.get("message"),
                "created_at": alert.get("created_at"),
            }
            requests.post(webhook_url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"Webhook 通知失败: {e}")
    
    return notifier