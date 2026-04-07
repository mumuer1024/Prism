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
from src.database.models import User, MarketplaceTemplate, UserConfig, UserSource
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
    get_user_dailyhot_categories,
    get_user_dailyhot_categories_detail,
    update_user_dailyhot_categories,
    get_prompt_history,
    rollback_prompt,
)
from src.defaults import (
    get_default_prompt,
    get_tool_display_name,
    TOOL_TYPES,
)
from src.utils.prompt_validator import (
    PromptValidator,
    ValidationResult,
    get_placeholders_for_tool,
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
    default_prompt: Optional[str] = None  # 系统默认 Prompt
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
    is_preset: bool = False  # 是否预设数据源
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
    source_type: str = Field(default="rss", pattern="^rss$", description="数据源类型（仅支持 RSS）")
    tool_type: str = Field(..., description="所属工具类型")


class SourceUpdateRequest(BaseModel):
    """数据源更新请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    source_type: Optional[str] = Field(None, pattern="^rss$")
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
# Prompt 验证相关模型
# ============================================================================

class PlaceholderInfoResponse(BaseModel):
    """占位符信息响应"""
    placeholder: str
    description: str
    required: bool = False
    example: str = ""


class PlaceholdersResponse(BaseModel):
    """占位符列表响应"""
    tool_type: str
    placeholders: List[PlaceholderInfoResponse]


class ValidateResponse(BaseModel):
    """验证结果响应"""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    used_placeholders: List[str] = []
    missing_placeholders: List[str] = []
    unknown_placeholders: List[str] = []


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
        default_prompt=default_prompt,
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
# Prompt 版本历史 API
# ============================================================================

class PromptHistoryItem(BaseModel):
    """Prompt 历史版本项"""
    id: int
    version: int
    prompt_content: str
    change_reason: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class PromptHistoryResponse(BaseModel):
    """Prompt 历史响应"""
    tool_type: str
    tool_name: str
    current_version: int
    history: List[PromptHistoryItem]


class RollbackRequest(BaseModel):
    """回滚请求"""
    version: int = Field(..., ge=1, description="目标版本号")


@router.get(
    "/prompt/{tool_type}/history",
    response_model=PromptHistoryResponse,
    summary="获取 Prompt 版本历史",
    description="获取当前用户指定工具类型的 Prompt 版本历史",
)
async def get_prompt_version_history(
    tool_type: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
):
    """获取 Prompt 版本历史"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {tool_type}"
        )

    history = get_prompt_history(current_user.id, tool_type, limit)

    current_version = max([h["version"] for h in history], default=0)

    return PromptHistoryResponse(
        tool_type=tool_type,
        tool_name=get_tool_display_name(tool_type),
        current_version=current_version,
        history=[PromptHistoryItem(**h) for h in history],
    )


@router.post(
    "/prompt/{tool_type}/rollback",
    response_model=MessageResponse,
    summary="回滚 Prompt 到指定版本",
    description="将当前用户的 Prompt 回滚到指定的历史版本",
)
async def rollback_prompt_version(
    tool_type: str,
    request: RollbackRequest,
    current_user: User = Depends(get_current_user),
):
    """回滚 Prompt 到指定版本"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {tool_type}"
        )

    success = rollback_prompt(current_user.id, tool_type, request.version)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"版本 {request.version} 不存在或回滚失败"
        )

    return MessageResponse(message=f"Prompt 已回滚到版本 {request.version}")


# ============================================================================
# Prompt 验证 API
# ============================================================================

@router.get(
    "/prompt/{tool_type}/placeholders",
    response_model=PlaceholdersResponse,
    summary="获取支持的占位符",
    description="获取指定工具类型支持的占位符列表及其描述",
)
async def get_tool_placeholders(
    tool_type: str,
):
    """获取工具支持的占位符列表"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {tool_type}。有效类型: {', '.join(TOOL_TYPES)}"
        )

    placeholders = get_placeholders_for_tool(tool_type)

    return PlaceholdersResponse(
        tool_type=tool_type,
        placeholders=[PlaceholderInfoResponse(**p) for p in placeholders],
    )


