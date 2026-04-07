# -*- coding: utf-8 -*-
"""
用户配置 API 路由 - v2.1 激活码架构

提供用户自定义 Prompt 和数据源配置的 REST API 端点
使用 /api/user-config 前缀
使用 device_id 进行认证（替代原有的 JWT）
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.database.connection import get_db, get_db_context
from src.database import crud
from src.database.models import MarketplaceTemplate
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
from src.defaults import get_default_prompt, get_tool_display_name, TOOL_TYPES
from src.utils.prompt_validator import PromptValidator, get_placeholders_for_tool

router = APIRouter()


# ============================================================================
# 依赖注入：通过 device_id 获取 code_id
# ============================================================================

def get_code_id_from_device(device_id: str, db: Session) -> int:
    """
    通过 device_id 获取关联的激活码 ID
    
    Raises:
        HTTPException: 设备未绑定激活码
    """
    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少 device_id 参数"
        )
    
    activation_code = crud.get_activation_code_by_device_id(db, device_id)
    
    if not activation_code:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="设备未激活"
        )
    
    return activation_code.id


# ============================================================================
# Pydantic 模型定义
# ============================================================================

class DeviceIdRequest(BaseModel):
    """设备 ID 请求基类"""
    device_id: str = Field(..., min_length=1, description="设备 ID")


class PromptResponse(BaseModel):
    """Prompt 配置响应"""
    tool_type: str
    tool_name: str
    has_custom: bool
    prompt_content: str
    default_prompt: Optional[str] = None
    is_active: bool = True


class PromptUpdateRequest(BaseModel):
    """Prompt 更新请求"""
    device_id: str
    content: str = Field(..., min_length=1, max_length=50000)


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
    is_preset: bool = False
    is_user_defined: bool = False


class SourceCreateRequest(BaseModel):
    """数据源创建请求"""
    device_id: str
    name: str = Field(..., min_length=1, max_length=255)
    url: str = Field(..., min_length=1, max_length=500)
    source_type: str = Field(default="rss", pattern="^rss$")
    tool_type: str


class SourceUpdateRequest(BaseModel):
    """数据源更新请求"""
    device_id: str
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[str] = Field(None, min_length=1, max_length=500)
    is_enabled: Optional[bool] = None


class SourceToggleRequest(BaseModel):
    """数据源启用/禁用请求"""
    device_id: str
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

@router.post("/prompt", response_model=PromptListResponse)
async def list_prompts(
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """获取所有 Prompt 配置"""
    code_id = get_code_id_from_device(body.device_id, db)
    prompts = get_all_user_prompts(code_id)
    return PromptListResponse(prompts=[PromptResponse(**p) for p in prompts])


@router.post("/prompt/{tool_type}", response_model=PromptResponse)
async def get_prompt(
    tool_type: str,
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """获取指定工具的 Prompt 配置"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的工具类型: {tool_type}")

    code_id = get_code_id_from_device(body.device_id, db)
    prompt_content = get_user_prompt(code_id, tool_type)
    default_prompt = get_default_prompt(tool_type)

    with get_db_context() as db_ctx:
        record = get_user_prompt_record(code_id, tool_type, db_ctx)

    has_custom = record is not None and record.is_active

    return PromptResponse(
        tool_type=tool_type,
        tool_name=get_tool_display_name(tool_type),
        has_custom=has_custom,
        prompt_content=prompt_content,
        default_prompt=default_prompt,
        is_active=record.is_active if record else True,
    )


@router.put("/prompt/{tool_type}", response_model=MessageResponse)
async def update_prompt(
    tool_type: str,
    body: PromptUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新 Prompt 配置"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的工具类型: {tool_type}")

    code_id = get_code_id_from_device(body.device_id, db)
    success = save_user_prompt(code_id, tool_type, body.content)

    if not success:
        raise HTTPException(status_code=500, detail="保存 Prompt 失败")

    return MessageResponse(message=f"{get_tool_display_name(tool_type)} Prompt 已更新")


