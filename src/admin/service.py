# -*- coding: utf-8 -*-
"""
管理员服务层

处理用户管理、兑换码管理等业务逻辑
"""

from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
import logging
import csv
import io
import json

from src.database.models import User, RedemptionCode, TopupRecord, InviteRecord, Admin, AuditLog
from src.database.crud import create_redemption_codes, get_user_by_id
from src.config import settings

logger = logging.getLogger(__name__)


class AdminService:
    """管理员服务"""

    def __init__(self, db: Session):
        self.db = db

    # ==========================================
    # 审计日志
    # ==========================================

    def log_action(
        self,
        admin_id: int,
        admin_username: str,
        action: str,
        action_category: str,
        target_type: str = None,
        target_id: str = None,
        target_info: dict = None,
        action_detail: dict = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> AuditLog:
        """
        记录审计日志

        Args:
            admin_id: 管理员ID
            admin_username: 管理员用户名
            action: 操作类型
            action_category: 操作分类
            target_type: 目标类型
            target_id: 目标ID
            target_info: 目标信息
            action_detail: 操作详情
            ip_address: IP地址
            user_agent: User-Agent

        Returns:
            AuditLog: 审计日志记录
        """
        log = AuditLog(
            admin_id=admin_id,
            admin_username=admin_username,
            action=action,
            action_category=action_category,
            target_type=target_type,
            target_id=target_id,
            target_info=json.dumps(target_info, ensure_ascii=False) if target_info else None,
            action_detail=json.dumps(action_detail, ensure_ascii=False) if action_detail else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        logger.info(f"审计日志: admin={admin_username}, action={action}, target={target_type}:{target_id}")

        return log

    def get_audit_logs(
        self,
        page: int = 1,
        limit: int = 50,
        admin_id: int = None,
        action: str = None,
        action_category: str = None,
        target_type: str = None,
        start_date: datetime = None,
        end_date: datetime = None,
    ) -> Tuple[List[AuditLog], int]:
        """
        获取审计日志列表

        Args:
            page: 页码
            limit: 每页数量
            admin_id: 管理员ID筛选
            action: 操作类型筛选
            action_category: 操作分类筛选
            target_type: 目标类型筛选
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            Tuple[List[AuditLog], int]: 日志列表和总数
        """
        query = self.db.query(AuditLog)

        if admin_id:
            query = query.filter(AuditLog.admin_id == admin_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if action_category:
            query = query.filter(AuditLog.action_category == action_category)
        if target_type:
            query = query.filter(AuditLog.target_type == target_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        query = query.order_by(desc(AuditLog.created_at))

        total = query.count()
        offset = (page - 1) * limit
        logs = query.offset(offset).limit(limit).all()

        return logs, total

    # ==========================================
    # 用户管理
    # ==========================================

    def get_users(
        self,
        page: int = 1,
        limit: int = 20,
        search: str = None,
        is_banned: bool = None,
    ) -> Tuple[List[User], int]:
        """
        获取用户列表

        Args:
            page: 页码
            limit: 每页数量
            search: 搜索关键词
            is_banned: 封禁状态筛选

        Returns:
            Tuple[List[User], int]: 用户列表和总数
        """
        query = self.db.query(User)

        # 搜索筛选
        if search:
            query = query.filter(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.nickname.ilike(f"%{search}%"),
                )
            )

        # 封禁状态筛选
        if is_banned is not None:
            query = query.filter(User.is_banned == is_banned)

        # 排序
        query = query.order_by(desc(User.created_at))

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * limit
        users = query.offset(offset).limit(limit).all()

        return users, total

    def get_user_detail(self, user_id: int) -> Optional[dict]:
        """
        获取用户详情

        Args:
            user_id: 用户 ID

        Returns:
            Optional[dict]: 用户详情
        """
        user = get_user_by_id(self.db, user_id)
        if not user:
            return None

        # 获取充值统计
        topup_stats = self.db.query(
            func.sum(TopupRecord.count).label("total_count"),
            func.sum(TopupRecord.bonus_count).label("total_bonus"),
        ).filter(TopupRecord.user_id == user_id).first()

        total_topup = topup_stats.total_count or 0
        total_bonus = topup_stats.total_bonus or 0

        # 获取邀请统计
        invite_stats = self._get_invite_stats(user_id)

        return {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url or user.oauth_avatar,
            "usage_count": user.usage_count,
            "invite_code": user.invite_code,
            "invited_by": user.invited_by,
            "has_redeemed_first": user.has_redeemed_first,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "is_banned": user.is_banned,
            "banned_at": user.banned_at,
            "banned_reason": user.banned_reason,
            "oauth_provider": user.oauth_provider,
            "created_at": user.created_at,
            "last_login_at": user.last_login_at,
            "total_topup_count": total_topup,
            "total_bonus_count": total_bonus,
            "invite_stats": invite_stats,
        }

    def ban_user(self, user_id: int, reason: str) -> dict:
        """
        封禁用户

        Args:
            user_id: 用户 ID
            reason: 封禁原因

        Returns:
            dict: 封禁结果
        """
        user = get_user_by_id(self.db, user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        if user.is_banned:
            return {"success": False, "message": "用户已被封禁"}

        user.is_banned = True
        user.banned_at = datetime.utcnow()
        user.banned_reason = reason
        user.is_active = False

        self.db.commit()

        logger.info(f"用户 {user_id} 已被封禁，原因: {reason}")

        return {
            "success": True,
            "message": "用户已封禁",
            "user_id": user_id,
            "banned_at": user.banned_at,
            "banned_reason": reason,
        }

    def unban_user(self, user_id: int) -> dict:
        """
        解禁用户

        Args:
            user_id: 用户 ID

        Returns:
            dict: 解禁结果
        """
        user = get_user_by_id(self.db, user_id)
        if not user:
            return {"success": False, "message": "用户不存在"}

        if not user.is_banned:
            return {"success": False, "message": "用户未被封禁"}

        user.is_banned = False
        user.banned_at = None
        user.banned_reason = None
        user.is_active = True

        self.db.commit()

        logger.info(f"用户 {user_id} 已解禁")

        return {
            "success": True,
            "message": "用户已解禁",
            "user_id": user_id,
        }

    def batch_ban_users(
        self,
        user_ids: List[int],
        reason: str,
        admin_id: int = None,
        admin_username: str = None,
        ip_address: str = None,
    ) -> dict:
        """
        批量封禁用户

        Args:
            user_ids: 用户ID列表
            reason: 封禁原因
            admin_id: 管理员ID（用于审计日志）
            admin_username: 管理员用户名（用于审计日志）
            ip_address: IP地址（用于审计日志）

        Returns:
            dict: 批量封禁结果
        """
        results = {
            "total": len(user_ids),
            "succeeded": 0,
            "failed": 0,
            "failed_ids": [],
            "details": [],
        }

        banned_at = datetime.utcnow()

        for user_id in user_ids:
            user = get_user_by_id(self.db, user_id)

            if not user:
                results["failed"] += 1
                results["failed_ids"].append(user_id)
                results["details"].append({
                    "user_id": user_id,
                    "success": False,
                    "message": "用户不存在"
                })
                continue

            if user.is_banned:
                results["failed"] += 1
                results["failed_ids"].append(user_id)
                results["details"].append({
                    "user_id": user_id,
                    "success": False,
                    "message": "用户已被封禁",
                    "email": user.email
                })
                continue

            # 执行封禁
            user.is_banned = True
            user.banned_at = banned_at
            user.banned_reason = reason
            user.is_active = False

            results["succeeded"] += 1
            results["details"].append({
                "user_id": user_id,
                "success": True,
                "message": "封禁成功",
                "email": user.email
            })

        self.db.commit()

        # 记录审计日志
        if admin_id and admin_username:
            self.log_action(
                admin_id=admin_id,
                admin_username=admin_username,
                action="batch_ban_users",
                action_category="user_management",
                target_type="users",
                target_id=",".join(str(uid) for uid in user_ids),
                target_info={
                    "user_ids": user_ids,
                    "count": len(user_ids),
                },
                action_detail={
                    "reason": reason,
                    "succeeded": results["succeeded"],
                    "failed": results["failed"],
                    "banned_at": banned_at.isoformat(),
                },
                ip_address=ip_address,
            )

        logger.info(f"批量封禁用户: total={len(user_ids)}, succeeded={results['succeeded']}, failed={results['failed']}")

        return {
            "success": results["succeeded"] > 0,
            "message": f"成功封禁 {results['succeeded']} 个用户，失败 {results['failed']} 个",
            **results
        }

    def get_user_stats(self) -> dict:
        """
        获取用户统计

        Returns:
            dict: 用户统计信息
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        total_users = self.db.query(User).count()
        active_users = self.db.query(User).filter(User.is_active == True, User.is_banned == False).count()
        banned_users = self.db.query(User).filter(User.is_banned == True).count()

        new_users_today = self.db.query(User).filter(User.created_at >= today_start).count()
        new_users_this_week = self.db.query(User).filter(User.created_at >= week_start).count()
        new_users_this_month = self.db.query(User).filter(User.created_at >= month_start).count()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "banned_users": banned_users,
            "new_users_today": new_users_today,
            "new_users_this_week": new_users_this_week,
            "new_users_this_month": new_users_this_month,
        }

    def get_revenue_stats(self) -> dict:
        """
        获取充值统计

        Returns:
            dict: 充值统计信息
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # 充值统计
        topup_stats = self.db.query(
            func.sum(TopupRecord.count).label("total_count"),
            func.sum(TopupRecord.bonus_count).label("total_bonus"),
        ).first()

        # 兑换码统计
        total_codes_used = self.db.query(RedemptionCode).filter(RedemptionCode.used == True).count()
        total_codes_unused = self.db.query(RedemptionCode).filter(RedemptionCode.used == False).count()

        # 今日/本周/本月充值记录数
        topup_today = self.db.query(TopupRecord).filter(TopupRecord.created_at >= today_start).count()
        topup_week = self.db.query(TopupRecord).filter(TopupRecord.created_at >= week_start).count()
        topup_month = self.db.query(TopupRecord).filter(TopupRecord.created_at >= month_start).count()

        return {
            "total_topup_count": topup_stats.total_count or 0,
            "total_bonus_count": topup_stats.total_bonus or 0,
            "total_codes_used": total_codes_used,
            "total_codes_unused": total_codes_unused,
            "topup_records_today": topup_today,
            "topup_records_this_week": topup_week,
            "topup_records_this_month": topup_month,
        }

    def _get_invite_stats(self, user_id: int) -> dict:
        """
        获取邀请统计

        Args:
            user_id: 用户 ID

        Returns:
            dict: 邀请统计
        """
        total_invited = self.db.query(InviteRecord).filter(
            InviteRecord.inviter_id == user_id
        ).count()

        active_invited = self.db.query(InviteRecord).filter(
            InviteRecord.inviter_id == user_id,
            InviteRecord.bonus_given == True,
        ).count()

        total_bonus = self.db.query(func.sum(InviteRecord.bonus_count)).filter(
            InviteRecord.inviter_id == user_id,
            InviteRecord.bonus_given == True,
        ).scalar() or 0

        return {
            "total_invited": total_invited,
            "active_invited": active_invited,
            "total_bonus": total_bonus,
        }

    # ==========================================
    # 兑换码管理
    # ==========================================

    def generate_codes(
        self,
        count: int,
        usage_count: int,
        expire_days: int = 365,
        note: str = None,
    ) -> dict:
        """
        批量生成兑换码

        Args:
            count: 生成数量
            usage_count: 每个兑换码的使用次数
            expire_days: 有效期天数
            note: 备注

        Returns:
            dict: 生成结果
        """
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        expires_at = datetime.utcnow() + timedelta(days=expire_days)

        codes = create_redemption_codes(
            db=self.db,
            batch_id=batch_id,
            count_per_code=usage_count,
            num_codes=count,
            expires_at=expires_at,
            description=note,
        )

        logger.info(f"批量生成兑换码: batch_id={batch_id}, count={count}, usage_count={usage_count}")

        return {
            "success": True,
            "message": f"成功生成 {count} 个兑换码",
            "batch_id": batch_id,
            "codes": [c.code for c in codes],
            "count": count,
            "usage_count_per_code": usage_count,
            "expires_at": expires_at,
        }

    def get_batches(self) -> List[dict]:
        """
        获取兑换码批次列表

        Returns:
            List[dict]: 批次列表
        """
        # 查询所有批次
        batches = self.db.query(
            RedemptionCode.batch_id,
            func.count(RedemptionCode.id).label("total_codes"),
            func.sum(RedemptionCode.count).label("total_count"),
            func.min(RedemptionCode.created_at).label("created_at"),
            func.max(RedemptionCode.expires_at).label("expires_at"),
            func.sum(RedemptionCode.used == True).label("used_codes"),
        ).group_by(RedemptionCode.batch_id).all()

        result = []
        for batch in batches:
            result.append({
                "batch_id": batch.batch_id,
                "total_codes": batch.total_codes,
                "used_codes": batch.used_codes or 0,
                "unused_codes": batch.total_codes - (batch.used_codes or 0),
                "total_count": batch.total_count,
                "created_at": batch.created_at,
                "expires_at": batch.expires_at,
            })

        return result

    def get_batch_detail(self, batch_id: str) -> Optional[dict]:
        """
        获取批次详情

        Args:
            batch_id: 批次号

        Returns:
            Optional[dict]: 批次详情
        """
        codes = self.db.query(RedemptionCode).filter(
            RedemptionCode.batch_id == batch_id
        ).order_by(desc(RedemptionCode.created_at)).all()

        if not codes:
            return None

        # 统计
        total_codes = len(codes)
        used_codes = sum(1 for c in codes if c.used)
        total_count = sum(c.count for c in codes)

        # 构建兑换码列表
        code_list = []
        for code in codes:
            used_by_email = None
            if code.used and code.used_by:
                user = get_user_by_id(self.db, code.used_by)
                if user:
                    used_by_email = user.email

            code_list.append({
                "id": code.id,
                "code": code.code,
                "count": code.count,
                "batch_id": code.batch_id,
                "used": code.used,
                "used_by": code.used_by,
                "used_by_email": used_by_email,
                "used_at": code.used_at,
                "expires_at": code.expires_at,
                "created_at": code.created_at,
            })

        return {
            "batch_id": batch_id,
            "description": codes[0].description if codes else None,
            "total_codes": total_codes,
            "used_codes": used_codes,
            "unused_codes": total_codes - used_codes,
            "total_count": total_count,
            "expires_at": codes[0].expires_at if codes else None,
            "created_at": codes[0].created_at if codes else None,
            "codes": code_list,
        }

    def export_codes(self, batch_id: str) -> dict:
        """
        导出兑换码

        Args:
            batch_id: 批次号

        Returns:
            dict: 导出结果
        """
        codes = self.db.query(RedemptionCode).filter(
            RedemptionCode.batch_id == batch_id
        ).all()

        if not codes:
            return {"success": False, "message": "批次不存在"}

        # 构建 CSV 数据
        csv_data = []
        for code in codes:
            used_by_email = None
            if code.used and code.used_by:
                user = get_user_by_id(self.db, code.used_by)
                if user:
                    used_by_email = user.email

            csv_data.append({
                "code": code.code,
                "count": code.count,
                "used": "已使用" if code.used else "未使用",
                "used_by": used_by_email or "",
                "used_at": code.used_at.strftime("%Y-%m-%d %H:%M") if code.used_at else "",
                "expires_at": code.expires_at.strftime("%Y-%m-%d") if code.expires_at else "",
                "created_at": code.created_at.strftime("%Y-%m-%d %H:%M") if code.created_at else "",
            })

        logger.info(f"导出兑换码: batch_id={batch_id}, count={len(codes)}")

        return {
            "success": True,
            "message": f"成功导出 {len(codes)} 个兑换码",
            "batch_id": batch_id,
            "codes": csv_data,
        }