@router.post(
    "/prompt/{tool_type}/validate",
    response_model=ValidateResponse,
    summary="验证 Prompt",
    description="验证 Prompt 内容的有效性，检查长度和占位符",
)
async def validate_prompt_content(
    tool_type: str,
    request: PromptUpdateRequest,
):
    """验证 Prompt 内容"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {tool_type}。有效类型: {', '.join(TOOL_TYPES)}"
        )

    validator = PromptValidator()
    result = validator.validate(tool_type, request.content)

    return ValidateResponse(
        is_valid=result.is_valid,
        errors=result.errors,
        warnings=result.warnings,
        used_placeholders=result.used_placeholders,
        missing_placeholders=result.missing_placeholders,
        unknown_placeholders=result.unknown_placeholders,
    )


@router.get(
    "/prompt/placeholders/all",
    summary="获取所有工具的占位符",
    description="获取所有工具类型支持的占位符映射（公开接口）",
)
async def get_all_placeholders():
    """获取所有工具的占位符映射"""
    validator = PromptValidator()
    all_placeholders = validator.get_all_placeholders()

    result = {}
    for tool_type, placeholders in all_placeholders.items():
        result[tool_type] = [p.to_dict() for p in placeholders]

    return {"placeholders": result}


# ============================================================================
# 预设广场 API
# ============================================================================

class TemplateResponse(BaseModel):
    """预设模板响应"""
    id: int
    title: str
    description: str
    tool_type: str
    tool_name: str
    tags: List[str] = []
    is_official: bool
    import_count: int
    created_at: str

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """预设模板列表响应"""
    templates: List[TemplateResponse]
    total: int


class TemplateDetailResponse(BaseModel):
    """预设模板详情响应"""
    id: int
    title: str
    description: str
    tool_type: str
    tool_name: str
    prompt_content: str
    tags: List[str] = []
    is_official: bool
    import_count: int
    created_at: str

    class Config:
        from_attributes = True


@router.get(
    "/marketplace",
    response_model=TemplateListResponse,
    summary="获取预设广场模板列表",
    description="获取预设广场的 Prompt 模板列表",
)
async def list_marketplace_templates(
    tool_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取预设广场模板列表"""
    query = db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.is_published == True,
    )

    if tool_type:
        query = query.filter(MarketplaceTemplate.tool_type == tool_type)

    total = query.count()
    offset = (page - 1) * limit
    templates = query.order_by(MarketplaceTemplate.import_count.desc()).offset(offset).limit(limit).all()

    return TemplateListResponse(
        templates=[_template_to_response(t) for t in templates],
        total=total,
    )


@router.get(
    "/marketplace/{template_id}",
    response_model=TemplateDetailResponse,
    summary="获取预设模板详情",
    description="获取指定预设模板的详细信息",
)
async def get_marketplace_template(
    template_id: int,
    db: Session = Depends(get_db),
):
    """获取预设模板详情"""
    template = db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.id == template_id,
        MarketplaceTemplate.is_published == True,
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    return _template_to_detail_response(template)


@router.post(
    "/marketplace/{template_id}/import",
    response_model=MessageResponse,
    summary="导入预设模板",
    description="将预设广场的模板导入到用户的 Prompt 配置中",
)
async def import_marketplace_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """导入预设模板"""
    template = db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.id == template_id,
        MarketplaceTemplate.is_published == True,
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="模板不存在"
        )

    # 保存到用户配置
    success = save_user_prompt(
        current_user.id,
        template.tool_type,
        template.prompt_content,
        change_reason=f"从预设广场导入: {template.title}"
    )

    if success:
        # 增加导入计数
        template.import_count += 1
        db.commit()

    return MessageResponse(message=f"模板 '{template.title}' 已导入到 {get_tool_display_name(template.tool_type)}")


def _template_to_response(template: MarketplaceTemplate) -> TemplateResponse:
    """转换模板为响应格式"""
    import json
    tags = []
    if template.tags:
        try:
            tags = json.loads(template.tags)
        except:
            tags = []

    return TemplateResponse(
        id=template.id,
        title=template.title,
        description=template.description,
        tool_type=template.tool_type,
        tool_name=get_tool_display_name(template.tool_type),
        tags=tags,
        is_official=template.is_official,
        import_count=template.import_count,
        created_at=template.created_at.isoformat() if template.created_at else "",
    )


