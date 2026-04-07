#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
赏金猎人 (Bounty Hunter)
扫描多个平台寻找赚钱机会：
- V2EX 急单：筛选"有偿"、"求助"等关键词，按紧急程度打分
- HN Who is hiring：每月招聘帖解析科技/AI机会

v2.1 改造：报告按用户隔离，优先读取用户传入的 LLM Key
"""
import sys
import os
import argparse
import logging
import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.sensors.v2ex_radar import V2EXRadar
from src.sensors.hn_hiring_sensor import HNHiringSensor
from src.config import setup_logging
from src.defaults.prompts import get_default_bounty_keywords, DEFAULT_BOUNTY_REPORT_TEMPLATE

logger = logging.getLogger(__name__)

# 基础目录
BASE_DIR = Path(__file__).parent.resolve()


def get_user_report_dir() -> Path:
    """
    获取用户报告目录（按用户隔离）
    
    Returns:
        报告目录路径
    """
    user_id = os.getenv("USER_ID", "anonymous")
    return BASE_DIR / "reports" / f"user_{user_id}" / "tactical"


def get_user_llm_config() -> Dict:
    """
    获取 LLM 配置（优先用户传入，回退全局 .env）
    
    Returns:
        LLM 配置字典
    """
    return {
        'api_key': os.getenv("USER_LLM_API_KEY") or os.getenv("LLM_API_KEY", ""),
        'base_url': os.getenv("USER_LLM_BASE_URL") or os.getenv("LLM_BASE_URL", ""),
        'model': os.getenv("USER_LLM_MODEL") or os.getenv("LLM_MODEL", ""),
        'api_format': os.getenv("USER_LLM_API_FORMAT") or os.getenv("LLM_API_FORMAT", "openai"),
    }


def _get_bounty_keywords(user_id: Optional[int] = None) -> Dict:
    """
    获取赏金猎人关键词配置

    Args:
        user_id: 用户 ID（可选，用于读取用户自定义配置）

    Returns:
        关键词配置字典
    """
    # 默认关键词
    default_keywords = get_default_bounty_keywords()

    if not user_id:
        return default_keywords

    # 尝试读取用户自定义配置
    try:
        from src.config_loader import get_user_prompt
        user_prompt = get_user_prompt(user_id, "bounty")

        if user_prompt:
            # 尝试从 prompt 中解析关键词
            import re
            keyword_match = re.search(r'关键词[：:]\s*([^\n]+)', user_prompt)
            if keyword_match:
                keywords_str = keyword_match.group(1)
                custom_keywords = {
                    'money_keywords': [k.strip() for k in keywords_str.split('、') if k.strip()]
                }
                logger.info(f"使用用户自定义关键词: {custom_keywords['money_keywords']}")
                # 合并用户关键词与默认关键词
                return {
                    'money_keywords': custom_keywords.get('money_keywords', default_keywords['money_keywords']),
                    'pain_keywords': default_keywords['pain_keywords'],
                    'desperation_keywords': default_keywords['desperation_keywords'],
                    'tech_keywords': default_keywords['tech_keywords'],
                }
    except Exception as e:
        logger.warning(f"读取用户配置失败，使用默认配置: {e}")

    return default_keywords


def _fetch_v2ex_leads(keywords_config: Dict, days: int) -> List[Any]:
    """
    抓取 V2EX 赏金机会

    Args:
        keywords_config: 关键词配置
        days: 扫描天数

    Returns:
        商机线索列表
    """
    logger.info("[Phase 1] 扫描 V2EX 急单...")
    logger.info(f"  关键词: {keywords_config['money_keywords'][:5]} 等")

    try:
        v2ex_radar = V2EXRadar(custom_keywords=keywords_config)
        leads = v2ex_radar.fetch_leads(days=days)
        logger.info(f"V2EX 获取成功: {len(leads)} 条")
        return leads
    except Exception as e:
        logger.error(f"V2EX 获取失败: {e}")
        return []


def _fetch_hn_hiring(limit: int = 30) -> List[Any]:
    """
    抓取 HN Who is hiring 招聘机会

    Args:
        limit: 返回数量限制

    Returns:
        招聘机会列表
    """
    logger.info("[Phase 2] 扫描 HN Who is hiring...")

    try:
        with HNHiringSensor() as sensor:
            opportunities = sensor.fetch_opportunities(limit=limit)
            logger.info(f"HN Hiring 获取成功: {len(opportunities)} 条")
            return opportunities
    except Exception as e:
        logger.error(f"HN Hiring 获取失败: {e}")
        return []


def _generate_v2ex_section(leads: List[Any], keywords_config: Dict) -> List[str]:
    """
    生成 V2EX 报告部分

    Args:
        leads: 商机线索列表
        keywords_config: 关键词配置

    Returns:
        Markdown 行列表
    """
    lines = []

    lines.append("## 💼 V2EX 赏金机会")
    lines.append(f"> 筛选关键词: {', '.join(keywords_config['money_keywords'][:6])}\n")

    if leads:
        for i, lead in enumerate(leads[:15], 1):
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

    return lines


def _generate_hn_section(opportunities: List[Any]) -> List[str]:
    """
    生成 HN Hiring 报告部分

    Args:
        opportunities: 招聘机会列表

    Returns:
        Markdown 行列表
    """
    lines = []

    lines.append("## 🏢 HN Who is hiring")
    lines.append("> Hacker News 每月招聘帖 - 科技/AI 行业精选\n")

    if opportunities:
        # 添加原帖信息
        if opportunities[0].source_post_title:
            lines.append(f"**原帖:** {opportunities[0].source_post_title}")
            lines.append(f"**HN 链接:** https://news.ycombinator.com/item?id={opportunities[0].source_post_id}")
            lines.append("")

        for i, opp in enumerate(opportunities[:20], 1):
            lines.append(f"### {i}. {opp.company}")
            lines.append(f"**职位:** {opp.position}")
            lines.append(f"**地点:** {opp.location}")
            if opp.tags:
                lines.append(f"**标签:** {', '.join(opp.tags[:5])}")
            if opp.url:
                lines.append(f"**链接:** {opp.url}")
            lines.append(f"> {opp.description[:100]}...")
            lines.append("")
    else:
        lines.append("*暂无符合条件的招聘机会*")
        lines.append("")
        lines.append("> 💡 **诊断建议:**")
        lines.append("> - HN 招聘帖数据可能未更新，请稍后重试")
        lines.append("> - 可手动访问 [HN Who is hiring](https://news.ycombinator.com) 查看")
        lines.append("")

    return lines


def _generate_action_plan(v2ex_leads: List[Any], hn_opps: List[Any]) -> List[str]:
    """
    生成行动计划建议

    Args:
        v2ex_leads: V2EX 商机
        hn_opps: HN 招聘机会

    Returns:
        Markdown 行列表
    """
    lines = []

    lines.append("---")
    lines.append("")
    lines.append("## 🎯 行动计划建议")
    lines.append("")

    # V2EX 行动建议
    lines.append("### 针对 V2EX 急单")
    if v2ex_leads:
        top_lead = v2ex_leads[0]
        lines.append(f"1. **优先联系** [{top_lead.title}]({top_lead.url}) (评分: {top_lead.desperation_score})")
        lines.append("2. 准备你的作品集/简历链接，V2EX 用户喜欢直接了当")
        lines.append("3. 报价时预留 20% 议价空间")
    else:
        lines.append("- 暂无高优先级机会，建议明天再查看")
    lines.append("")

    # HN Hiring 行动建议
    lines.append("### 针对 HN 招聘")
    if hn_opps:
        # 统计热门技术标签
        all_tags = []
        for opp in hn_opps:
            all_tags.extend(opp.tags)
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        lines.append("1. **热门技术方向:** " + ", ".join([f"{t[0]}({t[1]})" for t in top_tags]))
        lines.append("2. 优先投递 Remote 职位，竞争相对较小")
        lines.append("3. 在评论区留下你的作品集链接，增加曝光")
    else:
        lines.append("- 暂无招聘数据，建议手动访问 HN 查看")
    lines.append("")

    return lines


def _generate_ai_analysis(report_content: str, user_prompt: str) -> str:
    """
    调用 LLM 生成深度分析

    Args:
        report_content: 报告内容
        user_prompt: 用户自定义 Prompt

    Returns:
        AI 分析内容
    """
    from llm_client import chat
    from src.defaults.prompts import get_default_prompt

    # 优先读取用户传入的 LLM 配置
    llm_config = get_user_llm_config()
    if not llm_config['api_key']:
        logger.warning("LLM API Key 未配置，跳过 AI 分析")
        return ""

    # 获取默认分析 prompt
    default_analysis_prompt = get_default_prompt("bounty_analysis") or ""

    # 构建完整 prompt
    system_prompt = f"""你是一位资深的自由职业顾问和技术外包专家。

