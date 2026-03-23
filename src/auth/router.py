# -*- coding: utf-8 -*-
"""
认证 API 路由

提供认证相关的 REST API 端点
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from src.database.connection import get_db
from src.database.models import User
from src.database import crud
from src.auth.schemas import (
    SendCodeRequest,
    SendCodeResponse,
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ResetPasswordRequest,
    LogoutResponse,
    ErrorResponse,
    OAuthAuthorizeResponse,
    OAuthCallbackResponse,
    OAuthProvidersResponse,
    OAuthLinkResponse,
)
from src.auth.service import AuthService
from src.auth.dependencies import get_current_user
from src.auth.utils.jwt_handler import create_access_token, create_refresh_token
from src.auth.oauth.github import GitHubOAuthService
from src.auth.oauth.wechat import WeChatOAuthService
from src.auth.oauth.state import state_manager
from src.auth.oauth.exceptions import OAuthError, OAuthStateError
from src.config import settings

router = APIRouter()


# ==========================================
# 验证码相关 API
# ==========================================

@router.post(
    "/send-code",
    response_model=SendCodeResponse,
    responses={
        400: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
    },
    summary="发送验证码",
    description="发送邮箱验证码，用于注册或重置密码",
)
async def send_verification_code(
    request: SendCodeRequest,
    db: Session = Depends(get_db),
):
    """发送验证码"""
    # 检查功能开关
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    auth_service = AuthService(db)
    success, message = await auth_service.send_verification_code(
        email=request.email,
        purpose=request.purpose,
    )
    
    if not success:
        # 根据错误类型返回不同状态码
        if "等待" in message:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=message
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
    
    return SendCodeResponse(
        success=True,
        message=message,
    )


# ==========================================
# 注册相关 API
# ==========================================

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
    summary="用户注册",
    description="使用邮箱和验证码注册新用户",
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db),
):
    """用户注册"""
    # 检查功能开关
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    auth_service = AuthService(db)
    user, refresh_token, message = await auth_service.register(
        email=request.email,
        password=request.password,
        code=request.code,
        invite_code=request.invite_code,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    # 生成访问令牌
    access_token = create_access_token({"sub": str(user.id)})
    
    return RegisterResponse(
        success=True,
        message=message,
        data={
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


# ==========================================
# 登录相关 API
# ==========================================

@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        401: {"model": ErrorResponse},
    },
    summary="用户登录",
    description="使用邮箱和密码登录",
)
async def login(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db),
):
    """用户登录"""
    # 检查功能开关
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    # 获取客户端信息
    device_info = http_request.headers.get("user-agent", "")
    ip_address = http_request.client.host if http_request.client else None
    
    auth_service = AuthService(db)
    user, refresh_token, message = await auth_service.login(
        email=request.email,
        password=request.password,
        device_info=device_info,
        ip_address=ip_address,
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成访问令牌
    access_token = create_access_token({"sub": str(user.id)})
    
    return LoginResponse(
        success=True,
        message=message,
        data={
            "user": user.to_dict(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="用户登出",
    description="退出登录，撤销令牌",
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户登出"""
    auth_service = AuthService(db)
    await auth_service.logout(current_user.id)
    
    return LogoutResponse(
        success=True,
        message="已成功登出",
    )


# ==========================================
# Token 相关 API
# ==========================================

