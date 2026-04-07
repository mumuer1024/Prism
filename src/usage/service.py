# -*- coding: utf-8 -*-
"""
使用次数服务（激活码架构）

提供次数检查、扣减、推荐奖励触发等核心业务逻辑
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from src.database.models import ActivationCode, AnonymousUsage
from src.database import crud
from src.config import settings

logger = logging.getLogger(__name__)

# 每日免费限额
FREE_DAILY_LIMIT = 3

# 推荐奖励次数
REFERRAL_BONUS_COUNT = 3


class UsageService:
    """使用次数服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_balance(
        self,
        device_id: Optional[str] = None,
        visitor_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取次数余额

        有 device_id → 激活码逻辑
        否则 → 匿名用户逻辑

        Args:
            device_id: 设备 ID（已激活用户）
            visitor_id: 访客 ID（匿名用户）

        Returns:
            dict: 余额信息
        """
        # 计算明天 0 点（免费次数重置时间）
        tomorrow = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) + timedelta(days=1)

        # 优先检查 device_id（已激活用户）
        if device_id:
            activation_code = crud.get_activation_code_by_device_id(self.db, device_id)

            if activation_code:
                # 获取推荐码信息
                referral_record = crud.get_referral_code_by_code_id(self.db, activation_code.id)

                return {
                    "user_type": "activated",
                    "paid_remaining": activation_code.remaining,
                    "free_remaining": FREE_DAILY_LIMIT,  # 已激活用户无免费限制
                    "free_limit": FREE_DAILY_LIMIT,
                    "free_reset_at": tomorrow.isoformat(),
                    "referral_code": referral_record.referral_code if referral_record else None,
                    "referral_count": referral_record.referral_count if referral_record else 0,
                }

        # 匿名用户
        if visitor_id:
            anon = crud.reset_anonymous_daily_usage(self.db, visitor_id)
            free_remaining = max(0, FREE_DAILY_LIMIT - anon.daily_count)

            return {
                "user_type": "anonymous",
                "paid_remaining": 0,
                "free_remaining": free_remaining,
                "free_limit": FREE_DAILY_LIMIT,
                "free_reset_at": tomorrow.isoformat(),
                "referral_code": None,
                "referral_count": None,
            }

        # 无有效标识
        return {
            "user_type": "unknown",
            "paid_remaining": 0,
            "free_remaining": 0,
            "free_limit": FREE_DAILY_LIMIT,
            "free_reset_at": tomorrow.isoformat(),
            "referral_code": None,
            "referral_count": None,
        }

    def check_usage(
        self,
        device_id: Optional[str] = None,
        visitor_id: Optional[str] = None,
        tool_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        检查使用权限

        Args:
            device_id: 设备 ID
            visitor_id: 访客 ID
            tool_type: 工具类型

        Returns:
            dict: {
                can_use: bool,
                source: str,
                remaining: int,
                message: str (optional)
            }
        """
        # 优先检查 device_id（已激活用户）
        if device_id:
            activation_code = crud.get_activation_code_by_device_id(self.db, device_id)

            if activation_code:
                if activation_code.remaining > 0:
                    return {
                        "can_use": True,
                        "source": "paid",
                        "remaining": activation_code.remaining,
                    }
                else:
                    return {
                        "can_use": False,
                        "source": "paid",
                        "remaining": 0,
                        "message": "次数已用完，请购买新激活码",
                    }

        # 匿名用户
        if visitor_id:
            anon = crud.reset_anonymous_daily_usage(self.db, visitor_id)
            free_remaining = max(0, FREE_DAILY_LIMIT - anon.daily_count)

            if free_remaining > 0:
                return {
                    "can_use": True,
                    "source": "free",
                    "remaining": free_remaining,
                }
            else:
                return {
                    "can_use": False,
                    "source": "free",
                    "remaining": 0,
                    "message": "今日免费次数已用完，请激活激活码",
                }

        # 无有效标识
        return {
            "can_use": False,
            "source": "unknown",
            "remaining": 0,
            "message": "请提供设备 ID 或访客 ID",
        }

    def consume(
        self,
        device_id: Optional[str] = None,
        visitor_id: Optional[str] = None,
        tool_type: Optional[str] = None,
        amount: int = 1,
    ) -> Dict[str, Any]:
        """
        扣减次数 + 触发推荐奖励检查

        Args:
            device_id: 设备 ID
            visitor_id: 访客 ID
            tool_type: 工具类型
            amount: 扣减次数

        Returns:
            dict: {
                success: bool,
                source: str,
                remaining: int,
                referral_rewarded: bool,
                referral_bonus: int,
                message: str (optional)
            }
        """
        # 先检查权限
        check_result = self.check_usage(device_id, visitor_id, tool_type)

        if not check_result.get("can_use"):
            return {
                "success": False,
                "message": check_result.get("message", "无使用权限"),
                "source": check_result.get("source"),
                "remaining": 0,
                "referral_rewarded": False,
                "referral_bonus": 0,
            }

        source = check_result["source"]
        referral_rewarded = False
        referral_bonus = 0

        # 执行扣减
        if source == "paid" and device_id:
            # 已激活用户：扣减付费次数
            activation_code = crud.get_activation_code_by_device_id(self.db, device_id)

            if activation_code:
                # 扣减次数
                crud.deduct_activation_code_quota(self.db, activation_code.id, amount)

                # 检查是否触发推荐奖励（首次消费）
                if activation_code.referral_code_used and not activation_code.referral_rewarded:
                    # 查询推荐码
                    referral = crud.get_referral_code_by_code(
                        self.db,
                        activation_code.referral_code_used,
                    )

                    if referral:
                        # 给推荐人 +3 次
                        crud.add_quota_to_activation_code(
                            self.db,
                            referral.code_id,
                            REFERRAL_BONUS_COUNT,
                        )

                        # 给被推荐人 +3 次
                        crud.add_quota_to_activation_code(
                            self.db,
                            activation_code.id,
                            REFERRAL_BONUS_COUNT,
                        )

                        # 更新推荐统计
                        crud.update_referral_stats(
                            self.db,
                            referral.id,
                            increment_referral=True,
                            reward_amount=REFERRAL_BONUS_COUNT,
                        )

                        # 标记已发放奖励
                        activation_code.referral_rewarded = True
                        self.db.commit()

                        referral_rewarded = True
                        referral_bonus = REFERRAL_BONUS_COUNT

                        logger.info(
                            f"推荐奖励已发放: referral_code={referral.referral_code}, "
                            f"inviter_bonus={REFERRAL_BONUS_COUNT}, "
                            f"invitee_bonus={REFERRAL_BONUS_COUNT}"
                        )

                # 更新设备活跃时间
                crud.update_device_last_seen(self.db, device_id)

                remaining = activation_code.remaining

        elif source == "free" and visitor_id:
            # 匿名用户：扣减免费次数
            anon = crud.increment_anonymous_usage(self.db, visitor_id, amount)
            remaining = max(0, FREE_DAILY_LIMIT - anon.daily_count)

        else:
            return {
                "success": False,
                "message": "扣减失败",
                "source": source,
                "remaining": 0,
                "referral_rewarded": False,
                "referral_bonus": 0,
            }

        return {
            "success": True,
            "source": source,
            "remaining": remaining,
            "referral_rewarded": referral_rewarded,
            "referral_bonus": referral_bonus,
        }

    def get_config(self) -> Dict[str, Any]:
        """
        获取使用配置

        Returns:
            dict: 配置信息
        """
        return {
            "free_daily_limit": FREE_DAILY_LIMIT,
            "referral_bonus_count": REFERRAL_BONUS_COUNT,
            "device_limit": 3,
        }