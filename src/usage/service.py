# -*- coding: utf-8 -*-
"""
使用次数服务

提供使用次数检查、扣减、匿名用户管理等核心业务逻辑
"""

import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from src.database.models import User, AnonymousUser
from src.database import crud
from src.config import settings


class UsageService:
    """使用次数服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_usage(
        self,
        user: Optional[User] = None,
        visitor_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tool_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        检查使用权限
        
        Args:
            user: 已登录用户（可选）
            visitor_id: 匿名用户设备指纹（可选）
            ip_address: 客户端 IP 地址（可选）
            tool_type: 工具类型（可选，用于权限检查）
        
        Returns:
            dict: {
                can_use: bool,
                source: str,  # paid / free / anonymous
                remaining: int,
                cache_type: str,  # premium / free
                cache_hours: int,
                message: str (optional)
            }
        """
        # 检查是否启用用户系统
        if not settings.FEATURE_USER_SYSTEM:
            # 未启用用户系统，所有人都可以使用
            return {
                "can_use": True,
                "source": "free",
                "remaining": 999999,
                "cache_type": "free",
                "cache_hours": settings.FREE_CACHE_HOURS,
            }
        
        # 已登录用户
        if user:
            return self._check_registered_user(user, tool_type)
        
        # 匿名用户
        if visitor_id and ip_address:
            return self._check_anonymous_user(visitor_id, ip_address, tool_type)
        
        # 未提供足够信息
        return {
            "can_use": False,
            "message": "请登录或提供访客标识",
        }
    
    def _check_registered_user(
        self,
        user: User,
        tool_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """检查已注册用户的使用权限"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # 付费用户有剩余次数
        if user.usage_count > 0:
            # 检查工具权限（如果指定了工具类型）
            if tool_type and not self._check_tool_access(tool_type, is_paid=True):
                return {
                    "can_use": False,
                    "message": f"工具 '{tool_type}' 暂不可用",
                }
            
            return {
                "can_use": True,
                "source": "paid",
                "remaining": user.usage_count,
                "cache_type": "premium",
                "cache_hours": settings.PREMIUM_CACHE_HOURS,
            }
        
        # 次数用尽，检查免费额度
        if user.free_usage_date != today:
            # 重置每日免费额度
            user.free_usage_date = today
            user.free_usage_count = 0
            self.db.commit()
        
        remaining = settings.FREE_DAILY_LIMIT - user.free_usage_count
        
        if remaining > 0:
            # 检查工具权限（免费用户只能使用基础工具）
            if tool_type and not self._check_tool_access(tool_type, is_paid=False):
                return {
                    "can_use": False,
                    "message": f"工具 '{tool_type}' 仅限付费用户使用",
                }
            
            return {
                "can_use": True,
                "source": "free",
                "remaining": remaining,
                "cache_type": "free",  # 付费用户次数用尽后，新数据使用免费缓存
                "cache_hours": settings.FREE_CACHE_HOURS,
            }
        
        return {
            "can_use": False,
            "message": "今日免费额度已用完，请充值使用次数",
        }
    
    def _check_anonymous_user(
        self,
        visitor_id: str,
        ip_address: str,
        tool_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """检查匿名用户的使用权限"""
        # 获取或创建匿名用户
        anonymous = self._get_or_create_anonymous(visitor_id, ip_address)
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # 重置每日额度
        if anonymous.free_usage_date != today:
            anonymous.free_usage_date = today
            anonymous.free_usage_count = 0
            anonymous.last_seen_at = datetime.utcnow()
            self.db.commit()
        
        remaining = settings.FREE_DAILY_LIMIT - anonymous.free_usage_count
        
        if remaining > 0:
            # 检查工具权限（匿名用户只能使用基础工具）
            if tool_type and not self._check_tool_access(tool_type, is_paid=False):
                return {
                    "can_use": False,
                    "message": f"工具 '{tool_type}' 仅限付费用户使用",
                }
            
            return {
                "can_use": True,
                "source": "anonymous",
                "remaining": remaining,
                "cache_type": "free",
                "cache_hours": 0,  # 匿名用户不缓存
            }
        
        return {
            "can_use": False,
            "message": "今日免费额度已用完，请登录获取更多功能",
        }
    
    def deduct_usage(
        self,
        user: Optional[User] = None,
        visitor_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        tool_type: Optional[str] = None,
        amount: int = 1,
    ) -> Dict[str, Any]:
        """
        扣减使用次数
        
        Returns:
            dict: {
                success: bool,
                source: str,
                remaining: int,
                cache_type: str,
                cache_expires_at: str (optional),
                message: str (optional)
            }
        """
        # 先检查权限
        check_result = self.check_usage(user, visitor_id, ip_address, tool_type)
        
        if not check_result.get("can_use"):
            return {
                "success": False,
                "message": check_result.get("message", "无使用权限"),
            }
        
        # 执行扣减
        if user:
            if check_result["source"] == "paid":
                user.usage_count -= amount
            else:
                user.free_usage_count += amount
            self.db.commit()
            remaining = user.usage_count if check_result["source"] == "paid" else settings.FREE_DAILY_LIMIT - user.free_usage_count
        else:
            anonymous = self._get_or_create_anonymous(visitor_id, ip_address)
            anonymous.free_usage_count += amount
            anonymous.last_seen_at = datetime.utcnow()
            self.db.commit()
            remaining = settings.FREE_DAILY_LIMIT - anonymous.free_usage_count
        
        # 计算缓存过期时间
        cache_expires_at = None
        if check_result["cache_hours"] > 0:
            cache_expires_at = datetime.utcnow() + timedelta(hours=check_result["cache_hours"])
        
        return {
            "success": True,
            "source": check_result["source"],
            "remaining": remaining,
            "cache_type": check_result["cache_type"],
            "cache_expires_at": cache_expires_at.isoformat() if cache_expires_at else None,
        }
    
    def get_balance(
        self,
        user: Optional[User] = None,
        visitor_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取使用次数余额
        
        Returns:
            dict: {
                user_type: str,  # paid / free / anonymous
                paid_count: int,
                free_remaining: int,
                free_limit: int,
                free_reset_at: str
            }
        """
        # 计算明天 0 点（免费次数重置时间）
        tomorrow = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # 已登录用户
        if user:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # 重置每日免费额度
            if user.free_usage_date != today:
                user.free_usage_date = today
                user.free_usage_count = 0
                self.db.commit()
            
            user_type = "paid" if user.usage_count > 0 else "free"
            free_remaining = settings.FREE_DAILY_LIMIT - user.free_usage_count
            
            return {
                "user_type": user_type,
                "paid_count": user.usage_count,
                "free_remaining": free_remaining,
                "free_limit": settings.FREE_DAILY_LIMIT,
                "free_reset_at": tomorrow.isoformat(),
            }
        
        # 匿名用户
        if visitor_id and ip_address:
            anonymous = self._get_or_create_anonymous(visitor_id, ip_address)
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # 重置每日免费额度
            if anonymous.free_usage_date != today:
                anonymous.free_usage_date = today
                anonymous.free_usage_count = 0
                anonymous.last_seen_at = datetime.utcnow()
                self.db.commit()
            
            free_remaining = settings.FREE_DAILY_LIMIT - anonymous.free_usage_count
            
            return {
                "user_type": "anonymous",
                "paid_count": 0,
                "free_remaining": free_remaining,
                "free_limit": settings.FREE_DAILY_LIMIT,
                "free_reset_at": tomorrow.isoformat(),
            }
        
        return {
            "user_type": "unknown",
            "paid_count": 0,
            "free_remaining": 0,
            "free_limit": settings.FREE_DAILY_LIMIT,
            "free_reset_at": tomorrow.isoformat(),
        }
    
    def register_anonymous(
        self,
        visitor_id: str,
        ip_address: str,
    ) -> Dict[str, Any]:
        """
        注册匿名用户
        
        Returns:
            dict: {
                anonymous_id: str,
                visitor_hash: str,
                free_remaining: int
            }
        """
        anonymous = self._get_or_create_anonymous(visitor_id, ip_address)
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        
        # 重置每日免费额度
        if anonymous.free_usage_date != today:
            anonymous.free_usage_date = today
            anonymous.free_usage_count = 0
            self.db.commit()
        
        free_remaining = settings.FREE_DAILY_LIMIT - anonymous.free_usage_count
        
        return {
            "anonymous_id": f"anon_{anonymous.id}",
            "visitor_hash": anonymous.visitor_hash[:16],
            "free_remaining": free_remaining,
        }
    
    def _get_or_create_anonymous(
        self,
        visitor_id: str,
        ip_address: str,
    ) -> AnonymousUser:
        """获取或创建匿名用户"""
        # 生成访客哈希
        visitor_hash = hashlib.sha256(f"{ip_address}:{visitor_id}".encode()).hexdigest()
        
        # 查找现有匿名用户
        anonymous = self.db.query(AnonymousUser).filter(
            AnonymousUser.visitor_hash == visitor_hash
        ).first()
        
        if not anonymous:
            # 创建新的匿名用户
            today = datetime.utcnow().strftime("%Y-%m-%d")
            anonymous = AnonymousUser(
                visitor_hash=visitor_hash,
                ip_address=ip_address,
                free_usage_date=today,
                free_usage_count=0,
            )
            self.db.add(anonymous)
            self.db.commit()
            self.db.refresh(anonymous)
        
        return anonymous
    
    def _check_tool_access(self, tool_type: str, is_paid: bool) -> bool:
        """
        检查工具访问权限
        
        Args:
            tool_type: 工具类型
            is_paid: 是否为付费用户
        
        Returns:
            bool: 是否有权限访问
        """
        # 付费用户可以使用所有工具
        if is_paid:
            return True
        
        # 免费用户只能使用免费工具
        free_tools = settings.FREE_TOOLS
        return tool_type in free_tools
    
    def _check_source_access(self, source_type: str, is_paid: bool) -> bool:
        """
        检查数据源访问权限
        
        Args:
            source_type: 数据源类型
            is_paid: 是否为付费用户
        
        Returns:
            bool: 是否有权限访问
        """
        # 付费用户可以使用所有数据源
        if is_paid:
            return True
        
        # 免费用户只能使用免费数据源
        free_sources = settings.FREE_SOURCES
        return source_type in free_sources