def _template_to_detail_response(template: MarketplaceTemplate) -> TemplateDetailResponse:
    """转换模板为详情响应格式"""
    import json
    tags = []
    if template.tags:
        try:
            tags = json.loads(template.tags)
        except:
            tags = []

    return TemplateDetailResponse(
        id=template.id,
        title=template.title,
        description=template.description,
        tool_type=template.tool_type,
        tool_name=get_tool_display_name(template.tool_type),
        prompt_content=template.prompt_content,
        tags=tags,
        is_official=template.is_official,
        import_count=template.import_count,
        created_at=template.created_at.isoformat() if template.created_at else "",
    )


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
    description="添加用户自定义数据源（仅支持 RSS）",
)
async def create_source(
    request: SourceCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """添加自定义数据源"""
    # 验证 tool_type
    valid_tool_types = ["mission", "alpha", "bounty"]
    if request.tool_type not in valid_tool_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的工具类型: {request.tool_type}。有效类型: {', '.join(valid_tool_types)}"
        )

    # 仅支持 RSS
    if request.source_type != "rss":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="仅支持 RSS 格式数据源"
        )

    # 检查上限
    current_count = db.query(UserSource).filter(UserSource.user_id == current_user.id).count()
    is_paid = current_user.usage_count > 0
    max_limit = 10 if is_paid else 3

    if current_count >= max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"已达上限（{max_limit}条），{'升级后可添加更多' if not is_paid else '请删除现有数据源'}"
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


# ============================================================================
# DailyHotApi 分类配置 API
# ============================================================================

class DailyHotCategoryItem(BaseModel):
    """分类配置项"""
    category: str
    is_enabled: bool


class DailyHotCategoriesResponse(BaseModel):
    """分类配置响应"""
    enabled: List[str]
    available: List[dict]


class DailyHotCategoriesUpdateRequest(BaseModel):
    """分类更新请求"""
    categories: List[str] = Field(..., min_length=1, description="要启用的分类列表")


@router.get(
    "/dailyhot/categories",
    response_model=DailyHotCategoriesResponse,
    summary="获取 DailyHotApi 分类配置",
    description="获取当前用户的 DailyHotApi 分类配置及可用分类列表",
)
async def get_dailyhot_categories(
    current_user: User = Depends(get_current_user),
):
    """获取 DailyHotApi 分类配置"""
    # 获取用户启用的分类
    enabled = get_user_dailyhot_categories(current_user.id)

    # 获取分类映射
    from src.sensors.dailyhot_sensor import CATEGORY_MAP

    available = []
    for key, data in CATEGORY_MAP.items():
        available.append({
            "key": key,
            "label": data["label"],
            "platforms": [p["name"] for p in data["platforms"]],
        })

    return DailyHotCategoriesResponse(
        enabled=enabled,
        available=available,
    )


@router.put(
    "/dailyhot/categories",
    response_model=MessageResponse,
    summary="更新 DailyHotApi 分类配置",
    description="更新当前用户的 DailyHotApi 分类启用状态",
)
async def update_dailyhot_categories(
    request: DailyHotCategoriesUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    """更新 DailyHotApi 分类配置"""
    success = update_user_dailyhot_categories(current_user.id, request.categories)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="更新分类配置失败，请确保至少选择一个有效分类"
        )

    return MessageResponse(message=f"分类配置已更新: {', '.join(request.categories)}")


@router.get(
    "/dailyhot/category-map",
    summary="获取分类映射",
    description="获取所有分类与子平台的映射关系（公开接口，无需登录）",
)
async def get_dailyhot_category_map():
    """获取分类映射（公开接口）"""
    from src.sensors.dailyhot_sensor import CATEGORY_MAP

    result = []
    for key, data in CATEGORY_MAP.items():
        result.append({
            "key": key,
            "label": data["label"],
            "platforms": data["platforms"],
        })

    return {"categories": result}


# ============================================================================
# 用户配置 API（GitHub Token 等）
# ============================================================================

class UserConfigResponse(BaseModel):
    """用户配置响应"""
    config_key: str
    has_value: bool
    updated_at: Optional[str] = None


