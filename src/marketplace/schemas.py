# -*- coding: utf-8 -*-
"""
预设广场 Pydantic 模型

定义 API 请求和响应的数据结构
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class TemplateResponse(BaseModel):
    """模板响应模型"""
    id: int
    title: str
    description: str
    tool_type: str
    prompt_content: Optional[str] = None  # 列表接口不返回，详情接口返回
    tags: List[str] = Field(default_factory=list)
    is_official: bool = True
    is_published: bool = True
    import_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[TemplateResponse]
    total: int


class TemplateImportResponse(BaseModel):
    """模板导入响应"""
    success: bool
    message: str
    tool_type: Optional[str] = None
    template_title: Optional[str] = None


class TemplateCreateRequest(BaseModel):
    """模板创建请求（管理员用）"""
    title: str = Field(..., min_length=1, max_length=255, description="模板标题")
    description: str = Field(..., min_length=1, max_length=2000, description="模板描述")
    tool_type: str = Field(..., description="工具类型")
    prompt_content: str = Field(..., min_length=1, description="Prompt 内容")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    is_official: bool = Field(default=True, description="是否官方模板")
    is_published: bool = Field(default=True, description="是否发布")


class TemplateUpdateRequest(BaseModel):
    """模板更新请求（管理员用）"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1, max_length=2000)
    tool_type: Optional[str] = None
    prompt_content: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    is_official: Optional[bool] = None
    is_published: Optional[bool] = None


class TemplatePublishRequest(BaseModel):
    """模板发布/下架请求（管理员用）"""
    is_published: bool = Field(..., description="是否发布")