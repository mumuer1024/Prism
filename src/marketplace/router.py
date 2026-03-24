# -*- coding: utf-8 -*-
"""
预设广场 API 路由

提供用户侧的模板浏览和导入接口
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.auth.dependencies import get_current_user
from src.config_loader import save_user_prompt
from src.marketplace.schemas import (
    TemplateResponse,
    TemplateListResponse,
    TemplateImportResponse,
)
from src.marketplace.crud import (
    get_templates,
    get_template_by_id,
    increment_import_count,
    VALID_TOOL_TYPES,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/templates", response_model=TemplateListResponse)
def list_templates(
    tool_type: Optional[str] = Query(None, description="筛选工具类型"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
):
    """
    获取模板列表

    - 支持按 tool_type 筛选
    - 只返回已发布的模板
    - 按导入次数和创建时间排序
    - 列表接口不返回 prompt_content（节省带宽）
    """
    # 验证 tool_type
    if tool_type and tool_type not in VALID_TOOL_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"无效的 tool_type，有效值: {', '.join(VALID_TOOL_TYPES)}"
        )

    templates, total = get_templates(
        db=db,
        tool_type=tool_type,
        is_published=True,
        skip=skip,
        limit=limit,
    )

    # 转换为响应模型，列表接口不返回 prompt_content
    template_responses = []
    for t in templates:
        template_responses.append(TemplateResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            tool_type=t.tool_type,
            prompt_content=None,  # 列表接口不返回
            tags=t.to_dict().get("tags", []),
            is_official=t.is_official,
            is_published=t.is_published,
            import_count=t.import_count,
            created_at=t.created_at,
            updated_at=t.updated_at,
        ))

    return TemplateListResponse(templates=template_responses, total=total)


@router.get("/templates/{template_id}", response_model=TemplateResponse)
def get_template_detail(
    template_id: int,
    db: Session = Depends(get_db),
):
    """
    获取模板详情

    - 返回完整的 prompt_content
    - 只返回已发布的模板
    """
    template = get_template_by_id(db=db, template_id=template_id, include_unpublished=False)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    data = template.to_dict()
    return TemplateResponse(
        id=template.id,
        title=template.title,
        description=template.description,
        tool_type=template.tool_type,
        prompt_content=template.prompt_content,  # 详情接口返回完整内容
        tags=data.get("tags", []),
        is_official=template.is_official,
        is_published=template.is_published,
        import_count=template.import_count,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


@router.post("/templates/{template_id}/import", response_model=TemplateImportResponse)
def import_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    导入模板到用户配置

    权限校验流程：
    1. 依赖注入验证登录（未登录返回 401）
    2. 检查付费状态（usage_count > 0）
    3. 查询模板是否存在
    4. 调用 save_user_prompt 保存配置
    5. 原子操作增加 import_count

    返回：
    - success: 是否成功
    - message: 提示信息
    - tool_type: 导入的工具类型
    - template_title: 模板标题
    """
    # 1. 校验付费状态（后端二次校验，防止前端绕过）
    if current_user.usage_count <= 0:
        logger.warning(f"用户 {current_user.id} 尝试导入模板但次数不足")
        raise HTTPException(
            status_code=403,
            detail="您的使用次数已用尽，请充值后使用"
        )

    # 2. 查询模板
    template = get_template_by_id(db=db, template_id=template_id, include_unpublished=False)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 3. 保存到用户配置（复用 Phase 1 的 save_user_prompt）
    success = save_user_prompt(
        user_id=current_user.id,
        tool_type=template.tool_type,
        content=template.prompt_content,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="导入失败，请稍后重试"
        )

    # 4. 原子操作增加导入次数
    increment_import_count(db=db, template_id=template_id)

    logger.info(
        f"用户 {current_user.id} 成功导入模板 {template_id} "
        f"(title={template.title}, tool_type={template.tool_type})"
    )

    return TemplateImportResponse(
        success=True,
        message="导入成功，请前往配置页查看",
        tool_type=template.tool_type,
        template_title=template.title,
    )