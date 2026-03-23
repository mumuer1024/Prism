# -*- coding: utf-8 -*-
"""
OAuth 异常定义
"""


class OAuthError(Exception):
    """OAuth 认证异常基类"""
    
    def __init__(self, message: str, provider: str = None):
        self.message = message
        self.provider = provider
        super().__init__(self.message)
    
    def __str__(self):
        if self.provider:
            return f"[{self.provider}] {self.message}"
        return self.message


class OAuthStateError(OAuthError):
    """State 验证失败异常"""
    
    def __init__(self, message: str = "授权状态验证失败，请重试"):
        super().__init__(message, "STATE")


class OAuthTokenError(OAuthError):
    """Token 获取失败异常"""
    
    def __init__(self, message: str, provider: str = None):
        super().__init__(message, provider)


class OAuthUserError(OAuthError):
    """用户信息获取失败异常"""
    
    def __init__(self, message: str, provider: str = None):
        super().__init__(message, provider)