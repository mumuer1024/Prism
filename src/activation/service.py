# -*- coding: utf-8 -*-
"""
激活码模块 - 业务逻辑

提供激活码验证、设备绑定、推荐码管理等核心业务逻辑
"""

import re
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.models import ActivationCode, Device, ReferralCode
from src.database import crud

logger = logging.getLogger(__name__)

# 激活码格式正则（PRISM-XXXX-XXXX-XXXX，不区分大小写）
ACTIVATION_CODE_PATTERN = re.compile(r"^PRISM-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$", re.IGNORECASE)

# 推荐码格式正则（REF-XXXXXX，不区分大小写）
REFERRAL_CODE_PATTERN = re.compile(r"^REF-[A-Z0-9]{6}$", re.IGNORECASE)

# 设备数量上限
DEVICE_LIMIT = 3

# 次数规格定义
QUOTA_SPECS = {
    "S": 3,
    "M": 6,
    "L": 10,
    "XL": 20,
    "XXL": 50,
    "XXXL": 100,
}


class ActivationService:
    """激活码服务"""

    def __init__(self, db: Session):
        self.db = db

    def validate_activation_code_format(self, code: str) -> bool:
        """
        验证激活码格式

        Args:
            code: 激活码字符串

        Returns:
            bool: 格式是否正确
        """
        if not code:
            return False
        return bool(ACTIVATION_CODE_PATTERN.match(code.strip()))

    def validate_referral_code_format(self, referral_code: str) -> bool:
        """
        验证推荐码格式

        Args:
            referral_code: 推荐码字符串

        Returns:
            bool: 格式是否正确
        """
        if not referral_code:
            return False
        return bool(REFERRAL_CODE_PATTERN.match(referral_code.strip()))

    def activate(
        self,
        code: str,
        device_id: str,
        device_name: Optional[str] = None,
        referral_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        激活激活码

        流程：
        1. 验证激活码格式
        2. 查询激活码是否存在且有效
        3. 检查设备数量限制
        4. 绑定设备（幂等）
        5. 首次激活时生成推荐码
        6. 如填写推荐码，验证并记录
        7. 返回激活结果

        Args:
            code: 激活码
            device_id: 设备 ID
            device_name: 设备名称
            referral_code: 推荐码（可选）

        Returns:
            dict: {
                success: bool,
                message: str,
                data: dict (optional)
            }
        """
        # 1. 验证激活码格式
        code = code.strip().upper()
        if not self.validate_activation_code_format(code):
            return {
                "success": False,
                "message": "激活码格式错误，正确格式：PRISM-XXXX-XXXX-XXXX",
                "error_code": "INVALID_FORMAT",
            }

        # 2. 查询激活码
        activation_code = crud.get_activation_code_by_code(self.db, code)
        if not activation_code:
            return {
                "success": False,
                "message": "激活码不存在",
                "error_code": "CODE_NOT_FOUND",
            }

        # 检查激活码是否有剩余次数
        if activation_code.remaining <= 0:
            return {
                "success": False,
                "message": "激活码次数已用完",
                "error_code": "CODE_EXHAUSTED",
            }

        # 3. 检查设备数量限制（幂等：同一设备已绑定则跳过）
        existing_device = self.db.query(Device).filter(
            Device.code_id == activation_code.id,
            Device.device_id == device_id,
        ).first()

        if existing_device:
            # 幂等：设备已绑定，更新活跃时间
            existing_device.last_seen = datetime.utcnow()
            if device_name:
                existing_device.device_name = device_name
            self.db.commit()
            logger.info(f"设备已绑定，更新活跃时间: device_id={device_id[:16]}...")
        else:
            # 检查设备数量
            device_count = crud.count_devices_by_code_id(self.db, activation_code.id)
            if device_count >= DEVICE_LIMIT:
                return {
                    "success": False,
                    "message": f"已达设备上限（{DEVICE_LIMIT}个），请先解绑一个设备",
                    "error_code": "DEVICE_LIMIT_REACHED",
                }

            # 绑定新设备
            try:
                device = crud.create_device(
                    self.db,
                    activation_code.id,
                    device_id,
                    device_name,
                )
                if not device:
                    return {
                        "success": False,
                        "message": "设备绑定失败",
                        "error_code": "DEVICE_BIND_FAILED",
                    }
            except IntegrityError as e:
                # 唯一约束冲突（并发）
                logger.warning(f"设备绑定并发冲突: {e}")
                self.db.rollback()
                return {
                    "success": False,
                    "message": "设备绑定失败，请重试",
                    "error_code": "DEVICE_BIND_CONFLICT",
                }

        # 4. 首次激活：标记激活时间，生成推荐码
        if not activation_code.is_activated:
            activation_code.is_activated = True
            activation_code.activated_at = datetime.utcnow()
            self.db.commit()

            # 生成推荐码
            referral = crud.create_referral_code(self.db, activation_code.id)
            logger.info(f"激活码首次激活: code={code}, referral={referral.referral_code}")

        # 5. 处理推荐码（如果填写了）
        if referral_code:
            referral_code = referral_code.strip().upper()

            # 验证推荐码格式
            if not self.validate_referral_code_format(referral_code):
                logger.warning(f"推荐码格式错误: {referral_code}")
                # 不阻断激活，只是忽略推荐码
            else:
                # 查询推荐码是否存在
                referral = crud.get_referral_code_by_code(self.db, referral_code)
                if referral:
                    # 检查是否使用自己的推荐码
                    if referral.code_id == activation_code.id:
                        logger.warning(f"用户尝试使用自己的推荐码: code={code}")
                    else:
                        # 记录推荐码（奖励延迟到首次消费时触发）
                        activation_code.referral_code_used = referral_code
                        self.db.commit()
                        logger.info(f"推荐码已记录: code={code}, referral={referral_code}")
                else:
                    logger.warning(f"推荐码不存在: {referral_code}")

        # 6. 返回结果
        device_count = crud.count_devices_by_code_id(self.db, activation_code.id)
        referral_record = crud.get_referral_code_by_code_id(self.db, activation_code.id)

        return {
            "success": True,
            "message": "激活成功",
            "data": {
                "code_id": activation_code.id,
                "code": activation_code.code,
                "quota": activation_code.quota,
                "remaining": activation_code.remaining,
                "is_activated": activation_code.is_activated,
                "referral_code": referral_record.referral_code if referral_record else None,
                "device_count": device_count,
                "device_limit": DEVICE_LIMIT,
            },
        }

    def get_status(self, device_id: str) -> Dict[str, Any]:
        """
        查询激活状态

        通过 device_id 查询关联的激活码状态

        Args:
            device_id: 设备 ID

        Returns:
            dict: {
                success: bool,
                is_activated: bool,
                data: dict (optional)
            }
        """
        # 查询设备关联的激活码
        activation_code = crud.get_activation_code_by_device_id(self.db, device_id)

        if not activation_code:
            return {
                "success": True,
                "is_activated": False,
                "data": None,
            }

        # 获取推荐码信息
        referral_record = crud.get_referral_code_by_code_id(self.db, activation_code.id)
        device_count = crud.count_devices_by_code_id(self.db, activation_code.id)

        return {
            "success": True,
            "is_activated": True,
            "data": {
                "code_id": activation_code.id,
                "code": activation_code.code,
                "quota": activation_code.quota,
                "remaining": activation_code.remaining,
                "is_activated": activation_code.is_activated,
                "referral_code": referral_record.referral_code if referral_record else None,
                "device_count": device_count,
                "referral_count": referral_record.referral_count if referral_record else 0,
                "total_rewarded": referral_record.total_rewarded if referral_record else 0,
            },
        }

    def get_devices(self, device_id: str) -> Dict[str, Any]:
        """
        获取已绑定设备列表

        Args:
            device_id: 当前设备 ID

        Returns:
            dict: {
                success: bool,
                devices: List[dict],
                total: int,
                limit: int
            }
        """
        # 查询设备关联的激活码
        activation_code = crud.get_activation_code_by_device_id(self.db, device_id)

        if not activation_code:
            return {
                "success": False,
                "message": "设备未绑定激活码",
                "devices": [],
                "total": 0,
                "limit": DEVICE_LIMIT,
            }

        # 获取设备列表
        devices = crud.get_devices_by_code_id(self.db, activation_code.id)

        device_list = []
        for d in devices:
            device_list.append({
                "id": d.id,
                "device_id": d.device_id,
                "device_name": d.device_name,
                "last_seen": d.last_seen.isoformat() if d.last_seen else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "is_current": d.device_id == device_id,
            })

        return {
            "success": True,
            "devices": device_list,
            "total": len(device_list),
            "limit": DEVICE_LIMIT,
            "current_device_id": device_id,
        }

    def delete_device(
        self,
        device_id: str,
        device_db_id: int,
    ) -> Dict[str, Any]:
        """
        解绑设备

        Args:
            device_id: 当前设备 ID（用于验证）
            device_db_id: 要解绑的设备数据库 ID

        Returns:
            dict: {
                success: bool,
                message: str
            }
        """
        # 查询当前设备关联的激活码
        activation_code = crud.get_activation_code_by_device_id(self.db, device_id)

        if not activation_code:
            return {
                "success": False,
                "message": "设备未绑定激活码",
            }

        # 查询要解绑的设备
        target_device = crud.get_device_by_id(self.db, device_db_id)

        if not target_device:
            return {
                "success": False,
                "message": "设备不存在",
            }

        # 检查设备是否属于同一激活码
        if target_device.code_id != activation_code.id:
            return {
                "success": False,
                "message": "无权解绑此设备",
            }

        # 不能解绑当前设备（至少保留一个）
        if target_device.device_id == device_id:
            return {
                "success": False,
                "message": "不能解绑当前设备",
            }

        # 解绑设备
        success = crud.delete_device(self.db, device_db_id)

        if success:
            return {
                "success": True,
                "message": "设备已解绑",
            }
        else:
            return {
                "success": False,
                "message": "解绑失败",
            }

    def get_referral(self, device_id: str) -> Dict[str, Any]:
        """
        获取专属推荐码

        Args:
            device_id: 设备 ID

        Returns:
            dict: {
                success: bool,
                data: dict (optional)
            }
        """
        # 查询设备关联的激活码
        activation_code = crud.get_activation_code_by_device_id(self.db, device_id)

        if not activation_code:
            return {
                "success": False,
                "message": "设备未绑定激活码",
                "data": None,
            }

        # 获取推荐码
        referral_record = crud.get_referral_code_by_code_id(self.db, activation_code.id)

        if not referral_record:
            return {
                "success": False,
                "message": "推荐码不存在",
                "data": None,
            }

        return {
            "success": True,
            "data": {
                "referral_code": referral_record.referral_code,
                "referral_count": referral_record.referral_count,
                "total_rewarded": referral_record.total_rewarded,
                "code_id": activation_code.id,
            },
        }

    def add_quota(
        self,
        device_id: str,
        new_code: str,
    ) -> Dict[str, Any]:
        """
        使用新激活码叠加次数

        Args:
            device_id: 设备 ID
            new_code: 新激活码

        Returns:
            dict: {
                success: bool,
                message: str,
                data: dict (optional)
            }
        """
        # 验证新激活码
        new_code = new_code.strip().upper()
        if not self.validate_activation_code_format(new_code):
            return {
                "success": False,
                "message": "激活码格式错误",
                "error_code": "INVALID_FORMAT",
            }

        # 查询新激活码
        new_activation = crud.get_activation_code_by_code(self.db, new_code)
        if not new_activation:
            return {
                "success": False,
                "message": "激活码不存在",
                "error_code": "CODE_NOT_FOUND",
            }

        if new_activation.remaining <= 0:
            return {
                "success": False,
                "message": "激活码次数已用完",
                "error_code": "CODE_EXHAUSTED",
            }

        # 查询当前设备关联的激活码
        current_activation = crud.get_activation_code_by_device_id(self.db, device_id)

        if not current_activation:
            # 当前设备未激活，执行激活流程
            return self.activate(new_code, device_id)

        # 将新激活码的次数转移到当前激活码
        # 新激活码标记为已用完
        transfer_amount = new_activation.remaining
        new_activation.remaining = 0
        new_activation.is_activated = True
        new_activation.activated_at = datetime.utcnow()

        # 当前激活码增加次数
        current_activation.quota += transfer_amount
        current_activation.remaining += transfer_amount

        self.db.commit()

        logger.info(f"次数叠加成功: current_code={current_activation.code}, new_code={new_code}, amount={transfer_amount}")

        return {
            "success": True,
            "message": f"成功叠加 {transfer_amount} 次",
            "data": {
                "code_id": current_activation.id,
                "code": current_activation.code,
                "quota": current_activation.quota,
                "remaining": current_activation.remaining,
            },
        }

    @staticmethod
    def get_quota_specs() -> List[Dict[str, Any]]:
        """
        获取次数规格定义

        Returns:
            List[dict]: 规格列表
        """
        return [
            {"spec": spec, "quota": quota}
            for spec, quota in QUOTA_SPECS.items()
        ]