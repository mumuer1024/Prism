# -*- coding: utf-8 -*-
"""
数据库 CRUD 操作

提供所有数据库表的基本 CRUD 操作函数
"""

import hashlib
import secrets
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from src.database.models import (
    User,
    VerificationCode,
    RefreshToken,
    RedemptionCode,
    TopupRecord,
    InviteRecord,
)
from src.config import settings

logger = logging.getLogger(__name__)


# ==========================================
# 用户相关 CRUD
# ==========================================

def create_user(
    db: Session,
    email: str,
    password_hash: str,
    invite_code: str,
    invited_by: int = None,
    oauth_provider: str = None,
    oauth_id: str = None,
    oauth_name: str = None,
    oauth_avatar: str = None,
) -> User:
    """
    创建新用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
        password_hash: 密码哈希（OAuth 用户可为 None）
        invite_code: 用户专属邀请码
        invited_by: 邀请人 ID（可选）
        oauth_provider: OAuth 提供商（可选）
        oauth_id: OAuth 用户 ID（可选）
        oauth_name: OAuth 用户名（可选）
        oauth_avatar: OAuth 头像（可选）
    
    Returns:
        User: 创建的用户对象
    """
    user = User(
        email=email,
        password_hash=password_hash,
        invite_code=invite_code,
        invited_by=invited_by,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id,
        oauth_name=oauth_name,
        oauth_avatar=oauth_avatar,
        usage_count=0,
        is_active=True,
        is_verified=True if oauth_provider else False,  # OAuth 用户自动验证
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"用户创建成功: id={user.id}, email={email}")
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    通过邮箱获取用户
    
    Args:
        db: 数据库会话
        email: 用户邮箱
    
    Returns:
        Optional[User]: 用户对象，不存在则返回 None
    """
    return db.query(User).filter(User.email == email.lower()).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    通过 ID 获取用户
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
    
    Returns:
        Optional[User]: 用户对象，不存在则返回 None
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_invite_code(db: Session, invite_code: str) -> Optional[User]:
    """
    通过邀请码获取用户
    
    Args:
        db: 数据库会话
        invite_code: 邀请码
    
    Returns:
        Optional[User]: 用户对象，不存在则返回 None
    """
    return db.query(User).filter(User.invite_code == invite_code.upper()).first()


def get_user_by_oauth(db: Session, provider: str, oauth_id: str) -> Optional[User]:
    """
    通过 OAuth 信息获取用户
    
    Args:
        db: 数据库会话
        provider: OAuth 提供商
        oauth_id: OAuth 用户 ID
    
    Returns:
        Optional[User]: 用户对象，不存在则返回 None
    """
    return db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_id == oauth_id
    ).first()


def link_oauth_to_user(
    db: Session,
    user_id: int,
    oauth_provider: str,
    oauth_id: str,
    oauth_name: str,
    oauth_avatar: str = None,
) -> Optional[User]:
    """
    将 OAuth 账号绑定到已有用户
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        oauth_provider: OAuth 提供商
        oauth_id: OAuth 用户 ID
        oauth_name: OAuth 用户名
        oauth_avatar: OAuth 头像
    
    Returns:
        Optional[User]: 更新后的用户对象
    """
    user = get_user_by_id(db, user_id)
    if user:
        # 检查是否已被其他用户绑定
        existing = get_user_by_oauth(db, oauth_provider, oauth_id)
        if existing and existing.id != user_id:
            logger.warning(f"OAuth 账号已被其他用户绑定: provider={oauth_provider}, oauth_id={oauth_id}")
            return None
        
        user.oauth_provider = oauth_provider
        user.oauth_id = oauth_id
        user.oauth_name = oauth_name
        user.oauth_avatar = oauth_avatar
        db.commit()
        db.refresh(user)
        logger.info(f"OAuth 账号绑定成功: user_id={user_id}, provider={oauth_provider}")
    return user


def update_user_usage_count(db: Session, user_id: int, delta: int) -> User:
    """
    更新用户使用次数
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        delta: 变化量（正数增加，负数减少）
    
    Returns:
        User: 更新后的用户对象
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.usage_count = max(0, user.usage_count + delta)
        db.commit()
        db.refresh(user)
    return user


