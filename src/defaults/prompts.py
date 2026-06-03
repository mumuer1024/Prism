# -*- coding: utf-8 -*-
"""
默认 Prompt 配置

存储各功能模块的默认 Prompt 模板
"""

from typing import Optional, Dict

# ============================================================================
# 情报日报 (Mission) - 报告生成模板
# ============================================================================
DEFAULT_MISSION_PROMPT = """# 🌐 全球情报日报 (Global Intel Briefing)
**日期:** {date_str}
**生成时间:** {time_str}
**数据源:** HN, GitHub, 36Kr, WallStreetCN, V2EX, PH, ArXiv, X

---

## 🛠️ 技术趋势 (Tech Trends)
> Hacker News + GitHub Trending

## 💰 资本动向 (Capital Flow)
> 36Kr + 华尔街见闻（AI/科技领域精选）

## 📚 学术前沿 (Research)
> ArXiv AI/ML Papers

## 💎 产品精选 (Product Gems)
> Product Hunt Today

## 🐦 社交热议 (Social)
> X (Twitter) - AI/Tech Discussions

## 🗣️ 社区热点 (Community)
> V2EX 热门

## 💡 深度洞察 (Insights)
> HN Top Blogs - 精选技术博客

---
> 🤖 **本文由 AI 生成，仅供参考。** 内容可能存在偏差，不代表原文观点，不构成任何投资或决策建议。
*报告由 Unified Intelligence Engine V2 自动生成*
"""

# ============================================================================
# 情报日报 (Mission) - AI 深度分析默认 Prompt
# ============================================================================
DEFAULT_MISSION_ANALYSIS_PROMPT = """请基于以上情报日报内容，从商业机会和行业趋势角度提供深度洞察。

要求：
1. 提供 3-5 条核心洞察，每条洞察包含：
   - 洞察标题（简洁有力）
   - 背景分析（为什么会发生）
   - 行动建议（具体可执行）

2. 重点关注：
   - 新兴技术趋势的变现潜力
   - 市场空白和用户痛点
   - 可在 1-2 周内启动的小而快机会

3. 输出风格：
   - 专业但易懂
   - 避免泛泛而谈，给出具体建议
   - 适合技术从业者阅读

请直接输出分析内容，不需要重复报告内容。"""

# ============================================================================
# 赏金猎人 (Bounty Hunter) - 关键词配置
# ============================================================================
DEFAULT_BOUNTY_KEYWORDS = {
    "money_keywords": [
        "外包", "兼职", "有偿", "预算", "报价", "招", "急", "付费",
        "代写", "私活", "合作", "开发", "求购", "悬赏", "报酬",
        "价格", "费用", "多少钱", "收费", "接单", "项目", "甲方"
    ],
    "pain_keywords": [
        "求助", "帮忙", "不懂", "救命", "怎么做", "太难", "崩溃", "无法", "报错",
        "不会", "求教", "求大佬", "有没有人", "小白", "新手", "搞不定",
        "折腾", "卡住", "解决不了", "求指导", "求解答", "头疼"
    ],
    "desperation_keywords": [
        "在线等", "有偿", "急", "救命", "红包", "崩溃", "求大佬", "付费解决",
        "今晚", "明天", "截止", "最后", "加急", "马上", "立刻", "紧急",
        "求求", "跪求", "在线等", "速回"
    ],
    "tech_keywords": [
        "FPGA", "Verilog", "Python", "爬虫", "脚本", "Web3", "Solana",
        "Rust", "图像", "视觉", "识别", "抠图", "Automation", "Bot",
        "Vue", "React", "Node", "Java", "Go", "TypeScript", "小程序",
        "App", "网站", "后端", "前端", "数据库", "API", "自动化",
        "Chrome", "插件", "扩展", "爬虫", "数据采集", "机器学习", "AI"
    ],
}

