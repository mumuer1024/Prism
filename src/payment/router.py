# -*- coding: utf-8 -*-
"""
支付 API 路由

提供支付相关的 REST API 端点。
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.auth.dependencies import get_current_user
from src.payment.service import get_payment_service, PaymentService
from src.payment.schemas import (
    PackageListResponse,
    PackageResponse,
    OrderCreateRequest,
    OrderResponse,
    OrderListResponse,
    OrderStatusResponse,
    PaymentCreateResponse,
    MockPayRequest,
    MockPayResponse,
    MessageResponse,
)

router = APIRouter()


# ============================================================================
# 套餐 API
# ============================================================================

@router.get(
    "/packages",
    response_model=PackageListResponse,
    summary="获取套餐列表",
    description="获取可购买的次数套餐列表（公开接口）",
)
async def list_packages(
    db: Session = Depends(get_db),
):
    """获取套餐列表"""
    service = get_payment_service()
    packages = service.get_packages(db)

    return PackageListResponse(
        packages=[PackageResponse(**p.to_dict()) for p in packages]
    )


@router.get(
    "/packages/{package_id}",
    response_model=PackageResponse,
    summary="获取套餐详情",
    description="获取指定套餐的详细信息",
)
async def get_package(
    package_id: int,
    db: Session = Depends(get_db),
):
    """获取套餐详情"""
    service = get_payment_service()
    package = service.get_package(db, package_id)

    if not package:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="套餐不存在"
        )

    return PackageResponse(**package.to_dict())


# ============================================================================
# 订单 API
# ============================================================================

@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建支付订单",
    description="创建支付订单，返回订单信息和支付二维码",
)
async def create_order(
    request: OrderCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """创建支付订单"""
    service = get_payment_service()

    # 创建订单
    order = service.create_order(
        db=db,
        user_id=current_user.id,
        package_id=request.package_id,
        payment_method=request.payment_method,
    )

    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="创建订单失败，请检查套餐和支付方式"
        )

    # 发起支付
    payment_result = await service.initiate_payment(db, order.order_no)

    if not payment_result or not payment_result.success:
        # 支付发起失败，返回订单但标记错误
        pass

    return OrderResponse(**order.to_dict())


@router.get(
    "/orders",
    response_model=OrderListResponse,
    summary="获取用户订单列表",
    description="获取当前用户的支付订单列表",
)
async def list_orders(
    status: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户订单列表"""
    service = get_payment_service()
    orders = service.get_user_orders(
        db=db,
        user_id=current_user.id,
        status=status,
        limit=limit,
    )

    return OrderListResponse(
        orders=[OrderResponse(**o.to_dict()) for o in orders],
        total=len(orders),
    )


@router.get(
    "/orders/{order_no}",
    response_model=OrderResponse,
    summary="获取订单详情",
    description="获取指定订单的详细信息",
)
async def get_order(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取订单详情"""
    service = get_payment_service()
    order = service.get_order(db, order_no)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 检查权限
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此订单"
        )

    return OrderResponse(**order.to_dict())


@router.get(
    "/orders/{order_no}/status",
    response_model=OrderStatusResponse,
    summary="查询订单状态",
    description="查询订单支付状态（用于轮询）",
)
async def get_order_status(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询订单状态"""
    service = get_payment_service()
    order = service.get_order(db, order_no)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 检查权限
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此订单"
        )

    return OrderStatusResponse(
        order_no=order.order_no,
        status=order.status,
        is_paid=order.is_paid(),
        paid_at=order.paid_at.isoformat() if order.paid_at else None,
        usage_count=order.usage_count + order.bonus_count,
        message=_get_status_message(order.status),
    )


def _get_status_message(status: str) -> str:
    """获取状态消息"""
    messages = {
        "pending": "等待支付",
        "paid": "支付成功",
        "failed": "支付失败",
        "cancelled": "订单已取消",
        "refunded": "已退款",
    }
    return messages.get(status, "未知状态")


@router.post(
    "/orders/{order_no}/cancel",
    response_model=MessageResponse,
    summary="取消订单",
    description="取消待支付的订单",
)
async def cancel_order(
    order_no: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消订单"""
    service = get_payment_service()
    order = service.get_order(db, order_no)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 检查权限
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此订单"
        )

    # 关闭订单
    success = await service.close_order(db, order_no)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无法取消订单，可能已支付或已取消"
        )

    return MessageResponse(message="订单已取消")


# ============================================================================
# 支付渠道 API
# ============================================================================

@router.get(
    "/channels",
    summary="获取可用支付渠道",
    description="获取当前可用的支付渠道列表",
)
async def list_channels():
    """获取可用支付渠道"""
    service = get_payment_service()
    channels = service.get_available_channels()

    return {
        "channels": [
            {
                "name": ch.channel_name,
                "display_name": ch.channel_display_name,
                "available": ch.is_available,
            }
            for ch in channels
        ]
    }


# ============================================================================
# 回调 API
# ============================================================================

@router.post(
    "/callback/wechat",
    summary="微信支付回调",
    description="接收微信支付结果通知",
)
async def wechat_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """微信支付回调"""
    # TODO: 验证签名
    data = await request.json()

    service = get_payment_service()
    success = await service.handle_payment_callback(db, "wechat", data)

    if success:
        return {"code": "SUCCESS", "message": "成功"}
    else:
        return {"code": "FAIL", "message": "失败"}


@router.post(
    "/callback/alipay",
    summary="支付宝回调",
    description="接收支付宝结果通知",
)
async def alipay_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """支付宝回调"""
    # TODO: 验证签名
    data = await request.json()

    service = get_payment_service()
    success = await service.handle_payment_callback(db, "alipay", data)

    if success:
        return "success"
    else:
        return "fail"


# ============================================================================
# 模拟支付 API（开发测试用）
# ============================================================================

@router.post(
    "/mock/pay",
    response_model=MockPayResponse,
    summary="模拟支付",
    description="模拟支付成功（仅开发测试环境可用）",
)
async def mock_pay(
    request: MockPayRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """模拟支付"""
    service = get_payment_service()

    # 检查订单
    order = service.get_order(db, request.order_no)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="订单不存在"
        )

    # 检查权限
    if order.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此订单"
        )

    # 执行模拟支付
    success = await service.mock_pay(db, request.order_no)

    return MockPayResponse(
        success=success,
        order_no=request.order_no,
        message="支付成功" if success else "支付失败",
    )