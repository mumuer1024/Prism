# -*- coding: utf-8 -*-
"""
API 监控中间件

记录 API 请求和响应，监控性能和错误
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.database.models import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index

logger = logging.getLogger(__name__)


# ============================================================================
# API 请求记录模型
# ============================================================================

class APIRequestLog(Base):
    """
    API 请求日志表

    记录所有 API 请求的详细信息
    """
    __tablename__ = "api_request_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 请求信息
    request_path = Column(String(500), nullable=False, index=True)
    request_method = Column(String(10), nullable=False)
    query_params = Column(Text, nullable=True)  # 查询参数
    request_body = Column(Text, nullable=True)  # 请求体（可选）
    
    # 响应信息
    response_status = Column(Integer, nullable=False, index=True)
    response_time_ms = Column(Float, nullable=False)  # 响应时间（毫秒）
    response_size = Column(Integer, nullable=True)  # 响应大小（字节）
    
    # 用户信息
    user_id = Column(Integer, nullable=True, index=True)
    client_ip = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # 错误信息
    error_message = Column(Text, nullable=True)
    error_type = Column(String(100), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_api_log_path_status", "request_path", "response_status"),
        Index("idx_api_log_created_at", "created_at"),
        Index("idx_api_log_user_id", "user_id"),
    )

    def __repr__(self):
        return f"<APIRequestLog(id={self.id}, path='{self.request_path}', status={self.response_status})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "request_path": self.request_path,
            "request_method": self.request_method,
            "query_params": self.query_params,
            "response_status": self.response_status,
            "response_time_ms": round(self.response_time_ms, 2),
            "response_size": self.response_size,
            "user_id": self.user_id,
            "client_ip": self.client_ip,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# API 监控中间件
# ============================================================================

class APIMonitorMiddleware(BaseHTTPMiddleware):
    """
    API 监控中间件
    
    功能：
    - 记录所有 API 请求
    - 监控响应时间
    - 记录错误信息
    - 支持慢请求告警
    """
    
    # 不记录的路径（前缀匹配）
    EXCLUDED_PATHS = [
        "/static",
        "/favicon",
        "/health",
        "/metrics",
    ]
    
    # 慢请求阈值（毫秒）
    SLOW_REQUEST_THRESHOLD = 3000
    
    # 敏感字段（不记录）
    SENSITIVE_FIELDS = ["password", "token", "secret", "api_key", "authorization"]
    
    def __init__(self, app, db_session_factory: Callable):
        super().__init__(app)
        self.db_session_factory = db_session_factory
    
    async def dispatch(self, request: Request, call_next):
        """处理请求"""
        # 检查是否排除的路径
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.EXCLUDED_PATHS):
            return await call_next(request)
        
        # 记录开始时间
        start_time = time.time()
        
        # 提取请求信息
        request_method = request.method
        query_params = str(request.query_params) if request.query_params else None
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")[:500]
        user_id = self._extract_user_id(request)
        
        # 初始化响应变量
        response = None
        error_message = None
        error_type = None
        
        try:
            # 调用下一个中间件/路由
            response = await call_next(request)
            return response
        except Exception as e:
            # 记录错误
            error_message = str(e)
            error_type = type(e).__name__
            raise
        finally:
            # 计算响应时间
            response_time_ms = (time.time() - start_time) * 1000
            
            # 获取响应状态
            response_status = response.status_code if response else 500
            
            # 记录请求日志
            try:
                self._save_log(
                    request_path=path,
                    request_method=request_method,
                    query_params=query_params,
                    response_status=response_status,
                    response_time_ms=response_time_ms,
                    user_id=user_id,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    error_message=error_message,
                    error_type=error_type,
                )
            except Exception as e:
                logger.error(f"保存 API 日志失败: {e}")
            
            # 慢请求告警
            if response_time_ms > self.SLOW_REQUEST_THRESHOLD:
                logger.warning(
                    f"慢请求告警: {request_method} {path} "
                    f"耗时 {response_time_ms:.0f}ms"
                )
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端 IP"""
        # 尝试从代理头获取
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # 直接获取
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _extract_user_id(self, request: Request) -> Optional[int]:
        """从请求中提取用户 ID"""
        # 从 state 中获取（如果已认证）
        if hasattr(request.state, "user_id"):
            return request.state.user_id
        
        # 从 Authorization 头解析（简化版）
        # 实际应该通过 JWT 解析
        return None
    
    def _save_log(
        self,
        request_path: str,
        request_method: str,
        query_params: Optional[str],
        response_status: int,
        response_time_ms: float,
        user_id: Optional[int],
        client_ip: str,
        user_agent: str,
        error_message: Optional[str],
        error_type: Optional[str],
    ):
        """保存请求日志"""
        from src.database.connection import get_db_context
        
        with get_db_context() as db:
            log = APIRequestLog(
                request_path=request_path,
                request_method=request_method,
                query_params=query_params,
                response_status=response_status,
                response_time_ms=response_time_ms,
                user_id=user_id,
                client_ip=client_ip,
                user_agent=user_agent,
                error_message=error_message,
                error_type=error_type,
            )
            db.add(log)
            db.commit()


