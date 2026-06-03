# -*- coding: utf-8 -*-
"""
配置读取层 (Config Loader) - v2.1 激活码架构

提供用户配置的读取、写入、重置功能
支持 Prompt 配置和数据源配置
支持 Prompt 版本历史记录和回滚

注意：所有函数使用 code_id（激活码ID）替代原有的 user_id
"""

import logging
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.database.connection import get_db_context
from src.database.models import UserPrompt, UserPromptHistory, UserSource, DailyHotCategoryConfig
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

def get_user_prompt(code_id: int, tool_type: str) -> str:
    """
    获取用户自定义 Prompt，无则返回空字符串

    Args:
        code_id: 激活码 ID
        tool_type: 工具类型 (mission / bounty_v2ex / alpha / revenue)

    Returns:
        Prompt 内容字符串，无自定义配置时返回空字符串
    """
    with get_db_context() as db:
        prompt = db.query(UserPrompt).filter(
            UserPrompt.code_id == code_id,
            UserPrompt.tool_type == tool_type,
            UserPrompt.is_active == True,
        ).first()

        if prompt:
            logger.debug(f"使用用户自定义 Prompt: code_id={code_id}, tool_type={tool_type}")
            return prompt.prompt_content

        return ""


def get_user_prompt_with_default(code_id: int, tool_type: str) -> str:
    """
    获取用户自定义 Prompt，无则返回默认 Prompt

    Args:
        code_id: 激活码 ID
        tool_type: 工具类型

    Returns:
        Prompt 内容字符串
    """
    user_prompt = get_user_prompt(code_id, tool_type)
    if user_prompt:
        return user_prompt

    default = get_default_prompt(tool_type)
    if default:
        return default

    return ""


def get_user_prompt_record(code_id: int, tool_type: str, db: Session) -> Optional[UserPrompt]:
    """
    获取用户 Prompt 记录对象（用于 API）

    Args:
        code_id: 激活码 ID
        tool_type: 工具类型
        db: 数据库会话

    Returns:
        UserPrompt 对象或 None
    """
    return db.query(UserPrompt).filter(
        UserPrompt.code_id == code_id,
        UserPrompt.tool_type == tool_type,
    ).first()


def save_user_prompt(code_id: int, tool_type: str, content: str, change_reason: str = None) -> bool:
    """
    保存用户自定义 Prompt（带版本历史记录）

    Args:
        code_id: 激活码 ID
        tool_type: 工具类型
        content: Prompt 内容
        change_reason: 更改原因（可选）

    Returns:
        是否保存成功
    """
    try:
        with get_db_context() as db:
            existing = db.query(UserPrompt).filter(
                UserPrompt.code_id == code_id,
                UserPrompt.tool_type == tool_type,
            ).first()

            if existing:
                _save_prompt_history(db, existing)
                existing.prompt_content = content
                existing.is_active = True
                logger.info(f"更新用户 Prompt: code_id={code_id}, tool_type={tool_type}")
                _save_prompt_history(db, existing, change_reason)
            else:
                new_prompt = UserPrompt(
                    code_id=code_id,
                    tool_type=tool_type,
                    prompt_content=content,
                    is_active=True,
                )
                db.add(new_prompt)
                db.flush()
                logger.info(f"创建用户 Prompt: code_id={code_id}, tool_type={tool_type}")
                _save_prompt_history(db, new_prompt, "初始版本")

            return True
    except Exception as e:
        logger.error(f"保存用户 Prompt 失败: {e}")
        return False


def _save_prompt_history(
    db: Session,
    prompt: UserPrompt,
    change_reason: str = None,
) -> None:
    """保存 Prompt 版本历史"""
    max_version = db.query(func.max(UserPromptHistory.version)).filter(
        UserPromptHistory.user_prompt_id == prompt.id,
    ).scalar() or 0

    history = UserPromptHistory(
        user_prompt_id=prompt.id,
        code_id=prompt.code_id,
        tool_type=prompt.tool_type,
        prompt_content=prompt.prompt_content,
        version=max_version + 1,
        change_reason=change_reason,
    )
    db.add(history)
    db.flush()