{default_analysis_prompt}

用户的个性化分析需求：
{user_prompt}"""

    user_message = f"""以下是赏金猎人报告的完整内容，请根据系统指令和个性化需求进行分析：

{report_content}"""

    try:
        logger.info(f"调用 LLM 生成深度分析: model={llm_config['model']}")
        result = chat(
            prompt=user_message,
            system=system_prompt,
            base_url=llm_config['base_url'],
            api_key=llm_config['api_key'],
            model=llm_config['model'],
            api_format=llm_config['api_format'],
            temperature=0.7,
            max_tokens=2048,
            timeout=180,
        )
        if result:
            logger.info(f"AI 分析生成成功，长度: {len(result)}")
            return result
        else:
            logger.warning("LLM 返回空结果")
            return ""
    except Exception as e:
        logger.error(f"AI 分析生成失败: {e}")
        return ""


def generate_bounty_report(days: int = 1, user_id: Optional[int] = None):
    """
    扫描赏金机会并生成报告。

    Args:
        days: 扫描天数
        user_id: 用户ID，用于读取用户自定义配置。为None时使用默认配置。
    """
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.datetime.now().strftime("%H:%M")

    print("=" * 60)
    print("  💰 BOUNTY HUNTER - 赏金猎人")
    print("=" * 60)
    print(f"\n开始扫描赏金机会... 日期: {date_str}")

    # 获取用户报告目录（按用户隔离）
    report_dir = get_user_report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"Bounty_Hunter_{date_str}.md"

    # 获取关键词配置
    keywords_config = _get_bounty_keywords(user_id)

    # 获取用户自定义 Prompt（用于 AI 分析）
    user_prompt = ""
    if user_id:
        try:
            from src.config_loader import get_user_prompt
            user_prompt = get_user_prompt(user_id, "bounty")
        except Exception as e:
            logger.warning(f"读取用户 Prompt 失败: {e}")

    # 1. 抓取数据
    v2ex_leads = _fetch_v2ex_leads(keywords_config, days)
    hn_opps = _fetch_hn_hiring(limit=30)

    # 2. 生成执行摘要
    summary_lines = [
        f"- **V2EX 机会:** {len(v2ex_leads)} 个潜在急单",
        f"- **HN 招聘:** {len(hn_opps)} 个科技/AI 职位",
    ]
    summary = "\n".join(summary_lines)

    # 3. 生成报告内容
    content_parts = []

    # V2EX 部分
    content_parts.extend(_generate_v2ex_section(v2ex_leads, keywords_config))

    # 分隔符
    content_parts.extend(["---", "", ""])

    # HN Hiring 部分
    content_parts.extend(_generate_hn_section(hn_opps))

    # 行动计划
    content_parts.extend(_generate_action_plan(v2ex_leads, hn_opps))

    # 4. 使用模板构建完整报告
    content = "\n".join(content_parts)

    report_body = DEFAULT_BOUNTY_REPORT_TEMPLATE.format(
        date_str=date_str,
        days=days,
        time_str=time_str,
        summary=summary,
        content=content,
    )

    # 5. 如果有用户自定义 Prompt，追加 AI 深度分析
    if user_prompt:
        ai_analysis = _generate_ai_analysis(report_body, user_prompt)
        if ai_analysis:
            report_body += "\n\n---\n\n## 🔮 深度洞察\n\n" + ai_analysis

    # 6. 保存报告
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_body)

    logger.info(f"赏金猎人报告已生成: {report_file}")
    print(f"\n✅ 报告已保存: {report_file}")
    print(f"   V2EX 机会: {len(v2ex_leads)}")
    print(f"   HN 招聘: {len(hn_opps)}")

    return report_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="赏金猎人 - 扫描多平台寻找赚钱机会")
    parser.add_argument("days", nargs="?", type=int, default=1, help="扫描天数 (默认: 1)")
    parser.add_argument("--user-id", type=int, default=None, help="用户ID，用于读取用户自定义配置")
    args = parser.parse_args()

    generate_bounty_report(days=args.days, user_id=args.user_id)