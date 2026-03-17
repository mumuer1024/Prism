#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Alpha 雷达 (Alpha Radar)
通过 Grok 搜索 X/Twitter 上的最新开源项目，专注于：
- Solana / Web3 领域的 CLI 工具
- 有"包装变现"潜力的开源代码
- 自动验证 GitHub 链接是否有效
"""
import sys
import os
import argparse
import logging
import datetime
import re
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.sensors.x_grok_sensor import fetch_grok_intel
from src.utils.verifier import verify_link
from src.config import setup_logging

logger = logging.getLogger(__name__)

REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports", "web3")

# Alpha 雷达专用搜索查询
ALPHA_QUERIES = [
    "Solana CLI tools open source 2025 2026",
    "Web3 developer tools CLI GitHub",
    "crypto trading bot open source",
    "blockchain automation scripts",
    "DeFi tools CLI open source",
]


def extract_github_links(text: str) -> list:
    """从文本中提取 GitHub 链接"""
    pattern = r'https?://github\.com/[a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+'
    return list(set(re.findall(pattern, text)))


def parse_grok_projects(response: str) -> list:
    """
    解析 Grok 返回的内容，提取项目信息。
    尝试解析 JSON 格式或从文本中提取结构化信息。
    """
    projects = []

    # 尝试提取 JSON 数组
    try:
        # 寻找 JSON 代码块
        json_match = re.search(r'```json\s*(\[.*?\])\s*```', response, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            for item in data:
                projects.append({
                    "name": item.get("name", "Unknown"),
                    "description": item.get("description", ""),
                    "url": item.get("url", ""),
                    "github": item.get("github", ""),
                    "category": item.get("category", "General"),
                    "potential": item.get("potential", "Unknown"),
                })
            return projects
    except Exception as e:
        logger.debug(f"JSON parsing failed: {e}")

    # 从文本中提取项目信息
    lines = response.split('\n')
    current_project = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检测项目标题（通常以数字或特定符号开头）
        title_match = re.match(r'^[\d\*\-\•]+\.?\s*\*?\*?([^\*\n]+)\*?\*?', line)
        if title_match and len(line) < 100:
            if current_project:
                projects.append(current_project)
            current_project = {
                "name": title_match.group(1).strip(),
                "description": "",
                "url": "",
                "github": "",
                "category": "General",
                "potential": "",
            }
        elif current_project:
            # 检测 GitHub 链接
            github_links = extract_github_links(line)
            if github_links:
                current_project["github"] = github_links[0]

            # 检测一般 URL
            url_match = re.search(r'https?://[^\s\)]+', line)
            if url_match and not current_project["url"]:
                url = url_match.group(0).rstrip('.,;')
                if "github.com" not in url:
                    current_project["url"] = url

            # 累积描述
            if len(line) > 20 and "http" not in line:
                current_project["description"] += line + " "

    if current_project:
        projects.append(current_project)

    return projects


def verify_project_links(projects: list) -> list:
    """验证项目的 GitHub 链接是否有效"""
    logger.info("开始验证项目链接...")
    verified_projects = []

    for project in projects:
        github_url = project.get("github", "")
        if github_url:
            logger.info(f"  验证: {project['name']}")
            is_valid = verify_link(github_url, timeout=5.0)
            project["verified"] = is_valid
            if is_valid:
                logger.info(f"    ✅ 有效")
            else:
                logger.info(f"    ❌ 无效或无法访问")
        else:
            project["verified"] = None

        verified_projects.append(project)

    return verified_projects


def generate_alpha_radar_report():
    """
    扫描 Web3/Solana 开源项目并生成报告。
    """
    setup_logging()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    print("=" * 60)
    print("  ⛏️ ALPHA RADAR - Web3 开源项目雷达")
    print("=" * 60)
    print(f"\n开始扫描 Web3/Solana 开源项目... 日期: {date_str}")

    os.makedirs(REPORT_DIR, exist_ok=True)
    report_file = os.path.join(REPORT_DIR, f"Alpha_Radar_{date_str}.md")

    all_projects = []

    # 对每个查询使用 Grok 搜索
    for query in ALPHA_QUERIES:
        logger.info(f"[Grok] 搜索: {query}")

        prompt = f"""Search X (Twitter) and find the latest open source projects related to: {query}.

Find projects from 2025-2026 only. For each project, provide:
1. Project name
2. Brief description (what it does)
3. GitHub URL (if available)
4. Why it has monetization potential

Format your response as a structured list. Focus on CLI tools, developer tools, and automation scripts.

