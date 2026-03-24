# -*- coding: utf-8 -*-
"""
用户配置 API 路由

提供用户自定义 Prompt 和数据源配置的 REST API 端点
使用 /api/user-config 前缀，避免与现有 /api/config 冲突
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.connection import get_db, get_db_context
from src.database.models import User
from src.auth.dependencies import get_current_user
from src.config_loader import (
    get_user_prompt,
    get_user_prompt_record,
    save_user_prompt,
    reset_user_prompt,
    get_all_user_prompts,
    get_user_sources,
    get_all_user_sources,
    add_user_source,
    update_user_source,
    delete_user_source,
    toggle_user_source,
)
from src.defaults import (
    get_default_prompt,
    get_tool_display_name,
    TOOL_TYPES,
)

router = APIRouter()


# ============================================================================
# Pydantic 模型定义
# ============================================================================

class PromptResponse(BaseModel):
    """Prompt 配置响应"""
    tool_type: str
    tool_name: str
    has_custom: bool
    prompt_content: str
    is_active: bool = True

    class Config:
        from_attributes = True


class PromptUpdateRequest(BaseModel):
    """Prompt 更新请求"""
    content: str = Field(..., min_length=1, max_length=50000, description="Prompt 内容")


class PromptListResponse(BaseModel):
    """Prompt 列表响应"""
    prompts: List[PromptResponse]


class SourceResponse(BaseModel):
    """数据源响应"""
    id: Optional[int] = None
    name: str
    url: str
    source_type: str
    tool_type: str
    is_enabled: bool = True
    is_user_defined: bool = False
    requires_key: Optional[str] = None
    icon: Optional[str] = None
    desc: Optional[str] = None

    class Config:
        from_attributes = True


class SourceCreateRequest(BaseModel):
    """数据源创建请求"""
    name: str = Field(..., min_length=1, max_length=255, description="数据源名称")
    url: str = Field(..., min_length=1, max_length=500, description="数据源 URL")
    source_type: str = Field(..., pattern="^(rss|webpage)$", description="数据源类型")
    tool_type: str = Field(..., description="所属工具类型")


class SourceUpdateRequest(BaseModel):
    """数据源更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    source_type: Optional[str] = Field(None, pattern="^(rss|webpage)$")
    tool_type: Optional[str] = None
    is_enabled: Optional[bool] = None


class SourceToggleRequest(BaseModel):
    """数据源启用/禁用请求"""
    enabled: bool


class SourceListResponse(BaseModel):
    """数据源列表响应"""
    sources: List[SourceResponse]


class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
    success: bool = True


# ============================================================================
# Prompt 配置 API
# ============================================================================

@router.get(
    "/prompt",
    response_model=PromptListResponse,
    summary="获取所有 Prompt 配置",
    description="获取当前用户所有工具类型的 Prompt 配置",
)
async def list_prompts(
    current_user: User = Depends(get_current_user),
):
    """获取所有 Prompt 配置"""
    prompts = get_all_user_prompts(current_user.id)
    return PromptListResponse(
        prompts=[PromptResponse(**p) for p in prompts]
    )


@router.get(
    "/prompt/{tool_type}",
    response_model=PromptResponse,
    summary="获取指定工具的 Prompt 配置",
    description="获取当前用户指定工具类型的 Prompt 配置",
)
async def get_prompt(
    tool_type: str,
    current_user: User = Depends(get_current_user),
):
    """获取指定工具的 Prompt 配置"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {tool_type}。有效类型: {', '.join(TOOL_TYPES)}"
        )

    prompt_content = get_user_prompt(current_user.id, tool_type)
    default_prompt = get_default_prompt(tool_type)
    
    with get_db_context() as db:
        record = get_user_prompt_record(current_user.id, tool_type, db)
    
    has_custom = record is not None and record.is_active

    return PromptResponse(
        tool_type=tool_type,
        tool_name=get_tool_display_name(tool_type),
        has_custom=has_custom,
        prompt_content=prompt_content,
        is_active=record.is_active if record else True,
    )


@router.put(
    "/prompt/{tool_type}",
    response_model=MessageResponse,
    summary="更新 Prompt 配置",
    description="更新当前用户指定工具类型的 Prompt 配置",
)
async def update_prompt(
    tool_type: str,
    request: PromptUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """更新 Prompt 配置"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {tool_type}。有效类型: {', '.join(TOOL_TYPES)}"
        )

    success = save_user_prompt(current_user.id, tool_type, request.content)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="保存 Prompt 失败"
        )

    return MessageResponse(message=f"{get_tool_display_name(tool_type)} Prompt 已更新")


