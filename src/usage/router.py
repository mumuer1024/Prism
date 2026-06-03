# -*- coding: utf-8 -*-
"""
使用次数路由（激活码架构）

提供使用次数相关的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.usage.schemas import (
    UsageBalanceRequest,
    UsageConsumeRequest,
    UsageCheckRequest,
    UsageBalanceResponse,
    UsageBalanceData,
    UsageConsumeResponse,
    UsageConsumeData,
    UsageCheckResponse,
    UsageCheckData,
    UsageConfigResponse,
    UsageConfigData,
)
from src.usage.service import UsageService

router = APIRouter(prefix="/usage", tags=["使用次数"])


def get_client_ip(request: Request) -> str:
    """获取客户端 IP 地址"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    if request.client:
        return request.client.host

    return "127.0.0.1"


@router.post(
    "/balance",
    response_model=UsageBalanceResponse,
    summary="查询次数余额",
    description="查询激活码次数余额或匿名用户免费额度",
)
async def get_balance(
    body: UsageBalanceRequest,
    db: Session = Depends(get_db),
):
    """
    查询次数余额

    - 有 device_id → 激活码逻辑，返回付费次数
    - 否则 → 匿名用户逻辑，返回免费额度
    """
    service = UsageService(db)
    result = service.get_balance(
        device_id=body.device_id,
        visitor_id=body.visitor_id,
    )

    return UsageBalanceResponse(
        success=True,
        data=UsageBalanceData(
            user_type=result.get("user_type", "unknown"),
            paid_remaining=result.get("paid_remaining", 0),
            free_remaining=result.get("free_remaining", 0),
            free_limit=result.get("free_limit", 3),
            free_reset_at=result.get("free_reset_at"),
            referral_code=result.get("referral_code"),
            referral_count=result.get("referral_count"),
        ),
    )


@router.post(
    "/consume",
    response_model=UsageConsumeResponse,
    summary="扣减次数",
    description="扣减使用次数，首次消费时触发推荐奖励",
)
async def consume_usage(
    body: UsageConsumeRequest,
    db: Session = Depends(get_db),
):
    """
    扣减次数

    - 有 device_id → 扣减激活码次数，触发推荐奖励检查
    - 否则 → 扣减匿名用户免费次数
    """
    service = UsageService(db)
    result = service.consume(
        device_id=body.device_id,
        visitor_id=body.visitor_id,
        tool_type=body.tool_type,
        amount=body.amount,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result.get("message", "无使用权限"),
        )

    return UsageConsumeResponse(
        success=True,
        message="消费成功",
        data=UsageConsumeData(
            success=True,
            source=result.get("source"),
            remaining=result.get("remaining", 0),
            referral_rewarded=result.get("referral_rewarded", False),
            referral_bonus=result.get("referral_bonus", 0),
        ),
    )


@router.post(
    "/check",
    response_model=UsageCheckResponse,
    summary="检查使用权限",
    description="检查是否有权限使用指定功能",
)
async def check_usage(
    body: UsageCheckRequest,
    db: Session = Depends(get_db),
):
    """
    检查使用权限

    - 返回是否可使用、来源类型、剩余次数
    """
    service = UsageService(db)
    result = service.check_usage(
        device_id=body.device_id,
        visitor_id=body.visitor_id,
        tool_type=body.tool_type,
    )

    return UsageCheckResponse(
        success=True,
        data=UsageCheckData(
            can_use=result.get("can_use", False),
            source=result.get("source"),
            remaining=result.get("remaining", 0),
        ),
    )


@router.get(
    "/config",
    response_model=UsageConfigResponse,
    summary="获取使用配置",
    description="获取免费额度、推荐奖励等配置信息",
)
async def get_usage_config():
    """
    获取使用配置

    - 返回免费限额、推荐奖励次数等
    """
    service = UsageService(None)
    config = service.get_config()

    return UsageConfigResponse(
        success=True,
        data=UsageConfigData(
            free_daily_limit=config.get("free_daily_limit", 3),
            referral_bonus_count=config.get("referral_bonus_count", 3),
            device_limit=config.get("device_limit", 3),
        ),
    )