If possible, format as JSON:
```json
[
  {{
    "name": "Project Name",
    "description": "What it does",
    "github": "https://github.com/user/repo",
    "potential": "Why it can be monetized"
  }}
]
```"""

        try:
            response = fetch_grok_intel(query, override_prompt=prompt)
            projects = parse_grok_projects(response)
            logger.info(f"  找到 {len(projects)} 个项目")
            all_projects.extend(projects)
        except Exception as e:
            logger.error(f"搜索失败 ({query}): {e}")

    # 去重
    seen = set()
    unique_projects = []
    for p in all_projects:
        key = p.get("github") or p.get("name", "").lower()
        if key and key not in seen:
            seen.add(key)
            unique_projects.append(p)

    logger.info(f"去重后共 {len(unique_projects)} 个项目")

    # 验证 GitHub 链接
    if unique_projects:
        unique_projects = verify_project_links(unique_projects)

    # 分类项目
    solana_projects = [p for p in unique_projects if "solana" in p.get("description", "").lower() or "solana" in p.get("name", "").lower()]
    web3_projects = [p for p in unique_projects if any(kw in p.get("description", "").lower() for kw in ["web3", "ethereum", "defi", "blockchain", "crypto"])]
    cli_projects = [p for p in unique_projects if "cli" in p.get("description", "").lower() or "command" in p.get("description", "").lower()]
    other_projects = [p for p in unique_projects if p not in solana_projects and p not in web3_projects and p not in cli_projects]

    # 生成报告
    lines = [
        f"# ⛏️ Alpha 雷达报告 (Web3 开源项目扫描)",
        f"**日期:** {date_str}",
        f"**扫描时间:** {datetime.datetime.now().strftime('%H:%M')}",
        f"**数据来源:** X/Twitter via Grok",
        "",
        "---",
        "",
        "## 📊 扫描摘要",
        "",
        f"- **总项目数:** {len(unique_projects)}",
        f"- **Solana 生态:** {len(solana_projects)} 个项目",
        f"- **Web3/DeFi:** {len(web3_projects)} 个项目",
        f"- **CLI 工具:** {len(cli_projects)} 个项目",
        f"- **其他:** {len(other_projects)} 个项目",
        "",
        "> ⚠️ **注意:** 项目链接已自动验证，✅ 表示可访问，❌ 表示无效或无法验证",
        "",
        "---",
        "",
    ]

    # Solana 项目
    if solana_projects:
        lines.append("## 🔷 Solana 生态项目")
        lines.append("")
        for i, p in enumerate(solana_projects[:10], 1):
            verified_icon = "✅" if p.get("verified") else ("❌" if p.get("verified") == False else "⏸️")
            lines.append(f"### {i}. {verified_icon} {p['name']}")
            if p.get("github"):
                lines.append(f"**GitHub:** [{p['github']}]({p['github']})")
            if p.get("description"):
                lines.append(f"> {p['description'][:200]}...")
            if p.get("potential"):
                lines.append(f"**变现潜力:** {p['potential']}")
            lines.append("")

    # Web3 项目
    if web3_projects:
        lines.append("---")
        lines.append("")
        lines.append("## 🌐 Web3/DeFi 项目")
        lines.append("")
        for i, p in enumerate(web3_projects[:10], 1):
            verified_icon = "✅" if p.get("verified") else ("❌" if p.get("verified") == False else "⏸️")
            lines.append(f"### {i}. {verified_icon} {p['name']}")
            if p.get("github"):
                lines.append(f"**GitHub:** [{p['github']}]({p['github']})")
            if p.get("description"):
                lines.append(f"> {p['description'][:200]}...")
            if p.get("potential"):
                lines.append(f"**变现潜力:** {p['potential']}")
            lines.append("")

    # CLI 工具
    if cli_projects:
        lines.append("---")
        lines.append("")
        lines.append("## 🛠️ CLI 开发工具")
        lines.append("")
        for i, p in enumerate(cli_projects[:10], 1):
            verified_icon = "✅" if p.get("verified") else ("❌" if p.get("verified") == False else "⏸️")
            lines.append(f"### {i}. {verified_icon} {p['name']}")
            if p.get("github"):
                lines.append(f"**GitHub:** [{p['github']}]({p['github']})")
            if p.get("description"):
                lines.append(f"> {p['description'][:200]}...")
            lines.append("")

    # 其他项目
    if other_projects:
        lines.append("---")
        lines.append("")
        lines.append("## 📦 其他有趣项目")
        lines.append("")
        for i, p in enumerate(other_projects[:5], 1):
            verified_icon = "✅" if p.get("verified") else ("❌" if p.get("verified") == False else "⏸️")
            lines.append(f"### {i}. {verified_icon} {p['name']}")
            if p.get("github"):
                lines.append(f"**GitHub:** [{p['github']}]({p['github']})")
            if p.get("description"):
                lines.append(f"> {p['description'][:150]}...")
            lines.append("")

    # 变现建议
    lines.append("---")
    lines.append("")
    lines.append("## 💡 变现策略建议")
    lines.append("")
    lines.append("### 1. 包装变现 (Wrapper Monetization)")
    lines.append("- 找到热门的 CLI 工具，做一个更友好的 GUI 版本")
    lines.append("- 在 Product Hunt 发布，提供 SaaS 托管服务")
    lines.append("")
    lines.append("### 2. 扩展插件 (Plugin Ecosystem)")
    lines.append("- 为流行的开源工具开发付费插件")
    lines.append("- 提供高级功能或企业支持")
    lines.append("")
    lines.append("### 3. 教程/课程 (Education)")
    lines.append("- 为新工具创建教程、模板或最佳实践指南")
    lines.append("- 在 Gumroad 或 Lemon Squeezy 销售")
    lines.append("")
    lines.append("### 4. 托管服务 (Managed Service)")
    lines.append("- 为自托管工具提供一键部署服务")
    lines.append("- 面向非技术用户的简化方案")
    lines.append("")
    lines.append("---")
    lines.append("*报告由 Alpha 雷达系统自动生成*")

    # 保存报告
    final_content = "\n".join(lines)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(final_content)

    logger.info(f"Alpha 雷达报告已生成: {report_file}")
    print(f"\n✅ 报告已保存: {report_file}")
    print(f"   找到项目: {len(unique_projects)}")
    verified_count = sum(1 for p in unique_projects if p.get("verified"))
    print(f"   已验证: {verified_count}")

    return report_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Alpha 雷达 - 扫描 Web3/Solana 开源项目")
    args = parser.parse_args()

    generate_alpha_radar_report()
