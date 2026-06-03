# -*- coding: utf-8 -*-
"""
错误追踪模块

记录和管理应用错误，支持错误聚合和告警
"""

import logging
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import Base
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Index

logger = logging.getLogger(__name__)


# ============================================================================
# 错误记录模型
# ============================================================================

class ErrorRecord(Base):
    """
    错误记录表

    存储应用运行时的错误信息
    """
    __tablename__ = "error_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 错误基本信息
    error_type = Column(String(100), nullable=False, index=True)  # 错误类型
    error_message = Column(Text, nullable=False)  # 错误消息
    stack_trace = Column(Text, nullable=True)  # 堆栈跟踪
    
    # 请求上下文
    request_path = Column(String(500), nullable=True, index=True)  # 请求路径
    request_method = Column(String(10), nullable=True)  # 请求方法
    user_id = Column(Integer, nullable=True, index=True)  # 用户ID
    
    # 错误分类
    category = Column(String(50), nullable=True, index=True)  # 错误分类
    severity = Column(String(20), default="error", nullable=False)  # 严重程度: debug, info, warning, error, critical
    
    # 状态
    is_resolved = Column(Boolean, default=False, nullable=False)  # 是否已解决
    resolved_at = Column(DateTime, nullable=True)  # 解决时间
    resolved_by = Column(Integer, nullable=True)  # 解决人
    
    # 聚合信息
    fingerprint = Column(String(64), nullable=True, index=True)  # 错误指纹（用于聚合）
    occurrence_count = Column(Integer, default=1, nullable=False)  # 出现次数
    last_occurred_at = Column(DateTime, default=datetime.utcnow, nullable=False)  # 最后出现时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # 额外数据
    extra_data = Column(Text, nullable=True)  # JSON 格式的额外数据

    __table_args__ = (
        Index("idx_error_created_at", "created_at"),
        Index("idx_error_type_resolved", "error_type", "is_resolved"),
        Index("idx_error_fingerprint", "fingerprint"),
    )

    def __repr__(self):
        return f"<ErrorRecord(id={self.id}, type='{self.error_type}', severity='{self.severity}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "request_path": self.request_path,
            "request_method": self.request_method,
            "user_id": self.user_id,
            "category": self.category,
            "severity": self.severity,
            "is_resolved": self.is_resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "fingerprint": self.fingerprint,
            "occurrence_count": self.occurrence_count,
            "last_occurred_at": self.last_occurred_at.isoformat() if self.last_occurred_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 错误追踪服务
# ============================================================================

