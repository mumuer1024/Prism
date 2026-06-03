# -*- coding: utf-8 -*-
"""
OAuth State 管理
用于防止 CSRF 攻击
"""

import time
import uuid
import secrets
from typing import Optional, Dict, Any
from urllib.parse import urlencode


class OAuthStateManager:
    """
    OAuth State 管理器
    
    使用内存存储 state，适用于单机部署
    生产环境建议迁移到 Redis
    """
    
    # State 存储（内存）
    _states: Dict[str, Dict[str, Any]] = {}
    
    # State 过期时间（秒）
    STATE_EXPIRE_SECONDS = 600  # 10 分钟
    
    @classmethod
    def generate_state(cls, redirect_uri: str = None, extra_data: Dict[str, Any] = None) -> str:
        """
        生成唯一的 state 字符串
        
        Args:
            redirect_uri: 回调后的重定向 URI
            extra_data: 额外的数据
            
        Returns:
            state 字符串
        """
        # 生成随机 state
        state = secrets.token_urlsafe(32)
        
        # 存储状态信息
        cls._states[state] = {
            "redirect_uri": redirect_uri,
            "extra_data": extra_data or {},
            "created_at": time.time(),
            "expires_at": time.time() + cls.STATE_EXPIRE_SECONDS
        }
        
        # 清理过期状态
        cls._cleanup_expired()
        
        return state
    
    @classmethod
    def validate_state(cls, state: str) -> Optional[Dict[str, Any]]:
        """
        验证 state 是否有效
        
        Args:
            state: 要验证的 state 字符串
            
        Returns:
            如果有效返回存储的数据，无效返回 None
        """
        if state not in cls._states:
            return None
        
        state_data = cls._states[state]
        
        # 检查是否过期
        if time.time() > state_data["expires_at"]:
            del cls._states[state]
            return None
        
        return state_data
    
    @classmethod
    def consume_state(cls, state: str) -> Optional[Dict[str, Any]]:
        """
        消费 state（一次性使用）
        
        验证 state 后立即删除，防止重放攻击
        
        Args:
            state: 要消费的 state 字符串
            
        Returns:
            如果有效返回存储的数据，无效返回 None
        """
        state_data = cls.validate_state(state)
        
        if state_data:
            # 删除已使用的 state
            del cls._states[state]
        
        return state_data
    
    @classmethod
    def _cleanup_expired(cls):
        """清理过期的 state"""
        current_time = time.time()
        expired_states = [
            state for state, data in cls._states.items()
            if current_time > data["expires_at"]
        ]
        
        for state in expired_states:
            del cls._states[state]
    
    @classmethod
    def clear_all(cls):
        """清除所有 state（测试用）"""
        cls._states.clear()
    
    @classmethod
    def get_state_count(cls) -> int:
        """获取当前 state 数量（监控用）"""
        return len(cls._states)


# 全局单例
state_manager = OAuthStateManager()