def update_last_login(db: Session, user_id: int) -> None:
    """
    更新最后登录时间
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.last_login_at = datetime.utcnow()
        db.commit()


def update_password(db: Session, user_id: int, new_password_hash: str) -> None:
    """
    更新用户密码
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        new_password_hash: 新密码哈希
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.password_hash = new_password_hash
        db.commit()


def update_user_usage(db: Session, user_id: int, **kwargs) -> User:
    """
    更新用户信息
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        **kwargs: 要更新的字段
    
    Returns:
        User: 更新后的用户对象
    """
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user


# ==========================================
# 验证码相关 CRUD
# ==========================================

def create_verification_code(
    db: Session,
    email: str,
    code: str,
    purpose: str,
    expires_minutes: int = 5,
) -> VerificationCode:
    """
    创建验证码
    
    Args:
        db: 数据库会话
        email: 邮箱
        code: 验证码
        purpose: 用途 (register, reset_password)
        expires_minutes: 过期时间（分钟）
    
    Returns:
        VerificationCode: 创建的验证码对象
    """
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    vc = VerificationCode(
        email=email.lower(),
        code=code,
        purpose=purpose,
        expires_at=expires_at,
    )
    db.add(vc)
    db.commit()
    db.refresh(vc)
    
    return vc


def get_valid_verification_code(
    db: Session,
    email: str,
    code: str,
    purpose: str,
) -> Optional[VerificationCode]:
    """
    获取有效的验证码
    
    Args:
        db: 数据库会话
        email: 邮箱
        code: 验证码
        purpose: 用途
    
    Returns:
        Optional[VerificationCode]: 验证码对象，无效则返回 None
    """
    return db.query(VerificationCode).filter(
        VerificationCode.email == email.lower(),
        VerificationCode.code == code,
        VerificationCode.purpose == purpose,
        VerificationCode.used == False,
        VerificationCode.expires_at > datetime.utcnow(),
    ).first()


def mark_code_as_used(db: Session, code_id: int) -> None:
    """
    标记验证码为已使用
    
    Args:
        db: 数据库会话
        code_id: 验证码 ID
    """
    vc = db.query(VerificationCode).filter(VerificationCode.id == code_id).first()
    if vc:
        vc.used = True
        db.commit()


def can_send_code(
    db: Session,
    email: str,
    purpose: str,
    cooldown_seconds: int = 60,
) -> Tuple[bool, int]:
    """
    检查是否可以发送验证码
    
    Args:
        db: 数据库会话
        email: 邮箱
        purpose: 用途
        cooldown_seconds: 冷却时间（秒）
    
    Returns:
        Tuple[bool, int]: (是否可以发送, 剩余冷却时间)
    """
    cutoff_time = datetime.utcnow() - timedelta(seconds=cooldown_seconds)
    
    recent_code = db.query(VerificationCode).filter(
        VerificationCode.email == email.lower(),
        VerificationCode.purpose == purpose,
        VerificationCode.created_at > cutoff_time,
    ).order_by(VerificationCode.created_at.desc()).first()
    
    if recent_code:
        elapsed = (datetime.utcnow() - recent_code.created_at).total_seconds()
        remaining = max(0, cooldown_seconds - int(elapsed))
        return False, remaining
    
    return True, 0


def delete_expired_codes(db: Session) -> int:
    """
    删除过期验证码
    
    Args:
        db: 数据库会话
    
    Returns:
        int: 删除的数量
    """
    result = db.query(VerificationCode).filter(
        VerificationCode.expires_at < datetime.utcnow()
    ).delete()
    db.commit()
    return result


# ==========================================
# Token 相关 CRUD
# ==========================================