# ============================================================================
# 赏金猎人 (Bounty Hunter) - 分析 Prompt
# ============================================================================
DEFAULT_BOUNTY_ANALYSIS_PROMPT = """请基于以下赏金猎人报告内容，提供深度洞察和行动建议。

要求：
1. 分析当前商机机会的特点：
   - 技术领域分布（前端/后端/AI/Web3等）
   - 预估价格区间（基于帖子描述）
   - 紧急程度排序建议

2. 提供具体行动建议：
   - 如何快速验证需求真实性
   - 如何准备简历/作品集
   - 如何报价和议价技巧

3. 重点关注科技/AI行业需求信号：
   - AI 相关外包需求趋势
   - Web3/区块链开发机会
   - 自动化工具需求
   - 移动端/小程序需求

请直接输出分析内容，简洁有力，避免泛泛而谈。"""

# ============================================================================
# 赏金猎人 (Bounty Hunter) - 报告模板
# ============================================================================
DEFAULT_BOUNTY_REPORT_TEMPLATE = """# 💰 赏金猎人报告 (Bounty Hunter Report)
**日期:** {date_str}
**扫描范围:** 过去 {days} 天
**生成时间:** {time_str}

---

## 🎯 执行摘要

{summary}

---

{content}

---

> 🤖 **本文由 AI 生成，仅供参考。** 内容可能存在偏差，不构成任何投资或决策建议。
*报告由赏金猎人系统自动生成*
"""

# ============================================================================
# Alpha 雷达 - Grok 搜索 Prompt
# ============================================================================
DEFAULT_ALPHA_PROMPT = """Search X (Twitter) and find the latest open source projects related to: {query}.

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

# Alpha 雷达专用搜索查询
ALPHA_QUERIES = [
    "Solana CLI tools open source 2025 2026",
    "Web3 developer tools CLI GitHub",
    "crypto trading bot open source",
    "blockchain automation scripts",
    "DeFi tools CLI open source",
]

# ============================================================================
# 营收分析师 - 分析 Prompt
# ============================================================================
DEFAULT_REVENUE_PROMPT = """你是一位资深的商业分析师和独立开发者导师。请仔细阅读以下情报日报内容，并从中挖掘出具体的商业和个人品牌机会。

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

# ============================================================================
# 工具类型枚举
# ============================================================================
TOOL_TYPES = [
    "mission",           # 情报日报
    "mission_analysis",  # 情报日报 - AI 分析
    "bounty",            # 赏金猎人
    "bounty_analysis",   # 赏金猎人 - AI 分析
    "alpha",             # Alpha 雷达
    "revenue",           # 营收分析师
]


def get_default_prompt(tool_type: str) -> Optional[str]:
    """
    获取指定工具类型的默认 Prompt

    Args:
        tool_type: 工具类型 (mission / mission_analysis / bounty / bounty_analysis / alpha / revenue)

    Returns:
        默认 Prompt 字符串，如果类型无效则返回 None
    """
    prompts = {
        "mission": DEFAULT_MISSION_PROMPT,
        "mission_analysis": DEFAULT_MISSION_ANALYSIS_PROMPT,
        "bounty": DEFAULT_BOUNTY_ANALYSIS_PROMPT,
        "bounty_analysis": DEFAULT_BOUNTY_ANALYSIS_PROMPT,
        "alpha": DEFAULT_ALPHA_PROMPT,
        "revenue": DEFAULT_REVENUE_PROMPT,
    }
    return prompts.get(tool_type)


def get_default_bounty_keywords() -> Dict:
    """
    获取赏金猎人的默认关键词配置

    Returns:
        关键词配置字典
    """
    return DEFAULT_BOUNTY_KEYWORDS.copy()


def get_tool_display_name(tool_type: str) -> str:
    """
    获取工具类型的显示名称

    Args:
        tool_type: 工具类型

    Returns:
        显示名称
    """
    names = {
        "mission": "情报日报",
        "mission_analysis": "情报日报 - AI分析",
        "bounty": "赏金猎人",
        "bounty_analysis": "赏金猎人 - AI分析",
        "alpha": "Alpha雷达",
        "revenue": "营收分析师",
    }
    return names.get(tool_type, tool_type)