# -*- coding: utf-8 -*-
"""
配置读取层 (Config Loader)

提供用户配置的读取、写入、重置功能
支持 Prompt 配置和数据源配置
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy.orm import Session

from src.database.connection import get_db_context
from src.database.models import UserPrompt, UserSource
from src.defaults import (
    get_default_prompt,
    get_default_sources,
    get_official_sources,
    get_tool_display_name,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Prompt 配置相关函数
# ============================================================================

def get_user_prompt(user_id: int, tool_type: str) -> str:
    """
    获取用户自定义 Prompt，无则返回默认 Prompt

    Args:
        user_id: 用户 ID
        tool_type: 工具类型 (mission / bounty_v2ex / bounty_chrome / alpha / revenue)

    Returns:
        Prompt 内容字符串
    """
    with get_db_context() as db:
        prompt = db.query(UserPrompt).filter(
            UserPrompt.user_id == user_id,
            UserPrompt.tool_type == tool_type,
            UserPrompt.is_active == True,
        ).first()

        if prompt:
            logger.debug(f"使用用户自定义 Prompt: user_id={user_id}, tool_type={tool_type}")
            return prompt.prompt_content

        # 返回默认 Prompt
        default = get_default_prompt(tool_type)
        if default:
            logger.debug(f"使用默认 Prompt: tool_type={tool_type}")
            return default

        logger.warning(f"未找到 Prompt 配置: tool_type={tool_type}")
        return ""


def get_user_prompt_record(user_id: int, tool_type: str, db: Session) -> Optional[UserPrompt]:
    """
    获取用户 Prompt 记录对象（用于 API）

    Args:
        user_id: 用户 ID
        tool_type: 工具类型
        db: 数据库会话

    Returns:
        UserPrompt 对象或 None
    """
    return db.query(UserPrompt).filter(
        UserPrompt.user_id == user_id,
        UserPrompt.tool_type == tool_type,
    ).first()


def save_user_prompt(user_id: int, tool_type: str, content: str) -> bool:
    """
    保存用户自定义 Prompt

    Args:
        user_id: 用户 ID
        tool_type: 工具类型
        content: Prompt 内容

    Returns:
        是否保存成功
    """
    try:
        with get_db_context() as db:
            # 查找现有记录
            existing = db.query(UserPrompt).filter(
                UserPrompt.user_id == user_id,
                UserPrompt.tool_type == tool_type,
            ).first()

            if existing:
                existing.prompt_content = content
                existing.is_active = True
                logger.info(f"更新用户 Prompt: user_id={user_id}, tool_type={tool_type}")
            else:
                new_prompt = UserPrompt(
                    user_id=user_id,
                    tool_type=tool_type,
                    prompt_content=content,
                    is_active=True,
                )
                db.add(new_prompt)
                logger.info(f"创建用户 Prompt: user_id={user_id}, tool_type={tool_type}")

            return True
    except Exception as e:
        logger.error(f"保存用户 Prompt 失败: {e}")
        return False


def reset_user_prompt(user_id: int, tool_type: str) -> bool:
    """
    重置用户 Prompt 为默认值（删除用户自定义记录）

    Args:
        user_id: 用户 ID
        tool_type: 工具类型

    Returns:
        是否重置成功
    """
    try:
        with get_db_context() as db:
            deleted = db.query(UserPrompt).filter(
                UserPrompt.user_id == user_id,
                UserPrompt.tool_type == tool_type,
            ).delete()

            if deleted > 0:
                logger.info(f"重置用户 Prompt: user_id={user_id}, tool_type={tool_type}")
            return True
    except Exception as e:
        logger.error(f"重置用户 Prompt 失败: {e}")
        return False


def get_all_user_prompts(user_id: int) -> List[Dict[str, Any]]:
    """
    获取用户所有工具类型的 Prompt 配置

    Args:
        user_id: 用户 ID

    Returns:
        Prompt 配置列表
    """
    from src.defaults import TOOL_TYPES

    result = []
    with get_db_context() as db:
        for tool_type in TOOL_TYPES:
            record = get_user_prompt_record(user_id, tool_type, db)
            default_prompt = get_default_prompt(tool_type)

            result.append({
                "tool_type": tool_type,
                "tool_name": get_tool_display_name(tool_type),
                "has_custom": record is not None and record.is_active,
                "prompt_content": record.prompt_content if record and record.is_active else default_prompt,
                "is_active": record.is_active if record else True,
            })

    return result


# ============================================================================
# 数据源配置相关函数
# ============================================================================

def get_user_sources(user_id: int, tool_type: str) -> List[Dict[str, Any]]:
    """
    获取用户启用的数据源列表，无则返回默认数据源列表

    Args:
        user_id: 用户 ID
        tool_type: 工具类型 (mission / alpha / bounty)

    Returns:
        数据源配置列表
    """
    with get_db_context() as db:
        # 查询用户自定义数据源
        user_sources = db.query(UserSource).filter(
            UserSource.user_id == user_id,
            UserSource.tool_type == tool_type,
            UserSource.is_enabled == True,
        ).all()

        if user_sources:
            logger.debug(f"使用用户自定义数据源: user_id={user_id}, tool_type={tool_type}, count={len(user_sources)}")
            return [s.to_dict() for s in user_sources]

        # 返回默认数据源
        default_sources = get_default_sources(tool_type)
        logger.debug(f"使用默认数据源: tool_type={tool_type}, count={len(default_sources)}")
        return default_sources


def get_all_user_sources(user_id: int, tool_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    获取用户所有数据源配置（包含官方预设和自定义）

    Args:
        user_id: 用户 ID
        tool_type: 可选，筛选指定工具类型

    Returns:
        数据源配置列表
    """
    result = []

    with get_db_context() as db:
        # 获取官方预设数据源
        official_sources = get_official_sources(tool_type)

        # 获取用户自定义数据源
        query = db.query(UserSource).filter(UserSource.user_id == user_id)
        if tool_type:
            query = query.filter(UserSource.tool_type == tool_type)
        user_sources = query.all()

        # 合并结果
        for src in official_sources:
            result.append({
                **src,
                "is_user_defined": False,
                "user_source_id": None,
            })

        for src in user_sources:
            result.append({
                **src.to_dict(),
                "is_user_defined": True,
                "user_source_id": src.id,
            })

    return result


