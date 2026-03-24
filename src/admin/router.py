# -*- coding: utf-8 -*-
"""
管理员 API 路由

提供模板管理等管理员专用接口
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import Admin
from src.auth.dependencies import get_current_admin
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


# ── 模板管理 API ───────────────────────────────────────────────

@router.post("/marketplace/templates", response_model=TemplateResponse)
def admin_create_template(
    request: TemplateCreateRequest,
    admin: Admin = Depends(get_current_admin),
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

    logger.info(f"管理员 {admin.user_id} 创建模板: id={template.id}, title={template.title}")

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
    admin: Admin = Depends(get_current_admin),
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

    logger.info(f"管理员 {admin.user_id} 更新模板: id={template_id}")

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
    admin: Admin = Depends(get_current_admin),
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
    logger.info(f"管理员 {admin.user_id} {action}模板: id={template_id}")

    return {
        "success": True,
        "message": f"模板已{action}",
        "template_id": template_id,
        "is_published": request.is_published,
    }


@router.delete("/marketplace/templates/{template_id}")
def admin_delete_template(
    template_id: int,
    admin: Admin = Depends(get_current_admin),
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

    logger.info(f"管理员 {admin.user_id} 删除模板: id={template_id}")

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
    admin: Admin = Depends(get_current_admin),
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