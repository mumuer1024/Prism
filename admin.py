#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prism 管理工具
用于生成兑换码、管理用户等管理操作
"""

import sys
import os
import argparse
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import get_db_context
from src.database.crud import create_redemption_codes
from src.database.models import User, RedemptionCode


def generate_codes(count: int, uses_per_code: int, prefix: str = "PRISM-"):
    """
    生成兑换码
    
    Args:
        count: 生成数量
        uses_per_code: 每个兑换码的使用次数
        prefix: 兑换码前缀
    """
    import uuid
    from datetime import datetime, timedelta
    
    print(f"\n正在生成 {count} 个兑换码，每个可使用 {uses_per_code} 次...\n")
    
    with get_db_context() as db:
        try:
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            expires_at = datetime.utcnow() + timedelta(days=365)
            
            codes = create_redemption_codes(
                db=db,
                batch_id=batch_id,
                count_per_code=uses_per_code,
                num_codes=count,
                expires_at=expires_at,
            )
            
            print("生成成功！兑换码列表：")
            print("-" * 40)
            for code in codes:
                print(f"  {code.code}  ({code.count} 次)")
            print("-" * 40)
            print(f"共 {len(codes)} 个兑换码\n")
            
        except Exception as e:
            print(f"生成失败: {e}")


def list_codes(limit: int = 20, show_all: bool = False):
    """列出兑换码"""
    with get_db_context() as db:
        query = db.query(RedemptionCode).order_by(RedemptionCode.created_at.desc())
        
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
        print("-" * 90)
        print(f"{'兑换码':<20} {'次数':<6} {'状态':<8} {'使用者':<25} {'使用时间':<12}")
        print("-" * 90)
        
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
            
            print(f"{code.code:<20} {code.count:<6} {status:<8} {user_email:<25} {used_time:<12}")
        
        print("-" * 90)
        print()


def list_users(limit: int = 20):
    """列出用户"""
    with get_db_context() as db:
        users = db.query(User).order_by(User.created_at.desc()).limit(limit).all()
        
        if not users:
            print("\n暂无用户\n")
            return
        
        print(f"\n最近 {len(users)} 个用户：")
        print("-" * 80)
        print(f"{'ID':<6} {'邮箱':<25} {'次数':<8} {'邀请码':<18} {'注册时间':<12}")
        print("-" * 80)
        
        for user in users:
            created = user.created_at.strftime("%Y-%m-%d") if user.created_at else "-"
            print(f"{user.id:<6} {user.email:<25} {user.usage_count:<8} {user.invite_code or '-':<18} {created:<12}")
        
        print("-" * 80)
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Prism 管理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python admin.py generate-codes -n 5 -c 10    # 生成5个兑换码，每个10次
  python admin.py list-codes                   # 列出最近20个兑换码
  python admin.py list-codes --all             # 列出所有兑换码
  python admin.py list-users                   # 列出最近20个用户
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # generate-codes 命令
    gen_parser = subparsers.add_parser("generate-codes", help="生成兑换码")
    gen_parser.add_argument("-n", "--number", type=int, default=5, help="生成数量 (默认: 5)")
    gen_parser.add_argument("-c", "--count", type=int, default=10, help="每个兑换码的使用次数 (默认: 10)")
    gen_parser.add_argument("-p", "--prefix", type=str, default="PRISM-", help="兑换码前缀 (默认: PRISM-)")

    # list-codes 命令
    list_codes_parser = subparsers.add_parser("list-codes", help="列出兑换码")
    list_codes_parser.add_argument("-l", "--limit", type=int, default=20, help="显示数量 (默认: 20)")
    list_codes_parser.add_argument("--all", action="store_true", help="显示所有兑换码")

    # list-users 命令
    list_users_parser = subparsers.add_parser("list-users", help="列出用户")
    list_users_parser.add_argument("-l", "--limit", type=int, default=20, help="显示数量 (默认: 20)")

    args = parser.parse_args()

    if args.command == "generate-codes":
        generate_codes(args.number, args.count, args.prefix)
    elif args.command == "list-codes":
        list_codes(args.limit, show_all=getattr(args, 'all', False))
    elif args.command == "list-users":
        list_users(args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()