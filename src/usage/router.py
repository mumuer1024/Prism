# -*- coding: utf-8 -*-
"""
使用次数路由

提供使用次数相关的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.auth.dependencies import get_current_user_optional
from src.usage.schemas import (
    UsageCheckRequest,
    UsageDeductRequest,
    UsageBalanceRequest,
    AnonymousRegisterRequest,
    UsageCheckResponse,
    UsageCheckData,
    UsageDeductResponse,
    UsageDeductData,
    UsageBalanceResponse,
    UsageBalanceData,
    AnonymousRegisterResponse,
    AnonymousRegisterData,
)
from src.usage.service import UsageService
from src.config import settings


router = APIRouter(prefix="/usage", tags=["使用次数"])


def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    # 优先从 X-Forwarded-For 获取（反向代理场景）
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    # 从 X-Real-IP 获取
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 直接连接场景
    if request.client:
        return request.client.host
    
    return "127.0.0.1"


@router.post(
    "/check",
    response_model=UsageCheckResponse,
    summary="检查使用权限",
    description="检查用户是否有权限使用指定工具，返回剩余次数和缓存策略",
)
async def check_usage(
    request: Request,
    body: UsageCheckRequest,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    检查使用权限
    
    - 已登录用户：检查付费次数或免费额度
    - 匿名用户：检查每日免费额度（需要 visitor_id）
    """
    if not settings.FEATURE_USER_SYSTEM:
        # 未启用用户系统，所有人都可以使用
        return UsageCheckResponse(
            success=True,
            data=UsageCheckData(
                can_use=True,
                source="free",
                remaining=999999,
                cache_type="free",
                cache_hours=settings.FREE_CACHE_HOURS,
            )
        )
    
    service = UsageService(db)
    ip_address = get_client_ip(request)
    
    result = service.check_usage(
        user=current_user,
        visitor_id=body.visitor_id,
        ip_address=ip_address,
        tool_type=body.tool_type,
    )
    
    return UsageCheckResponse(
        success=result.get("can_use", False),
        data=UsageCheckData(
            can_use=result.get("can_use", False),
            source=result.get("source"),
            remaining=result.get("remaining", 0),
            cache_type=result.get("cache_type"),
            cache_hours=result.get("cache_hours", 0),
            message=result.get("message"),
        )
    )


@router.post(
    "/deduct",
    response_model=UsageDeductResponse,
    summary="扣减使用次数",
    description="扣减用户使用次数，返回缓存策略",
)
async def deduct_usage(
    request: Request,
    body: UsageDeductRequest,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    扣减使用次数
    
    - 已登录用户：优先扣减付费次数，其次扣减免费额度
    - 匿名用户：扣减每日免费额度
    """
    if not settings.FEATURE_USER_SYSTEM:
        # 未启用用户系统，不扣减
        return UsageDeductResponse(
            success=True,
            message="扣减成功",
            data=UsageDeductData(
                success=True,
                source="free",
                remaining=999999,
                cache_type="free",
            )
        )
    
    service = UsageService(db)
    ip_address = get_client_ip(request)
    
    result = service.deduct_usage(
        user=current_user,
        visitor_id=body.visitor_id,
        ip_address=ip_address,
        tool_type=body.tool_type,
        amount=body.amount,
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.get("message", "无使用权限"),
        )
    
    return UsageDeductResponse(
        success=True,
        message="扣减成功",
        data=UsageDeductData(
            success=True,
            source=result.get("source"),
            remaining=result.get("remaining", 0),
            cache_type=result.get("cache_type"),
            cache_expires_at=result.get("cache_expires_at"),
        )
    )


@router.get(
    "/balance",
    response_model=UsageBalanceResponse,
    summary="获取使用次数余额",
    description="获取用户的付费次数余额和免费额度",
)
async def get_balance(
    request: Request,
    visitor_id: str = None,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    获取使用次数余额
    
    - 已登录用户：返回付费次数和免费额度
    - 匿名用户：返回免费额度（需要 visitor_id）
    """
    service = UsageService(db)
    ip_address = get_client_ip(request)
    
    result = service.get_balance(
        user=current_user,
        visitor_id=visitor_id,
        ip_address=ip_address,
    )
    
    return UsageBalanceResponse(
        success=True,
        data=UsageBalanceData(
            user_type=result.get("user_type", "unknown"),
            paid_count=result.get("paid_count", 0),
            free_remaining=result.get("free_remaining", 0),
            free_limit=result.get("free_limit", settings.FREE_DAILY_LIMIT),
            free_reset_at=result.get("free_reset_at"),
        )
    )


@router.post(
    "/anonymous/register",
    response_model=AnonymousRegisterResponse,
    summary="注册匿名用户",
    description="为匿名用户创建使用记录，用于免费额度管理",
)
async def register_anonymous(
    request: Request,
    body: AnonymousRegisterRequest,
    db: Session = Depends(get_db),
):
    """
    注册匿名用户
    
    - 接收前端生成的设备指纹（visitor_id）
    - 创建匿名用户记录
    - 返回免费额度信息
    """
    if not settings.FEATURE_USER_SYSTEM:
        return AnonymousRegisterResponse(
            success=True,
            message="注册成功",
            data=AnonymousRegisterData(
                anonymous_id="anon_0",
                visitor_hash="default",
                free_remaining=settings.FREE_DAILY_LIMIT,
            )
        )
    
    service = UsageService(db)
    ip_address = get_client_ip(request)
    
    result = service.register_anonymous(
        visitor_id=body.visitor_id,
        ip_address=ip_address,
    )
    
    return AnonymousRegisterResponse(
        success=True,
        message="注册成功",
        data=AnonymousRegisterData(
            anonymous_id=result["anonymous_id"],
            visitor_hash=result["visitor_hash"],
            free_remaining=result["free_remaining"],
        )
    )


@router.get(
    "/config",
    summary="获取使用配置",
    description="获取免费额度、缓存时长等配置信息（公开接口）",
)
async def get_usage_config():
    """
    获取使用配置
    
    返回免费额度限制、免费工具列表等配置信息
    """
    return {
        "success": True,
        "data": {
            "free_daily_limit": settings.FREE_DAILY_LIMIT,
            "free_tools": settings.FREE_TOOLS,
            "free_sources": settings.FREE_SOURCES,
            "premium_cache_hours": settings.PREMIUM_CACHE_HOURS,
            "free_cache_hours": settings.FREE_CACHE_HOURS,
            "feature_user_system": settings.FEATURE_USER_SYSTEM,
        }
    }