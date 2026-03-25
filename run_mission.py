import sys
import os
import argparse
import logging
import datetime
from typing import Optional

from src.intel_collector import fetch_all_sources
from src.report_generator import generate_report
from src.config import setup_logging

logger = logging.getLogger(__name__)

# Configuration
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "daily_briefings")


def generate_morning_report(days: int = 1, user_id: Optional[int] = None):
    """
    Orchestrate the collection of intelligence using Unified Engine V2.
    Supports Daily (days=1) or Weekly/Custom (days>1) briefings.

    Args:
        days: 分析天数
        user_id: 用户ID，用于读取用户自定义配置。为None时使用默认配置。
    """
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 读取用户配置（如果有 user_id）
    user_prompt = None
    user_sources = None
    dailyhot_categories = None
    if user_id:
        try:
            from src.config_loader import get_user_prompt, get_user_sources, get_user_dailyhot_categories
            user_prompt = get_user_prompt(user_id, "mission")
            user_sources = get_user_sources(user_id, "mission")
            dailyhot_categories = get_user_dailyhot_categories(user_id)
            logger.info(f"使用用户配置: user_id={user_id}, custom_sources={len(user_sources) if user_sources else 0}, dailyhot_categories={dailyhot_categories}")
        except Exception as e:
            logger.warning(f"读取用户配置失败，使用默认配置: {e}")

    if days == 1:
        report_title = f"每日商业情报简报: {date_str}"
        file_name = f"Morning_Report_{date_str}.md"
        limit = 15
    else:
        report_title = f"周期性情报简报 (过去 {days} 天): {date_str}"
        file_name = f"Weekly_Report_{days}Days_{date_str}.md"
        limit = 30

    report_file = os.path.join(REPORT_DIR, file_name)
    os.makedirs(REPORT_DIR, exist_ok=True)

    logger.info(f"开始生成情报简报 (Unified V2) - 周期: {days} 天, 目标: {file_name}")

    # 1. Fetch from all sources (parallelized)
    # 注意：当前版本暂不支持用户自定义数据源，使用默认数据源
    intel = fetch_all_sources(limit_per_source=limit)

    # 2. Fetch DailyHotApi data (热榜数据)
    dailyhot_data = _fetch_dailyhot_data(
        categories=dailyhot_categories,
        limit_per_platform=10,
        user_id=user_id,
    )
    if dailyhot_data:
        intel["dailyhot"] = dailyhot_data
        logger.info(f"DailyHotApi 数据已添加: {len(dailyhot_data)} 条")

    # 3. Generate Report
    body = generate_report(intel, date_str)

    # 如果有用户自定义 prompt，添加到报告开头作为说明
    prompt_note = ""
    if user_prompt:
        prompt_note = f"\n> ⚙️ **用户自定义配置已生效**\n> \n> {user_prompt[:200]}{'...' if len(user_prompt) > 200 else ''}\n"

    final_content = f"# {report_title}{prompt_note}\n\n" + body.replace("# 🌐 全球情报日报 (Global Intel Briefing)", "")

    # 4. Save
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"简报已生成: {report_file}")


def _fetch_dailyhot_data(
    categories: Optional[list] = None,
    limit_per_platform: int = 10,
    user_id: Optional[int] = None,
) -> list:
    """
    获取 DailyHotApi 热榜数据

    Args:
        categories: 分类列表，如 ["tech", "dev"]。为 None 时使用默认值。
        limit_per_platform: 每个平台的条目数量限制
        user_id: 用户 ID（用于日志）

    Returns:
        热榜数据列表，失败时返回空列表
    """
    # 默认分类
    if not categories:
        categories = ["tech", "dev"]

    try:
        from src.sensors.dailyhot_sensor import DailyHotSensor

        sensor = DailyHotSensor()
        items = sensor.fetch_by_categories(categories, limit_per_platform)

        # 转换为字典列表
        data = [item.to_dict() for item in items]

        logger.info(f"DailyHotApi 获取成功: {len(data)} 条, categories={categories}")
        return data

    except ImportError as e:
        logger.warning(f"DailyHotApi Sensor 模块未找到，跳过热榜数据: {e}")
        return []

    except Exception as e:
        # 静默降级：DailyHotApi 不可用时不中断主流程
        logger.warning(f"DailyHotApi 获取失败，静默降级: {e}")
        return []


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="生成商业情报简报 (Unified V2)")
    parser.add_argument("days", nargs="?", type=int, default=1, help="分析天数 (默认: 1)")
    parser.add_argument("--user-id", type=int, default=None, help="用户ID，用于读取用户自定义配置")
    args = parser.parse_args()

    generate_morning_report(days=args.days, user_id=args.user_id)