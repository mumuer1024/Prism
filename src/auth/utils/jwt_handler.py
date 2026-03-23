"""
JWT Token 处理工具

提供 JWT Token 的生成、验证、刷新功能
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import hashlib
import secrets

from src.config import settings


class JWTHandler:
    """JWT Token 处理类"""
    
    def __init__(
        self,
        secret_key: str = None,
        algorithm: str = None,
        access_token_expire_minutes: int = None,
        refresh_token_expire_days: int = None
    ):
        self.secret_key = secret_key or settings.JWT_SECRET_KEY
        self.algorithm = algorithm or settings.JWT_ALGORITHM
        self.access_token_expire_minutes = access_token_expire_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire_days = refresh_token_expire_days or settings.REFRESH_TOKEN_EXPIRE_DAYS
    
    def create_access_token(
        self,
        user_id: int,
        email: str,
        usage_count: int = 0,
        additional_claims: Dict[str, Any] = None
    ) -> str:
        """
        创建 Access Token
        
        Args:
            user_id: 用户 ID
            email: 用户邮箱
            usage_count: 使用次数
            additional_claims: 额外的 claims
            
        Returns:
            JWT Access Token 字符串
        """
        now = datetime.utcnow()
        expire = now + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            'sub': str(user_id),          # Subject (用户 ID)
            'email': email,                # 用户邮箱
            'usage_count': usage_count,    # 使用次数
            'type': 'access',              # Token 类型
            'iat': now,                    # Issued At
            'exp': expire,                 # Expiration
        }
        
        if additional_claims:
            payload.update(additional_claims)
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: int,
        device_info: str = None,
        ip_address: str = None
    ) -> tuple:
        """
        创建 Refresh Token
        
        Args:
            user_id: 用户 ID
            device_info: 设备信息
            ip_address: IP 地址
            
        Returns:
            (refresh_token, token_hash, expires_at) 元组
        """
        # 生成随机 token
        random_bytes = secrets.token_bytes(32)
        refresh_token = secrets.token_urlsafe(32)
        
        # 计算过期时间
        now = datetime.utcnow()
        expires_at = now + timedelta(days=self.refresh_token_expire_days)
        
        # 计算 token 哈希（用于存储）
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        
        # 创建 JWT 格式的 refresh token（可选，这里使用简单格式）
        payload = {
            'sub': str(user_id),
            'token_hash': token_hash[:16],  # 只存部分哈希用于验证
            'type': 'refresh',
            'iat': now,
            'exp': expires_at,
            'device': device_info,
            'ip': ip_address
        }
        
        jwt_token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        
        return jwt_token, token_hash, expires_at
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证 Access Token
        
        Args:
            token: JWT Token 字符串
            
        Returns:
            解码后的 payload，验证失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查 token 类型
            if payload.get('type') != 'access':
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            # Token 已过期
            return None
        except jwt.InvalidTokenError:
            # Token 无效
            return None
    
    def verify_refresh_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证 Refresh Token
        
        Args:
            token: JWT Refresh Token 字符串
            
        Returns:
            解码后的 payload，验证失败返回 None
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # 检查 token 类型
            if payload.get('type') != 'refresh':
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def decode_token_without_verification(self, token: str) -> Optional[Dict[str, Any]]:
        """
        解码 Token（不验证签名，用于调试）
        
        Args:
            token: JWT Token 字符串
            
        Returns:
            解码后的 payload
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError:
            return None


# 全局实例
jwt_handler = JWTHandler()


# 便捷函数
def create_access_token(
    user_id: int,
    email: str,
    usage_count: int = 0,
    additional_claims: Dict[str, Any] = None
) -> str:
    """创建 Access Token 的便捷函数"""
    return jwt_handler.create_access_token(user_id, email, usage_count, additional_claims)


def create_refresh_token(
    user_id: int,
    device_info: str = None,
    ip_address: str = None
) -> tuple:
    """创建 Refresh Token 的便捷函数"""
    return jwt_handler.create_refresh_token(user_id, device_info, ip_address)


def verify_token(token: str, token_type: str = 'access') -> Optional[Dict[str, Any]]:
    """
    验证 Token 的便捷函数
    
    Args:
        token: JWT Token 字符串
        token_type: 'access' 或 'refresh'
        
    Returns:
        解码后的 payload，验证失败返回 None
    """
    if token_type == 'access':
        return jwt_handler.verify_access_token(token)
    elif token_type == 'refresh':
        return jwt_handler.verify_refresh_token(token)
    return None