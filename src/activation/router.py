# -*- coding: utf-8 -*-
"""
激活码模块 - API 路由

提供激活码相关的 API 端点
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.activation.schemas import (
    ActivateRequest,
    StatusRequest,
    DeviceListRequest,
    DeviceDeleteRequest,
    ReferralRequest,
    ActivateResponse,
    ActivationData,
    StatusResponse,
    StatusData,
    DeviceListResponse,
    DeviceListData,
    DeviceDeleteResponse,
    ReferralResponse,
    ReferralData,
    QuotaSpecsResponse,
    QuotaSpecData,
)
from src.activation.service import ActivationService
from src.config import settings

router = APIRouter()


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
    "/activate",
    response_model=ActivateResponse,
    summary="激活激活码",
    description="输入激活码激活，绑定设备，返回激活状态和推荐码",
)
async def activate(
    body: ActivateRequest,
    db: Session = Depends(get_db),
):
    """
    激活激活码

    - 验证激活码格式和有效性
    - 绑定设备（幂等）
    - 首次激活生成推荐码
    - 可填写推荐码获得推荐奖励（首次消费时触发）
    """
    service = ActivationService(db)
    result = service.activate(
        code=body.code,
        device_id=body.device_id,
        device_name=body.device_name,
        referral_code=body.referral_code,
    )

    if not result.get("success"):
        error_code = result.get("error_code", "UNKNOWN")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "激活失败"),
        )

    data = result.get("data", {})
    return ActivateResponse(
        success=True,
        message=result.get("message", "激活成功"),
        data=ActivationData(
            code_id=data.get("code_id"),
            code=data.get("code"),
            quota=data.get("quota"),
            remaining=data.get("remaining"),
            is_activated=data.get("is_activated", True),
            referral_code=data.get("referral_code"),
            device_count=data.get("device_count", 1),
            device_limit=data.get("device_limit", 3),
        ),
    )


@router.post(
    "/status",
    response_model=StatusResponse,
    summary="查询激活状态",
    description="通过 device_id 查询当前激活状态和剩余次数",
)
async def get_status(
    body: StatusRequest,
    db: Session = Depends(get_db),
):
    """
    查询激活状态

    - 检查设备是否已绑定激活码
    - 返回激活码信息和推荐码
    """
    service = ActivationService(db)
    result = service.get_status(device_id=body.device_id)

    if not result.get("is_activated"):
        return StatusResponse(
            success=True,
            data=None,
        )

    data = result.get("data", {})
    return StatusResponse(
        success=True,
        data=StatusData(
            is_activated=True,
            code_id=data.get("code_id"),
            code=data.get("code"),
            quota=data.get("quota"),
            remaining=data.get("remaining"),
            referral_code=data.get("referral_code"),
            device_count=data.get("device_count"),
            referral_count=data.get("referral_count", 0),
            total_rewarded=data.get("total_rewarded", 0),
        ),
    )


@router.post(
    "/devices",
    response_model=DeviceListResponse,
    summary="获取设备列表",
    description="获取当前激活码绑定的所有设备",
)
async def get_devices(
    body: DeviceListRequest,
    db: Session = Depends(get_db),
):
    """
    获取设备列表

    - 显示所有已绑定设备
    - 标识当前设备
    """
    service = ActivationService(db)
    result = service.get_devices(device_id=body.device_id)

    if not result.get("success"):
        return DeviceListResponse(
            success=False,
            data=None,
        )

    from src.activation.schemas import DeviceData
    devices = [
        DeviceData(
            id=d.get("id"),
            device_id=d.get("device_id"),
            device_name=d.get("device_name"),
            last_seen=d.get("last_seen"),
            created_at=d.get("created_at"),
            is_current=d.get("is_current", False),
        )
        for d in result.get("devices", [])
    ]

    return DeviceListResponse(
        success=True,
        data=DeviceListData(
            devices=devices,
            total=result.get("total", 0),
            limit=result.get("limit", 3),
            current_device_id=result.get("current_device_id", ""),
        ),
    )


@router.delete(
    "/devices/{device_db_id}",
    response_model=DeviceDeleteResponse,
    summary="解绑设备",
    description="解绑指定设备（不能解绑当前设备）",
)
async def delete_device(
    device_db_id: int,
    body: DeviceDeleteRequest,
    db: Session = Depends(get_db),
):
    """
    解绑设备

    - 需要提供当前设备 ID 用于验证
    - 不能解绑当前设备
    """
    service = ActivationService(db)
    result = service.delete_device(
        device_id=body.device_id,
        device_db_id=device_db_id,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "解绑失败"),
        )

    return DeviceDeleteResponse(
        success=True,
        message=result.get("message", "设备已解绑"),
    )


@router.post(
    "/referral",
    response_model=ReferralResponse,
    summary="获取推荐码",
    description="获取当前激活码的专属推荐码",
)
async def get_referral(
    body: ReferralRequest,
    db: Session = Depends(get_db),
):
    """
    获取推荐码

    - 返回专属推荐码
    - 显示已推荐人数和累计奖励
    """
    service = ActivationService(db)
    result = service.get_referral(device_id=body.device_id)

    if not result.get("success"):
        return ReferralResponse(
            success=False,
            data=None,
        )

    data = result.get("data", {})
    return ReferralResponse(
        success=True,
        data=ReferralData(
            referral_code=data.get("referral_code"),
            referral_count=data.get("referral_count", 0),
            total_rewarded=data.get("total_rewarded", 0),
            code_id=data.get("code_id"),
        ),
    )


@router.post(
    "/add-quota",
    response_model=ActivateResponse,
    summary="叠加次数",
    description="使用新激活码为当前账号叠加次数",
)
async def add_quota(
    body: ActivateRequest,
    db: Session = Depends(get_db),
):
    """
    叠加次数

    - 使用新激活码增加次数
    - 如果设备未激活，则执行激活流程
    """
    service = ActivationService(db)
    result = service.add_quota(
        device_id=body.device_id,
        new_code=body.code,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "叠加失败"),
        )

    data = result.get("data", {})
    return ActivateResponse(
        success=True,
        message=result.get("message", "叠加成功"),
        data=ActivationData(
            code_id=data.get("code_id"),
            code=data.get("code"),
            quota=data.get("quota"),
            remaining=data.get("remaining"),
            is_activated=True,
            device_count=0,
            device_limit=3,
        ),
    )


@router.get(
    "/specs",
    response_model=QuotaSpecsResponse,
    summary="获取次数规格",
    description="获取所有可购买的次数规格",
)
async def get_quota_specs():
    """
    获取次数规格

    - 返回所有规格定义（S/M/L/XL/XXL/XXXL）
    """
    specs = ActivationService.get_quota_specs()
    return QuotaSpecsResponse(
        success=True,
        data=[QuotaSpecData(spec=s["spec"], quota=s["quota"]) for s in specs],
    )