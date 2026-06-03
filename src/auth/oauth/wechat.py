# -*- coding: utf-8 -*-
"""
微信 OAuth 服务（预留）
实现微信开放平台 OAuth 2.0 认证流程

文档: https://developers.weixin.qq.com/doc/oplatform/Website_App/WeChat_Login/WeChat_Login.html
"""

import httpx
from typing import Dict, Any, Optional
from urllib.parse import urlencode
from src.auth.oauth.exceptions import OAuthTokenError, OAuthUserError


class WeChatOAuthService:
    """
    微信 OAuth 服务（预留实现）
    
    注意：
    - 需要在微信开放平台注册应用获取 AppID 和 AppSecret
    - 网站应用微信登录功能需要通过微信认证
    - 目前为预留接口，功能暂未开放
    """
    
    # 微信开放平台 OAuth 端点
    WECHAT_AUTHORIZE_URL = "https://open.weixin.qq.com/connect/qrconnect"
    WECHAT_TOKEN_URL = "https://api.weixin.qq.com/sns/oauth2/access_token"
    WECHAT_USER_URL = "https://api.weixin.qq.com/sns/userinfo"
    WECHAT_REFRESH_URL = "https://api.weixin.qq.com/sns/oauth2/refresh_token"
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        redirect_uri: str
    ):
        """
        初始化微信 OAuth 服务
        
        Args:
            app_id: 微信开放平台 AppID
            app_secret: 微信开放平台 AppSecret
            redirect_uri: 回调地址
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
    
    def get_authorize_url(self, state: str, scope: str = "snsapi_login") -> str:
        """
        生成微信授权 URL（二维码扫码）
        
        Args:
            state: 防 CSRF 的状态码
            scope: 请求的权限范围
                   - snsapi_login: 网页授权，需要扫码
                   - snsapi_base: 静默授权（仅获取 openid）
                   - snsapi_userinfo: 获取用户信息
            
        Returns:
            完整的授权 URL
        """
        params = {
            "appid": self.app_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": scope,
            "state": state
        }
        return f"{self.WECHAT_AUTHORIZE_URL}?{urlencode(params)}#wechat_redirect"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        用授权码换取访问令牌
        
        Args:
            code: 微信返回的授权码
            
        Returns:
            包含 access_token 的字典
            
        Raises:
            OAuthTokenError: 获取 token 失败
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.WECHAT_TOKEN_URL,
                params={
                    "appid": self.app_id,
                    "secret": self.app_secret,
                    "code": code,
                    "grant_type": "authorization_code"
                }
            )
            
            data = response.json()
            
            if "errcode" in data and data["errcode"] != 0:
                error_desc = data.get("errmsg", "unknown error")
                raise OAuthTokenError(f"获取令牌失败：{error_desc}", "wechat")
            
            return data
    
    async def get_user_info(self, access_token: str, openid: str) -> Dict[str, Any]:
        """
        获取微信用户信息
        
        Args:
            access_token: 访问令牌
            openid: 用户唯一标识
            
        Returns:
            用户信息字典
            
        Raises:
            OAuthUserError: 获取用户信息失败
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.WECHAT_USER_URL,
                params={
                    "access_token": access_token,
                    "openid": openid
                }
            )
            
            data = response.json()
            
            if "errcode" in data and data["errcode"] != 0:
                error_desc = data.get("errmsg", "unknown error")
                raise OAuthUserError(f"获取用户信息失败：{error_desc}", "wechat")
            
            return {
                "wechat_openid": data.get("openid"),
                "wechat_unionid": data.get("unionid"),
                "nickname": data.get("nickname"),
                "sex": data.get("sex"),  # 1: 男, 2: 女
                "province": data.get("province"),
                "city": data.get("city"),
                "country": data.get("country"),
                "headimgurl": data.get("headimgurl"),
                "privilege": data.get("privilege", [])
            }
    
    async def authenticate(self, code: str) -> Dict[str, Any]:
        """
        完整的微信 OAuth 认证流程
        
        Args:
            code: 微信返回的授权码
            
        Returns:
            用户信息字典
            
        Raises:
            OAuthTokenError: Token 获取失败
            OAuthUserError: 用户信息获取失败
        """
        # 1. 用 code 换取 access_token 和 openid
        token_data = await self.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        openid = token_data["openid"]
        
        # 2. 获取用户信息
        user_info = await self.get_user_info(access_token, openid)
        
        # 合并 token 信息
        user_info["access_token"] = access_token
        user_info["refresh_token"] = token_data.get("refresh_token")
        user_info["expires_in"] = token_data.get("expires_in")
        
        return user_info
    
    def is_configured(self) -> bool:
        """
        检查微信 OAuth 是否已配置
        
        Returns:
            是否已正确配置
        """
        return bool(self.app_id and self.app_secret)
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新 access_token
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            新的 token 信息
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                self.WECHAT_REFRESH_URL,
                params={
                    "appid": self.app_id,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                }
            )
            
            data = response.json()
            
            if "errcode" in data and data["errcode"] != 0:
                error_desc = data.get("errmsg", "unknown error")
                raise OAuthTokenError(f"刷新令牌失败：{error_desc}", "wechat")
            
            return data