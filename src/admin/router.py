# -*- coding: utf-8 -*-
"""
管理员 API 路由

提供用户管理、兑换码管理、模板管理等管理员专用接口
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.auth.dependencies import get_admin_user
from src.admin.service import AdminService
from src.admin.schemas import (
    UserListResponse,
    UserDetailResponse,
    BanUserRequest,
    BanUserResponse,
    UnbanUserResponse,
    UserStatsResponse,
    RevenueStatsResponse,
    GenerateCodesRequest,
    GenerateCodesResponse,
    BatchListResponse,
    BatchDetailResponse,
    ExportCodesResponse,
    BatchBanRequest,
    BatchBanResponse,
    AuditLogListResponse,
    AuditAction,
    AuditCategory,
)
from src.marketplace.schemas import (
    TemplateResponse,
    TemplateCreateRequest,
    TemplateUpdateRequest,
    TemplatePublishRequest,
)
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


# ── 辅助函数 ───────────────────────────────────────────────

def get_client_ip(request: Request) -> str:
    """获取客户端IP地址"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ── 用户管理 API ───────────────────────────────────────────────

@router.get("/users", response_model=dict)
def admin_list_users(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词"),
    is_banned: bool = Query(None, description="筛选封禁状态"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取用户列表（管理员）

    Args:
        page: 页码
        limit: 每页数量
        search: 搜索关键词（邮箱/昵称）
        is_banned: 封禁状态筛选
        admin: 当前管理员
        db: 数据库会话

    Returns:
        用户列表
    """
    service = AdminService(db)
    users, total = service.get_users(
        page=page,
        limit=limit,
        search=search,
        is_banned=is_banned,
    )

    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "usage_count": user.usage_count,
            "invite_code": user.invite_code,
            "is_active": user.is_active,
            "is_banned": user.is_banned,
            "banned_at": user.banned_at.isoformat() if user.banned_at else None,
            "banned_reason": user.banned_reason,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        })

    return {
        "users": user_list,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/users/{user_id}", response_model=dict)
def admin_get_user_detail(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取用户详情（管理员）

    Args:
        user_id: 用户 ID
        admin: 当前管理员
        db: 数据库会话

    Returns:
        用户详情
    """
    service = AdminService(db)
    user_detail = service.get_user_detail(user_id)

    if not user_detail:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 处理 datetime 字段
    for key in ["created_at", "last_login_at", "banned_at"]:
        if user_detail.get(key):
            user_detail[key] = user_detail[key].isoformat()

    return {
        "success": True,
        "data": user_detail,
    }


@router.patch("/users/{user_id}/ban", response_model=BanUserResponse)
def admin_ban_user(
    user_id: int,
    request: BanUserRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    封禁用户（管理员）

    Args:
        user_id: 用户 ID
        request: 封禁请求
        admin: 当前管理员
        db: 数据库会话

    Returns:
        封禁结果
    """
    service = AdminService(db)
    result = service.ban_user(user_id, request.reason)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    logger.info(f"管理员 {current_user.id} 封禁用户: user_id={user_id}, reason={request.reason}")

    return BanUserResponse(
        success=True,
        message=result["message"],
        user_id=user_id,
        banned_at=result["banned_at"],
        banned_reason=request.reason,
    )


@router.patch("/users/{user_id}/unban", response_model=UnbanUserResponse)
def admin_unban_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    解禁用户（管理员）

    Args:
        user_id: 用户 ID
        admin: 当前管理员
        db: 数据库会话

    Returns:
        解禁结果
    """
    service = AdminService(db)
    result = service.unban_user(user_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    logger.info(f"管理员 {current_user.id} 解禁用户: user_id={user_id}")

    return UnbanUserResponse(
        success=True,
        message=result["message"],
        user_id=user_id,
    )


@router.post("/users/batch-ban", response_model=BatchBanResponse)
def admin_batch_ban_users(
    request: BatchBanRequest,
    http_request: Request,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    批量封禁用户（管理员）

    Args:
        request: 批量封禁请求
        http_request: HTTP请求对象
        admin: 当前管理员
        db: 数据库会话

    Returns:
        批量封禁结果
    """
    service = AdminService(db)

    # 获取管理员邮箱
    from src.database.crud import get_user_by_id
    admin_user = get_user_by_id(db, current_user.id)
    admin_email = admin_user.email if admin_user else "unknown"

    result = service.batch_ban_users(
        user_ids=request.user_ids,
        reason=request.reason,
        admin_id=current_user.id,
        admin_email=admin_email,
        ip_address=get_client_ip(http_request),
    )

    logger.info(f"管理员 {current_user.id} 批量封禁用户: count={len(request.user_ids)}, succeeded={result['succeeded']}")

    return BatchBanResponse(
        success=result["success"],
        message=result["message"],
        total=result["total"],
        succeeded=result["succeeded"],
        failed=result["failed"],
        failed_ids=result["failed_ids"],
        details=result["details"],
    )


# ── 审计日志 API ───────────────────────────────────────────────

@router.get("/audit-logs")
def admin_get_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(50, ge=1, le=200, description="每页数量"),
    admin_id: int = Query(None, description="管理员ID筛选"),
    action: str = Query(None, description="操作类型筛选"),
    action_category: str = Query(None, description="操作分类筛选"),
    target_type: str = Query(None, description="目标类型筛选"),
    start_date: str = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(None, description="结束日期 (YYYY-MM-DD)"),
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取审计日志列表（管理员）

    Args:
        page: 页码
        limit: 每页数量
        admin_id: 管理员ID筛选
        action: 操作类型筛选
        action_category: 操作分类筛选
        target_type: 目标类型筛选
        start_date: 开始日期
        end_date: 结束日期
        admin: 当前管理员
        db: 数据库会话

    Returns:
        审计日志列表
    """
    service = AdminService(db)

    # 解析日期
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    logs, total = service.get_audit_logs(
        page=page,
        limit=limit,
        admin_id=admin_id,
        action=action,
        action_category=action_category,
        target_type=target_type,
        start_date=start_dt,
        end_date=end_dt,
    )

    return {
        "logs": [log.to_dict() for log in logs],
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/audit-logs/actions")
def admin_get_audit_actions(
    current_user: User = Depends(get_admin_user),
):
    """
    获取所有审计操作类型（管理员）

    Args:
        admin: 当前管理员

    Returns:
        操作类型列表
    """
    return {
        "actions": [
            {"value": AuditAction.BAN_USER, "label": "封禁用户"},
            {"value": AuditAction.UNBAN_USER, "label": "解禁用户"},
            {"value": AuditAction.BATCH_BAN_USERS, "label": "批量封禁用户"},
            {"value": AuditAction.GENERATE_CODES, "label": "生成兑换码"},
            {"value": AuditAction.EXPORT_CODES, "label": "导出兑换码"},
            {"value": AuditAction.CREATE_TEMPLATE, "label": "创建模板"},
            {"value": AuditAction.UPDATE_TEMPLATE, "label": "更新模板"},
            {"value": AuditAction.DELETE_TEMPLATE, "label": "删除模板"},
        ],
        "categories": [
            {"value": AuditCategory.USER_MANAGEMENT, "label": "用户管理"},
            {"value": AuditCategory.CODE_MANAGEMENT, "label": "兑换码管理"},
            {"value": AuditCategory.TEMPLATE_MANAGEMENT, "label": "模板管理"},
            {"value": AuditCategory.SYSTEM_CONFIG, "label": "系统配置"},
        ]
    }


@router.get("/stats/users", response_model=UserStatsResponse)
def admin_get_user_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取用户统计（管理员）

    Args:
        admin: 当前管理员
        db: 数据库会话

    Returns:
        用户统计信息
    """
    service = AdminService(db)
    stats = service.get_user_stats()

    return UserStatsResponse(**stats)


@router.get("/stats/revenue", response_model=RevenueStatsResponse)
def admin_get_revenue_stats(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取充值统计（管理员）

    Args:
        admin: 当前管理员
        db: 数据库会话

    Returns:
        充值统计信息
    """
    service = AdminService(db)
    stats = service.get_revenue_stats()

    return RevenueStatsResponse(**stats)


# ── 兑换码管理 API ───────────────────────────────────────────────

@router.post("/codes/generate", response_model=GenerateCodesResponse)
def admin_generate_codes(
    request: GenerateCodesRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    批量生成兑换码（管理员）

    Args:
        request: 生成请求
        admin: 当前管理员
        db: 数据库会话

    Returns:
        生成结果
    """
    service = AdminService(db)
    result = service.generate_codes(
        count=request.count,
        usage_count=request.usage_count,
        expire_days=request.expire_days,
        note=request.note,
    )

    logger.info(f"管理员 {current_user.id} 生成兑换码: batch_id={result['batch_id']}, count={request.count}")

    return GenerateCodesResponse(
        success=True,
        message=result["message"],
        batch_id=result["batch_id"],
        codes=result["codes"],
        count=result["count"],
        usage_count_per_code=result["usage_count_per_code"],
        expires_at=result["expires_at"],
    )


@router.get("/codes/batches")
def admin_list_batches(
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取兑换码批次列表（管理员）

    Args:
        admin: 当前管理员
        db: 数据库会话

    Returns:
        批次列表
    """
    service = AdminService(db)
    batches = service.get_batches()

    # 处理 datetime 字段
    for batch in batches:
        if batch.get("created_at"):
            batch["created_at"] = batch["created_at"].isoformat()
        if batch.get("expires_at"):
            batch["expires_at"] = batch["expires_at"].isoformat()

    return {
        "batches": batches,
        "total": len(batches),
    }


@router.get("/codes/batches/{batch_id}")
def admin_get_batch_detail(
    batch_id: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取批次详情（管理员）

    Args:
        batch_id: 批次号
        admin: 当前管理员
        db: 数据库会话

    Returns:
        批次详情
    """
    service = AdminService(db)
    detail = service.get_batch_detail(batch_id)

    if not detail:
        raise HTTPException(status_code=404, detail="批次不存在")

    # 处理 datetime 字段
    for key in ["created_at", "expires_at"]:
        if detail.get(key):
            detail[key] = detail[key].isoformat()

    for code in detail["codes"]:
        for key in ["created_at", "expires_at", "used_at"]:
            if code.get(key):
                code[key] = code[key].isoformat()

    return {
        "success": True,
        "data": detail,
    }


@router.get("/codes/batches/{batch_id}/export")
def admin_export_codes(
    batch_id: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    导出兑换码（管理员）

    Args:
        batch_id: 批次号
        admin: 当前管理员
        db: 数据库会话

    Returns:
        导出结果
    """
    service = AdminService(db)
    result = service.export_codes(batch_id)

    if not result["success"]:
        raise HTTPException(status_code=404, detail=result["message"])

    logger.info(f"管理员 {current_user.id} 导出兑换码: batch_id={batch_id}")

    return {
        "success": True,
        "message": result["message"],
        "batch_id": batch_id,
        "codes": result["codes"],
    }


# ── 模板管理 API ───────────────────────────────────────────────

@router.post("/marketplace/templates", response_model=TemplateResponse)
def admin_create_template(
    request: TemplateCreateRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    新增模板（管理员）

    Args:
        request: 模板创建请求
        admin: 当前管理员
        db: 数据库会话

    Returns:
        创建的模板
    """
    # 验证 tool_type
    if request.tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的 tool_type，有效值: {', '.join(VALID_TOOL_TYPES)}"
        )

    template = create_template(
        db=db,
        title=request.title,
        description=request.description,
        tool_type=request.tool_type,
        prompt_content=request.prompt_content,
        tags=request.tags,
        is_official=request.is_official,
        is_published=request.is_published,
    )

    logger.info(f"管理员 {current_user.id} 创建模板: id={template.id}, title={template.title}")

    data = template.to_dict()
    return TemplateResponse(
        id=template.id,
        title=template.title,
        description=template.description,
        tool_type=template.tool_type,
        prompt_content=template.prompt_content,
        tags=data.get("tags", []),
        is_official=template.is_official,
        is_published=template.is_published,
        import_count=template.import_count,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.put("/marketplace/templates/{template_id}", response_model=TemplateResponse)
def admin_update_template(
    template_id: int,
    request: TemplateUpdateRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    编辑模板（管理员）

    Args:
        template_id: 模板 ID
        request: 模板更新请求
        admin: 当前管理员
        db: 数据库会话

    Returns:
        更新后的模板
    """
    # 验证 tool_type（如果提供）
    if request.tool_type and request.tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的 tool_type，有效值: {', '.join(VALID_TOOL_TYPES)}"
        )

    # 构建更新字段
    update_data = {}
    if request.title is not None:
        update_data["title"] = request.title
    if request.description is not None:
        update_data["description"] = request.description
    if request.tool_type is not None:
        update_data["tool_type"] = request.tool_type
    if request.prompt_content is not None:
        update_data["prompt_content"] = request.prompt_content
    if request.tags is not None:
        update_data["tags"] = request.tags
    if request.is_official is not None:
        update_data["is_official"] = request.is_official
    if request.is_published is not None:
        update_data["is_published"] = request.is_published

    template = update_template(db=db, template_id=template_id, **update_data)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    logger.info(f"管理员 {current_user.id} 更新模板: id={template_id}")

    data = template.to_dict()
    return TemplateResponse(
        id=template.id,
        title=template.title,
        description=template.description,
        tool_type=template.tool_type,
        prompt_content=template.prompt_content,
        tags=data.get("tags", []),
        is_official=template.is_official,
        is_published=template.is_published,
        import_count=template.import_count,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.patch("/marketplace/templates/{template_id}/publish")
def admin_publish_template(
    template_id: int,
    request: TemplatePublishRequest,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    上架/下架模板（管理员）

    Args:
        template_id: 模板 ID
        request: 发布请求
        admin: 当前管理员
        db: 数据库会话

    Returns:
        操作结果
    """
    template = update_template(
        db=db,
        template_id=template_id,
        is_published=request.is_published,
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    action = "上架" if request.is_published else "下架"
    logger.info(f"管理员 {current_user.id} {action}模板: id={template_id}")

    return {
        "success": True,
        "message": f"模板已{action}",
        "template_id": template_id,
        "is_published": request.is_published,
    }


@router.delete("/marketplace/templates/{template_id}")
def admin_delete_template(
    template_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    删除模板（管理员）

    Args:
        template_id: 模板 ID
        admin: 当前管理员
        db: 数据库会话

    Returns:
        操作结果
    """
    success = delete_template(db=db, template_id=template_id)

    if not success:
        raise HTTPException(status_code=404, detail="模板不存在")

    logger.info(f"管理员 {current_user.id} 删除模板: id={template_id}")

    return {
        "success": True,
        "message": "模板已删除",
        "template_id": template_id,
    }


@router.get("/marketplace/templates")
def admin_list_templates(
    tool_type: str = None,
    include_unpublished: bool = True,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db),
):
    """
    获取模板列表（管理员，可查看未发布的）

    Args:
        tool_type: 可选，筛选工具类型
        include_unpublished: 是否包含未发布的模板
        skip: 跳过数量
        limit: 返回数量
        admin: 当前管理员
        db: 数据库会话

    Returns:
        模板列表
    """
    # 验证 tool_type
    if tool_type and tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的 tool_type，有效值: {', '.join(VALID_TOOL_TYPES)}"
        )

    # include_unpublished=True 时不过滤 is_published
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