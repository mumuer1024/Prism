# -*- coding: utf-8 -*-
"""
数据库 CRUD 操作 - 激活码架构

提供激活码相关的数据库 CRUD 操作函数（v2.1 激活码架构）
"""

import secrets
import string
import logging
import bcrypt
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from src.database.models import (
    ActivationCode,
    Device,
    ReferralCode,
    AnonymousUsage,
    AdminUser,
    AuditLog,
    MarketplaceTemplate,
    UserPrompt,
    UserSource,
    UserConfig,
    DailyHotCategoryConfig,
)

logger = logging.getLogger(__name__)


# ==========================================
# 激活码相关 CRUD
# ==========================================

def generate_activation_code(
    prefix: str = "PRISM-",
    segment_length: int = 4,
    num_segments: int = 3,
) -> str:
    """
    生成激活码

    格式: PRISM-XXXX-XXXX-XXXX（不区分大小写）

    Args:
        prefix: 前缀
        segment_length: 每段长度
        num_segments: 段数

    Returns:
        str: 激活码
    """
    chars = string.ascii_uppercase + string.digits
    segments = []
    for _ in range(num_segments):
        segment = ''.join(secrets.choice(chars) for _ in range(segment_length))
        segments.append(segment)
    return f"{prefix}{'-'.join(segments)}"


def create_activation_code(
    db: Session,
    quota: int,
    code: str = None,
) -> ActivationCode:
    """
    创建激活码

    Args:
        db: 数据库会话
        quota: 次数（3/6/10/20/50/100）
        code: 激活码（可选，不提供则自动生成）

    Returns:
        ActivationCode: 创建的激活码对象
    """
    if not code:
        # 生成唯一激活码
        while True:
            code = generate_activation_code()
            existing = db.query(ActivationCode).filter(
                ActivationCode.code == code
            ).first()
            if not existing:
                break

    ac = ActivationCode(
        code=code.upper(),
        quota=quota,
        remaining=quota,
        is_activated=False,
    )
    db.add(ac)
    db.commit()
    db.refresh(ac)

    logger.info(f"激活码创建成功: code={ac.code}, quota={quota}")
    return ac


def create_activation_codes_batch(
    db: Session,
    quota: int,
    num_codes: int,
) -> List[ActivationCode]:
    """
    批量创建激活码

    Args:
        db: 数据库会话
        quota: 次数
        num_codes: 创建数量

    Returns:
        List[ActivationCode]: 创建的激活码列表
    """
    codes = []
    for _ in range(num_codes):
        ac = create_activation_code(db, quota)
        codes.append(ac)

    logger.info(f"批量创建激活码: num={num_codes}, quota={quota}")
    return codes


def get_activation_code_by_code(
    db: Session,
    code: str,
) -> Optional[ActivationCode]:
    """
    通过激活码字符串获取激活码

    Args:
        db: 数据库会话
        code: 激活码（不区分大小写）

    Returns:
        Optional[ActivationCode]: 激活码对象
    """
    return db.query(ActivationCode).filter(
        ActivationCode.code == code.upper()
    ).first()


def get_activation_code_by_id(
    db: Session,
    code_id: int,
) -> Optional[ActivationCode]:
    """
    通过 ID 获取激活码

    Args:
        db: 数据库会话
        code_id: 激活码 ID

    Returns:
        Optional[ActivationCode]: 激活码对象
    """
    return db.query(ActivationCode).filter(
        ActivationCode.id == code_id
    ).first()


