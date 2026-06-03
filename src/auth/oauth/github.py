# -*- coding: utf-8 -*-
"""
GitHub OAuth 服务
实现 GitHub OAuth 2.0 认证流程
"""

import httpx
from typing import Optional, Dict, Any
from urllib.parse import urlencode
from src.auth.oauth.exceptions import OAuthTokenError, OAuthUserError


class GitHubOAuthService:
    """
    GitHub OAuth 服务
    
    文档: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
    """
    
    # GitHub OAuth 端点
    GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_URL = "https://api.github.com/user"
    GITHUB_EMAIL_URL = "https://api.github.com/user/emails"
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        """
        初始化 GitHub OAuth 服务
        
        Args:
            client_id: GitHub OAuth App 的 Client ID
            client_secret: GitHub OAuth App 的 Client Secret
            redirect_uri: 回调地址
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
    
    def get_authorize_url(self, state: str, scope: str = "user:email") -> str:
        """
        生成 GitHub 授权 URL
        
        Args:
            state: 防 CSRF 的状态码
            scope: 请求的权限范围，默认 user:email
            
        Returns:
            完整的授权 URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope,
            "state": state,
            "response_type": "code"
        }
        return f"{self.GITHUB_AUTHORIZE_URL}?{urlencode(params)}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        用授权码换取访问令牌
        
        Args:
            code: GitHub 返回的授权码
            
        Returns:
            包含 access_token 的字典
            
        Raises:
            OAuthTokenError: 获取 token 失败
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.GITHUB_TOKEN_URL,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": self.redirect_uri
                },
                headers={
                    "Accept": "application/json"
                }
            )
            
            data = response.json()
            
            if "error" in data:
                error_desc = data.get("error_description", data.get("error", "unknown error"))
                raise OAuthTokenError(f"获取令牌失败：{error_desc}", "github")
            
            if "access_token" not in data:
                raise OAuthTokenError("获取令牌失败：响应中无 access_token", "github")
            
            return data
    
    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """
        获取 GitHub 用户信息
        
        Args:
            access_token: 访问令牌
            
        Returns:
            用户信息字典，包含:
            - github_id: GitHub 用户 ID
            - login: GitHub 用户名
            - name: 显示名称
            - email: 主邮箱
            - avatar_url: 头像 URL
            
        Raises:
            OAuthUserError: 获取用户信息失败
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 获取用户基本信息
            user_response = await client.get(
                self.GITHUB_USER_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            if user_response.status_code != 200:
                raise OAuthUserError(
                    f"获取用户信息失败：HTTP {user_response.status_code}",
                    "github"
                )
            
            user_data = user_response.json()
            
            # 获取用户邮箱列表
            email_response = await client.get(
                self.GITHUB_EMAIL_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            
            # 找到主邮箱（已验证的主邮箱）
            primary_email = None
            if email_response.status_code == 200:
                emails = email_response.json()
                # 优先选择已验证的主邮箱
                for email_info in emails:
                    if email_info.get("primary") and email_info.get("verified"):
                        primary_email = email_info.get("email")
                        break
                # 如果没有主邮箱，选择第一个已验证的邮箱
                if not primary_email:
                    for email_info in emails:
                        if email_info.get("verified"):
                            primary_email = email_info.get("email")
                            break
            
            return {
                "github_id": str(user_data["id"]),
                "login": user_data.get("login"),
                "name": user_data.get("name") or user_data.get("login"),
                "email": primary_email,
                "avatar_url": user_data.get("avatar_url"),
                "bio": user_data.get("bio"),
                "location": user_data.get("location"),
                "company": user_data.get("company"),
                "blog": user_data.get("blog")
            }
    
    async def authenticate(self, code: str) -> Dict[str, Any]:
        """
        完整的 GitHub OAuth 认证流程
        
        Args:
            code: GitHub 返回的授权码
            
        Returns:
            用户信息字典
            
        Raises:
            OAuthTokenError: Token 获取失败
            OAuthUserError: 用户信息获取失败
        """
        # 1. 用 code 换取 access_token
        token_data = await self.exchange_code_for_token(code)
        access_token = token_data["access_token"]
        
        # 2. 获取用户信息
        user_info = await self.get_user_info(access_token)
        
        return user_info
    
    def is_configured(self) -> bool:
        """
        检查 GitHub OAuth 是否已配置
        
        Returns:
            是否已正确配置
        """
        return bool(self.client_id and self.client_secret)