@router.delete(
    "/prompt/{tool_type}",
    response_model=MessageResponse,
    summary="重置 Prompt 配置",
    description="重置当前用户指定工具类型的 Prompt 为默认值",
)
async def reset_prompt(
    tool_type: str,
    current_user: User = Depends(get_current_user),
):
    """重置 Prompt 配置"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {tool_type}。有效类型: {', '.join(TOOL_TYPES)}"
        )

    success = reset_user_prompt(current_user.id, tool_type)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置 Prompt 失败"
        )

    return MessageResponse(message=f"{get_tool_display_name(tool_type)} Prompt 已重置为默认值")


# ============================================================================
# 数据源配置 API
# ============================================================================

@router.get(
    "/sources",
    response_model=SourceListResponse,
    summary="获取所有数据源配置",
    description="获取当前用户所有数据源配置（包含官方预设和自定义）",
)
async def list_all_sources(
    current_user: User = Depends(get_current_user),
):
    """获取所有数据源配置"""
    sources = get_all_user_sources(current_user.id)
    return SourceListResponse(
        sources=[SourceResponse(**s) for s in sources]
    )


@router.get(
    "/sources/{tool_type}",
    response_model=SourceListResponse,
    summary="获取指定工具的数据源配置",
    description="获取当前用户指定工具类型的数据源配置",
)
async def list_sources_by_tool(
    tool_type: str,
    current_user: User = Depends(get_current_user),
):
    """获取指定工具的数据源配置"""
    sources = get_all_user_sources(current_user.id, tool_type)
    return SourceListResponse(
        sources=[SourceResponse(**s) for s in sources]
    )


@router.post(
    "/sources",
    response_model=SourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加自定义数据源",
    description="添加用户自定义数据源（RSS 或网页）",
)
async def create_source(
    request: SourceCreateRequest,
    current_user: User = Depends(get_current_user),
):
    """添加自定义数据源"""
    # 验证 tool_type
    valid_tool_types = ["mission", "alpha", "bounty"]
    if request.tool_type not in valid_tool_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {request.tool_type}。有效类型: {', '.join(valid_tool_types)}"
        )

    source_id = add_user_source(
        user_id=current_user.id,
        name=request.name,
        url=request.url,
        source_type=request.source_type,
        tool_type=request.tool_type,
    )

    if not source_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="添加数据源失败"
        )

    return SourceResponse(
        id=source_id,
        name=request.name,
        url=request.url,
        source_type=request.source_type,
        tool_type=request.tool_type,
        is_enabled=True,
        is_user_defined=True,
    )


@router.put(
    "/sources/{source_id}",
    response_model=MessageResponse,
    summary="更新数据源配置",
    description="更新用户自定义数据源配置",
)
async def update_source(
    source_id: int,
    request: SourceUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """更新数据源配置"""
    success = update_user_source(
        source_id=source_id,
        user_id=current_user.id,
        name=request.name,
        url=request.url,
        source_type=request.source_type,
        tool_type=request.tool_type,
        is_enabled=request.is_enabled,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据源不存在或无权限修改"
        )

    return MessageResponse(message="数据源已更新")


@router.delete(
    "/sources/{source_id}",
    response_model=MessageResponse,
    summary="删除数据源",
    description="删除用户自定义数据源",
)
async def remove_source(
    source_id: int,
    current_user: User = Depends(get_current_user),
):
    """删除数据源"""
    success = delete_user_source(source_id, current_user.id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据源不存在或无权限删除"
        )

    return MessageResponse(message="数据源已删除")


@router.patch(
    "/sources/{source_id}/toggle",
    response_model=MessageResponse,
    summary="启用/禁用数据源",
    description="启用或禁用用户数据源",
)
async def toggle_source(
    source_id: int,
    request: SourceToggleRequest,
    current_user: User = Depends(get_current_user),
):
    """启用/禁用数据源"""
    success = toggle_user_source(source_id, current_user.id, request.enabled)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="数据源不存在或无权限修改"
        )

    status_text = "已启用" if request.enabled else "已禁用"
    return MessageResponse(message=f"数据源{status_text}")