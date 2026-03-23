# -*- coding: utf-8 -*-
"""
数据库 ORM 模型

定义所有数据库表的 SQLAlchemy 模型
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, 
    Numeric, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship

from src.database.connection import Base


class User(Base):
    """
    用户表
    
    存储用户基本信息、OAuth 信息、使用次数、邀请关系等
    """
    __tablename__ = "users"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本信息
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # OAuth 用户可能没有密码
    
    # OAuth 信息
    oauth_provider = Column(String(50), nullable=True)  # github, wechat
    oauth_id = Column(String(255), nullable=True)  # OAuth 平台的用户 ID
    oauth_name = Column(String(255), nullable=True)  # OAuth 用户名
    oauth_avatar = Column(String(500), nullable=True)  # OAuth 头像
    
    # 使用次数
    usage_count = Column(Integer, default=0, nullable=False)
    
    # 邀请系统
    invited_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    invite_code = Column(String(50), unique=True, nullable=True)  # 用户专属邀请码
    has_redeemed_first = Column(Boolean, default=False, nullable=False)  # 是否已享受首次充值返利
    
    # 免费用户每日使用
    free_usage_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    free_usage_count = Column(Integer, default=0, nullable=False)
    
    # 用户信息
    nickname = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    
    # 状态
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # 邮箱是否验证
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    
    # 关系
    refresh_tokens = relationship(
        "RefreshToken", 
        back_populates="user", 
        cascade="all, delete-orphan"
    )
    topup_records = relationship(
        "TopupRecord", 
        back_populates="user",
        cascade="all, delete-orphan"
    )
    redemption_codes_used = relationship(
        "RedemptionCode",
        back_populates="used_by_user",
        foreign_keys="RedemptionCode.used_by"
    )
    
    # 作为邀请人的记录
    invite_records_as_inviter = relationship(
        "InviteRecord",
        foreign_keys="InviteRecord.inviter_id",
        back_populates="inviter"
    )
    
    # 作为被邀请人的记录
    invite_records_as_invitee = relationship(
        "InviteRecord",
        foreign_keys="InviteRecord.invitee_id",
        back_populates="invitee"
    )
    
    # 生成的报告
    reports = relationship(
        "Report",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', usage_count={self.usage_count})>"
    
    def to_dict(self):
        """转换为字典（用于 API 响应）"""
        return {
            "id": self.id,
            "email": self.email,
            "nickname": self.nickname,
            "avatar_url": self.avatar_url or self.oauth_avatar,
            "usage_count": self.usage_count,
            "invite_code": self.invite_code,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }


class AnonymousUser(Base):
    """
    匿名用户表
    
    存储未注册用户的使用记录，用于免费额度限制
    """
    __tablename__ = "anonymous_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 匿名用户标识（设备指纹 + IP 的哈希）
    visitor_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256 哈希
    ip_address = Column(String(50), nullable=True)
    
    # 每日免费使用额度
    free_usage_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    free_usage_count = Column(Integer, default=0, nullable=False)
    
    # 时间戳
    first_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        Index("idx_anon_visitor", "visitor_hash"),
        Index("idx_anon_date", "free_usage_date"),
    )
    
    # 关系
    reports = relationship("Report", back_populates="anonymous_user")
    
    def __repr__(self):
        return f"<AnonymousUser(visitor_hash='{self.visitor_hash[:16]}...', free_count={self.free_usage_count})>"


class VerificationCode(Base):
    """
    验证码表
    
    用于邮箱验证、密码重置等场景
    """
    __tablename__ = "verification_codes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(10), nullable=False)  # 6 位验证码
    purpose = Column(String(50), nullable=False)  # register, reset_password
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 索引
    __table_args__ = (
        Index("idx_vc_email_purpose", "email", "purpose"),
    )
    
    def __repr__(self):
        return f"<VerificationCode(email='{self.email}', purpose='{self.purpose}', used={self.used})>"
    
    def is_valid(self) -> bool:
        """检查验证码是否有效"""
        return not self.used and self.expires_at > datetime.utcnow()


class RefreshToken(Base):
    """
    刷新令牌表
    
    存储用户的刷新令牌，支持多设备登录
    """
    __tablename__ = "refresh_tokens"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False)  # SHA256 哈希
    device_info = Column(String(255), nullable=True)  # 设备信息（User-Agent）
    ip_address = Column(String(50), nullable=True)  # IP 地址
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="refresh_tokens")
    
    # 索引
    __table_args__ = (
        Index("idx_rt_user", "user_id"),
        Index("idx_rt_expires", "expires_at"),
    )
    
    def __repr__(self):
        return f"<RefreshToken(user_id={self.user_id}, revoked={self.revoked})>"
    
    def is_valid(self) -> bool:
        """检查令牌是否有效"""
        return not self.revoked and self.expires_at > datetime.utcnow()


class RedemptionCode(Base):
    """
    兑换码表
    
    存储用户购买的使用次数兑换码
    """
    __tablename__ = "redemption_codes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)  # PRISM-XXXXXXXX
    count = Column(Integer, nullable=False)  # 可兑换的使用次数
    
    # 批次管理
    batch_id = Column(String(50), nullable=False, index=True)  # 批次号
    price = Column(Numeric(10, 2), nullable=True)  # 价格（用于统计）
    description = Column(Text, nullable=True)  # 描述
    
    # 使用状态
    used = Column(Boolean, default=False, nullable=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)  # 过期时间（可选）
    
    # 关系
    used_by_user = relationship(
        "User",
        back_populates="redemption_codes_used",
        foreign_keys=[used_by]
    )
    
    # 索引
    __table_args__ = (
        Index("idx_rc_code", "code"),
        Index("idx_rc_batch", "batch_id"),
        Index("idx_rc_used", "used"),
    )
    
    def __repr__(self):
        return f"<RedemptionCode(code='{self.code}', count={self.count}, used={self.used})>"
    
    def is_valid(self) -> bool:
        """检查兑换码是否有效"""
        if self.used:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True


class TopupRecord(Base):
    """
    充值记录表
    
    记录用户的充值历史
    """
    __tablename__ = "topup_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 充值来源
    source = Column(String(50), nullable=False)  # redemption_code, wechat_pay
    code_id = Column(Integer, ForeignKey("redemption_codes.id"), nullable=True)  # 兑换码 ID
    
    # 充值金额
    count = Column(Integer, nullable=False)  # 充值次数
    bonus_count = Column(Integer, default=0, nullable=False)  # 赠送次数（如邀请返利）
    
    # 返利信息
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_bonus_given = Column(Boolean, default=False, nullable=False)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="topup_records", foreign_keys=[user_id])
    redemption_code = relationship("RedemptionCode", foreign_keys=[code_id])
    inviter = relationship("User", foreign_keys=[invited_by])
    
    # 索引
    __table_args__ = (
        Index("idx_tr_user", "user_id"),
        Index("idx_tr_created", "created_at"),
    )
    
    def __repr__(self):
        return f"<TopupRecord(user_id={self.user_id}, count={self.count}, source='{self.source}')>"


class InviteRecord(Base):
    """
    邀请记录表
    
    记录邀请关系和奖励发放情况
    """
    __tablename__ = "invite_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # 奖励状态
    bonus_given = Column(Boolean, default=False, nullable=False)  # 是否已发放奖励
    bonus_count = Column(Integer, default=0, nullable=False)  # 奖励次数
    bonus_at = Column(DateTime, nullable=True)  # 奖励发放时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 关系
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="invite_records_as_inviter")
    invitee = relationship("User", foreign_keys=[invitee_id], back_populates="invite_records_as_invitee")
    
    # 索引
    __table_args__ = (
        Index("idx_ir_inviter", "inviter_id"),
        Index("idx_ir_invitee", "invitee_id"),
        UniqueConstraint("inviter_id", "invitee_id", name="uq_invite_relation"),
    )
    
    def __repr__(self):
        return f"<InviteRecord(inviter_id={self.inviter_id}, invitee_id={self.invitee_id}, bonus_given={self.bonus_given})>"


class Admin(Base):
    """
    管理员表
    
    存储管理员信息和权限
    """
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    role = Column(String(50), default="admin", nullable=False)  # admin, super_admin
    permissions = Column(Text, nullable=True)  # JSON 格式的权限列表
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User")
    
    def __repr__(self):
        return f"<Admin(user_id={self.user_id}, role='{self.role}')>"


class Report(Base):
    """
    报告表
    
    存储用户生成的情报报告，支持缓存
    """
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 用户关联（可为空，匿名用户）
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    anonymous_id = Column(Integer, ForeignKey("anonymous_users.id", ondelete="SET NULL"), nullable=True)
    
    # 报告内容
    report_type = Column(String(50), nullable=False)  # bounty_hunter, alpha_radar, etc.
    content = Column(Text, nullable=True)  # 报告内容（JSON 格式）
    
    # 用户类型和缓存
    user_type_at_creation = Column(String(20), nullable=False, default="anonymous")  # paid, free, anonymous
    cache_type = Column(String(20), nullable=False, default="free")  # premium, free
    cache_expires_at = Column(DateTime, nullable=True)  # 缓存过期时间
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系
    user = relationship("User", back_populates="reports")
    anonymous_user = relationship("AnonymousUser", back_populates="reports")
    
    # 索引
    __table_args__ = (
        Index("idx_report_user", "user_id"),
        Index("idx_report_anon", "anonymous_id"),
        Index("idx_report_type", "report_type"),
        Index("idx_report_cache", "cache_type", "cache_expires_at"),
    )
    
    def __repr__(self):
        return f"<Report(id={self.id}, type='{self.report_type}', user_type='{self.user_type_at_creation}')>"
    
    def is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if not self.cache_expires_at:
            return False
        return self.cache_expires_at > datetime.utcnow()
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "report_type": self.report_type,
            "user_type": self.user_type_at_creation,
            "cache_type": self.cache_type,
            "cache_expires_at": self.cache_expires_at.isoformat() if self.cache_expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


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