@router.delete("/prompt/{tool_type}", response_model=MessageResponse)
async def reset_prompt(
    tool_type: str,
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """重置 Prompt 配置"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的工具类型: {tool_type}")

    code_id = get_code_id_from_device(body.device_id, db)
    success = reset_user_prompt(code_id, tool_type)

    if not success:
        raise HTTPException(status_code=500, detail="重置 Prompt 失败")

    return MessageResponse(message=f"{get_tool_display_name(tool_type)} Prompt 已重置")


# ============================================================================
# Prompt 版本历史 API
# ============================================================================

class PromptHistoryItem(BaseModel):
    id: int
    version: int
    prompt_content: str
    change_reason: Optional[str] = None
    created_at: str


class PromptHistoryResponse(BaseModel):
    tool_type: str
    tool_name: str
    current_version: int
    history: List[PromptHistoryItem]


class RollbackRequest(BaseModel):
    device_id: str
    version: int = Field(..., ge=1)


@router.post("/prompt/{tool_type}/history", response_model=PromptHistoryResponse)
async def get_prompt_version_history(
    tool_type: str,
    body: DeviceIdRequest,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """获取 Prompt 版本历史"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的工具类型: {tool_type}")

    code_id = get_code_id_from_device(body.device_id, db)
    history = get_prompt_history(code_id, tool_type, limit)
    current_version = max([h["version"] for h in history], default=0)

    return PromptHistoryResponse(
        tool_type=tool_type,
        tool_name=get_tool_display_name(tool_type),
        current_version=current_version,
        history=[PromptHistoryItem(**h) for h in history],
    )


@router.post("/prompt/{tool_type}/rollback", response_model=MessageResponse)
async def rollback_prompt_version(
    tool_type: str,
    body: RollbackRequest,
    db: Session = Depends(get_db),
):
    """回滚 Prompt 到指定版本"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的工具类型: {tool_type}")

    code_id = get_code_id_from_device(body.device_id, db)
    success = rollback_prompt(code_id, tool_type, body.version)

    if not success:
        raise HTTPException(status_code=404, detail=f"版本 {body.version} 不存在或回滚失败")

    return MessageResponse(message=f"Prompt 已回滚到版本 {body.version}")


# ============================================================================
# Prompt 验证 API
# ============================================================================

class PlaceholdersResponse(BaseModel):
    tool_type: str
    placeholders: List[dict]


class ValidateResponse(BaseModel):
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    used_placeholders: List[str] = []
    missing_placeholders: List[str] = []
    unknown_placeholders: List[str] = []


@router.get("/prompt/{tool_type}/placeholders", response_model=PlaceholdersResponse)
async def get_tool_placeholders(tool_type: str):
    """获取工具支持的占位符列表"""
    if tool_type not in TOOL_TYPES:
        raise HTTPException(status_code=400, detail=f"无效的工具类型: {tool_type}")

    placeholders = get_placeholders_for_tool(tool_type)
    return PlaceholdersResponse(tool_type=tool_type, placeholders=placeholders)


@router.get("/prompt/placeholders/all")
async def get_all_placeholders():
    """获取所有工具的占位符映射"""
    validator = PromptValidator()
    all_placeholders = validator.get_all_placeholders()
    return {"placeholders": {k: [p.to_dict() for p in v] for k, v in all_placeholders.items()}}


# ============================================================================
# 预设广场 API（公开接口，无需认证）
# ============================================================================

class TemplateResponse(BaseModel):
    id: int
    title: str
    description: str
    tool_type: str
    tool_name: str
    tags: List[str] = []
    is_official: bool
    import_count: int
    created_at: str


class TemplateListResponse(BaseModel):
    templates: List[TemplateResponse]
    total: int


class ImportTemplateRequest(BaseModel):
    device_id: str


@router.get("/marketplace", response_model=TemplateListResponse)
async def list_marketplace_templates(
    tool_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取预设广场模板列表"""
    query = db.query(MarketplaceTemplate).filter(MarketplaceTemplate.is_published == True)

    if tool_type:
        query = query.filter(MarketplaceTemplate.tool_type == tool_type)

    total = query.count()
    offset = (page - 1) * limit
    templates = query.order_by(MarketplaceTemplate.import_count.desc()).offset(offset).limit(limit).all()

    return TemplateListResponse(
        templates=[_template_to_response(t) for t in templates],
        total=total,
    )


@router.post("/marketplace/{template_id}/import", response_model=MessageResponse)
async def import_marketplace_template(
    template_id: int,
    body: ImportTemplateRequest,
    db: Session = Depends(get_db),
):
    """导入预设模板"""
    code_id = get_code_id_from_device(body.device_id, db)

    template = db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.id == template_id,
        MarketplaceTemplate.is_published == True,
    ).first()

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    success = save_user_prompt(code_id, template.tool_type, template.prompt_content)

    if success:
        template.import_count += 1
        db.commit()

    return MessageResponse(message=f"模板 '{template.title}' 已导入")


def _template_to_response(template: MarketplaceTemplate) -> TemplateResponse:
    import json
    tags = []
    if template.tags:
        try:
            tags = json.loads(template.tags)
        except:
            pass

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


# ============================================================================
# 数据源配置 API
# ============================================================================