def get_activation_code_by_device_id(
    db: Session,
    device_id: str,
) -> Optional[ActivationCode]:
    """
    通过设备 ID 获取关联的激活码

    Args:
        db: 数据库会话
        device_id: 设备 ID

    Returns:
        Optional[ActivationCode]: 激活码对象
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        return device.activation_code
    return None


def update_activation_code(
    db: Session,
    code_id: int,
    **kwargs,
) -> Optional[ActivationCode]:
    """
    更新激活码

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        **kwargs: 要更新的字段

    Returns:
        Optional[ActivationCode]: 更新后的激活码对象
    """
    ac = get_activation_code_by_id(db, code_id)
    if ac:
        for key, value in kwargs.items():
            if hasattr(ac, key):
                setattr(ac, key, value)
        db.commit()
        db.refresh(ac)
    return ac


def add_quota_to_activation_code(
    db: Session,
    code_id: int,
    amount: int,
) -> Optional[ActivationCode]:
    """
    给激活码增加次数

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        amount: 增加次数

    Returns:
        Optional[ActivationCode]: 更新后的激活码对象
    """
    ac = get_activation_code_by_id(db, code_id)
    if ac:
        ac.quota += amount
        ac.remaining += amount
        db.commit()
        db.refresh(ac)
        logger.info(f"激活码增加次数: code={ac.code}, amount={amount}, remaining={ac.remaining}")
    return ac


def deduct_activation_code_quota(
    db: Session,
    code_id: int,
    amount: int = 1,
) -> Optional[ActivationCode]:
    """
    扣减激活码次数

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        amount: 扣减次数

    Returns:
        Optional[ActivationCode]: 更新后的激活码对象
    """
    ac = get_activation_code_by_id(db, code_id)
    if ac and ac.remaining >= amount:
        ac.remaining -= amount
        db.commit()
        db.refresh(ac)
        logger.info(f"激活码扣减次数: code={ac.code}, amount={amount}, remaining={ac.remaining}")
    return ac


def deactivate_activation_code(
    db: Session,
    code_id: int,
) -> Optional[ActivationCode]:
    """
    作废激活码

    Args:
        db: 数据库会话
        code_id: 激活码 ID

    Returns:
        Optional[ActivationCode]: 更新后的激活码对象
    """
    ac = get_activation_code_by_id(db, code_id)
    if ac:
        ac.remaining = 0
        db.commit()
        db.refresh(ac)
        logger.info(f"激活码已作废: code={ac.code}")
    return ac


def list_activation_codes(
    db: Session,
    is_activated: bool = None,
    has_remaining: bool = None,
    limit: int = 50,
    offset: int = 0,
) -> List[ActivationCode]:
    """
    查询激活码列表

    Args:
        db: 数据库会话
        is_activated: 是否已激活（可选）
        has_remaining: 是否有剩余次数（可选）
        limit: 限制数量
        offset: 偏移量

    Returns:
        List[ActivationCode]: 激活码列表
    """
    query = db.query(ActivationCode)

    if is_activated is not None:
        query = query.filter(ActivationCode.is_activated == is_activated)

    if has_remaining is not None:
        if has_remaining:
            query = query.filter(ActivationCode.remaining > 0)
        else:
            query = query.filter(ActivationCode.remaining == 0)

    return query.order_by(
        desc(ActivationCode.created_at)
    ).offset(offset).limit(limit).all()


# ==========================================
# 设备相关 CRUD
# ==========================================

def create_device(
    db: Session,
    code_id: int,
    device_id: str,
    device_name: str = None,
) -> Optional[Device]:
    """
    创建设备绑定（幂等）

    如果设备已绑定，不重复插入，直接返回现有设备

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        device_id: 设备 ID
        device_name: 设备名称

    Returns:
        Optional[Device]: 设备对象（失败返回 None）
    """
    # 检查是否已绑定
    existing = db.query(Device).filter(
        Device.code_id == code_id,
        Device.device_id == device_id,
    ).first()

    if existing:
        # 幂等：已存在则更新 last_seen
        existing.last_seen = datetime.utcnow()
        if device_name:
            existing.device_name = device_name
        db.commit()
        db.refresh(existing)
        logger.info(f"设备已绑定，更新活跃时间: device_id={device_id[:16]}...")
        return existing

    # 检查设备数量限制
    device_count = db.query(Device).filter(Device.code_id == code_id).count()
    if device_count >= 3:
        logger.warning(f"设备数量已达上限: code_id={code_id}, count={device_count}")
        return None

    # 创建新设备绑定
    device = Device(
        code_id=code_id,
        device_id=device_id,
        device_name=device_name,
        last_seen=datetime.utcnow(),
    )
    db.add(device)
    db.commit()
    db.refresh(device)

    logger.info(f"设备绑定成功: code_id={code_id}, device_id={device_id[:16]}...")
    return device


def get_devices_by_code_id(
    db: Session,
    code_id: int,
) -> List[Device]:
    """
    获取激活码绑定的所有设备

    Args:
        db: 数据库会话
        code_id: 激活码 ID

    Returns:
        List[Device]: 设备列表
    """
    return db.query(Device).filter(
        Device.code_id == code_id
    ).order_by(desc(Device.last_seen)).all()


def get_device_by_id(
    db: Session,
    device_db_id: int,
) -> Optional[Device]:
    """
    通过数据库 ID 获取设备

    Args:
        db: 数据库会话
        device_db_id: 设备数据库 ID

    Returns:
        Optional[Device]: 设备对象
    """
    return db.query(Device).filter(Device.id == device_db_id).first()


def delete_device(
    db: Session,
    device_db_id: int,
) -> bool:
    """
    解绑设备

    Args:
        db: 数据库会话
        device_db_id: 设备数据库 ID

    Returns:
        bool: 是否成功
    """
    device = get_device_by_id(db, device_db_id)
    if device:
        db.delete(device)
        db.commit()
        logger.info(f"设备已解绑: device_id={device.device_id[:16]}...")
        return True
    return False


def update_device_last_seen(
    db: Session,
    device_id: str,
) -> Optional[Device]:
    """
    更新设备最后活跃时间

    Args:
        db: 数据库会话
        device_id: 设备 ID

    Returns:
        Optional[Device]: 设备对象
    """
    device = db.query(Device).filter(Device.device_id == device_id).first()
    if device:
        device.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(device)
    return device


def count_devices_by_code_id(
    db: Session,
    code_id: int,
) -> int:
    """
    统计激活码绑定的设备数量

    Args:
        db: 数据库会话
        code_id: 激活码 ID

    Returns:
        int: 设备数量
    """
    return db.query(Device).filter(Device.code_id == code_id).count()


# ==========================================
# 推荐码相关 CRUD
# ==========================================

def generate_referral_code(length: int = 6) -> str:
    """
    生成推荐码

    格式: REF-XXXXXX（6位大写字母数字）

    Args:
        length: 随机部分长度

    Returns:
        str: 推荐码
    """
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(secrets.choice(chars) for _ in range(length))
    return f"REF-{random_part}"


def create_referral_code(
    db: Session,
    code_id: int,
) -> ReferralCode:
    """
    创建推荐码

    Args:
        db: 数据库会话
        code_id: 激活码 ID

    Returns:
        ReferralCode: 推荐码对象
    """
    # 检查是否已存在
    existing = db.query(ReferralCode).filter(ReferralCode.code_id == code_id).first()
    if existing:
        return existing

    # 生成唯一推荐码
    while True:
        referral_code = generate_referral_code()
        existing = db.query(ReferralCode).filter(
            ReferralCode.referral_code == referral_code
        ).first()
        if not existing:
            break

    rc = ReferralCode(
        code_id=code_id,
        referral_code=referral_code,
    )
    db.add(rc)
    db.commit()
    db.refresh(rc)

    logger.info(f"推荐码创建成功: code_id={code_id}, referral_code={referral_code}")
    return rc


def get_referral_code_by_code(
    db: Session,
    referral_code: str,
) -> Optional[ReferralCode]:
    """
    通过推荐码字符串获取推荐码

    Args:
        db: 数据库会话
        referral_code: 推荐码

    Returns:
        Optional[ReferralCode]: 推荐码对象
    """
    return db.query(ReferralCode).filter(
        ReferralCode.referral_code == referral_code.upper()
    ).first()


def get_referral_code_by_code_id(
    db: Session,
    code_id: int,
) -> Optional[ReferralCode]:
    """
    通过激活码 ID 获取推荐码

    Args:
        db: 数据库会话
        code_id: 激活码 ID

    Returns:
        Optional[ReferralCode]: 推荐码对象
    """
    return db.query(ReferralCode).filter(
        ReferralCode.code_id == code_id
    ).first()


def update_referral_stats(
    db: Session,
    referral_code_id: int,
    increment_referral: bool = True,
    reward_amount: int = 0,
) -> Optional[ReferralCode]:
    """
    更新推荐统计

    Args:
        db: 数据库会话
        referral_code_id: 推荐码 ID
        increment_referral: 是否增加推荐人数
        reward_amount: 增加奖励次数

    Returns:
        Optional[ReferralCode]: 更新后的推荐码对象
    """
    rc = db.query(ReferralCode).filter(ReferralCode.id == referral_code_id).first()
    if rc:
        if increment_referral:
            rc.referral_count += 1
        if reward_amount > 0:
            rc.total_rewarded += reward_amount
        db.commit()
        db.refresh(rc)
    return rc


# ==========================================
# 匿名用户相关 CRUD
# ==========================================

def get_or_create_anonymous_usage(
    db: Session,
    visitor_id: str,
) -> AnonymousUsage:
    """
    获取或创建匿名用户使用记录

    Args:
        db: 数据库会话
        visitor_id: 访客 ID

    Returns:
        AnonymousUsage: 匿名用户记录
    """
    anon = db.query(AnonymousUsage).filter(
        AnonymousUsage.visitor_id == visitor_id
    ).first()

    if not anon:
        anon = AnonymousUsage(
            visitor_id=visitor_id,
            daily_count=0,
            daily_date=datetime.utcnow().strftime("%Y-%m-%d"),
        )
        db.add(anon)
        db.commit()
        db.refresh(anon)

    return anon


def reset_anonymous_daily_usage(
    db: Session,
    visitor_id: str,
) -> AnonymousUsage:
    """
    重置匿名用户每日使用次数

    Args:
        db: 数据库会话
        visitor_id: 访客 ID

    Returns:
        AnonymousUsage: 更新后的记录
    """
    anon = get_or_create_anonymous_usage(db, visitor_id)
    today = datetime.utcnow().strftime("%Y-%m-%d")

    if anon.daily_date != today:
        anon.daily_date = today
        anon.daily_count = 0
        anon.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(anon)

    return anon


def increment_anonymous_usage(
    db: Session,
    visitor_id: str,
    amount: int = 1,
) -> AnonymousUsage:
    """
    增加匿名用户使用次数

    Args:
        db: 数据库会话
        visitor_id: 访客 ID
        amount: 增加次数

    Returns:
        AnonymousUsage: 更新后的记录
    """
    anon = reset_anonymous_daily_usage(db, visitor_id)
    anon.daily_count += amount
    anon.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(anon)
    return anon


def get_anonymous_remaining_quota(
    db: Session,
    visitor_id: str,
    daily_limit: int = 3,
) -> int:
    """
    获取匿名用户剩余免费次数

    Args:
        db: 数据库会话
        visitor_id: 访客 ID
        daily_limit: 每日免费限额

    Returns:
        int: 剩余次数
    """
    anon = reset_anonymous_daily_usage(db, visitor_id)
    return max(0, daily_limit - anon.daily_count)


# ==========================================
# 管理员相关 CRUD
# ==========================================

def get_admin_by_username(
    db: Session,
    username: str,
) -> Optional[AdminUser]:
    """
    通过用户名获取管理员

    Args:
        db: 数据库会话
        username: 用户名

    Returns:
        Optional[AdminUser]: 管理员对象
    """
    return db.query(AdminUser).filter(
        AdminUser.username == username
    ).first()


def verify_admin_password(
    db: Session,
    username: str,
    password: str,
) -> Optional[AdminUser]:
    """
    验证管理员密码

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        Optional[AdminUser]: 验证成功返回管理员对象
    """
    admin = get_admin_by_username(db, username)
    if admin:
        if bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
            return admin
    return None


def create_admin_user(
    db: Session,
    username: str,
    password: str,
) -> AdminUser:
    """
    创建管理员

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        AdminUser: 创建的管理员对象
    """
    password_hash = bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    admin = AdminUser(
        username=username,
        password_hash=password_hash,
        is_admin=True,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)

    logger.info(f"管理员创建成功: username={username}")
    return admin


def update_admin_password(
    db: Session,
    admin_id: int,
    new_password: str,
) -> Optional[AdminUser]:
    """
    更新管理员密码

    Args:
        db: 数据库会话
        admin_id: 管理员 ID
        new_password: 新密码

    Returns:
        Optional[AdminUser]: 更新后的管理员对象
    """
    admin = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if admin:
        admin.password_hash = bcrypt.hashpw(
            new_password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        db.commit()
        db.refresh(admin)
        logger.info(f"管理员密码已更新: username={admin.username}")
    return admin


# ==========================================
# 审计日志相关 CRUD
# ==========================================

def create_audit_log(
    db: Session,
    admin_id: int,
    admin_username: str,
    action: str,
    action_category: str,
    target_type: str = None,
    target_id: str = None,
    target_info: dict = None,
    action_detail: dict = None,
    ip_address: str = None,
    user_agent: str = None,
) -> AuditLog:
    """
    创建审计日志

    Args:
        db: 数据库会话
        admin_id: 管理员 ID
        admin_username: 管理员用户名
        action: 操作类型
        action_category: 操作分类
        target_type: 目标类型
        target_id: 目标 ID
        target_info: 目标信息（dict）
        action_detail: 操作详情（dict）
        ip_address: IP 地址
        user_agent: User-Agent

    Returns:
        AuditLog: 创建的审计日志
    """
    import json

    log = AuditLog(
        admin_id=admin_id,
        admin_username=admin_username,
        action=action,
        action_category=action_category,
        target_type=target_type,
        target_id=target_id,
        target_info=json.dumps(target_info) if target_info else None,
        action_detail=json.dumps(action_detail) if action_detail else None,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def get_audit_logs(
    db: Session,
    admin_id: int = None,
    action: str = None,
    action_category: str = None,
    limit: int = 50,
    offset: int = 0,
) -> List[AuditLog]:
    """
    查询审计日志

    Args:
        db: 数据库会话
        admin_id: 管理员 ID（可选）
        action: 操作类型（可选）
        action_category: 操作分类（可选）
        limit: 限制数量
        offset: 偏移量

    Returns:
        List[AuditLog]: 审计日志列表
    """
    query = db.query(AuditLog)

    if admin_id is not None:
        query = query.filter(AuditLog.admin_id == admin_id)

    if action:
        query = query.filter(AuditLog.action == action)

    if action_category:
        query = query.filter(AuditLog.action_category == action_category)

    return query.order_by(
        desc(AuditLog.created_at)
    ).offset(offset).limit(limit).all()


# ==========================================
# 预设广场相关 CRUD
# ==========================================

def get_marketplace_templates(
    db: Session,
    tool_type: str = None,
    is_published: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> List[MarketplaceTemplate]:
    """
    获取预设广场模板列表

    Args:
        db: 数据库会话
        tool_type: 工具类型（可选）
        is_published: 是否已发布
        limit: 限制数量
        offset: 偏移量

    Returns:
        List[MarketplaceTemplate]: 模板列表
    """
    query = db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.is_published == is_published
    )

    if tool_type:
        query = query.filter(MarketplaceTemplate.tool_type == tool_type)

    return query.order_by(
        desc(MarketplaceTemplate.import_count),
        desc(MarketplaceTemplate.created_at)
    ).offset(offset).limit(limit).all()


def get_marketplace_template_by_id(
    db: Session,
    template_id: int,
) -> Optional[MarketplaceTemplate]:
    """
    通过 ID 获取模板

    Args:
        db: 数据库会话
        template_id: 模板 ID

    Returns:
        Optional[MarketplaceTemplate]: 模板对象
    """
    return db.query(MarketplaceTemplate).filter(
        MarketplaceTemplate.id == template_id
    ).first()


def increment_template_import_count(
    db: Session,
    template_id: int,
) -> Optional[MarketplaceTemplate]:
    """
    增加模板导入次数

    Args:
        db: 数据库会话
        template_id: 模板 ID

    Returns:
        Optional[MarketplaceTemplate]: 更新后的模板
    """
    template = get_marketplace_template_by_id(db, template_id)
    if template:
        template.import_count += 1
        db.commit()
        db.refresh(template)
    return template


# ==========================================
# 用户配置相关 CRUD（code_id 版本）
# ==========================================

def get_user_prompt_by_code_id(
    db: Session,
    code_id: int,
    tool_type: str,
) -> Optional[UserPrompt]:
    """
    获取用户 Prompt 配置

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        tool_type: 工具类型

    Returns:
        Optional[UserPrompt]: Prompt 配置
    """
    return db.query(UserPrompt).filter(
        UserPrompt.code_id == code_id,
        UserPrompt.tool_type == tool_type,
        UserPrompt.is_active == True,
    ).first()


def create_or_update_user_prompt(
    db: Session,
    code_id: int,
    tool_type: str,
    prompt_content: str,
) -> UserPrompt:
    """
    创建或更新用户 Prompt 配置

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        tool_type: 工具类型
        prompt_content: Prompt 内容

    Returns:
        UserPrompt: Prompt 配置对象
    """
    existing = db.query(UserPrompt).filter(
        UserPrompt.code_id == code_id,
        UserPrompt.tool_type == tool_type,
    ).first()

    if existing:
        existing.prompt_content = prompt_content
        existing.is_active = True
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    prompt = UserPrompt(
        code_id=code_id,
        tool_type=tool_type,
        prompt_content=prompt_content,
        is_active=True,
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    return prompt


def get_user_sources_by_code_id(
    db: Session,
    code_id: int,
    tool_type: str = None,
) -> List[UserSource]:
    """
    获取用户数据源配置

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        tool_type: 工具类型（可选）

    Returns:
        List[UserSource]: 数据源列表
    """
    query = db.query(UserSource).filter(
        UserSource.code_id == code_id,
        UserSource.is_enabled == True,
    )

    if tool_type:
        query = query.filter(UserSource.tool_type == tool_type)

    return query.all()


def get_user_config_by_key(
    db: Session,
    code_id: int,
    config_key: str,
) -> Optional[UserConfig]:
    """
    获取用户配置

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        config_key: 配置键

    Returns:
        Optional[UserConfig]: 配置对象
    """
    return db.query(UserConfig).filter(
        UserConfig.code_id == code_id,
        UserConfig.config_key == config_key,
    ).first()


def set_user_config(
    db: Session,
    code_id: int,
    config_key: str,
    config_value: str,
) -> UserConfig:
    """
    设置用户配置

    Args:
        db: 数据库会话
        code_id: 激活码 ID
        config_key: 配置键
        config_value: 配置值

    Returns:
        UserConfig: 配置对象
    """
    existing = get_user_config_by_key(db, code_id, config_key)

    if existing:
        existing.config_value = config_value
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    config = UserConfig(
        code_id=code_id,
        config_key=config_key,
        config_value=config_value,
    )
    db.add(config)
    db.commit()
    db.refresh(config)

    return config


def get_dailyhot_configs_by_code_id(
    db: Session,
    code_id: int,
) -> List[DailyHotCategoryConfig]:
    """
    获取用户 DailyHot 分类配置

    Args:
        db: 数据库会话
        code_id: 激活码 ID

    Returns:
        List[DailyHotCategoryConfig]: 分类配置列表
    """
    return db.query(DailyHotCategoryConfig).filter(
        DailyHotCategoryConfig.code_id == code_id,
        DailyHotCategoryConfig.is_enabled == True,
    ).all()