class ErrorTracker:
    """错误追踪服务"""
    
    # 错误分类映射
    CATEGORY_MAP = {
        "ConnectionError": "network",
        "TimeoutError": "network",
        "HTTPError": "api",
        "ValueError": "validation",
        "KeyError": "data",
        "TypeError": "code",
        "AttributeError": "code",
        "IntegrityError": "database",
        "OperationalError": "database",
    }
    
    # 严重程度映射
    SEVERITY_MAP = {
        500: "critical",  # 服务器错误
        429: "warning",   # 限流
        403: "warning",   # 权限
        401: "info",      # 认证
        404: "info",      # 未找到
        400: "warning",   # 请求错误
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_error(
        self,
        error: Exception,
        request_path: Optional[str] = None,
        request_method: Optional[str] = None,
        user_id: Optional[int] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> ErrorRecord:
        """
        记录错误
        
        Args:
            error: 异常对象
            request_path: 请求路径
            request_method: 请求方法
            user_id: 用户ID
            extra_data: 额外数据
        
        Returns:
            ErrorRecord 实例
        """
        import hashlib
        import json
        
        # 获取错误信息
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # 生成错误指纹（用于聚合相同错误）
        fingerprint_data = f"{error_type}:{error_message}:{request_path}"
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        # 分类错误
        category = self._categorize_error(error_type)
        severity = self._determine_severity(error)
        
        # 检查是否存在相同指纹的错误
        existing = self.db.query(ErrorRecord).filter(
            ErrorRecord.fingerprint == fingerprint,
            ErrorRecord.is_resolved == False
        ).first()
        
        if existing:
            # 更新现有记录
            existing.occurrence_count += 1
            existing.last_occurred_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"错误聚合: {error_type} 出现次数 {existing.occurrence_count}")
            return existing
        
        # 创建新记录
        record = ErrorRecord(
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            request_path=request_path,
            request_method=request_method,
            user_id=user_id,
            category=category,
            severity=severity,
            fingerprint=fingerprint,
            extra_data=json.dumps(extra_data) if extra_data else None,
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.warning(f"新错误记录: {error_type} - {error_message[:100]}")
        
        return record
    
    def _categorize_error(self, error_type: str) -> str:
        """分类错误"""
        return self.CATEGORY_MAP.get(error_type, "unknown")
    
    def _determine_severity(self, error: Exception) -> str:
        """确定错误严重程度"""
        # 如果有状态码属性
        if hasattr(error, 'status_code'):
            return self.SEVERITY_MAP.get(error.status_code, "error")
        return "error"
    
    def get_errors(
        self,
        is_resolved: Optional[bool] = None,
        severity: Optional[str] = None,
        category: Optional[str] = None,
        hours: int = 24,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """
        获取错误列表
        
        Args:
            is_resolved: 是否已解决
            severity: 严重程度
            category: 分类
            hours: 时间范围（小时）
            skip: 跳过数量
            limit: 返回数量
        
        Returns:
            (errors, total) 元组
        """
        query = self.db.query(ErrorRecord)
        
        # 时间过滤
        if hours > 0:
            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.filter(ErrorRecord.created_at >= since)
        
        # 状态过滤
        if is_resolved is not None:
            query = query.filter(ErrorRecord.is_resolved == is_resolved)
        
        # 严重程度过滤
        if severity:
            query = query.filter(ErrorRecord.severity == severity)
        
        # 分类过滤
        if category:
            query = query.filter(ErrorRecord.category == category)
        
        # 排序和分页
        query = query.order_by(desc(ErrorRecord.last_occurred_at))
        total = query.count()
        errors = query.offset(skip).limit(limit).all()
        
        return errors, total
    
    def resolve_error(self, error_id: int, resolved_by: Optional[int] = None) -> bool:
        """
        标记错误为已解决
        
        Args:
            error_id: 错误ID
            resolved_by: 解决人ID
        
        Returns:
            是否成功
        """
        record = self.db.query(ErrorRecord).filter(
            ErrorRecord.id == error_id
        ).first()
        
        if not record:
            return False
        
        record.is_resolved = True
        record.resolved_at = datetime.utcnow()
        record.resolved_by = resolved_by
        
        self.db.commit()
        return True
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取错误统计
        
        Args:
            hours: 时间范围（小时）
        
        Returns:
            统计数据字典
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # 总错误数
        total = self.db.query(ErrorRecord).filter(
            ErrorRecord.created_at >= since
        ).count()
        
        # 未解决错误数
        unresolved = self.db.query(ErrorRecord).filter(
            ErrorRecord.created_at >= since,
            ErrorRecord.is_resolved == False
        ).count()
        
        # 按严重程度分组
        by_severity = {}
        for severity in ["critical", "error", "warning", "info"]:
            count = self.db.query(ErrorRecord).filter(
                ErrorRecord.created_at >= since,
                ErrorRecord.severity == severity
            ).count()
            by_severity[severity] = count
        
        # 按分类分组
        by_category = {}
        for category in ["network", "api", "database", "code", "validation", "data", "unknown"]:
            count = self.db.query(ErrorRecord).filter(
                ErrorRecord.created_at >= since,
                ErrorRecord.category == category
            ).count()
            if count > 0:
                by_category[category] = count
        
        return {
            "total": total,
            "unresolved": unresolved,
            "resolved": total - unresolved,
            "by_severity": by_severity,
            "by_category": by_category,
            "hours": hours,
        }
    
    def cleanup_old_errors(self, days: int = 30) -> int:
        """
        清理旧错误记录
        
        Args:
            days: 保留天数
        
        Returns:
            删除的记录数
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # 只删除已解决的旧错误
        result = self.db.query(ErrorRecord).filter(
            ErrorRecord.created_at < cutoff,
            ErrorRecord.is_resolved == True
        ).delete()
        
        self.db.commit()
        logger.info(f"清理了 {result} 条旧错误记录")
        return result


# ============================================================================
# 便捷函数
# ============================================================================

def track_error(
    db: Session,
    error: Exception,
    request_path: Optional[str] = None,
    request_method: Optional[str] = None,
    user_id: Optional[int] = None,
    extra_data: Optional[Dict[str, Any]] = None,
) -> Optional[ErrorRecord]:
    """
    便捷函数：记录错误
    
    Args:
        db: 数据库会话
        error: 异常对象
        request_path: 请求路径
        request_method: 请求方法
        user_id: 用户ID
        extra_data: 额外数据
    
    Returns:
        ErrorRecord 实例，失败返回 None
    """
    try:
        tracker = ErrorTracker(db)
        return tracker.record_error(
            error=error,
            request_path=request_path,
            request_method=request_method,
            user_id=user_id,
            extra_data=extra_data,
        )
    except Exception as e:
        logger.error(f"记录错误失败: {e}")
        return None