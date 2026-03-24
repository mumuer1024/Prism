# -*- coding: utf-8 -*-
"""
预设广场 CRUD 操作

提供模板的数据库操作函数
"""

import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.models import MarketplaceTemplate

logger = logging.getLogger(__name__)

# 有效的工具类型
VALID_TOOL_TYPES = [
    "mission",
    "bounty_v2ex",
    "bounty_chrome",
    "alpha",
    "revenue",
]


def get_templates(
    db: Session,
    tool_type: Optional[str] = None,
    is_published: Optional[bool] = True,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[MarketplaceTemplate], int]:
    """
    获取模板列表

    Args:
        db: 数据库会话
        tool_type: 可选，筛选指定工具类型
        is_published: 是否只返回已发布的模板，None 表示不过滤
        skip: 跳过数量
        limit: 返回数量

    Returns:
        (模板列表, 总数)
    """
    query = db.query(MarketplaceTemplate)

    if is_published is not None:
        query = query.filter(MarketplaceTemplate.is_published == is_published)

    if tool_type:
        query = query.filter(MarketplaceTemplate.tool_type == tool_type)

    # 按导入次数降序，创建时间降序
    query = query.order_by(
        MarketplaceTemplate.import_count.desc(),
        MarketplaceTemplate.created_at.desc()
    )

    total = query.count()
    templates = query.offset(skip).limit(limit).all()

    return templates, total


def get_template_by_id(
    db: Session,
    template_id: int,
    include_unpublished: bool = False,
) -> Optional[MarketplaceTemplate]:
    """
    根据 ID 获取模板

    Args:
        db: 数据库会话
        template_id: 模板 ID
        include_unpublished: 是否包含未发布的模板

    Returns:
        模板对象或 None
    """
    query = db.query(MarketplaceTemplate).filter(MarketplaceTemplate.id == template_id)

    if not include_unpublished:
        query = query.filter(MarketplaceTemplate.is_published == True)

    return query.first()


def increment_import_count(db: Session, template_id: int) -> bool:
    """
    原子操作：增加模板导入次数

    Args:
        db: 数据库会话
        template_id: 模板 ID

    Returns:
        是否成功
    """
    try:
        # 使用 SQL 原子操作，避免并发问题
        db.execute(
            text("UPDATE marketplace_templates SET import_count = import_count + 1 WHERE id = :id"),
            {"id": template_id}
        )
        db.commit()
        return True
    except Exception as e:
        logger.error(f"增加导入次数失败: {e}")
        db.rollback()
        return False


def create_template(
    db: Session,
    title: str,
    description: str,
    tool_type: str,
    prompt_content: str,
    tags: List[str] = None,
    is_official: bool = True,
    is_published: bool = True,
) -> MarketplaceTemplate:
    """
    创建模板

    Args:
        db: 数据库会话
        title: 模板标题
        description: 模板描述
        tool_type: 工具类型
        prompt_content: Prompt 内容
        tags: 标签列表
        is_official: 是否官方模板
        is_published: 是否发布

    Returns:
        创建的模板对象
    """
    tags_json = json.dumps(tags, ensure_ascii=False) if tags else None

    template = MarketplaceTemplate(
        title=title,
        description=description,
        tool_type=tool_type,
        prompt_content=prompt_content,
        tags=tags_json,
        is_official=is_official,
        is_published=is_published,
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    logger.info(f"创建模板: id={template.id}, title={title}, tool_type={tool_type}")
    return template


def update_template(
    db: Session,
    template_id: int,
    **kwargs,
) -> Optional[MarketplaceTemplate]:
    """
    更新模板

    Args:
        db: 数据库会话
        template_id: 模板 ID
        **kwargs: 要更新的字段

    Returns:
        更新后的模板对象或 None
    """
    template = db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.id == template_id
    ).first()

    if not template:
        return None

    # 处理 tags 字段
    if 'tags' in kwargs and kwargs['tags'] is not None:
        kwargs['tags'] = json.dumps(kwargs['tags'], ensure_ascii=False)

    for key, value in kwargs.items():
        if value is not None and hasattr(template, key):
            setattr(template, key, value)

    db.commit()
    db.refresh(template)

    logger.info(f"更新模板: id={template_id}")
    return template


def delete_template(db: Session, template_id: int) -> bool:
    """
    删除模板

    Args:
        db: 数据库会话
        template_id: 模板 ID

    Returns:
        是否成功
    """
    deleted = db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.id == template_id
    ).delete()

    if deleted > 0:
        db.commit()
        logger.info(f"删除模板: id={template_id}")
        return True

    return False