def add_user_source(
    user_id: int,
    name: str,
    url: str,
    source_type: str,
    tool_type: str,
) -> Optional[int]:
    """
    添加用户自定义数据源

    Args:
        user_id: 用户 ID
        name: 数据源名称
        url: 数据源 URL
        source_type: 类型 (rss / webpage)
        tool_type: 所属工具 (mission / alpha / bounty)

    Returns:
        新建数据源 ID，失败返回 None
    """
    try:
        with get_db_context() as db:
            new_source = UserSource(
                user_id=user_id,
                name=name,
                url=url,
                source_type=source_type,
                tool_type=tool_type,
                is_enabled=True,
            )
            db.add(new_source)
            db.flush()  # 获取 ID
            source_id = new_source.id
            logger.info(f"添加用户数据源: user_id={user_id}, name={name}, id={source_id}")
            return source_id
    except Exception as e:
        logger.error(f"添加用户数据源失败: {e}")
        return None


def update_user_source(
    source_id: int,
    user_id: int,
    name: Optional[str] = None,
    url: Optional[str] = None,
    source_type: Optional[str] = None,
    tool_type: Optional[str] = None,
    is_enabled: Optional[bool] = None,
) -> bool:
    """
    更新用户自定义数据源

    Args:
        source_id: 数据源 ID
        user_id: 用户 ID（用于权限验证）
        name: 新名称
        url: 新 URL
        source_type: 新类型
        tool_type: 新工具类型
        is_enabled: 是否启用

    Returns:
        是否更新成功
    """
    try:
        with get_db_context() as db:
            source = db.query(UserSource).filter(
                UserSource.id == source_id,
                UserSource.user_id == user_id,
            ).first()

            if not source:
                logger.warning(f"数据源不存在或无权限: source_id={source_id}, user_id={user_id}")
                return False

            if name is not None:
                source.name = name
            if url is not None:
                source.url = url
            if source_type is not None:
                source.source_type = source_type
            if tool_type is not None:
                source.tool_type = tool_type
            if is_enabled is not None:
                source.is_enabled = is_enabled

            logger.info(f"更新用户数据源: source_id={source_id}")
            return True
    except Exception as e:
        logger.error(f"更新用户数据源失败: {e}")
        return False


