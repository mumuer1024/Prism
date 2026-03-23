# -*- coding: utf-8 -*-
"""
认证服务

提供认证相关的业务逻辑
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from src.database.crud import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_by_invite_code,
    get_user_by_oauth,
    update_last_login,
    update_password,
    update_user_usage_count,
    create_verification_code,
    get_valid_verification_code,
    mark_code_as_used,
    can_send_code,
    create_refresh_token,
    get_valid_refresh_token,
    revoke_refresh_token,
    revoke_all_user_tokens,
    generate_unique_invite_code,
    create_invite_record,
)
from src.database.models import User
from src.auth.utils.jwt_handler import create_access_token, create_refresh_token as create_jwt_refresh_token
from src.auth.utils.password_handler import hash_password, verify_password, validate_password_strength
from src.auth.utils.email_service import EmailService, send_verification_code, generate_code
from src.config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        """
        初始化认证服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
        self.email_service = EmailService()
    
    # ==========================================
    # 验证码相关
    # ==========================================
    
    async def send_verification_code(
        self,
        email: str,
        purpose: str,
    ) -> Tuple[bool, str]:
        """
        发送验证码
        
        Args:
            email: 邮箱
            purpose: 用途 (register, reset_password)
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        email = email.lower()
        
        # 检查发送频率
        can_send, remaining = can_send_code(
            self.db,
            email,
            purpose,
            settings.VERIFY_CODE_RESEND_SECONDS,
        )
        
        if not can_send:
            return False, f"请等待 {remaining} 秒后再试"
        
        # 检查邮箱是否已注册（注册场景）
        if purpose == "register":
            existing_user = get_user_by_email(self.db, email)
            if existing_user:
                return False, "该邮箱已被注册"
        
        # 检查邮箱是否存在（重置密码场景）
        if purpose == "reset_password":
            existing_user = get_user_by_email(self.db, email)
            if not existing_user:
                return False, "该邮箱未注册"
        
        # 生成验证码
        code = generate_code(settings.VERIFY_CODE_LENGTH)
        
        # 存储验证码
        create_verification_code(
            self.db,
            email,
            code,
            purpose,
            settings.VERIFY_CODE_EXPIRE_MINUTES,
        )
        
        # 发送邮件
        success, message = await send_verification_code(
            to_email=email,
            code=code,
            purpose=purpose,
        )
        
        if success:
            logger.info(f"验证码发送成功: email={email}, purpose={purpose}")
            return True, "验证码已发送，请查收邮件"
        else:
            logger.error(f"验证码发送失败: email={email}, error={message}")
            return False, f"验证码发送失败: {message}"
    
    # ==========================================
    # 注册相关
    # ==========================================
    
    async def register(
        self,
        email: str,
        password: str,
        code: Optional[str] = None,
        invite_code: Optional[str] = None,
    ) -> Tuple[Optional[User], Optional[str], str]:
        """
        用户注册
        
        Args:
            email: 邮箱
            password: 密码
            code: 验证码（可选，如果提供则验证邮箱）
            invite_code: 邀请码（可选）
        
        Returns:
            Tuple[Optional[User], Optional[str], str]: (用户对象, 刷新令牌, 消息)
        """
        email = email.lower()
        
        # 验证密码强度
        is_valid, msg = validate_password_strength(password)
        if not is_valid:
            return None, None, msg
        
        # 验证验证码（如果提供了）
        email_verified = False
        if code:
            vc = get_valid_verification_code(self.db, email, code, "register")
            if not vc:
                return None, None, "验证码错误或已过期"
            email_verified = True
        
        # 检查邮箱是否已注册
        existing_user = get_user_by_email(self.db, email)
        if existing_user:
            return None, None, "该邮箱已被注册"
        
        # 验证邀请码（如果提供）
        inviter_id = None
        if invite_code:
            inviter = get_user_by_invite_code(self.db, invite_code)
            if not inviter:
                return None, None, "邀请码无效"
            inviter_id = inviter.id
        
        # 生成用户专属邀请码
        user_invite_code = generate_unique_invite_code(self.db)
        
        # 创建用户
        password_hash = hash_password(password)
        user = create_user(
            self.db,
            email=email,
            password_hash=password_hash,
            invite_code=user_invite_code,
            invited_by=inviter_id,
        )
        
        # 标记验证码已使用（如果提供了验证码）
        if code and email_verified:
            vc = get_valid_verification_code(self.db, email, code, "register")
            if vc:
                mark_code_as_used(self.db, vc.id)
        
        # 创建邀请记录
        if inviter_id:
            create_invite_record(self.db, inviter_id, user.id)
        
        # 生成 Token
        access_token = create_access_token(user_id=user.id, email=user.email, usage_count=user.usage_count)
        refresh_token, token_hash, expires_at = create_jwt_refresh_token(user_id=user.id)
        
        # 存储刷新令牌
        create_refresh_token(
            self.db,
            user.id,
            refresh_token,
            settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        
        logger.info(f"用户注册成功: id={user.id}, email={email}")
        
        return user, refresh_token, "注册成功"
    
    async def oauth_register(
        self,
        provider: str,
        oauth_id: str,
        oauth_name: str,
        oauth_avatar: str = None,
        email: str = None,
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        OAuth 注册/登录
        
        Args:
            provider: OAuth 提供商
            oauth_id: OAuth 用户 ID
            oauth_name: OAuth 用户名
            oauth_avatar: OAuth 头像
            email: 邮箱（可选）
        
        Returns:
            Tuple[Optional[User], Optional[str]]: (用户对象, 刷新令牌)
        """
        # 检查是否已存在 OAuth 用户
        user = get_user_by_oauth(self.db, provider, oauth_id)
        
        if user:
            # 已存在，更新信息并登录
            if oauth_name:
                user.oauth_name = oauth_name
            if oauth_avatar:
                user.oauth_avatar = oauth_avatar
            self.db.commit()
        else:
            # 不存在，创建新用户
            user_invite_code = generate_unique_invite_code(self.db)
            user = create_user(
                self.db,
                email=email or f"{provider}_{oauth_id}@placeholder.com",
                password_hash=None,  # OAuth 用户没有密码
                invite_code=user_invite_code,
                oauth_provider=provider,
                oauth_id=oauth_id,
                oauth_name=oauth_name,
                oauth_avatar=oauth_avatar,
            )
        
        # 更新登录时间
        update_last_login(self.db, user.id)
        
        # 生成 Token
        access_token = create_access_token(user_id=user.id, email=user.email, usage_count=user.usage_count)
        refresh_token, token_hash, expires_at = create_jwt_refresh_token(user_id=user.id)
        
        # 存储刷新令牌
        create_refresh_token(
            self.db,
            user.id,
            refresh_token,
            settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        
        logger.info(f"OAuth 登录成功: provider={provider}, oauth_id={oauth_id}")
        
        return user, refresh_token
    
    # ==========================================
    # 登录相关
    # ==========================================
    
    async def login(
        self,
        email: str,
        password: str,
        device_info: str = None,
        ip_address: str = None,
    ) -> Tuple[Optional[User], Optional[str], str]:
        """
        用户登录
        
        Args:
            email: 邮箱
            password: 密码
            device_info: 设备信息
            ip_address: IP 地址
        
        Returns:
            Tuple[Optional[User], Optional[str], str]: (用户对象, 刷新令牌, 消息)
        """
        email = email.lower()
        
        # 查询用户
        user = get_user_by_email(self.db, email)
        
        if not user:
            return None, None, "邮箱或密码错误"
        
        # 检查用户状态
        if not user.is_active:
            return None, None, "账户已被禁用"
        
        # OAuth 用户没有密码
        if not user.password_hash:
            return None, None, "该账户使用第三方登录，请使用对应方式登录"
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return None, None, "邮箱或密码错误"
        
        # 更新登录时间
        update_last_login(self.db, user.id)
        
        # 生成 Token
        access_token = create_access_token(user_id=user.id, email=user.email, usage_count=user.usage_count)
        refresh_token, token_hash, expires_at = create_jwt_refresh_token(user_id=user.id)
        
        # 存储刷新令牌
        create_refresh_token(
            self.db,
            user.id,
            refresh_token,
            settings.REFRESH_TOKEN_EXPIRE_DAYS,
            device_info=device_info,
            ip_address=ip_address,
        )
        
        logger.info(f"用户登录成功: id={user.id}, email={email}")
        
        return user, refresh_token, "登录成功"
    
    async def logout(
        self,
        user_id: int,
        refresh_token: str = None,
    ) -> bool:
        """
        用户登出
        
        Args:
            user_id: 用户 ID
            refresh_token: 刷新令牌（可选，不提供则撤销所有令牌）
        
        Returns:
            bool: 是否成功
        """
        if refresh_token:
            # 撤销指定令牌
            rt = get_valid_refresh_token(self.db, refresh_token)
            if rt:
                revoke_refresh_token(self.db, rt.id)
        else:
            # 撤销所有令牌
            revoke_all_user_tokens(self.db, user_id)
        
        logger.info(f"用户登出: user_id={user_id}")
        return True
    
    # ==========================================
    # Token 相关
    # ==========================================
    
    async def refresh_tokens(
        self,
        refresh_token: str,
    ) -> Tuple[Optional[str], Optional[str], str]:
        """
        刷新 Token
        
        Args:
            refresh_token: 刷新令牌
        
        Returns:
            Tuple[Optional[str], Optional[str], str]: (新 access_token, 新 refresh_token, 消息)
        """
        # 验证刷新令牌
        rt = get_valid_refresh_token(self.db, refresh_token)
        
        if not rt:
            return None, None, "刷新令牌无效或已过期"
        
        # 获取用户
        user = get_user_by_id(self.db, rt.user_id)
        
        if not user or not user.is_active:
            return None, None, "用户不存在或已被禁用"
        
        # 撤销旧的刷新令牌
        revoke_refresh_token(self.db, rt.id)
        
        # 生成新的 Token
        new_access_token = create_access_token(user_id=user.id, email=user.email, usage_count=user.usage_count)
        new_refresh_token, token_hash, expires_at = create_jwt_refresh_token(user_id=user.id)
        
        # 存储新的刷新令牌
        create_refresh_token(
            self.db,
            user.id,
            new_refresh_token,
            settings.REFRESH_TOKEN_EXPIRE_DAYS,
        )
        
        logger.info(f"Token 刷新成功: user_id={user.id}")
        
        return new_access_token, new_refresh_token, "Token 刷新成功"
    
    # ==========================================
    # 密码相关
    # ==========================================
    
    async def reset_password(
        self,
        email: str,
        code: str,
        new_password: str,
    ) -> Tuple[bool, str]:
        """
        重置密码
        
        Args:
            email: 邮箱
            code: 验证码
            new_password: 新密码
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        email = email.lower()
        
        # 验证密码强度
        is_valid, msg = validate_password_strength(new_password)
        if not is_valid:
            return False, msg
        
        # 验证验证码
        vc = get_valid_verification_code(self.db, email, code, "reset_password")
        if not vc:
            return False, "验证码错误或已过期"
        
        # 查询用户
        user = get_user_by_email(self.db, email)
        if not user:
            return False, "用户不存在"
        
        # 更新密码
        new_password_hash = hash_password(new_password)
        update_password(self.db, user.id, new_password_hash)
        
        # 标记验证码已使用
        mark_code_as_used(self.db, vc.id)
        
        # 撤销所有刷新令牌（强制重新登录）
        revoke_all_user_tokens(self.db, user.id)
        
        logger.info(f"密码重置成功: user_id={user.id}")
        
        return True, "密码重置成功，请重新登录"
    
    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
    ) -> Tuple[bool, str]:
        """
        修改密码
        
        Args:
            user_id: 用户 ID
            old_password: 旧密码
            new_password: 新密码
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        # 查询用户
        user = get_user_by_id(self.db, user_id)
        if not user:
            return False, "用户不存在"
        
        # 验证旧密码
        if not user.password_hash or not verify_password(old_password, user.password_hash):
            return False, "原密码错误"
        
        # 验证新密码强度
        is_valid, msg = validate_password_strength(new_password)
        if not is_valid:
            return False, msg
        
        # 更新密码
        new_password_hash = hash_password(new_password)
        update_password(self.db, user.id, new_password_hash)
        
        # 撤销所有刷新令牌（强制重新登录）
        revoke_all_user_tokens(self.db, user_id)
        
        logger.info(f"密码修改成功: user_id={user_id}")
        
        return True, "密码修改成功，请重新登录"