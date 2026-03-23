# src/user/router.py
"""
用户 API 路由
提供用户信息、兑换码充值、邀请统计等接口
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from src.database.connection import get_db
from src.database.models import User
from src.auth.dependencies import get_current_user
from src.user.schemas import (
    UserProfileResponse,
    RedeemRequest,
    RedeemResponse,
    InviteStatsResponse,
    UserOperationResponse,
)
from src.user.service import UserService
from src.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["用户管理"])


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="获取用户信息",
    description="""
获取当前用户的详细信息，包括：
- 基本信息（邮箱、昵称、头像等）
- 使用次数
- 邀请码
- 邀请统计
- 最近充值记录
    """,
)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取用户信息
    
    需要登录认证，返回当前用户的完整信息。
    """
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    service = UserService(db)
    result = await service.get_user_profile(current_user)
    return result


@router.post(
    "/redeem",
    response_model=RedeemResponse,
    responses={
        400: {"description": "兑换码无效或已使用"},
        503: {"description": "用户系统暂未开放"},
    },
    summary="兑换码充值",
    description="""
使用兑换码充值使用次数。

**邀请返利机制：**
- 被邀请人首次充值时，额外获得赠送次数
- 邀请人同时获得奖励次数
- 每个被邀请人只能享受一次首次充值奖励
    """,
)
async def redeem_code(
    request: RedeemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    兑换码充值
    
    - **code**: 兑换码（必填）
    
    返回兑换结果，包括：
    - 基础次数
    - 赠送次数（如有）
    - 总次数
    - 邀请人奖励信息
    """
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    service = UserService(db)
    result = await service.redeem_code(current_user, request.code.strip())
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["message"]
        )
    
    return RedeemResponse(
        success=True,
        message=result["message"],
        data=result["data"],
    )


@router.get(
    "/invite-stats",
    response_model=InviteStatsResponse,
    summary="获取邀请统计",
    description="""
获取当前用户的邀请统计信息，包括：
- 邀请码
- 总邀请人数
- 活跃邀请人数
- 获得的总奖励次数
- 邀请记录详情
    """,
)
async def get_invite_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取邀请统计
    
    需要登录认证，返回当前用户的邀请统计信息。
    """
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    service = UserService(db)
    result = await service.get_invite_statistics(current_user)
    return result


@router.get(
    "/usage",
    response_model=UserOperationResponse,
    summary="获取使用次数",
    description="获取当前用户的使用次数信息",
)
async def get_usage(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取使用次数
    
    返回当前用户的剩余使用次数。
    """
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    service = UserService(db)
    result = await service.get_user_usage(current_user)
    return UserOperationResponse(
        success=True,
        message="获取成功",
        data=result["data"],
    )