def delete_user_source(source_id: int, user_id: int) -> bool:
    """
    删除用户自定义数据源

    Args:
        source_id: 数据源 ID
        user_id: 用户 ID（用于权限验证）

    Returns:
        是否删除成功
    """
    try:
        with get_db_context() as db:
            deleted = db.query(UserSource).filter(
                UserSource.id == source_id,
                UserSource.user_id == user_id,
            ).delete()

            if deleted > 0:
                logger.info(f"删除用户数据源: source_id={source_id}, user_id={user_id}")
                return True
            else:
                logger.warning(f"数据源不存在或无权限: source_id={source_id}, user_id={user_id}")
                return False
    except Exception as e:
        logger.error(f"删除用户数据源失败: {e}")
        return False


def toggle_user_source(source_id: int, user_id: int, enabled: bool) -> bool:
    """
    启用/禁用用户数据源

    Args:
        source_id: 数据源 ID
        user_id: 用户 ID
        enabled: 是否启用

    Returns:
        是否操作成功
    """
    return update_user_source(source_id, user_id, is_enabled=enabled)


# ============================================================================
# 辅助函数
# ============================================================================

def get_user_config_summary(user_id: int) -> Dict[str, Any]:
    """
    获取用户配置摘要

    Args:
        user_id: 用户 ID

    Returns:
        配置摘要字典
    """
    prompts = get_all_user_prompts(user_id)
    sources = get_all_user_sources(user_id)

    return {
        "user_id": user_id,
        "prompts": {
            "total": len(prompts),
            "customized": sum(1 for p in prompts if p["has_custom"]),
        },
        "sources": {
            "total": len(sources),
            "user_defined": sum(1 for s in sources if s.get("is_user_defined")),
            "enabled": sum(1 for s in sources if s.get("is_enabled")),
        },
    }


# ============================================================================
# DailyHotApi 分类配置相关函数
# ============================================================================

# 默认启用的分类
DEFAULT_DAILYHOT_CATEGORIES = ["tech", "dev"]


def get_user_dailyhot_categories(user_id: int) -> List[str]:
    """
    获取用户启用的 DailyHotApi 分类列表

    Args:
        user_id: 用户 ID

    Returns:
        启用的分类列表，如 ["tech", "dev"]。无配置时返回默认值。
    """
    from src.database.models import DailyHotCategoryConfig

    try:
        with get_db_context() as db:
            configs = db.query(DailyHotCategoryConfig).filter(
                DailyHotCategoryConfig.user_id == user_id,
                DailyHotCategoryConfig.is_enabled == True,
            ).all()

            if configs:
                categories = [c.category for c in configs]
                logger.debug(f"用户 DailyHot 分类配置: user_id={user_id}, categories={categories}")
                return categories

            # 无配置时返回默认值
            logger.debug(f"用户无 DailyHot 分类配置，使用默认值: user_id={user_id}")
            return DEFAULT_DAILYHOT_CATEGORIES.copy()

    except Exception as e:
        logger.error(f"获取用户 DailyHot 分类配置失败: {e}")
        return DEFAULT_DAILYHOT_CATEGORIES.copy()


