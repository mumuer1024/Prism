# src/user/service.py
"""
用户服务层
处理用户信息、兑换码充值、邀请统计等业务逻辑
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from src.database.models import User, RedemptionCode
from src.database import crud
from src.config import settings

logger = logging.getLogger(__name__)


class UserService:
    """用户服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_profile(self, user: User) -> dict:
        """
        获取用户完整信息
        
        Args:
            user: 用户对象
            
        Returns:
            dict: 用户信息，包含邀请统计和最近充值记录
        """
        # 获取邀请统计
        invite_stats = crud.get_invite_stats(self.db, user.id)
        
        # 获取最近充值记录（最多5条）
        recent_topups = crud.get_topup_records_by_user(
            self.db, user.id, limit=5
        )
        
        # 构建用户信息
        user_data = {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
            "usage_count": user.usage_count,
            "invite_code": user.invite_code,
            "has_redeemed_first": user.has_redeemed_first,
            "is_verified": user.is_verified,
            "oauth_provider": user.oauth_provider,
            "oauth_name": user.oauth_name,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
        }
        
        # 构建充值记录
        topup_records = [
            {
                "id": t.id,
                "source": t.source,
                "count": t.count,
                "bonus_count": t.bonus_count,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in recent_topups
        ]
        
        return {
            "success": True,
            "data": {
                "user": user_data,
                "invite_stats": invite_stats,
                "recent_topups": topup_records,
            },
        }
    
    async def redeem_code(
        self,
        user: User,
        code: str,
    ) -> Dict[str, Any]:
        """
        兑换码充值
        
        Args:
            user: 用户对象
            code: 兑换码
            
        Returns:
            dict: 兑换结果
        """
        # 查询兑换码
        redemption_code = crud.get_redemption_code(self.db, code)
        
        if not redemption_code:
            return {
                "success": False,
                "message": "兑换码无效",
                "data": None,
            }
        
        # 检查是否已使用
        if redemption_code.used:
            return {
                "success": False,
                "message": "兑换码已被使用",
                "data": None,
            }
        
        # 检查是否过期
        if redemption_code.expires_at and redemption_code.expires_at < datetime.utcnow():
            return {
                "success": False,
                "message": "兑换码已过期",
                "data": None,
            }
        
        try:
            # 处理兑换（含邀请返利）
            result = crud.process_redemption_with_invite_bonus(
                db=self.db,
                user=user,
                redemption_code=redemption_code,
                invite_bonus_count=settings.INVITE_BONUS_COUNT,
                invitee_bonus_count=settings.INVITEE_BONUS_COUNT,
            )
            
            # 构建响应
            total = result["count"] + result["bonus_count"]
            message = f"兑换成功，获得 {total} 次使用机会"
            if result["bonus_count"] > 0:
                message += f"（含邀请赠送 {result['bonus_count']} 次）"
            
            logger.info(
                f"用户 {user.id} 兑换成功: code={code}, count={result['count']}, "
                f"bonus={result['bonus_count']}, inviter_bonus={result['inviter_bonus']}"
            )
            
            return {
                "success": True,
                "message": message,
                "data": {
                    "count": result["count"],
                    "bonus_count": result["bonus_count"],
                    "total_count": total,
                    "inviter_bonus": result["inviter_bonus"],
                    "inviter_bonus_count": result["inviter_bonus_count"],
                },
            }
            
        except Exception as e:
            logger.error(f"兑换失败: user={user.id}, code={code}, error={str(e)}")
            return {
                "success": False,
                "message": f"兑换失败：{str(e)}",
                "data": None,
            }
    
    async def get_invite_statistics(self, user: User) -> dict:
        """
        获取邀请统计
        
        Args:
            user: 用户对象
            
        Returns:
            dict: 邀请统计信息
        """
        # 获取统计信息
        stats = crud.get_invite_stats(self.db, user.id)
        
        # 获取邀请记录详情（最多20条）
        records = crud.get_invite_records_by_inviter(
            self.db, user.id, limit=20
        )
        
        # 构建邀请记录
        invite_records = []
        for record in records:
            invitee = crud.get_user_by_id(self.db, record.invitee_id)
            invite_records.append({
                "invitee_id": record.invitee_id,
                "invitee_email": invitee.email if invitee else None,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "bonus_given": record.bonus_given,
                "bonus_count": record.bonus_count,
                "bonus_at": record.bonus_at.isoformat() if record.bonus_at else None,
            })
        
        return {
            "success": True,
            "data": {
                "invite_code": user.invite_code,
                "total_invited": stats["total_invited"],
                "active_invited": stats["active_invited"],
                "total_bonus": stats["total_bonus"],
                "invite_records": invite_records,
            },
        }
    
    async def get_user_usage(self, user: User) -> dict:
        """
        获取用户使用次数信息
        
        Args:
            user: 用户对象
            
        Returns:
            dict: 使用次数信息
        """
        return {
            "success": True,
            "data": {
                "usage_count": user.usage_count,
                "has_redeemed_first": user.has_redeemed_first,
            },
        }