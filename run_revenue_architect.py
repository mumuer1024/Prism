#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
营收分析师 (Revenue Architect)
读取日报内容，用 LLM 自动分析出 5 类机会：
- 💰 变现机会: 能直接赚钱的项目/需求
- 🧠 学习机会: 值得深入研究的技术
- ✍️ 创作机会: 高互动潜力的内容选题
- 📈 涨粉机会: 可以蹭热度的趋势话题
- 🤝 背书机会: 参与贡献能建立信誉的开源项目
"""
import sys
import os
import argparse
import logging
import datetime
import glob
import re

# Windows 控制台 UTF-8 支持
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.config import setup_logging

# 尝试使用 llm_client 进行 LLM 调用
try:
    from llm_client import chat, list_models
    LLM_CLIENT_AVAILABLE = True
except ImportError:
    LLM_CLIENT_AVAILABLE = False
    print("Warning: llm_client.py 不可用，将尝试直接导入 config")

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "opportunities")
DAILY_REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "daily_briefings")

# 营收分析专用 Prompt
REVENUE_ANALYSIS_PROMPT = """你是一位资深的商业分析师和独立开发者导师。请仔细阅读以下情报日报内容，并从中挖掘出具体的商业和个人品牌机会。

请将机会分为以下 5 个类别，每个类别至少提供 3 个具体的行动建议：

## 1. 💰 变现机会 (Monetization Opportunities)
能直接转化为收入的项目或需求：
- 急迫的付费需求（外包、工具、服务）
- 可重写的低评分高流量产品
- 可以快速开发的 MVP 机会

## 2. 🧠 学习机会 (Learning Opportunities)
值得投入时间深入研究的技术或领域：
- 新兴但尚未成熟的技术
- 高需求但人才稀缺的技能
- 可能在未来 6-12 个月爆发的新趋势

## 3. ✍️ 创作机会 (Content Opportunities)
高互动潜力的内容选题：
- 教程、案例分析、对比评测
- Twitter/X 帖子、博客文章、视频选题
- Newsletter 或社区讨论话题

## 4. 📈 涨粉机会 (Growth Opportunities)
可以蹭热度的趋势话题：
- 当前热议的技术或事件
- 有争议但值得参与讨论的观点
- 可以借势营销的产品发布时机

## 5. 🤝 背书机会 (Credibility Opportunities)
参与贡献能建立信誉的开源项目：
- 适合贡献代码的热门项目
- 可以通过文档、测试、Issue 回复参与的项目
- 能快速获得 visibility 的小型项目

---

**输出格式要求：**

对于每个类别，请按以下格式输出：

### [类别名称]

**1. [机会标题]**
- **描述:** [简要说明这个机会是什么]
- **行动:** [具体的第一步行动]
- **预期收益:** [潜在收益或效果]
- **难度:** [低/中/高]
- **时间投入:** [预计需要的时间]

请确保每个建议都是具体的、可执行的，而不是泛泛而谈。优先推荐那些可以在 1-2 周内启动的小而快的胜利。

---

**待分析的情报内容：**