def hash_token(token: str) -> str:
    """
    对 Token 进行 SHA256 哈希
    
    Args:
        token: 原始 Token
    
    Returns:
        str: 哈希后的 Token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def create_refresh_token(
    db: Session,
    user_id: int,
    token: str,
    expires_days: int = 7,
    device_info: str = None,
    ip_address: str = None,
) -> RefreshToken:
    """
    创建刷新令牌
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        token: 原始刷新令牌
        expires_days: 过期天数
        device_info: 设备信息
        ip_address: IP 地址
    
    Returns:
        RefreshToken: 创建的刷新令牌对象
    """
    expires_at = datetime.utcnow() + timedelta(days=expires_days)
    token_hash = hash_token(token)
    
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_info=device_info,
        ip_address=ip_address,
    )
    db.add(rt)
    db.commit()
    db.refresh(rt)
    
    return rt


def get_valid_refresh_token(db: Session, token: str) -> Optional[RefreshToken]:
    """
    获取有效的刷新令牌
    
    Args:
        db: 数据库会话
        token: 原始刷新令牌
    
    Returns:
        Optional[RefreshToken]: 刷新令牌对象，无效则返回 None
    """
    token_hash = hash_token(token)
    
    return db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow(),
    ).first()


def get_refresh_token_by_hash(db: Session, token_hash: str) -> Optional[RefreshToken]:
    """
    通过哈希获取刷新令牌
    
    Args:
        db: 数据库会话
        token_hash: Token 哈希
    
    Returns:
        Optional[RefreshToken]: 刷新令牌对象
    """
    return db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()


def revoke_refresh_token(db: Session, token_id: int) -> None:
    """
    撤销刷新令牌
    
    Args:
        db: 数据库会话
        token_id: 令牌 ID
    """
    rt = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if rt:
        rt.revoked = True
        db.commit()


def revoke_token_by_hash(db: Session, token_hash: str) -> None:
    """
    通过哈希撤销刷新令牌
    
    Args:
        db: 数据库会话
        token_hash: Token 哈希
    """
    rt = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()
    if rt:
        rt.revoked = True
        db.commit()


def revoke_all_user_tokens(db: Session, user_id: int) -> int:
    """
    撤销用户所有刷新令牌
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
    
    Returns:
        int: 撤销的数量
    """
    result = db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id,
        RefreshToken.revoked == False,
    ).update({"revoked": True})
    db.commit()
    return result


def cleanup_expired_tokens(db: Session) -> int:
    """
    清理过期的刷新令牌
    
    Args:
        db: 数据库会话
    
    Returns:
        int: 删除的数量
    """
    result = db.query(RefreshToken).filter(
        or_(
            RefreshToken.expires_at < datetime.utcnow(),
            RefreshToken.revoked == True,
        )
    ).delete()
    db.commit()
    return result


# ==========================================
# 邀请码相关 CRUD
# ==========================================

def generate_unique_invite_code(
    db: Session,
    prefix: str = "PRISM-",
    length: int = 8,
) -> str:
    """
    生成唯一的邀请码
    
    格式: PRISM-A1B2C3D4（8位大写字母+数字）
    
    Args:
        db: 数据库会话
        prefix: 前缀
        length: 随机部分长度
    
    Returns:
        str: 唯一的邀请码
    """
    chars = string.ascii_uppercase + string.digits
    
    while True:
        # 生成随机部分
        random_part = ''.join(secrets.choice(chars) for _ in range(length))
        code = f"{prefix}{random_part}"
        
        # 检查是否已存在
        existing = db.query(User).filter(User.invite_code == code).first()
        if not existing:
            return code


# ==========================================
# 兑换码相关 CRUD
# ==========================================

def get_redemption_code(db: Session, code: str) -> Optional[RedemptionCode]:
    """
    获取兑换码
    
    Args:
        db: 数据库会话
        code: 兑换码
    
    Returns:
        Optional[RedemptionCode]: 兑换码对象
    """
    return db.query(RedemptionCode).filter(
        RedemptionCode.code == code.upper()
    ).first()


def use_redemption_code(
    db: Session,
    code_id: int,
    user_id: int,
) -> RedemptionCode:
    """
    使用兑换码
    
    Args:
        db: 数据库会话
        code_id: 兑换码 ID
        user_id: 使用者 ID
    
    Returns:
        RedemptionCode: 更新后的兑换码对象
    """
    rc = db.query(RedemptionCode).filter(RedemptionCode.id == code_id).first()
    if rc:
        rc.used = True
        rc.used_by = user_id
        rc.used_at = datetime.utcnow()
        db.commit()
        db.refresh(rc)
    return rc


def create_redemption_codes(
    db: Session,
    batch_id: str,
    count_per_code: int,
    num_codes: int,
    price: float = None,
    description: str = None,
    expires_at: datetime = None,
) -> List[RedemptionCode]:
    """
    批量创建兑换码
    
    Args:
        db: 数据库会话
        batch_id: 批次号
        count_per_code: 每个兑换码的次数
        num_codes: 创建数量
        price: 价格
        description: 描述
        expires_at: 过期时间
    
    Returns:
        List[RedemptionCode]: 创建的兑换码列表
    """
    codes = []
    chars = string.ascii_uppercase + string.digits
    
    for _ in range(num_codes):
        # 生成唯一兑换码
        while True:
            random_part = ''.join(secrets.choice(chars) for _ in range(8))
            code = f"PRISM-{random_part}"
            
            existing = db.query(RedemptionCode).filter(
                RedemptionCode.code == code
            ).first()
            if not existing:
                break
        
        rc = RedemptionCode(
            code=code,
            count=count_per_code,
            batch_id=batch_id,
            price=price,
            description=description,
            expires_at=expires_at,
        )
        codes.append(rc)
        db.add(rc)
    
    db.commit()
    
    for rc in codes:
        db.refresh(rc)
    
    return codes


def process_redemption_with_invite_bonus(
    db: Session,
    user: User,
    redemption_code: RedemptionCode,
    invite_bonus_count: int = 3,
    invitee_bonus_count: int = 3,
) -> dict:
    """
    处理兑换码充值并处理邀请返利
    
    邀请返利机制：
    - 被邀请人首次充值时，额外获得赠送次数（invitee_bonus_count）
    - 邀请人同时获得奖励次数（invite_bonus_count）
    - 每个被邀请人只能享受一次首次充值奖励
    
    Args:
        db: 数据库会话
        user: 用户对象（被邀请人）
        redemption_code: 兑换码对象
        invite_bonus_count: 邀请人获得奖励次数（默认3次）
        invitee_bonus_count: 被邀请人获得赠送次数（默认3次）
    
    Returns:
        dict: 处理结果
            - count: 兑换码基础次数
            - bonus_count: 被邀请人赠送次数
            - inviter_bonus: 邀请人是否获得奖励
            - inviter_bonus_count: 邀请人获得奖励次数
    """
    result = {
        "count": redemption_code.count,
        "bonus_count": 0,
        "inviter_bonus": False,
        "inviter_bonus_count": 0,
    }
    
    # 检查是否有邀请人且被邀请人未享受首次返利
    if user.invited_by and not user.has_redeemed_first:
        # 被邀请人获得赠送
        result["bonus_count"] = invitee_bonus_count
        result["inviter_bonus"] = True
        result["inviter_bonus_count"] = invite_bonus_count
        
        # 更新被邀请人状态
        user.has_redeemed_first = True
        user.usage_count += redemption_code.count + invitee_bonus_count
        
        # 邀请人获得赠送
        inviter = get_user_by_id(db, user.invited_by)
        if inviter:
            inviter.usage_count += invite_bonus_count
        
        # 更新邀请记录
        invite_record = get_invite_record(db, user.invited_by, user.id)
        if invite_record:
            invite_record.bonus_given = True
            invite_record.bonus_count = invite_bonus_count
            invite_record.bonus_at = datetime.utcnow()
    else:
        # 无邀请返利
        user.usage_count += redemption_code.count
    
    # 标记兑换码已使用
    redemption_code.used = True
    redemption_code.used_by = user.id
    redemption_code.used_at = datetime.utcnow()
    
    # 创建充值记录
    create_topup_record(
        db=db,
        user_id=user.id,
        source="redemption_code",
        count=redemption_code.count,
        bonus_count=result["bonus_count"],
        code_id=redemption_code.id,
        invited_by=user.invited_by if result["inviter_bonus"] else None,
        invited_bonus_given=result["inviter_bonus"],
    )
    
    db.commit()
    
    return result


# ==========================================
# 充值记录相关 CRUD
# ==========================================

def create_topup_record(
    db: Session,
    user_id: int,
    source: str,
    count: int,
    bonus_count: int = 0,
    code_id: int = None,
    invited_by: int = None,
    invited_bonus_given: bool = False,
) -> TopupRecord:
    """
    创建充值记录
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        source: 来源
        count: 充值次数
        bonus_count: 赠送次数
        code_id: 兑换码 ID
        invited_by: 邀请人 ID
        invited_bonus_given: 是否已发放邀请奖励
    
    Returns:
        TopupRecord: 创建的充值记录
    """
    record = TopupRecord(
        user_id=user_id,
        source=source,
        count=count,
        bonus_count=bonus_count,
        code_id=code_id,
        invited_by=invited_by,
        invited_bonus_given=invited_bonus_given,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


def get_topup_records_by_user(
    db: Session,
    user_id: int,
    limit: int = 20,
    offset: int = 0,
) -> List[TopupRecord]:
    """
    获取用户充值记录
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        List[TopupRecord]: 充值记录列表
    """
    return db.query(TopupRecord).filter(
        TopupRecord.user_id == user_id
    ).order_by(
        TopupRecord.created_at.desc()
    ).offset(offset).limit(limit).all()


# ==========================================
# 邀请记录相关 CRUD
# ==========================================

def create_invite_record(
    db: Session,
    inviter_id: int,
    invitee_id: int,
) -> InviteRecord:
    """
    创建邀请记录
    
    Args:
        db: 数据库会话
        inviter_id: 邀请人 ID
        invitee_id: 被邀请人 ID
    
    Returns:
        InviteRecord: 创建的邀请记录
    """
    record = InviteRecord(
        inviter_id=inviter_id,
        invitee_id=invitee_id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


def get_invite_record(
    db: Session,
    inviter_id: int,
    invitee_id: int,
) -> Optional[InviteRecord]:
    """
    获取邀请记录
    
    Args:
        db: 数据库会话
        inviter_id: 邀请人 ID
        invitee_id: 被邀请人 ID
    
    Returns:
        Optional[InviteRecord]: 邀请记录
    """
    return db.query(InviteRecord).filter(
        InviteRecord.inviter_id == inviter_id,
        InviteRecord.invitee_id == invitee_id,
    ).first()


def get_invite_records_by_inviter(
    db: Session,
    inviter_id: int,
    limit: int = 20,
    offset: int = 0,
) -> List[InviteRecord]:
    """
    获取邀请人的邀请记录
    
    Args:
        db: 数据库会话
        inviter_id: 邀请人 ID
        limit: 限制数量
        offset: 偏移量
    
    Returns:
        List[InviteRecord]: 邀请记录列表
    """
    return db.query(InviteRecord).filter(
        InviteRecord.inviter_id == inviter_id
    ).order_by(
        InviteRecord.created_at.desc()
    ).offset(offset).limit(limit).all()


def update_invite_bonus(
    db: Session,
    record_id: int,
    bonus_count: int = 3,
) -> InviteRecord:
    """
    更新邀请奖励状态
    
    Args:
        db: 数据库会话
        record_id: 记录 ID
        bonus_count: 奖励次数
    
    Returns:
        InviteRecord: 更新后的记录
    """
    record = db.query(InviteRecord).filter(InviteRecord.id == record_id).first()
    if record:
        record.bonus_given = True
        record.bonus_count = bonus_count
        record.bonus_at = datetime.utcnow()
        db.commit()
        db.refresh(record)
    return record


def get_invite_stats(db: Session, user_id: int) -> dict:
    """
    获取邀请统计
    
    Args:
        db: 数据库会话
        user_id: 用户 ID
    
    Returns:
        dict: 邀请统计信息
    """
    # 总邀请人数
    total_invited = db.query(InviteRecord).filter(
        InviteRecord.inviter_id == user_id
    ).count()
    
    # 已充值人数
    active_invited = db.query(InviteRecord).filter(
        InviteRecord.inviter_id == user_id,
        InviteRecord.bonus_given == True,
    ).count()
    
    # 累计奖励次数
    records = db.query(InviteRecord).filter(
        InviteRecord.inviter_id == user_id,
        InviteRecord.bonus_given == True,
    ).all()
    total_bonus = sum(r.bonus_count for r in records)
    
    return {
        "total_invited": total_invited,
        "active_invited": active_invited,
        "total_bonus": total_bonus,
    }


# ==========================================
# 用户数据删除
# ==========================================

def delete_user_data(db: Session, user_id: int) -> bool:
    """
    删除用户相关数据

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        bool: 是否成功
    """
    # 删除刷新令牌
    db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()

    # 删除验证码
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.email:
        db.query(VerificationCode).filter(VerificationCode.email == user.email).delete()

    # 删除充值记录
    db.query(TopupRecord).filter(TopupRecord.user_id == user_id).delete()

    # 删除邀请记录（作为邀请人）
    db.query(InviteRecord).filter(InviteRecord.inviter_id == user_id).delete()

    # 删除邀请记录（作为被邀请人）
    db.query(InviteRecord).filter(InviteRecord.invitee_id == user_id).delete()

    db.commit()

    logger.info(f"用户 {user_id} 相关数据已删除")

    return True