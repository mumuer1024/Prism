# -*- coding: utf-8 -*-
"""
预设广场模块

提供 Prompt 模板的浏览和导入功能
"""

from src.marketplace.schemas import (
    TemplateResponse,
    TemplateListResponse,
    TemplateImportResponse,
)
from src.marketplace.crud import (
    get_templates,
    get_template_by_id,
    increment_import_count,
)
from src.marketplace.router import router

__all__ = [
    "router",
    # Schemas
    "TemplateResponse",
    "TemplateListResponse",
    "TemplateImportResponse",
    # CRUD
    "get_templates",
    "get_template_by_id",
    "increment_import_count",
]