# ============================================================================
# API 统计服务
# ============================================================================

class APIStatsService:
    """API 统计服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """
        获取 API 统计
        
        Args:
            hours: 时间范围（小时）
        
        Returns:
            统计数据字典
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # 总请求数
        total = self.db.query(APIRequestLog).filter(
            APIRequestLog.created_at >= since
        ).count()
        
        # 成功请求数（2xx, 3xx）
        success = self.db.query(APIRequestLog).filter(
            APIRequestLog.created_at >= since,
            APIRequestLog.response_status < 400
        ).count()
        
        # 错误请求数（4xx, 5xx）
        errors = total - success
        
        # 平均响应时间
        avg_response_time = self.db.query(
            func.avg(APIRequestLog.response_time_ms)
        ).filter(
            APIRequestLog.created_at >= since
        ).scalar() or 0
        
        # 慢请求数
        slow_requests = self.db.query(APIRequestLog).filter(
            APIRequestLog.created_at >= since,
            APIRequestLog.response_time_ms > 3000
        ).count()
        
        # 按状态码分组
        by_status = {}
        for status_range in ["2xx", "3xx", "4xx", "5xx"]:
            if status_range == "2xx":
                count = self.db.query(APIRequestLog).filter(
                    APIRequestLog.created_at >= since,
                    APIRequestLog.response_status >= 200,
                    APIRequestLog.response_status < 300
                ).count()
            elif status_range == "3xx":
                count = self.db.query(APIRequestLog).filter(
                    APIRequestLog.created_at >= since,
                    APIRequestLog.response_status >= 300,
                    APIRequestLog.response_status < 400
                ).count()
            elif status_range == "4xx":
                count = self.db.query(APIRequestLog).filter(
                    APIRequestLog.created_at >= since,
                    APIRequestLog.response_status >= 400,
                    APIRequestLog.response_status < 500
                ).count()
            else:  # 5xx
                count = self.db.query(APIRequestLog).filter(
                    APIRequestLog.created_at >= since,
                    APIRequestLog.response_status >= 500
                ).count()
            by_status[status_range] = count
        
        # Top 端点
        top_endpoints = self._get_top_endpoints(since, limit=10)
        
        return {
            "total": total,
            "success": success,
            "errors": errors,
            "success_rate": round(success / total * 100, 2) if total > 0 else 0,
            "avg_response_time_ms": round(avg_response_time, 2),
            "slow_requests": slow_requests,
            "by_status": by_status,
            "top_endpoints": top_endpoints,
            "hours": hours,
        }
    
    def _get_top_endpoints(self, since: datetime, limit: int = 10) -> list:
        """获取热门端点"""
        from sqlalchemy import func
        
        results = self.db.query(
            APIRequestLog.request_path,
            func.count(APIRequestLog.id).label("count"),
            func.avg(APIRequestLog.response_time_ms).label("avg_time"),
        ).filter(
            APIRequestLog.created_at >= since
        ).group_by(
            APIRequestLog.request_path
        ).order_by(
            desc("count")
        ).limit(limit).all()
        
        return [
            {
                "path": r.request_path,
                "count": r.count,
                "avg_time_ms": round(r.avg_time, 2),
            }
            for r in results
        ]
    
    def get_slow_requests(
        self,
        hours: int = 24,
        threshold_ms: float = 3000,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple:
        """
        获取慢请求列表
        
        Args:
            hours: 时间范围（小时）
            threshold_ms: 慢请求阈值（毫秒）
            skip: 跳过数量
            limit: 返回数量
        
        Returns:
            (logs, total) 元组
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = self.db.query(APIRequestLog).filter(
            APIRequestLog.created_at >= since,
            APIRequestLog.response_time_ms > threshold_ms
        ).order_by(desc(APIRequestLog.response_time_ms))
        
        total = query.count()
        logs = query.offset(skip).limit(limit).all()
        
        return logs, total
    
    def cleanup_old_logs(self, days: int = 7) -> int:
        """
        清理旧日志
        
        Args:
            days: 保留天数
        
        Returns:
            删除的记录数
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        result = self.db.query(APIRequestLog).filter(
            APIRequestLog.created_at < cutoff
        ).delete()
        
        self.db.commit()
        logger.info(f"清理了 {result} 条旧 API 日志")
        return result


# 导入 func 用于聚合查询
from sqlalchemy import func