@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    responses={
        401: {"model": ErrorResponse},
    },
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """刷新令牌"""
    # 检查功能开关
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    auth_service = AuthService(db)
    new_access_token, new_refresh_token, message = await auth_service.refresh_tokens(
        refresh_token=request.refresh_token,
    )
    
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return RefreshTokenResponse(
        success=True,
        message=message,
        data={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


# ==========================================
# 密码相关 API
# ==========================================

@router.post(
    "/reset-password",
    response_model=SendCodeResponse,
    responses={
        400: {"model": ErrorResponse},
    },
    summary="重置密码",
    description="使用验证码重置密码",
)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """重置密码"""
    # 检查功能开关
    if not settings.FEATURE_USER_SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户系统暂未开放"
        )
    
    auth_service = AuthService(db)
    success, message = await auth_service.reset_password(
        email=request.email,
        code=request.code,
        new_password=request.new_password,
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    return SendCodeResponse(
        success=True,
        message=message,
    )


# ==========================================
# 用户信息 API
# ==========================================

@router.get(
    "/me",
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前用户信息"""
    return {
        "success": True,
        "data": {
            "user": current_user.to_dict(),
        }
    }


@router.get(
    "/status",
    summary="检查登录状态",
    description="检查用户是否已登录",
)
async def check_status(
    current_user: Optional[User] = Depends(get_current_user),
):
    """检查登录状态"""
    if current_user:
        return {
            "success": True,
            "data": {
                "logged_in": True,
                "user": current_user.to_dict(),
            }
        }
    else:
        return {
            "success": True,
            "data": {
                "logged_in": False,
                "user": None,
            }
        }


# ==========================================
# OAuth 相关 API
# ==========================================

def get_github_oauth_service() -> GitHubOAuthService:
    """获取 GitHub OAuth 服务实例"""
    return GitHubOAuthService(
        client_id=settings.GITHUB_CLIENT_ID,
        client_secret=settings.GITHUB_CLIENT_SECRET,
        redirect_uri=settings.GITHUB_REDIRECT_URI
    )


def get_wechat_oauth_service() -> WeChatOAuthService:
    """获取微信 OAuth 服务实例"""
    return WeChatOAuthService(
        app_id=settings.WECHAT_APP_ID,
        app_secret=settings.WECHAT_APP_SECRET,
        redirect_uri=settings.WECHAT_REDIRECT_URI
    )


@router.get(
    "/oauth/providers",
    response_model=OAuthProvidersResponse,
    summary="获取可用 OAuth 提供商",
    description="返回当前系统支持的 OAuth 登录方式",
)
async def get_oauth_providers():
    """获取可用的 OAuth 提供商"""
    providers = []
    
    if settings.FEATURE_OAUTH_GITHUB and settings.GITHUB_CLIENT_ID:
        providers.append({
            "name": "github",
            "display_name": "GitHub",
            "enabled": True,
            "icon": "github"
        })
    
    if settings.FEATURE_OAUTH_WECHAT and settings.WECHAT_APP_ID:
        providers.append({
            "name": "wechat",
            "display_name": "微信",
            "enabled": True,
            "icon": "wechat"
        })
    
    return OAuthProvidersResponse(
        success=True,
        data={
            "providers": providers
        }
    )


# ========== GitHub OAuth ==========

@router.get(
    "/oauth/github/authorize",
    response_model=OAuthAuthorizeResponse,
    responses={
        503: {"model": ErrorResponse},
    },
    summary="获取 GitHub 授权 URL",
    description="生成 GitHub OAuth 授权链接，前端跳转到该 URL 进行授权",
)
async def github_authorize(
    redirect_uri: Optional[str] = Query(None, description="授权成功后的前端跳转地址"),
):
    """获取 GitHub 授权 URL"""
    if not settings.FEATURE_OAUTH_GITHUB:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub 登录暂未开放"
        )
    
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth 未配置"
        )
    
    # 生成 state
    state = state_manager.generate_state(redirect_uri=redirect_uri)
    
    # 生成授权 URL
    service = get_github_oauth_service()
    authorize_url = service.get_authorize_url(state)
    
    return OAuthAuthorizeResponse(
        success=True,
        data={
            "authorize_url": authorize_url,
            "state": state
        }
    )


@router.get(
    "/oauth/github/callback",
    response_model=OAuthCallbackResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="GitHub OAuth 回调",
    description="GitHub 授权后的回调处理，完成登录或注册",
)
async def github_callback(
    code: str = Query(..., description="GitHub 返回的授权码"),
    state: str = Query(..., description="防 CSRF 的状态码"),
    db: Session = Depends(get_db),
):
    """GitHub OAuth 回调"""
    if not settings.FEATURE_OAUTH_GITHUB:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub 登录暂未开放"
        )
    
    # 验证 state
    state_data = state_manager.consume_state(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权状态验证失败，请重试"
        )
    
    try:
        # 获取 GitHub 用户信息
        service = get_github_oauth_service()
        user_info = await service.authenticate(code)
        
        github_id = user_info["github_id"]
        github_name = user_info["login"]
        github_email = user_info.get("email")
        github_avatar = user_info.get("avatar_url")
        
        # 查找是否已有 GitHub 账号
        user = crud.get_user_by_oauth(db, "github", github_id)
        is_new_user = False
        
        if not user:
            # 尝试通过邮箱查找已有用户
            if github_email:
                user = crud.get_user_by_email(db, github_email)
            
            if not user:
                # 创建新用户
                invite_code = crud.generate_unique_invite_code(db)
                user = crud.create_user(
                    db=db,
                    email=github_email,
                    password_hash=None,  # OAuth 用户无密码
                    invite_code=invite_code,
                    oauth_provider="github",
                    oauth_id=github_id,
                    oauth_name=github_name,
                    oauth_avatar=github_avatar,
                )
                is_new_user = True
            else:
                # 绑定 OAuth 到已有用户
                user = crud.link_oauth_to_user(
                    db=db,
                    user_id=user.id,
                    oauth_provider="github",
                    oauth_id=github_id,
                    oauth_name=github_name,
                    oauth_avatar=github_avatar,
                )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="用户创建失败"
            )
        
        # 更新登录时间
        crud.update_last_login(db, user.id)
        
        # 生成 Token
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        # 存储刷新令牌
        crud.create_refresh_token(
            db=db,
            user_id=user.id,
            token=refresh_token,
        )
        
        return OAuthCallbackResponse(
            success=True,
            data={
                "user": user.to_dict(),
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                "is_new_user": is_new_user
            }
        )
        
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/oauth/github/link",
    response_model=OAuthLinkResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="绑定 GitHub 账号",
    description="已登录用户绑定 GitHub 账号（用于设置密码等场景）",
)
async def github_link(
    code: str = Query(..., description="GitHub 返回的授权码"),
    state: str = Query(..., description="防 CSRF 的状态码"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """绑定 GitHub 账号到当前用户"""
    if not settings.FEATURE_OAUTH_GITHUB:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub 登录暂未开放"
        )
    
    # 验证 state
    state_data = state_manager.consume_state(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="授权状态验证失败，请重试"
        )
    
    try:
        # 获取 GitHub 用户信息
        service = get_github_oauth_service()
        user_info = await service.authenticate(code)
        
        github_id = user_info["github_id"]
        github_name = user_info["login"]
        github_avatar = user_info.get("avatar_url")
        
        # 绑定到当前用户
        user = crud.link_oauth_to_user(
            db=db,
            user_id=current_user.id,
            oauth_provider="github",
            oauth_id=github_id,
            oauth_name=github_name,
            oauth_avatar=github_avatar,
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该 GitHub 账号已被其他用户绑定"
            )
        
        return OAuthLinkResponse(
            success=True,
            message="GitHub 账号绑定成功"
        )
        
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ========== 微信 OAuth（预留）==========

@router.get(
    "/oauth/wechat/authorize",
    response_model=OAuthAuthorizeResponse,
    responses={
        503: {"model": ErrorResponse},
    },
    summary="获取微信授权 URL",
    description="生成微信 OAuth 授权链接（暂未开放）",
)
async def wechat_authorize(
    redirect_uri: Optional[str] = Query(None, description="授权成功后的前端跳转地址"),
):
    """获取微信授权 URL"""
    if not settings.FEATURE_OAUTH_WECHAT:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信登录暂未开放"
        )
    
    if not settings.WECHAT_APP_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信 OAuth 未配置"
        )
    
    # 生成 state
    state = state_manager.generate_state(redirect_uri=redirect_uri)
    
    # 生成授权 URL
    service = get_wechat_oauth_service()
    authorize_url = service.get_authorize_url(state)
    
    return OAuthAuthorizeResponse(
        success=True,
        data={
            "authorize_url": authorize_url,
            "state": state
        }
    )


@router.get(
    "/oauth/wechat/callback",
    response_model=OAuthCallbackResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    summary="微信 OAuth 回调",
    description="微信授权后的回调处理（暂未开放）",
)
async def wechat_callback(
    code: str = Query(..., description="微信返回的授权码"),
    state: str = Query(..., description="防 CSRF 的状态码"),
    db: Session = Depends(get_db),
):
    """微信 OAuth 回调"""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="微信登录暂未开放，敬请期待"
    )