class UserConfigUpdateRequest(BaseModel):
    """用户配置更新请求"""
    value: str = Field(..., min_length=1, max_length=2000, description="配置值")


class UserConfigListResponse(BaseModel):
    """用户配置列表响应"""
    configs: List[UserConfigResponse]


# 支持的用户配置键
SUPPORTED_CONFIG_KEYS = {
    "github_token": {
        "name": "GitHub Token",
        "description": "GitHub Personal Access Token，用于 GitHub Trending 数据源",
        "placeholder": "ghp_xxxx 或 github_pat_xxxx",
    },
    "producthunt_token": {
        "name": "Product Hunt Token",
        "description": "Product Hunt API Token，用于 Product Hunt 数据源",
        "placeholder": "API Token",
    },
    "tavily_token": {
        "name": "Tavily Token",
        "description": "Tavily AI 搜索 API Token",
        "placeholder": "tvly-xxxx",
    },
}


@router.get(
    "/keys",
    summary="获取支持的配置键列表",
    description="获取支持的用户配置键及其描述（公开接口）",
)
async def get_supported_config_keys():
    """获取支持的配置键列表"""
    return {"keys": SUPPORTED_CONFIG_KEYS}


@router.get(
    "/keys/values",
    response_model=UserConfigListResponse,
    summary="获取用户所有配置",
    description="获取当前用户的所有配置值（敏感值已脱敏）",
)
async def get_user_config_values(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户所有配置"""
    configs = db.query(UserConfig).filter(
        UserConfig.user_id == current_user.id,
    ).all()

    config_map = {c.config_key: c for c in configs}

    result = []
    for key in SUPPORTED_CONFIG_KEYS:
        config = config_map.get(key)
        result.append(UserConfigResponse(
            config_key=key,
            has_value=config is not None and bool(config.config_value),
            updated_at=config.updated_at.isoformat() if config and config.updated_at else None,
        ))

    return UserConfigListResponse(configs=result)


@router.get(
    "/keys/{config_key}",
    response_model=UserConfigResponse,
    summary="获取指定配置",
    description="获取当前用户指定配置的状态（敏感值不返回）",
)
async def get_user_config(
    config_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取指定配置"""
    if config_key not in SUPPORTED_CONFIG_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的配置键: {config_key}"
        )

    config = db.query(UserConfig).filter(
        UserConfig.user_id == current_user.id,
        UserConfig.config_key == config_key,
    ).first()

    return UserConfigResponse(
        config_key=config_key,
        has_value=config is not None and bool(config.config_value),
        updated_at=config.updated_at.isoformat() if config and config.updated_at else None,
    )


@router.put(
    "/keys/{config_key}",
    response_model=MessageResponse,
    summary="更新配置",
    description="更新当前用户的指定配置",
)
async def update_user_config(
    config_key: str,
    request: UserConfigUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新配置"""
    if config_key not in SUPPORTED_CONFIG_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的配置键: {config_key}"
        )

    # 查找现有配置
    config = db.query(UserConfig).filter(
        UserConfig.user_id == current_user.id,
        UserConfig.config_key == config_key,
    ).first()

    if config:
        config.config_value = request.value
    else:
        config = UserConfig(
            user_id=current_user.id,
            config_key=config_key,
            config_value=request.value,
        )
        db.add(config)

    db.commit()

    key_info = SUPPORTED_CONFIG_KEYS[config_key]
    return MessageResponse(message=f"{key_info['name']} 已保存")


@router.delete(
    "/keys/{config_key}",
    response_model=MessageResponse,
    summary="删除配置",
    description="删除当前用户的指定配置",
)
async def delete_user_config(
    config_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除配置"""
    if config_key not in SUPPORTED_CONFIG_KEYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的配置键: {config_key}"
        )

    deleted = db.query(UserConfig).filter(
        UserConfig.user_id == current_user.id,
        UserConfig.config_key == config_key,
    ).delete()

    db.commit()

    key_info = SUPPORTED_CONFIG_KEYS[config_key]
    if deleted > 0:
        return MessageResponse(message=f"{key_info['name']} 已删除")
    else:
        return MessageResponse(message=f"{key_info['name']} 未配置")