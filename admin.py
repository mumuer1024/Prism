#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prism 管理工具
用于生成兑换码、管理用户、查看统计等管理操作
"""

import sys
import os
import argparse
import csv
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_db_context
from src.database.crud import create_redemption_codes
from src.database.models import User, RedemptionCode, TopupRecord, InviteRecord


def generate_codes(count: int, uses_per_code: int, expire_days: int = 365, note: str = None, export: str = None):
    """
    生成兑换码

    Args:
        count: 生成数量
        uses_per_code: 每个兑换码的使用次数
        expire_days: 有效期天数
        note: 备注
        export: 导出文件路径（可选）
    """
    import uuid

    print(f"\n正在生成 {count} 个兑换码，每个可使用 {uses_per_code} 次，有效期 {expire_days} 天...\n")

    with get_db_context() as db:
        try:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            expires_at = datetime.utcnow() + timedelta(days=expire_days)

            codes = create_redemption_codes(
                db=db,
                batch_id=batch_id,
                count_per_code=uses_per_code,
                num_codes=count,
                expires_at=expires_at,
                description=note,
            )

            print("生成成功！")
            print("-" * 50)
            print(f"批次号: {batch_id}")
            print(f"数量: {len(codes)} 个")
            print(f"每个次数: {uses_per_code} 次")
            print(f"过期时间: {expires_at.strftime('%Y-%m-%d %H:%M')}")
            print("-" * 50)
            print("\n兑换码列表：")
            for code in codes:
                print(f"  {code.code}")
            print("-" * 50)
            print(f"共 {len(codes)} 个兑换码\n")

            # 导出到文件
            if export:
                export_codes_to_file(codes, batch_id, export)

        except Exception as e:
            print(f"生成失败: {e}")


def export_codes_to_file(codes, batch_id: str, filepath: str):
    """
    导出兑换码到文件

    Args:
        codes: 兑换码列表
        batch_id: 批次号
        filepath: 文件路径
    """
    try:
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['兑换码', '次数', '批次号', '过期时间'])
            for code in codes:
                writer.writerow([
                    code.code,
                    code.count,
                    batch_id,
                    code.expires_at.strftime('%Y-%m-%d') if code.expires_at else ''
                ])
        print(f"已导出到文件: {filepath}\n")
    except Exception as e:
        print(f"导出失败: {e}")


def list_codes(limit: int = 20, show_all: bool = False, batch: str = None, export: str = None):
    """
    列出兑换码

    Args:
        limit: 显示数量
        show_all: 显示全部
        batch: 筛选批次号
        export: 导出文件路径
    """
    with get_db_context() as db:
        query = db.query(RedemptionCode).order_by(RedemptionCode.created_at.desc())

        if batch:
            query = query.filter(RedemptionCode.batch_id == batch)

        if not show_all:
            query = query.limit(limit)

        codes = query.all()

        if not codes:
            print("\n暂无兑换码\n")
            return

        # 统计
        total = len(codes)
        used = sum(1 for c in codes if c.used)
        unused = total - used

        print(f"\n兑换码列表 (共 {total} 个，已使用 {used} 个，未使用 {unused} 个)：")
        print("-" * 100)
        print(f"{'兑换码':<20} {'次数':<6} {'状态':<8} {'批次号':<25} {'使用者':<20} {'使用时间':<12}")
        print("-" * 100)

        for code in codes:
            status = "✓ 已使用" if code.used else "○ 未使用"

            # 获取使用者邮箱
            user_email = "-"
            if code.used and code.used_by:
                user = db.query(User).filter(User.id == code.used_by).first()
                if user:
                    user_email = user.email

            # 使用时间
            used_time = code.used_at.strftime("%Y-%m-%d %H:%M") if code.used_at else "-"

            # 批次号截断显示
            batch_display = code.batch_id[:22] + "..." if len(code.batch_id) > 25 else code.batch_id

            print(f"{code.code:<20} {code.count:<6} {status:<8} {batch_display:<25} {user_email:<20} {used_time:<12}")

        print("-" * 100)
        print()

        # 导出
        if export:
            export_codes_to_file(codes, batch or "all", export)


def list_batches():
    """列出所有批次"""
    with get_db_context() as db:
        from sqlalchemy import func

        batches = db.query(
            RedemptionCode.batch_id,
            func.count(RedemptionCode.id).label('total'),
            func.sum(RedemptionCode.count).label('total_count'),
            func.min(RedemptionCode.created_at).label('created_at'),
            func.max(RedemptionCode.expires_at).label('expires_at'),
        ).group_by(RedemptionCode.batch_id).order_by(RedemptionCode.created_at.desc()).all()

        if not batches:
            print("\n暂无批次\n")
            return

        print(f"\n批次列表 (共 {len(batches)} 个批次)：")
        print("-" * 90)
        print(f"{'批次号':<30} {'总数':<8} {'总次数':<10} {'创建时间':<12} {'过期时间':<12}")
        print("-" * 90)

        for batch in batches:
            created = batch.created_at.strftime("%Y-%m-%d") if batch.created_at else "-"
            expires = batch.expires_at.strftime("%Y-%m-%d") if batch.expires_at else "-"
            print(f"{batch.batch_id:<30} {batch.total:<8} {batch.total_count:<10} {created:<12} {expires:<12}")

        print("-" * 90)
        print()


def list_users(limit: int = 20, search: str = None, banned: bool = None):
    """
    列出用户

    Args:
        limit: 显示数量
        search: 搜索关键词
        banned: 筛选封禁状态
    """
    with get_db_context() as db:
        query = db.query(User).order_by(User.created_at.desc())

        if search:
            query = query.filter(
                (User.email.ilike(f"%{search}%")) |
                (User.nickname.ilike(f"%{search}%"))
            )

        if banned is not None:
            query = query.filter(User.is_banned == banned)

        users = query.limit(limit).all()

        if not users:
            print("\n暂无用户\n")
            return

        print(f"\n用户列表 (显示 {len(users)} 个)：")
        print("-" * 100)
        print(f"{'ID':<6} {'邮箱':<25} {'昵称':<12} {'次数':<8} {'状态':<8} {'邀请码':<18} {'注册时间':<12}")
        print("-" * 100)

        for user in users:
            created = user.created_at.strftime("%Y-%m-%d") if user.created_at else "-"
            status = "封禁" if user.is_banned else "正常"
            nickname = (user.nickname[:10] + "...") if user.nickname and len(user.nickname) > 12 else (user.nickname or "-")
            print(f"{user.id:<6} {user.email:<25} {nickname:<12} {user.usage_count:<8} {status:<8} {user.invite_code or '-':<18} {created:<12}")

        print("-" * 100)
        print()


def show_stats():
    """显示统计信息"""
    with get_db_context() as db:
        from sqlalchemy import func

        # 用户统计
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True, User.is_banned == False).count()
        banned_users = db.query(User).filter(User.is_banned == True).count()

        # 今日新增
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        new_today = db.query(User).filter(User.created_at >= today).count()

        # 充值统计
        topup_stats = db.query(
            func.sum(TopupRecord.count).label('total'),
            func.sum(TopupRecord.bonus_count).label('bonus')
        ).first()

        # 兑换码统计
        total_codes = db.query(RedemptionCode).count()
        used_codes = db.query(RedemptionCode).filter(RedemptionCode.used == True).count()

        # 邀请统计
        total_invites = db.query(InviteRecord).count()

        print("\n" + "=" * 50)
        print("📊 Prism 数据统计")
        print("=" * 50)
        print(f"\n👥 用户统计:")
        print(f"   总用户数: {total_users}")
        print(f"   活跃用户: {active_users}")
        print(f"   封禁用户: {banned_users}")
        print(f"   今日新增: {new_today}")

        print(f"\n💎 充值统计:")
        print(f"   总充值次数: {topup_stats.total or 0}")
        print(f"   总赠送次数: {topup_stats.bonus or 0}")

        print(f"\n🎫 兑换码统计:")
        print(f"   总兑换码: {total_codes}")
        print(f"   已使用: {used_codes}")
        print(f"   未使用: {total_codes - used_codes}")

        print(f"\n🤝 邀请统计:")
        print(f"   总邀请记录: {total_invites}")

        print("\n" + "=" * 50 + "\n")


def ban_user(user_id: int, reason: str = "违规操作"):
    """
    封禁用户

    Args:
        user_id: 用户 ID
        reason: 封禁原因
    """
    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"\n用户 {user_id} 不存在\n")
            return

        if user.is_banned:
            print(f"\n用户 {user.email} 已被封禁\n")
            return

        user.is_banned = True
        user.banned_at = datetime.utcnow()
        user.banned_reason = reason
        user.is_active = False
        db.commit()

        print(f"\n✓ 用户 {user.email} 已封禁")
        print(f"  原因: {reason}")
        print(f"  时间: {user.banned_at.strftime('%Y-%m-%d %H:%M')}\n")


def unban_user(user_id: int):
    """
    解禁用户

    Args:
        user_id: 用户 ID
    """
    with get_db_context() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"\n用户 {user_id} 不存在\n")
            return

        if not user.is_banned:
            print(f"\n用户 {user.email} 未被封禁\n")
            return

        user.is_banned = False
        user.banned_at = None
        user.banned_reason = None
        user.is_active = True
        db.commit()

        print(f"\n✓ 用户 {user.email} 已解禁\n")


def main():
    parser = argparse.ArgumentParser(
        description="Prism 管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python admin.py generate-codes -n 5 -c 10              # 生成5个兑换码，每个10次
  python admin.py generate-codes -n 10 -c 20 -e codes.csv # 生成并导出到CSV
  python admin.py list-codes                              # 列出最近20个兑换码
  python admin.py list-codes --all                        # 列出所有兑换码
  python admin.py list-codes -b batch_20240101_xxx        # 按批次筛选
  python admin.py list-batches                            # 列出所有批次
  python admin.py list-users                              # 列出最近20个用户
  python admin.py list-users -s test@example.com          # 搜索用户
  python admin.py stats                                   # 显示统计信息
  python admin.py ban 1 -r "违规操作"                      # 封禁用户
  python admin.py unban 1                                 # 解禁用户
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # generate-codes 命令
    gen_parser = subparsers.add_parser("generate-codes", help="生成兑换码")
    gen_parser.add_argument("-n", "--number", type=int, default=5, help="生成数量 (默认: 5)")
    gen_parser.add_argument("-c", "--count", type=int, default=10, help="每个兑换码的使用次数 (默认: 10)")
    gen_parser.add_argument("-e", "--expire", type=int, default=365, help="有效期天数 (默认: 365)")
    gen_parser.add_argument("--note", type=str, default=None, help="备注信息")
    gen_parser.add_argument("--export", type=str, default=None, help="导出到CSV文件")

    # list-codes 命令
    list_codes_parser = subparsers.add_parser("list-codes", help="列出兑换码")
    list_codes_parser.add_argument("-l", "--limit", type=int, default=20, help="显示数量 (默认: 20)")
    list_codes_parser.add_argument("--all", action="store_true", help="显示所有兑换码")
    list_codes_parser.add_argument("-b", "--batch", type=str, default=None, help="筛选批次号")
    list_codes_parser.add_argument("--export", type=str, default=None, help="导出到CSV文件")

    # list-batches 命令
    subparsers.add_parser("list-batches", help="列出所有批次")

    # list-users 命令
    list_users_parser = subparsers.add_parser("list-users", help="列出用户")
    list_users_parser.add_argument("-l", "--limit", type=int, default=20, help="显示数量 (默认: 20)")
    list_users_parser.add_argument("-s", "--search", type=str, default=None, help="搜索关键词")
    list_users_parser.add_argument("--banned", action="store_true", help="只显示封禁用户")
    list_users_parser.add_argument("--active", action="store_true", help="只显示正常用户")

    # stats 命令
    subparsers.add_parser("stats", help="显示统计信息")

    # ban 命令
    ban_parser = subparsers.add_parser("ban", help="封禁用户")
    ban_parser.add_argument("user_id", type=int, help="用户 ID")
    ban_parser.add_argument("-r", "--reason", type=str, default="违规操作", help="封禁原因")

    # unban 命令
    unban_parser = subparsers.add_parser("unban", help="解禁用户")
    unban_parser.add_argument("user_id", type=int, help="用户 ID")

    args = parser.parse_args()

    if args.command == "generate-codes":
        generate_codes(args.number, args.count, args.expire, args.note, args.export)
    elif args.command == "list-codes":
        list_codes(args.limit, show_all=getattr(args, 'all', False), batch=args.batch, export=args.export)
    elif args.command == "list-batches":
        list_batches()
    elif args.command == "list-users":
        banned = True if getattr(args, 'banned', False) else (False if getattr(args, 'active', False) else None)
        list_users(args.limit, args.search, banned)
    elif args.command == "stats":
        show_stats()
    elif args.command == "ban":
        ban_user(args.user_id, args.reason)
    elif args.command == "unban":
        unban_user(args.user_id)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()