@router.post("/sources", response_model=SourceListResponse)
async def list_all_sources(
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """获取所有数据源配置"""
    code_id = get_code_id_from_device(body.device_id, db)
    sources = get_all_user_sources(code_id)
    return SourceListResponse(sources=[SourceResponse(**s) for s in sources])


@router.post("/sources/{tool_type}", response_model=SourceListResponse)
async def list_sources_by_tool(
    tool_type: str,
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """获取指定工具的数据源配置"""
    code_id = get_code_id_from_device(body.device_id, db)
    sources = get_all_user_sources(code_id, tool_type)
    return SourceListResponse(sources=[SourceResponse(**s) for s in sources])


@router.post("/sources/add", response_model=SourceResponse, status_code=201)
async def create_source(
    body: SourceCreateRequest,
    db: Session = Depends(get_db),
):
    """添加自定义数据源"""
    valid_tool_types = ["mission", "alpha", "bounty"]
    if body.tool_type not in valid_tool_types:
        raise HTTPException(status_code=400, detail=f"无效的工具类型: {body.tool_type}")

    if body.source_type != "rss":
        raise HTTPException(status_code=400, detail="仅支持 RSS 格式数据源")

    code_id = get_code_id_from_device(body.device_id, db)

    source_id = add_user_source(
        code_id=code_id,
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        tool_type=body.tool_type,
    )

    if not source_id:
        raise HTTPException(status_code=500, detail="添加数据源失败")

    return SourceResponse(
        id=source_id,
        name=body.name,
        url=body.url,
        source_type=body.source_type,
        tool_type=body.tool_type,
        is_enabled=True,
        is_user_defined=True,
    )


@router.put("/sources/{source_id}", response_model=MessageResponse)
async def update_source(
    source_id: int,
    body: SourceUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新数据源配置"""
    code_id = get_code_id_from_device(body.device_id, db)

    success = update_user_source(
        source_id=source_id,
        code_id=code_id,
        name=body.name,
        url=body.url,
        is_enabled=body.is_enabled,
    )

    if not success:
        raise HTTPException(status_code=404, detail="数据源不存在或无权限修改")

    return MessageResponse(message="数据源已更新")


@router.delete("/sources/{source_id}", response_model=MessageResponse)
async def remove_source(
    source_id: int,
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """删除数据源"""
    code_id = get_code_id_from_device(body.device_id, db)
    success = delete_user_source(source_id, code_id)

    if not success:
        raise HTTPException(status_code=404, detail="数据源不存在或无权限删除")

    return MessageResponse(message="数据源已删除")


@router.patch("/sources/{source_id}/toggle", response_model=MessageResponse)
async def toggle_source(
    source_id: int,
    body: SourceToggleRequest,
    db: Session = Depends(get_db),
):
    """启用/禁用数据源"""
    code_id = get_code_id_from_device(body.device_id, db)
    success = toggle_user_source(source_id, code_id, body.enabled)

    if not success:
        raise HTTPException(status_code=404, detail="数据源不存在或无权限修改")

    status_text = "已启用" if body.enabled else "已禁用"
    return MessageResponse(message=f"数据源{status_text}")


# ============================================================================
# DailyHotApi 分类配置 API
# ============================================================================

class DailyHotCategoriesResponse(BaseModel):
    enabled: List[str]
    available: List[dict]


class DailyHotCategoriesUpdateRequest(BaseModel):
    device_id: str
    categories: List[str] = Field(..., min_length=1)


@router.post("/dailyhot/categories", response_model=DailyHotCategoriesResponse)
async def get_dailyhot_categories(
    body: DeviceIdRequest,
    db: Session = Depends(get_db),
):
    """获取 DailyHotApi 分类配置"""
    code_id = get_code_id_from_device(body.device_id, db)
    enabled = get_user_dailyhot_categories(code_id)

    from src.sensors.dailyhot_sensor import CATEGORY_MAP
    available = [{"key": k, "label": v["label"], "platforms": [p["name"] for p in v["platforms"]]} for k, v in CATEGORY_MAP.items()]

    return DailyHotCategoriesResponse(enabled=enabled, available=available)


@router.put("/dailyhot/categories", response_model=MessageResponse)
async def update_dailyhot_categories(
    body: DailyHotCategoriesUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新 DailyHotApi 分类配置"""
    code_id = get_code_id_from_device(body.device_id, db)
    success = update_user_dailyhot_categories(code_id, body.categories)

    if not success:
        raise HTTPException(status_code=400, detail="更新分类配置失败")

    return MessageResponse(message=f"分类配置已更新: {', '.join(body.categories)}")


@router.get("/dailyhot/category-map")
async def get_dailyhot_category_map():
    """获取分类映射（公开接口）"""
    from src.sensors.dailyhot_sensor import CATEGORY_MAP
    return {"categories": [{"key": k, "label": v["label"], "platforms": v["platforms"]} for k, v in CATEGORY_MAP.items()]}