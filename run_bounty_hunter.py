#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
赏金猎人 (Bounty Hunter)
扫描 V2EX 和 Chrome 扩展商店，寻找赚钱机会：
- V2EX 急单：筛选"有偿"、"求助"等关键词，按紧急程度打分
- Chrome 扩展机会：找到"用户多但评分差"的扩展（适合重写竞品）
"""
import sys
import os
import argparse
import logging
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.sensors.v2ex_radar import V2EXRadar
from src.sensors.chrome_radar import ChromeRadar
from src.config import setup_logging

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "tactical")


def generate_bounty_report(days: int = 1):
    """
    扫描赏金机会并生成报告。
    """
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print("  💰 BOUNTY HUNTER - 赏金猎人")
    print("=" * 60)
    print(f"\n开始扫描赏金机会... 日期: {date_str}")

    os.makedirs(REPORT_DIR, exist_ok=True)
    report_file = os.path.join(REPORT_DIR, f"Bounty_Hunter_{date_str}.md")

    # 1. 扫描 V2EX 机会
    logger.info("[Phase 1] 扫描 V2EX 急单...")
    logger.info("  关键词: 外包/兼职/有偿/求助/急 等")
    v2ex_radar = V2EXRadar()
    v2ex_leads = v2ex_radar.fetch_leads(days=days)

    # 2. 扫描 Chrome 扩展商店
    logger.info("[Phase 2] 扫描 Chrome 扩展商店...")
    chrome_radar = ChromeRadar()
    chrome_opps = chrome_radar.scan_opportunities(limit=5)

    # 3. 生成报告
    lines = [
        f"# 💰 赏金猎人报告 (Bounty Hunter Report)",
        f"**日期:** {date_str}",
        f"**扫描范围:** 过去 {days} 天",
        f"**生成时间:** {datetime.datetime.now().strftime('%H:%M')}",
        "",
        "---",
        "",
        "## 🎯 执行摘要",
        "",
        f"- **V2EX 机会:** {len(v2ex_leads)} 个潜在急单",
        f"- **Chrome 扩展机会:** {len(chrome_opps)} 个'Ugly Cash Cows'",
        "",
        "---",
        "",
    ]

    # V2EX 部分
    lines.append("## 💼 V2EX 赏金机会")
    lines.append("> 筛选关键词: 有偿、外包、急、求助、付费\n")

    if v2ex_leads:
        for i, lead in enumerate(v2ex_leads[:15], 1):
            lines.append(f"### {i}. [{lead.title}]({lead.url})")
            lines.append(f"**紧急程度评分:** {lead.desperation_score}/100")
            lines.append(f"**标签:** {', '.join(lead.tags)}")
            lines.append(f"**发布时间:** {lead.posted_date}")
            lines.append(f"> {lead.summary[:150]}...")
            lines.append("")
    else:
        lines.append("*暂无符合条件的赏金机会*")
        lines.append("")
        lines.append("> 💡 **诊断建议:**")
        lines.append("> - V2EX RSS 源可能暂时无数据，建议稍后重试")
        lines.append("> - 检查网络是否能正常访问 v2ex.com")
        lines.append("> - 尝试增加扫描天数: `python run_bounty_hunter.py 3`")
        lines.append("")

    # Chrome 扩展部分
    lines.append("---")
    lines.append("")
    lines.append("## 🛒 Chrome 扩展'丑小鸭'机会")
    lines.append("> 筛选条件: 用户 >= 1000 + 评分 <= 4.2\n")
    lines.append("这些扩展用户多但满意度低，是重写竞品的绝佳机会。\n")

    if chrome_opps:
        for i, opp in enumerate(chrome_opps, 1):
            lines.append(f"### {i}. [{opp.name}]({opp.url})")
            lines.append(f"**评分:** {opp.rating} ⭐")
            lines.append(f"**用户量:** {opp.user_count_str} 用户")
            lines.append(f"> {opp.description}")
            if opp.kill_shot:
                lines.append(f"**痛点分析:** {opp.kill_shot}")
            lines.append("")
    else:
        lines.append("*未找到符合条件的 Chrome 扩展机会*")
        lines.append("")
        lines.append("> 💡 **诊断建议:**")
        lines.append("> - Chrome Web Store 页面可能需要动态渲染（静态爬虫无法获取数据）")
        lines.append("> - 建议使用 Playwright/Selenium 等浏览器自动化工具")
        lines.append("> - 可手动访问 [Chrome Web Store](https://chromewebstore.google.com) 查找机会")
        lines.append("")

    # 行动计划
    lines.append("---")
    lines.append("")
    lines.append("## 🎯 行动计划建议")
    lines.append("")
    lines.append("### 针对 V2EX 机会")
    if v2ex_leads:
        top_lead = v2ex_leads[0]
        lines.append(f"1. **优先联系** [{top_lead.title}]({top_lead.url}) (评分: {top_lead.desperation_score})")
        lines.append("2. 准备你的作品集/简历链接，V2EX 用户喜欢直接了当")
        lines.append("3. 报价时预留 20% 议价空间")
    else:
        lines.append("- 暂无高优先级机会，建议明天再查看")

    lines.append("")
    lines.append("### 针对 Chrome 扩展")
    if chrome_opps:
        lines.append("1. 访问差评最多的扩展页面，记录用户抱怨的具体功能")
        lines.append("2. 在 Product Hunt 或 GitHub 发布'更优雅'的替代方案")
        lines.append("3. 考虑开源策略 + 付费高级功能")
    else:
        lines.append("- 建议扩展扫描到其他品类（如 SEO 工具、社交媒体助手）")

    lines.append("")
    lines.append("---")
    lines.append("*报告由赏金猎人系统自动生成*")

    # 保存报告
    final_content = "\n".join(lines)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"赏金猎人报告已生成: {report_file}")
    print(f"\n✅ 报告已保存: {report_file}")
    print(f"   V2EX 机会: {len(v2ex_leads)}")
    print(f"   Chrome 扩展机会: {len(chrome_opps)}")

    return report_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="赏金猎人 - 扫描 V2EX 和 Chrome 扩展商店寻找机会")
    parser.add_argument("days", nargs="?", type=int, default=1, help="扫描天数 (默认: 1)")
    args = parser.parse_args()

    generate_bounty_report(days=args.days)