def get_user_dailyhot_categories_detail(user_id: int) -> List[Dict[str, Any]]:
    """
    获取用户 DailyHotApi 分类配置详情（包含启用状态）

    Args:
        user_id: 用户 ID

    Returns:
        分类配置列表，每项包含 category 和 is_enabled
    """
    from src.database.models import DailyHotCategoryConfig

    try:
        with get_db_context() as db:
            configs = db.query(DailyHotCategoryConfig).filter(
                DailyHotCategoryConfig.user_id == user_id,
            ).all()

            # 如果没有任何配置，返回默认值
            if not configs:
                return [
                    {"category": "tech", "is_enabled": True},
                    {"category": "dev", "is_enabled": True},
                    {"category": "news", "is_enabled": False},
                    {"category": "entertainment", "is_enabled": False},
                ]

            # 转换为字典方便查询
            config_map = {c.category: c.is_enabled for c in configs}

            # 返回所有分类的状态
            all_categories = ["tech", "dev", "news", "entertainment"]
            result = []
            for cat in all_categories:
                result.append({
                    "category": cat,
                    "is_enabled": config_map.get(cat, False),
                })

            return result

    except Exception as e:
        logger.error(f"获取用户 DailyHot 分类详情失败: {e}")
        # 返回默认配置
        return [
            {"category": "tech", "is_enabled": True},
            {"category": "dev", "is_enabled": True},
            {"category": "news", "is_enabled": False},
            {"category": "entertainment", "is_enabled": False},
        ]


def update_user_dailyhot_categories(
    user_id: int,
    categories: List[str],
) -> bool:
    """
    更新用户的 DailyHotApi 分类启用状态

    Args:
        user_id: 用户 ID
        categories: 要启用的分类列表，如 ["tech", "dev", "news"]

    Returns:
        是否更新成功
    """
    from src.database.models import DailyHotCategoryConfig

    # 验证分类有效性
    valid_categories = ["tech", "dev", "news", "entertainment"]
    for cat in categories:
        if cat not in valid_categories:
            logger.warning(f"无效的分类: {cat}")
            return False

    # 至少保留一个分类
    if not categories:
        logger.warning("至少需要启用一个分类")
        return False

    try:
        with get_db_context() as db:
            # 获取现有配置
            existing_configs = db.query(DailyHotCategoryConfig).filter(
                DailyHotCategoryConfig.user_id == user_id,
            ).all()

            existing_map = {c.category: c for c in existing_configs}

            # 更新或创建配置
            for cat in valid_categories:
                is_enabled = cat in categories

                if cat in existing_map:
                    # 更新现有记录
                    existing_map[cat].is_enabled = is_enabled
                else:
                    # 创建新记录
                    new_config = DailyHotCategoryConfig(
                        user_id=user_id,
                        category=cat,
                        is_enabled=is_enabled,
                    )
                    db.add(new_config)

            db.commit()
            logger.info(f"更新用户 DailyHot 分类配置: user_id={user_id}, enabled={categories}")
            return True

    except Exception as e:
        logger.error(f"更新用户 DailyHot 分类配置失败: {e}")
        return False


def init_user_dailyhot_categories(user_id: int) -> bool:
    """
    初始化用户的 DailyHotApi 分类配置（新用户调用）

    默认启用 tech 和 dev 分类

    Args:
        user_id: 用户 ID

    Returns:
        是否初始化成功
    """
    from src.database.models import DailyHotCategoryConfig

    try:
        with get_db_context() as db:
            # 检查是否已有配置
            existing = db.query(DailyHotCategoryConfig).filter(
                DailyHotCategoryConfig.user_id == user_id,
            ).first()

            if existing:
                logger.debug(f"用户已有 DailyHot 分类配置，跳过初始化: user_id={user_id}")
                return True

            # 创建默认配置
            for cat in DEFAULT_DAILYHOT_CATEGORIES:
                config = DailyHotCategoryConfig(
                    user_id=user_id,
                    category=cat,
                    is_enabled=True,
                )
                db.add(config)

            # 为其他分类创建禁用记录
            for cat in ["news", "entertainment"]:
                if cat not in DEFAULT_DAILYHOT_CATEGORIES:
                    config = DailyHotCategoryConfig(
                        user_id=user_id,
                        category=cat,
                        is_enabled=False,
                    )
                    db.add(config)

            db.commit()
            logger.info(f"初始化用户 DailyHot 分类配置: user_id={user_id}")
            return True

    except Exception as e:
        logger.error(f"初始化用户 DailyHot 分类配置失败: {e}")
        return False