{content}
"""


def find_latest_daily_report():
    """找到最近生成的日报文件"""
    report_pattern = os.path.join(DAILY_REPORT_DIR, "Morning_Report_*.md")
    reports = glob.glob(report_pattern)

    if not reports:
        # 也检查周报
        report_pattern = os.path.join(DAILY_REPORT_DIR, "Weekly_Report_*.md")
        reports = glob.glob(report_pattern)

    if not reports:
        return None

    # 按修改时间排序，取最新的
    reports.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return reports[0]


def read_report_content(report_path: str) -> str:
    """读取报告内容，提取关键部分"""
    with open(report_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 限制内容长度，避免超出 LLM 上下文（提升到 16000 以支持完整日报）
    max_chars = 16000
    if len(content) > max_chars:
        # 保留开头和各章节的关键部分
        lines = content.split('\n')
        truncated = []
        current_length = 0

        for line in lines:
            if current_length + len(line) > max_chars:
                break
            truncated.append(line)
            current_length += len(line) + 1

        content = '\n'.join(truncated)
        content += "\n\n[内容已截断，建议查看完整日报...]"

    return content


def call_llm_analysis(content: str) -> str:
    """调用 LLM 进行营收分析"""
    prompt = REVENUE_ANALYSIS_PROMPT.format(content=content)

    if LLM_CLIENT_AVAILABLE:
        try:
            # 尝试使用 llm_client
            import os
            from dotenv import load_dotenv
            load_dotenv()

            # 获取 LLM 配置
            base_url = os.getenv("LLM_BASE_URL", os.getenv("XAI_BASE_URL", ""))
            api_key = os.getenv("LLM_API_KEY", os.getenv("XAI_API_KEY", ""))
            model = os.getenv("LLM_MODEL", os.getenv("XAI_MODEL", "grok-beta"))
            api_format = os.getenv("LLM_API_FORMAT", "openai")

            if not api_key:
                return "错误: 未配置 LLM API Key。请设置 LLM_API_KEY 或 XAI_API_KEY。"

            logger.info(f"调用 LLM: {model}")
            
            # deepseek-reasoner 等推理模型需要更长时间
            timeout_seconds = 300  # 5分钟超时
            
            try:
                response = chat(
                    prompt=prompt,
                    system="你是一位资深的商业分析师和独立开发者导师。",
                    base_url=base_url,
                    api_key=api_key,
                    model=model,
                    api_format=api_format,
                    max_tokens=8192,  # 确保长报告不被截断
                    timeout=timeout_seconds
                )
                return response

            except Exception as timeout_error:
                # 检查是否是超时错误
                error_str = str(timeout_error).lower()
                if 'timeout' in error_str or '504' in error_str or 'timed out' in error_str:
                    print("⏳ 首次请求超时，正在重试（延长等待时间）...")
                    logger.warning(f"首次调用超时，尝试延长等待时间重试")
                    
                    # 第二次尝试，更长的超时时间
                    try:
                        response = chat(
                            prompt=prompt,
                            system="你是一位资深的商业分析师和独立开发者导师。",
                            base_url=base_url,
                            api_key=api_key,
                            model=model,
                            api_format=api_format,
                            max_tokens=8192,
                            timeout=420  # 7分钟
                        )
                        return response
                    except Exception as retry_error:
                        logger.error(f"重试也失败: {retry_error}")
                        return f"错误: 推理模型响应时间过长，建议使用普通模型或稍后重试。({retry_error})"
                else:
                    # 非超时错误直接返回
                    raise timeout_error

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            return f"错误: LLM 调用失败 - {str(e)}"
    else:
        return "错误: llm_client.py 不可用，无法进行 LLM 分析。"


def generate_revenue_architect_report(target_report: str = None):
    """
    分析日报内容并生成营收机会报告。
    """
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print("  🏗️ REVENUE ARCHITECT - 营收分析师")
    print("=" * 60)

    os.makedirs(REPORT_DIR, exist_ok=True)
    report_file = os.path.join(REPORT_DIR, f"Revenue_Analysis_{date_str}.md")

    # 1. 找到要分析的日报
    if target_report and os.path.exists(target_report):
        daily_report_path = target_report
    else:
        daily_report_path = find_latest_daily_report()

    if not daily_report_path:
        print("\n❌ 错误: 未找到可分析的日报文件。")
        print(f"   请先生成日报 (运行: python run_mission.py)")
        return None

    print(f"\n📄 分析报告: {os.path.basename(daily_report_path)}")

    # 2. 读取日报内容
    logger.info("读取日报内容...")
    content = read_report_content(daily_report_path)

    # 3. 调用 LLM 进行分析
    logger.info("调用 LLM 进行营收分析...")
    print("🤖 正在分析商业机会，请稍候...")

    analysis_result = call_llm_analysis(content)

    if analysis_result.startswith("错误:"):
        print(f"\n❌ {analysis_result}")
        return None

    # 4. 生成报告
    lines = [
        f"# 🏗️ 营收分析报告 (Revenue Architect)",
        f"**日期:** {date_str}",
        f"**来源报告:** {os.path.basename(daily_report_path)}",
        f"**分析时间:** {datetime.datetime.now().strftime('%H:%M')}",
        "",
        "---",
        "",
        "> 📌 **使用说明:** 本报告从情报日报中自动挖掘商业机会。建议优先关注标注为'难度: 低'且'时间投入: 短'的机会。",
        "",
        "---",
        "",
    ]

    lines.append(analysis_result)

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 🎯 下一步行动建议")
    lines.append("")
    lines.append("### 本周优先级 (Pick 3)")
    lines.append("从以上 5 个类别中，每类选择 1 个最吸引你的机会，本周内完成初步调研。")
    lines.append("")
    lines.append("### 快速验证清单")
    lines.append("- [ ] 这个机会解决的是真实存在的痛点吗？")
    lines.append("- [ ] 目标用户群体清晰吗？")
    lines.append("- [ ] 我能在 2 周内做出 MVP 吗？")
    lines.append("- [ ] 有没有现成的渠道可以推广？")
    lines.append("")
    lines.append("### 资源推荐")
    lines.append("- **快速建站:** Carrd.co, Webflow")
    lines.append("- **支付处理:** LemonSqueezy, Gumroad, Stripe")
    lines.append("- **用户获取:** Product Hunt, Twitter/X, Reddit")
    lines.append("- **学习资源:** IndieHackers, Starter Story")
    lines.append("")
    lines.append("---")
    lines.append("*报告由营收分析师系统自动生成*")

    # 保存报告
    final_content = "\n".join(lines)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"营收分析报告已生成: {report_file}")
    print(f"\n✅ 报告已保存: {report_file}")
    print(f"   分析报告来源: {os.path.basename(daily_report_path)}")

    return report_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="营收分析师 - 分析日报并挖掘商业机会")
    parser.add_argument("--report", "-r", type=str, help="指定要分析的日报文件路径")
    args = parser.parse_args()

    generate_revenue_architect_report(target_report=args.report)