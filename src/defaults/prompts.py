# -*- coding: utf-8 -*-
"""
默认 Prompt 配置

存储各功能模块的默认 Prompt 模板
"""

from typing import Optional

# ============================================================================
# 情报日报 (Mission) - 报告生成模板
# ============================================================================
DEFAULT_MISSION_PROMPT = """# 🌐 全球情报日报 (Global Intel Briefing)
**日期:** {date_str}
**生成时间:** {time_str}
**数据源:** HN, GitHub, 36Kr, WallStreetCN, V2EX, PH, ArXiv, X, XHS

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

## 📕 小红书雷达 (XHS Radar)
> 手动搜索指令 (点击链接进入搜索页)

## 💡 深度洞察 (Insights)
> HN Top Blogs - 精选技术博客

---
> 🤖 **本文由 AI 生成，仅供参考。** 内容可能存在偏差，不代表原文观点，不构成任何投资或决策建议。
*报告由 Unified Intelligence Engine V2 自动生成*
"""

# ============================================================================
# 赏金猎人 - V2EX 扫描 Prompt
# ============================================================================
DEFAULT_BOUNTY_V2EX_PROMPT = """筛选 V2EX 论坛中的赚钱机会。

关键词匹配规则：
- 必须包含：有偿、外包、兼职、求助、急、付费、悬赏 等关键词
- 排除：纯技术讨论、招聘正式员工

紧急程度评分标准：
- 90-100分：明确标价 + 时间紧迫 + 需求清晰
- 70-89分：有偿意向 + 需求较清晰
- 50-69分：可能付费 + 需求模糊
- 0-49分：潜在机会

输出格式：
- 标题
- 链接
- 紧急程度评分
- 标签分类
- 发布时间
- 摘要
"""

# ============================================================================
# 赏金猎人 - Chrome 扩展扫描 Prompt
# ============================================================================
DEFAULT_BOUNTY_CHROME_PROMPT = """扫描 Chrome 扩展商店，寻找"丑小鸭"机会。

筛选条件：
- 用户量 >= 1000
- 评分 <= 4.2
- 有明显痛点可优化

机会评估标准：
- 用户量大但评分低 = 重写竞品机会
- 功能单一但需求明确 = 快速复制机会
- 界面老旧但用户多 = UI优化机会

输出格式：
- 扩展名称
- 链接
- 评分
- 用户量
- 描述
- 痛点分析（kill_shot）
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
    "mission",        # 情报日报
    "bounty_v2ex",    # 赏金猎人 - V2EX
    "bounty_chrome",  # 赏金猎人 - Chrome
    "alpha",          # Alpha 雷达
    "revenue",        # 营收分析师
]


def get_default_prompt(tool_type: str) -> Optional[str]:
    """
    获取指定工具类型的默认 Prompt

    Args:
        tool_type: 工具类型 (mission / bounty_v2ex / bounty_chrome / alpha / revenue)

    Returns:
        默认 Prompt 字符串，如果类型无效则返回 None
    """
    prompts = {
        "mission": DEFAULT_MISSION_PROMPT,
        "bounty_v2ex": DEFAULT_BOUNTY_V2EX_PROMPT,
        "bounty_chrome": DEFAULT_BOUNTY_CHROME_PROMPT,
        "alpha": DEFAULT_ALPHA_PROMPT,
        "revenue": DEFAULT_REVENUE_PROMPT,
    }
    return prompts.get(tool_type)


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
        "bounty_v2ex": "赏金猎人 - V2EX",
        "bounty_chrome": "赏金猎人 - Chrome扩展",
        "alpha": "Alpha雷达",
        "revenue": "营收分析师",
    }
    return names.get(tool_type, tool_type)