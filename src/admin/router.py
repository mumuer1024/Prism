# -*- coding: utf-8 -*-
"""
管理员 API 路由（v2.1 激活码架构）

提供激活码管理、模板管理、审计日志等管理员专用接口
"""

import json
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import AdminUser, ActivationCode, Device, ReferralCode, AuditLog
from src.database import crud
from src.admin.dependencies import (
    get_admin_from_session,
    get_client_ip,
    create_admin_session,
    revoke_admin_session,
    verify_password,
    hash_password,
    get_admin_optional,
)
from src.admin.schemas import (
    # 管理员登录
    AdminLoginRequest,
    AdminLoginResponse,
    AdminInfoResponse,
    # 激活码管理
    GenerateActivationCodesRequest,
    GenerateActivationCodesResponse,
    ActivationCodeListResponse,
    ActivationCodeData,
    RevokeActivationCodeResponse,
    ActivationCodeDevicesResponse,
    DeviceBindingData,
    DashboardStatsResponse,
    # 审计日志
    AuditLogResponse,
)
from src.marketplace.schemas import TemplateResponse
from src.marketplace.crud import (
    get_templates,
    get_template_by_id,
    create_template,
    update_template,
    delete_template,
    VALID_TOOL_TYPES,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ==========================================
# 管理员登录 API
# ==========================================

@router.post("/login", response_model=AdminLoginResponse)
def admin_login(
    request: AdminLoginRequest,
    http_request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    管理员登录
    
    使用管理员账号密码登录，返回会话Token
    """
    # 查询管理员
    admin = db.query(AdminUser).filter(
        AdminUser.username == request.username
    ).first()
    
    if not admin:
        raise HTTPException(
            status_code=401,
            detail="账号或密码错误",
        )
    
    # 验证密码
    if not verify_password(request.password, admin.password_hash):
        raise HTTPException(
            status_code=401,
            detail="账号或密码错误",
        )
    
    # 创建会话
    ip = get_client_ip(http_request)
    token = create_admin_session(admin.id, ip)
    
    
    logger.info(f"管理员登录成功: username={admin.username}, ip={ip}")
    
    # 设置 Cookie
    response.set_cookie(
        key="admin_token",
        value=token,
        max_age=86400,  # 24小时
        httponly=True,
        samesite="strict",
    )
    
    return AdminLoginResponse(
        success=True,
        message="登录成功",
        token=token,
        admin_id=admin.id,
        username=admin.username,
    )


@router.post("/logout")
def admin_logout(
    http_request: Request,
    response: Response,
    admin: AdminUser = Depends(get_admin_optional),
):
    """
    管理员登出
    
    撤销会话Token
    """
    token = http_request.headers.get("X-Admin-Token")
    if not token:
        token = http_request.cookies.get("admin_token")
    
    if token:
        revoke_admin_session(token)
    
    response.delete_cookie("admin_token")
    
    return {"success": True, "message": "已登出"}


@router.get("/me", response_model=AdminInfoResponse)
def admin_get_me(
    admin: AdminUser = Depends(get_admin_from_session),
):
    """
    获取当前管理员信息
    """
    return AdminInfoResponse(
        id=admin.id,
        username=admin.username,
        is_active=True,  # AdminUser 没有 is_active 字段，默认返回 True
        created_at=admin.created_at,
        last_login_at=None,  # AdminUser 没有 last_login_at 字段
    )


@router.get("/check")
def admin_check_login(
    admin: AdminUser = Depends(get_admin_optional),
):
    """
    检查管理员登录状态
    """
    if admin:
        return {"is_logged_in": True, "username": admin.username}
    return {"is_logged_in": False}


# ==========================================
# 仪表盘统计 API
# ==========================================

@router.get("/stats", response_model=DashboardStatsResponse)
def admin_get_stats(
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    获取仪表盘统计数据
    
    - 总激活码数
    - 已激活/未激活数
    - 总次数/剩余次数
    - 设备数、推荐数
    - 今日/本周激活数
    """
    # 统计激活码
    total_codes = db.query(ActivationCode).count()
    activated_codes = db.query(ActivationCode).filter(
        ActivationCode.is_activated == True
    ).count()
    unused_codes = total_codes - activated_codes
    
    # 统计次数
    total_quota = db.query(ActivationCode).with_entities(
        ActivationCode.quota
    ).all()
    total_quota_sum = sum(q[0] or 0 for q in total_quota)
    
    total_remaining = db.query(ActivationCode).with_entities(
        ActivationCode.remaining
    ).all()
    total_remaining_sum = sum(r[0] or 0 for r in total_remaining)
    
    # 统计设备
    total_devices = db.query(Device).count()
    
    # 统计推荐
    total_referrals = db.query(ReferralCode).count()
    
    # 今日激活数
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0)
    today_activations = db.query(ActivationCode).filter(
        ActivationCode.activated_at >= today_start
    ).count()
    
    # 本周激活数
    week_start = today_start - timedelta(days=today_start.weekday())
    week_activations = db.query(ActivationCode).filter(
        ActivationCode.activated_at >= week_start
    ).count()
    
    return DashboardStatsResponse(
        total_codes=total_codes,
        activated_codes=activated_codes,
        unused_codes=unused_codes,
        total_quota=total_quota_sum,
        total_remaining=total_remaining_sum,
        total_devices=total_devices,
        total_referrals=total_referrals,
        today_activations=today_activations,
        week_activations=week_activations,
    )


# ==========================================
# 激活码管理 API
# ==========================================

@router.post("/codes/generate", response_model=GenerateActivationCodesResponse)
def admin_generate_activation_codes(
    request: GenerateActivationCodesRequest,
    http_request: Request,
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    批量生成激活码（管理员）
    
    Args:
        count: 生成数量（1-1000）
        quota: 每个激活码的次数
    
    Returns:
        生成的激活码列表
    """
    codes = []
    
    for _ in range(request.count):
        activation_code = crud.create_activation_code(db, quota=request.quota)
        if activation_code:
            codes.append(activation_code.code)
    
    # 记录审计日志
    audit_log = AuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action="generate_activation_codes",
        action_category="activation_code_management",
        target_type="activation_codes",
        target_id=None,
        action_detail=json.dumps({
            "count": request.count,
            "quota": request.quota,
            "note": request.note,
        }),
        ip_address=get_client_ip(http_request),
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"管理员 {admin.username} 生成激活码: count={request.count}, quota={request.quota}")
    
    return GenerateActivationCodesResponse(
        success=True,
        message=f"成功生成 {request.count} 个激活码",
        codes=codes,
        count=len(codes),
        quota=request.quota,
    )


@router.get("/codes", response_model=ActivationCodeListResponse)
def admin_list_activation_codes(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    is_activated: bool = Query(None),
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    查看激活码列表（管理员）
    
    Args:
        page: 页码
        limit: 每页数量
        search: 搜索激活码
        is_activated: 筛选激活状态
    
    Returns:
        激活码列表
    """
    query = db.query(ActivationCode)
    
    # 筛选
    if search:
        query = query.filter(ActivationCode.code.ilike(f"%{search}%"))
    
    if is_activated is not None:
        query = query.filter(ActivationCode.is_activated == is_activated)
    
    # 排序（未激活优先）
    query = query.order_by(ActivationCode.is_activated.asc(), ActivationCode.id.desc())
    
    # 分页
    total = query.count()
    codes = query.offset((page - 1) * limit).limit(limit).all()
    
    code_list = []
    for code in codes:
        # 统计设备数量
        device_count = db.query(Device).filter(Device.code_id == code.id).count()
        
        code_list.append(ActivationCodeData(
            id=code.id,
            code=code.code,
            quota=code.quota,
            remaining=code.remaining,
            is_activated=code.is_activated,
            activated_at=code.activated_at,
            device_count=device_count,
            referral_code_used=code.referral_code_used,
            referral_rewarded=code.referral_rewarded,
            created_at=code.created_at,
        ))
    
    return ActivationCodeListResponse(
        codes=code_list,
        total=total,
        page=page,
        limit=limit,
    )


@router.delete("/codes/{code_id}", response_model=RevokeActivationCodeResponse)
def admin_revoke_activation_code(
    code_id: int,
    http_request: Request,
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    作废激活码（管理员）
    
    将激活码的次数设为0，禁止继续使用
    """
    activation_code = db.query(ActivationCode).filter(ActivationCode.id == code_id).first()
    
    if not activation_code:
        raise HTTPException(status_code=404, detail="激活码不存在")
    
    # 作废激活码
    activation_code.remaining = 0
    db.commit()
    
    # 记录审计日志
    audit_log = AuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action="revoke_activation_code",
        action_category="activation_code_management",
        target_type="activation_code",
        target_id=str(code_id),
        action_detail=json.dumps({
            "code": activation_code.code,
            "original_remaining": activation_code.remaining,
        }),
        ip_address=get_client_ip(http_request),
    )
    db.add(audit_log)
    db.commit()
    
    logger.info(f"管理员 {admin.username} 作废激活码: id={code_id}, code={activation_code.code}")
    
    return RevokeActivationCodeResponse(
        success=True,
        message="激活码已作废",
        code_id=code_id,
        code=activation_code.code,
    )


@router.get("/codes/{code_id}/devices", response_model=ActivationCodeDevicesResponse)
def admin_get_activation_code_devices(
    code_id: int,
    http_request: Request,
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    查看激活码绑定的设备（管理员）

    显示该激活码绑定的所有设备信息
    """
    activation_code = db.query(ActivationCode).filter(ActivationCode.id == code_id).first()

    if not activation_code:
        raise HTTPException(status_code=404, detail="激活码不存在")

    # 查询设备
    devices = db.query(Device).filter(Device.code_id == code_id).all()

    device_list = [
        DeviceBindingData(
            id=d.id,
            device_id=d.device_id,
            device_name=d.device_name,
            last_seen=d.last_seen,
            created_at=d.created_at,
        )
        for d in devices
    ]

    # 记录审计日志
    audit_log = AuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action="view_code_devices",
        action_category="activation_code_management",
        target_type="activation_code",
        target_id=str(code_id),
        action_detail=json.dumps({
            "code": activation_code.code,
            "device_count": len(device_list),
        }),
        ip_address=get_client_ip(http_request),
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"管理员 {admin.username} 查看激活码设备: id={code_id}, device_count={len(device_list)}")

    return ActivationCodeDevicesResponse(
        success=True,
        code_id=code_id,
        code=activation_code.code,
        devices=device_list,
        device_count=len(device_list),
    )


# ==========================================
# 审计日志 API
# ==========================================

@router.get("/audit-logs")
def admin_get_audit_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    action: str = Query(None),
    action_category: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    获取审计日志列表（管理员）
    
    Args:
        page: 页码
        limit: 每页数量
        action: 操作类型筛选
        action_category: 操作分类筛选
        start_date: 开始日期 (YYYY-MM-DD)
        end_date: 结束日期 (YYYY-MM-DD)
    
    Returns:
        审计日志列表
    """
    query = db.query(AuditLog)
    
    # 筛选
    if action:
        query = query.filter(AuditLog.action == action)
    
    if action_category:
        query = query.filter(AuditLog.action_category == action_category)
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.created_at <= end_dt)
        except ValueError:
            pass
    
    # 排序
    query = query.order_by(AuditLog.id.desc())
    
    # 分页
    total = query.count()
    logs = query.offset((page - 1) * limit).limit(limit).all()
    
    log_list = []
    for log in logs:
        log_list.append({
            "id": log.id,
            "admin_id": log.admin_id,
            "admin_username": log.admin_username,
            "action": log.action,
            "action_category": log.action_category,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "action_detail": log.action_detail,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })
    
    return {
        "logs": log_list,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/audit-logs/actions")
def admin_get_audit_actions(
    admin: AdminUser = Depends(get_admin_from_session),
):
    """
    获取所有审计操作类型（管理员）
    """
    return {
        "actions": [
            {"value": "generate_activation_codes", "label": "生成激活码"},
            {"value": "revoke_activation_code", "label": "作废激活码"},
            {"value": "view_activation_code_devices", "label": "查看设备绑定"},
            {"value": "create_template", "label": "创建模板"},
            {"value": "update_template", "label": "更新模板"},
            {"value": "delete_template", "label": "删除模板"},
            {"value": "admin_login", "label": "管理员登录"},
            {"value": "admin_logout", "label": "管理员登出"},
        ],
        "categories": [
            {"value": "activation_code_management", "label": "激活码管理"},
            {"value": "template_management", "label": "模板管理"},
            {"value": "admin_auth", "label": "管理员认证"},
        ]
    }


# ==========================================
# 模板管理 API（保留）
# ==========================================

@router.post("/marketplace/templates")
def admin_create_template(
    request: dict,
    http_request: Request,
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    新增模板（管理员）
    """
    tool_type = request.get("tool_type")
    if tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的 tool_type，有效值: {', '.join(VALID_TOOL_TYPES)}"
        )

    template = create_template(
        db=db,
        title=request.get("title"),
        description=request.get("description"),
        tool_type=tool_type,
        prompt_content=request.get("prompt_content"),
        tags=request.get("tags"),
        is_official=request.get("is_official", False),
        is_published=request.get("is_published", False),
    )

    # 记录审计日志
    audit_log = AuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action="create_template",
        action_category="template_management",
        target_type="marketplace_template",
        target_id=str(template.id),
        action_detail=json.dumps({
            "title": template.title,
            "tool_type": template.tool_type,
            "is_official": template.is_official,
            "is_published": template.is_published,
        }),
        ip_address=get_client_ip(http_request),
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"管理员 {admin.username} 创建模板: id={template.id}")

    return {"success": True, "template": template.to_dict()}


