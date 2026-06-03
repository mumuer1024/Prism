# -*- coding: utf-8 -*-
"""
数据库 ORM 模型 - 激活码架构

定义所有数据库表的 SQLAlchemy 模型（v2.1 激活码架构）
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from src.database.connection import Base


# ============================================================================
# 核心激活码相关表
# ============================================================================

class ActivationCode(Base):
    """
    激活码表

    存储激活码、次数、激活状态、推荐奖励等信息
    """
    __tablename__ = "activation_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 激活码信息
    code = Column(String(32), unique=True, nullable=False, index=True)  # PRISM-XXXX-XXXX-XXXX

    # 次数管理
    quota = Column(Integer, nullable=False)  # 购买次数（3/6/10/20/50/100）
    remaining = Column(Integer, nullable=False)  # 剩余次数

    # 激活状态
    is_activated = Column(Boolean, default=False, nullable=False)
    activated_at = Column(DateTime, nullable=True)

    # 推荐奖励（延迟到首次消费时触发）
    referral_code_used = Column(String(16), nullable=True)  # 激活时填写的推荐码
    referral_rewarded = Column(Boolean, default=False, nullable=False)  # 被推荐奖励是否已发放

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    devices = relationship(
        "Device",
        back_populates="activation_code",
        cascade="all, delete-orphan"
    )
    referral_code_record = relationship(
        "ReferralCode",
        back_populates="activation_code",
        uselist=False,
        cascade="all, delete-orphan"
    )
    user_prompts = relationship(
        "UserPrompt",
        back_populates="activation_code",
        cascade="all, delete-orphan"
    )
    user_sources = relationship(
        "UserSource",
        back_populates="activation_code",
        cascade="all, delete-orphan"
    )
    user_configs = relationship(
        "UserConfig",
        back_populates="activation_code",
        cascade="all, delete-orphan"
    )
    dailyhot_configs = relationship(
        "DailyHotCategoryConfig",
        back_populates="activation_code",
        cascade="all, delete-orphan"
    )

    # 索引
    __table_args__ = (
        Index("idx_activation_code", "code"),
        Index("idx_activation_activated", "is_activated"),
    )

    def __repr__(self):
        return f"<ActivationCode(code='{self.code}', remaining={self.remaining}, activated={self.is_activated})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code": self.code,
            "quota": self.quota,
            "remaining": self.remaining,
            "is_activated": self.is_activated,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
            "referral_code_used": self.referral_code_used,
            "referral_rewarded": self.referral_rewarded,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Device(Base):
    """
    设备绑定表

    存储激活码绑定的设备信息，限制每个激活码最多3个设备
    """
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联激活码
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="CASCADE"), nullable=False)

    # 设备信息
    device_id = Column(String(64), nullable=False)  # crypto.randomUUID() 生成
    device_name = Column(String(100), nullable=True)  # 如 "Chrome on Windows"
    last_seen = Column(DateTime, nullable=True)  # 最后活跃时间

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    activation_code = relationship("ActivationCode", back_populates="devices")

    # 索引和唯一约束（防并发超限）
    __table_args__ = (
        Index("idx_device_code", "code_id"),
        Index("idx_device_device_id", "device_id"),
        UniqueConstraint("code_id", "device_id", name="uq_device_binding"),
    )

    def __repr__(self):
        return f"<Device(code_id={self.code_id}, device_id='{self.device_id[:16]}...')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code_id": self.code_id,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ReferralCode(Base):
    """
    推荐码表

    每个激活码激活后生成专属推荐码，用于推荐奖励
    """
    __tablename__ = "referral_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联激活码
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="CASCADE"), nullable=False, unique=True)

    # 推荐码信息
    referral_code = Column(String(16), unique=True, nullable=False)  # REF-XXXXXX

    # 推荐统计
    referral_count = Column(Integer, default=0, nullable=False)  # 成功推荐次数
    total_rewarded = Column(Integer, default=0, nullable=False)  # 累计获得奖励次数

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    activation_code = relationship("ActivationCode", back_populates="referral_code_record")

    # 索引
    __table_args__ = (
        Index("idx_referral_code", "referral_code"),
        Index("idx_referral_code_id", "code_id"),
    )

    def __repr__(self):
        return f"<ReferralCode(referral_code='{self.referral_code}', count={self.referral_count})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code_id": self.code_id,
            "referral_code": self.referral_code,
            "referral_count": self.referral_count,
            "total_rewarded": self.total_rewarded,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnonymousUsage(Base):
    """
    匿名用户使用记录表

    存储匿名用户的每日免费额度使用情况
    """
    __tablename__ = "anonymous_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 匿名用户标识
    visitor_id = Column(String(64), unique=True, nullable=False, index=True)  # 前端生成的 visitor_id

    # 每日免费额度
    daily_count = Column(Integer, default=0, nullable=False)
    daily_date = Column(String(10), nullable=True)  # YYYY-MM-DD，用于重置

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 索引
    __table_args__ = (
        Index("idx_anon_visitor", "visitor_id"),
        Index("idx_anon_date", "daily_date"),
    )

    def __repr__(self):
        return f"<AnonymousUsage(visitor_id='{self.visitor_id[:16]}...', count={self.daily_count})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "visitor_id": self.visitor_id,
            "daily_count": self.daily_count,
            "daily_date": self.daily_date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 管理员表（独立）
# ============================================================================

class AdminUser(Base):
    """
    管理员表

    管理员独立管理，不依赖激活码系统
    """
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<AdminUser(username='{self.username}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 审计日志表（保留，operator改为admin_id）
# ============================================================================

class AuditLog(Base):
    """
    审计日志表

    记录管理员操作日志，用于安全审计
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 操作者信息
    admin_id = Column(Integer, ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    admin_username = Column(String(50), nullable=False)

    # 操作类型
    action = Column(String(50), nullable=False)  # generate_codes, deactivate_code, etc.
    action_category = Column(String(50), nullable=False)  # code_management, etc.

    # 操作目标
    target_type = Column(String(50), nullable=True)  # code, device, etc.
    target_id = Column(String(255), nullable=True)
    target_info = Column(Text, nullable=True)  # JSON 格式

    # 操作详情
    action_detail = Column(Text, nullable=True)  # JSON 格式

    # 请求信息
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    admin = relationship("AdminUser", foreign_keys=[admin_id])

    # 索引
    __table_args__ = (
        Index("idx_audit_admin", "admin_id"),
        Index("idx_audit_action", "action"),
        Index("idx_audit_category", "action_category"),
        Index("idx_audit_created", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', admin={self.admin_username})>"

    def to_dict(self):
        """转换为字典"""
        import json

        target_info = None
        if self.target_info:
            try:
                target_info = json.loads(self.target_info)
            except (json.JSONDecodeError, TypeError):
                target_info = self.target_info

        action_detail = None
        if self.action_detail:
            try:
                action_detail = json.loads(self.action_detail)
            except (json.JSONDecodeError, TypeError):
                action_detail = self.action_detail

        return {
            "id": self.id,
            "admin_id": self.admin_id,
            "admin_username": self.admin_username,
            "action": self.action,
            "action_category": self.action_category,
            "target_type": self.target_type,
            "target_id": self.target_id,
            "target_info": target_info,
            "action_detail": action_detail,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 用户配置表（user_id改为code_id）
# ============================================================================

class UserPrompt(Base):
    """
    用户自定义Prompt配置表

    存储用户为各功能模块自定义的Prompt（code_id替代user_id）
    """
    __tablename__ = "user_prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="CASCADE"), nullable=False)
    tool_type = Column(String(50), nullable=False)  # mission / bounty_v2ex / alpha / revenue
    prompt_content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    activation_code = relationship("ActivationCode", back_populates="user_prompts")

    # 索引
    __table_args__ = (
        Index("idx_user_prompt_code", "code_id"),
        Index("idx_user_prompt_type", "tool_type"),
        UniqueConstraint("code_id", "tool_type", name="uq_user_prompt_code_type"),
    )

    def __repr__(self):
        return f"<UserPrompt(code_id={self.code_id}, tool_type='{self.tool_type}', active={self.is_active})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code_id": self.code_id,
            "tool_type": self.tool_type,
            "prompt_content": self.prompt_content,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserPromptHistory(Base):
    """
    用户 Prompt 版本历史表

    记录每次 Prompt 更新的历史版本，支持回滚（code_id替代user_id）
    """
    __tablename__ = "user_prompt_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_prompt_id = Column(Integer, ForeignKey("user_prompts.id", ondelete="CASCADE"), nullable=False)
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="CASCADE"), nullable=False)
    tool_type = Column(String(50), nullable=False)
    prompt_content = Column(Text, nullable=False)
    version = Column(Integer, nullable=False)
    change_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    user_prompt = relationship("UserPrompt", foreign_keys=[user_prompt_id])
    activation_code = relationship("ActivationCode", foreign_keys=[code_id])

    # 索引
    __table_args__ = (
        Index("idx_prompt_history_prompt", "user_prompt_id"),
        Index("idx_prompt_history_code", "code_id"),
        Index("idx_prompt_history_version", "user_prompt_id", "version", unique=True),
    )

    def __repr__(self):
        return f"<UserPromptHistory(prompt_id={self.user_prompt_id}, version={self.version})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_prompt_id": self.user_prompt_id,
            "code_id": self.code_id,
            "tool_type": self.tool_type,
            "prompt_content": self.prompt_content,
            "version": self.version,
            "change_reason": self.change_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserSource(Base):
    """
    用户数据源配置表

    存储用户自定义的数据源（code_id替代user_id）
    """
    __tablename__ = "user_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    source_type = Column(String(20), nullable=False)  # rss / webpage
    tool_type = Column(String(50), nullable=False)  # mission / alpha / bounty
    is_enabled = Column(Boolean, default=True, nullable=False)
    is_preset = Column(Boolean, default=False, nullable=False)
    category = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    activation_code = relationship("ActivationCode", back_populates="user_sources")

    # 索引
    __table_args__ = (
        Index("idx_user_source_code", "code_id"),
        Index("idx_user_source_type", "tool_type"),
    )

    def __repr__(self):
        return f"<UserSource(code_id={self.code_id}, name='{self.name}', type='{self.source_type}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code_id": self.code_id,
            "name": self.name,
            "url": self.url,
            "source_type": self.source_type,
            "tool_type": self.tool_type,
            "is_enabled": self.is_enabled,
            "is_preset": self.is_preset,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserConfig(Base):
    """
    用户配置表（键值对存储）

    存储用户的各类配置（code_id替代user_id）
    """
    __tablename__ = "user_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="CASCADE"), nullable=False)
    config_key = Column(String(100), nullable=False)
    config_value = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 关系
    activation_code = relationship("ActivationCode", back_populates="user_configs")

    # 索引
    __table_args__ = (
        Index("idx_user_config_code", "code_id"),
        Index("idx_user_config_key", "config_key"),
        UniqueConstraint("code_id", "config_key", name="uq_user_config_code_key"),
    )

    def __repr__(self):
        return f"<UserConfig(code_id={self.code_id}, key='{self.config_key}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code_id": self.code_id,
            "config_key": self.config_key,
            "config_value": self.config_value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DailyHotCategoryConfig(Base):
    """
    DailyHotApi 分类标签配置表

    存储用户启用的热榜分类配置（code_id替代user_id）
    """
    __tablename__ = "dailyhot_category_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code_id = Column(Integer, ForeignKey("activation_codes.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(50), nullable=False)  # tech / dev / news / entertainment
    is_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    activation_code = relationship("ActivationCode", back_populates="dailyhot_configs")

    # 索引和约束
    __table_args__ = (
        Index("idx_dailyhot_code", "code_id"),
        UniqueConstraint("code_id", "category", name="uq_dailyhot_code_category"),
    )

    def __repr__(self):
        return f"<DailyHotCategoryConfig(code_id={self.code_id}, category='{self.category}', enabled={self.is_enabled})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "code_id": self.code_id,
            "category": self.category,
            "is_enabled": self.is_enabled,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ============================================================================
# 预设广场（保留不变）
# ============================================================================

class MarketplaceTemplate(Base):
    """
    预设广场模板表

    存储官方维护的 Prompt 模板，供用户浏览和导入
    """
    __tablename__ = "marketplace_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    tool_type = Column(String(50), nullable=False)  # mission / bounty_v2ex / alpha / revenue
    prompt_content = Column(Text, nullable=False)
    tags = Column(Text, nullable=True)  # JSON 数组
    is_official = Column(Boolean, default=True, nullable=False)
    is_published = Column(Boolean, default=True, nullable=False)
    import_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 索引
    __table_args__ = (
        Index("idx_template_tool_type", "tool_type"),
        Index("idx_template_published", "is_published"),
    )

    def __repr__(self):
        return f"<MarketplaceTemplate(id={self.id}, title='{self.title}', tool_type='{self.tool_type}')>"

    def to_dict(self):
        """转换为字典"""
        import json
        tags = []
        if self.tags:
            try:
                tags = json.loads(self.tags)
            except (json.JSONDecodeError, TypeError):
                tags = []

        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "tool_type": self.tool_type,
            "prompt_content": self.prompt_content,
            "tags": tags,
            "is_official": self.is_official,
            "is_published": self.is_published,
            "import_count": self.import_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ============================================================================
# 数据库版本记录（保留）
# ============================================================================

class SchemaVersion(Base):
    """
    数据库版本记录表

    用于跟踪数据库迁移版本
    """
    __tablename__ = "schema_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, nullable=False, unique=True)
    applied_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<SchemaVersion(version={self.version}, applied_at='{self.applied_at}')>"