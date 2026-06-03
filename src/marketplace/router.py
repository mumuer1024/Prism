# -*- coding: utf-8 -*-
"""
预设广场 API 路由 - v2.1 激活码架构

提供用户侧的模板浏览和导入接口
使用 device_id 认证替代 JWT
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.database.connection import get_db
from src.database import crud
from src.config_loader import save_user_prompt
from src.marketplace.schemas import (
    TemplateResponse,
    TemplateListResponse,
)
from src.marketplace.crud import (
    get_templates,
    get_template_by_id,
    increment_import_count,
    VALID_TOOL_TYPES,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class DeviceIdRequest(BaseModel):
    """设备 ID 请求"""
    device_id: str


class TemplateImportResponse(BaseModel):
    """模板导入响应"""
    success: bool
    message: str
    tool_type: str
    template_title: str


def get_code_id_from_device(device_id: str, db: Session) -> int:
    """通过 device_id 获取激活码 ID"""
    if not device_id:
        raise HTTPException(status_code=401, detail="缺少 device_id")
    
    activation_code = crud.get_activation_code_by_device_id(db, device_id)
    
    if not activation_code:
        raise HTTPException(status_code=401, detail="设备未激活")
    
    return activation_code.id


@router.get("/templates", response_model=TemplateListResponse)
def list_templates(
    tool_type: Optional[str] = Query(None, description="筛选工具类型"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(50, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db),
):
    """获取模板列表（公开接口）"""
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

    template_responses = []
    for t in templates:
        template_responses.append(TemplateResponse(
            id=t.id,
            title=t.title,
            description=t.description,
            tool_type=t.tool_type,
            prompt_content=None,
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
    """获取模板详情（公开接口）"""
    template = get_template_by_id(db=db, template_id=template_id, include_unpublished=False)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

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


@router.post("/templates/{template_id}/import", response_model=TemplateImportResponse)
def import_template(
    template_id: int,
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """导入模板到用户配置"""
    code_id = get_code_id_from_device(body.device_id, db)

    # 检查是否有剩余次数
    activation = crud.get_activation_code_by_id(db, code_id)
    if activation.remaining <= 0:
        raise HTTPException(status_code=403, detail="您的使用次数已用尽")

    template = get_template_by_id(db=db, template_id=template_id, include_unpublished=False)

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    success = save_user_prompt(
        code_id=code_id,
        tool_type=template.tool_type,
        content=template.prompt_content,
    )

    if not success:
        raise HTTPException(status_code=500, detail="导入失败，请稍后重试")

    increment_import_count(db=db, template_id=template_id)

    logger.info(f"用户 code_id={code_id} 成功导入模板 {template_id}")

    return TemplateImportResponse(
        success=True,
        message="导入成功，请前往配置页查看",
        tool_type=template.tool_type,
        template_title=template.title,
    )