def get_prompt_history(
    code_id: int,
    tool_type: str,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """获取 Prompt 版本历史"""
    try:
        with get_db_context() as db:
            prompt = db.query(UserPrompt).filter(
                UserPrompt.code_id == code_id,
                UserPrompt.tool_type == tool_type,
            ).first()

            if not prompt:
                return []

            histories = db.query(UserPromptHistory).filter(
                UserPromptHistory.user_prompt_id == prompt.id,
            ).order_by(desc(UserPromptHistory.version)).limit(limit).all()

            return [h.to_dict() for h in histories]

    except Exception as e:
        logger.error(f"获取 Prompt 历史失败: {e}")
        return []


def rollback_prompt(code_id: int, tool_type: str, version: int) -> bool:
    """回滚 Prompt 到指定版本"""
    try:
        with get_db_context() as db:
            prompt = db.query(UserPrompt).filter(
                UserPrompt.code_id == code_id,
                UserPrompt.tool_type == tool_type,
            ).first()

            if not prompt:
                return False

            history = db.query(UserPromptHistory).filter(
                UserPromptHistory.user_prompt_id == prompt.id,
                UserPromptHistory.version == version,
            ).first()

            if not history:
                return False

            _save_prompt_history(db, prompt, "回滚前自动保存")
            prompt.prompt_content = history.prompt_content
            _save_prompt_history(db, prompt, f"回滚到版本 {version}")

            logger.info(f"Prompt 已回滚: code_id={code_id}, tool_type={tool_type}, version={version}")
            return True

    except Exception as e:
        logger.error(f"回滚 Prompt 失败: {e}")
        return False


def reset_user_prompt(code_id: int, tool_type: str) -> bool:
    """重置用户 Prompt 为默认值"""
    try:
        with get_db_context() as db:
            deleted = db.query(UserPrompt).filter(
                UserPrompt.code_id == code_id,
                UserPrompt.tool_type == tool_type,
            ).delete()

            if deleted > 0:
                logger.info(f"重置用户 Prompt: code_id={code_id}, tool_type={tool_type}")
            return True
    except Exception as e:
        logger.error(f"重置用户 Prompt 失败: {e}")
        return False


def get_all_user_prompts(code_id: int) -> List[Dict[str, Any]]:
    """获取用户所有工具类型的 Prompt 配置"""
    from src.defaults import TOOL_TYPES

    result = []
    with get_db_context() as db:
        for tool_type in TOOL_TYPES:
            record = get_user_prompt_record(code_id, tool_type, db)
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

def get_user_sources(code_id: int, tool_type: str) -> List[Dict[str, Any]]:
    """获取用户启用的数据源列表"""
    with get_db_context() as db:
        user_sources = db.query(UserSource).filter(
            UserSource.code_id == code_id,
            UserSource.tool_type == tool_type,
            UserSource.is_enabled == True,
        ).all()

        if user_sources:
            return [s.to_dict() for s in user_sources]

        return get_default_sources(tool_type)


def get_all_user_sources(code_id: int, tool_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """获取用户所有数据源配置"""
    result = []

    with get_db_context() as db:
        official_sources = get_official_sources(tool_type)

        query = db.query(UserSource).filter(UserSource.code_id == code_id)
        if tool_type:
            query = query.filter(UserSource.tool_type == tool_type)
        user_sources = query.all()

        for src in official_sources:
            result.append({
                **src,
                "is_preset": True,
                "is_user_defined": False,
                "user_source_id": None,
            })

        for src in user_sources:
            result.append({
                **src.to_dict(),
                "is_preset": src.is_preset,
                "is_user_defined": True,
                "user_source_id": src.id,
            })

    return result


def add_user_source(
    code_id: int,
    name: str,
    url: str,
    source_type: str,
    tool_type: str,
) -> Optional[int]:
    """添加用户自定义数据源"""
    try:
        with get_db_context() as db:
            new_source = UserSource(
                code_id=code_id,
                name=name,
                url=url,
                source_type=source_type,
                tool_type=tool_type,
                is_enabled=True,
            )
            db.add(new_source)
            db.flush()
            source_id = new_source.id
            logger.info(f"添加用户数据源: code_id={code_id}, name={name}, id={source_id}")
            return source_id
    except Exception as e:
        logger.error(f"添加用户数据源失败: {e}")
        return None


def update_user_source(
    source_id: int,
    code_id: int,
    name: Optional[str] = None,
    url: Optional[str] = None,
    source_type: Optional[str] = None,
    tool_type: Optional[str] = None,
    is_enabled: Optional[bool] = None,
) -> bool:
    """更新用户自定义数据源"""
    try:
        with get_db_context() as db:
            source = db.query(UserSource).filter(
                UserSource.id == source_id,
                UserSource.code_id == code_id,
            ).first()

            if not source:
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


def delete_user_source(source_id: int, code_id: int) -> bool:
    """删除用户自定义数据源"""
    try:
        with get_db_context() as db:
            deleted = db.query(UserSource).filter(
                UserSource.id == source_id,
                UserSource.code_id == code_id,
            ).delete()

            return deleted > 0
    except Exception as e:
        logger.error(f"删除用户数据源失败: {e}")
        return False


def toggle_user_source(source_id: int, code_id: int, enabled: bool) -> bool:
    """启用/禁用用户数据源"""
    return update_user_source(source_id, code_id, is_enabled=enabled)


# ============================================================================
# DailyHotApi 分类配置相关函数
# ============================================================================

DEFAULT_DAILYHOT_CATEGORIES = ["tech", "dev"]


def get_user_dailyhot_categories(code_id: int) -> List[str]:
    """获取用户启用的 DailyHotApi 分类列表"""
    try:
        with get_db_context() as db:
            configs = db.query(DailyHotCategoryConfig).filter(
                DailyHotCategoryConfig.code_id == code_id,
                DailyHotCategoryConfig.is_enabled == True,
            ).all()

            if configs:
                return [c.category for c in configs]

            return DEFAULT_DAILYHOT_CATEGORIES.copy()

    except Exception as e:
        logger.error(f"获取用户 DailyHot 分类配置失败: {e}")
        return DEFAULT_DAILYHOT_CATEGORIES.copy()


def get_user_dailyhot_categories_detail(code_id: int) -> List[Dict[str, Any]]:
    """获取用户 DailyHotApi 分类配置详情"""
    try:
        with get_db_context() as db:
            configs = db.query(DailyHotCategoryConfig).filter(
                DailyHotCategoryConfig.code_id == code_id,
            ).all()

            if not configs:
                return [
                    {"category": "tech", "is_enabled": True},
                    {"category": "dev", "is_enabled": True},
                    {"category": "news", "is_enabled": False},
                    {"category": "entertainment", "is_enabled": False},
                ]

            config_map = {c.category: c.is_enabled for c in configs}
            all_categories = ["tech", "dev", "news", "entertainment"]

            return [{"category": cat, "is_enabled": config_map.get(cat, False)} for cat in all_categories]

    except Exception as e:
        logger.error(f"获取用户 DailyHot 分类详情失败: {e}")
        return [
            {"category": "tech", "is_enabled": True},
            {"category": "dev", "is_enabled": True},
            {"category": "news", "is_enabled": False},
            {"category": "entertainment", "is_enabled": False},
        ]


def update_user_dailyhot_categories(code_id: int, categories: List[str]) -> bool:
    """更新用户的 DailyHotApi 分类启用状态"""
    valid_categories = ["tech", "dev", "news", "entertainment"]

    for cat in categories:
        if cat not in valid_categories:
            return False

    if not categories:
        return False

    try:
        with get_db_context() as db:
            existing_configs = db.query(DailyHotCategoryConfig).filter(
                DailyHotCategoryConfig.code_id == code_id,
            ).all()

            existing_map = {c.category: c for c in existing_configs}

            for cat in valid_categories:
                is_enabled = cat in categories

                if cat in existing_map:
                    existing_map[cat].is_enabled = is_enabled
                else:
                    new_config = DailyHotCategoryConfig(
                        code_id=code_id,
                        category=cat,
                        is_enabled=is_enabled,
                    )
                    db.add(new_config)

            logger.info(f"更新用户 DailyHot 分类配置: code_id={code_id}, enabled={categories}")
            return True

    except Exception as e:
        logger.error(f"更新用户 DailyHot 分类配置失败: {e}")
        return False


def get_user_config_summary(code_id: int) -> Dict[str, Any]:
    """获取用户配置摘要"""
    prompts = get_all_user_prompts(code_id)
    sources = get_all_user_sources(code_id)

    return {
        "code_id": code_id,
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