@router.put("/marketplace/templates/{template_id}")
def admin_update_template(
    template_id: int,
    request: dict,
    http_request: Request,
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    编辑模板（管理员）
    """
    # 获取原始模板信息用于审计
    original_template = get_template_by_id(db, template_id)
    if not original_template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template = update_template(
        db=db,
        template_id=template_id,
        **request
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 记录审计日志
    audit_log = AuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action="update_template",
        action_category="template_management",
        target_type="marketplace_template",
        target_id=str(template_id),
        action_detail=json.dumps({
            "title": template.title,
            "tool_type": template.tool_type,
            "changes": request,
        }),
        ip_address=get_client_ip(http_request),
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"管理员 {admin.username} 更新模板: id={template_id}")

    return {"success": True, "template": template.to_dict()}


@router.delete("/marketplace/templates/{template_id}")
def admin_delete_template(
    template_id: int,
    http_request: Request,
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    删除模板（管理员）
    """
    # 获取模板信息用于审计
    template = get_template_by_id(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    template_title = template.title
    template_tool_type = template.tool_type

    success = delete_template(db=db, template_id=template_id)

    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 记录审计日志
    audit_log = AuditLog(
        admin_id=admin.id,
        admin_username=admin.username,
        action="delete_template",
        action_category="template_management",
        target_type="marketplace_template",
        target_id=str(template_id),
        action_detail=json.dumps({
            "title": template_title,
            "tool_type": template_tool_type,
        }),
        ip_address=get_client_ip(http_request),
    )
    db.add(audit_log)
    db.commit()

    logger.info(f"管理员 {admin.username} 删除模板: id={template_id}")

    return {"success": True, "message": "模板已删除"}


@router.get("/marketplace/templates")
def admin_list_templates(
    tool_type: str = None,
    include_unpublished: bool = True,
    skip: int = 0,
    limit: int = 50,
    admin: AdminUser = Depends(get_admin_from_session),
    db: Session = Depends(get_db),
):
    """
    获取模板列表（管理员，可查看未发布的）
    """
    templates, total = get_templates(
        db=db,
        tool_type=tool_type,
        is_published=None if include_unpublished else True,
        skip=skip,
        limit=limit,
    )
    
    return {
        "templates": [t.to_dict() for t in templates],
        "total": total,
    }