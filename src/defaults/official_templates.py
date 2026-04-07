# -*- coding: utf-8 -*-
"""
官方预设模板种子数据

包含 11 个官方 Prompt 模板，覆盖 5 个工具类型
"""

# 官方模板数据
OFFICIAL_TEMPLATES = [
    # ==========================================
    # 情报日报模板 (mission) - 3 个
    # ==========================================
    {
        "title": "科技情报日报",
        "description": "专注于科技领域的情报日报模板，涵盖技术趋势、产品发布、学术前沿等板块。适合关注科技行业动态的用户。",
        "tool_type": "mission",
        "prompt_content": """# 🚀 科技情报日报 (Tech Intel Briefing)
**日期:** {date_str}
**生成时间:** {time_str}

---

## 🔥 今日热点 (Today's Highlights)
> 各平台最热门的科技话题

## 🛠️ 技术趋势 (Tech Trends)
> Hacker News + GitHub Trending

## 💎 产品发布 (New Products)
> Product Hunt Today - 最新产品

## 📚 学术前沿 (Research)
> ArXiv AI/ML Papers - 最新论文

## 🐦 社交热议 (Social)
> X (Twitter) - AI/Tech Discussions

## 💡 深度洞察 (Insights)
> HN Top Blogs - 技术博客精选

---
> 🤖 **本文由 AI 生成，仅供参考。**
*报告由 Prism Intelligence Engine 自动生成*
""",
        "tags": ["科技", "日报", "技术趋势", "AI"],
        "is_official": True,
        "is_published": True,
    },
    {
        "title": "商业情报日报",
        "description": "专注于商业和投资领域的情报日报模板，涵盖资本动向、市场机会、行业分析等板块。适合创业者和投资者。",
        "tool_type": "mission",
        "prompt_content": """# 💼 商业情报日报 (Business Intel Briefing)
**日期:** {date_str}
**生成时间:** {time_str}

---

## 💰 资本动向 (Capital Flow)
> 36Kr + 华尔街见闻 - 投融资动态

## 📈 市场机会 (Market Opportunities)
> 行业趋势 + 新兴赛道

## 🚀 创业动态 (Startup News)
> 新产品 + 新模式 + 新玩家

## 💡 商业洞察 (Business Insights)
> 成功案例 + 失败教训

## 🎯 竞品追踪 (Competitor Watch)
> 行业头部公司动态

---
> 🤖 **本文由 AI 生成，不构成投资建议。**
*报告由 Prism Intelligence Engine 自动生成*
""",
        "tags": ["商业", "投资", "创业", "市场分析"],
        "is_official": True,
        "is_published": True,
    },
    {
        "title": "开发者日报",
        "description": "专注于开发者领域的情报日报模板，涵盖开源项目、技术文章、工具推荐等板块。适合程序员和技术爱好者。",
        "tool_type": "mission",
        "prompt_content": """# 👨‍💻 开发者日报 (Developer Daily)
**日期:** {date_str}
**生成时间:** {time_str}

---

## 🔥 热门开源 (Trending Repos)
> GitHub Trending - 今日最火项目

## 📝 技术文章 (Tech Articles)
> HN Top Blogs + 技术博客精选

## 🛠️ 工具推荐 (Tool Picks)
> 开发者工具 + 效率神器

## 📚 学习资源 (Learning)
> 教程 + 课程 + 文档

## 🐛 坑点避雷 (Pitfalls)
> 常见问题 + 解决方案

## 💬 社区讨论 (Community)
> V2EX + 掘金热门话题

---
> 🤖 **本文由 AI 生成，供开发者参考。**
*报告由 Prism Intelligence Engine 自动生成*
""",
        "tags": ["开发者", "开源", "技术", "工具"],
        "is_official": True,
        "is_published": True,
    },

    # ==========================================
    # V2EX 赏金模板 (bounty_v2ex) - 2 个
    # ==========================================
    {
        "title": "技术外包机会扫描",
        "description": "专注于技术外包和开发需求的扫描模板，筛选有明确预算和需求的外包机会。",
        "tool_type": "bounty_v2ex",
        "prompt_content": """筛选 V2EX 论坛中的技术外包机会。

关键词匹配规则：
- 必须包含：外包、开发、预算、报价、项目、甲方 等关键词
- 技术栈：Python、JavaScript、Go、Java、React、Vue、Node.js 等
- 排除：纯技术讨论、招聘正式员工

紧急程度评分标准：
- 90-100分：明确预算 + 需求清晰 + 时间紧迫
- 70-89分：有预算意向 + 需求较清晰
- 50-69分：可能付费 + 需求模糊
- 0-49分：潜在机会

输出格式：
- 标题
- 链接
- 预算范围（如有）
- 技术栈要求
- 紧急程度评分
- 发布时间
- 需求摘要
""",
        "tags": ["外包", "技术", "开发", "项目"],
        "is_official": True,
        "is_published": True,
    },
    {
        "title": "设计兼职机会扫描",
        "description": "专注于设计和创意类兼职机会的扫描模板，筛选有明确需求的设计外包。",
        "tool_type": "bounty_v2ex",
        "prompt_content": """筛选 V2EX 论坛中的设计兼职机会。

关键词匹配规则：
- 必须包含：设计、UI、UX、Logo、海报、兼职、外包 等关键词
- 类型：UI设计、Logo设计、品牌设计、插画、动效 等
- 排除：纯技术讨论、招聘正式员工

紧急程度评分标准：
- 90-100分：明确预算 + 需求清晰 + 时间紧迫
- 70-89分：有预算意向 + 需求较清晰
- 50-69分：可能付费 + 需求模糊
- 0-49分：潜在机会

输出格式：
- 标题
- 链接
- 预算范围（如有）
- 设计类型
- 紧急程度评分
- 发布时间
- 需求摘要
""",
        "tags": ["设计", "兼职", "UI", "创意"],
        "is_official": True,
        "is_published": True,
    },

    # ==========================================
    # Alpha 雷达模板 (alpha) - 2 个
    # ==========================================
    {
        "title": "Web3 项目雷达",
        "description": "搜索 X/Twitter 上的 Web3 和区块链开源项目，发现早期投资或参与机会。",
        "tool_type": "alpha",
        "prompt_content": """Search X (Twitter) for the latest Web3 and blockchain open source projects related to: {query}.

Find projects from 2025-2026 only. Focus on:
- Solana ecosystem tools
- DeFi protocols and tools
- NFT and metaverse projects
- Crypto trading and analysis tools

For each project, provide:
1. Project name
2. Brief description (what it does)
3. GitHub URL (if available)
4. Token/TGE status
5. Why it has potential

Format your response as a structured list. Focus on CLI tools, developer tools, and automation scripts.

Output format:
```
## [Project Name]
- Description: ...
- GitHub: ...
- Token: Yes/No/Planned
- Potential: ...
- Action: ...
```
""",
        "tags": ["Web3", "区块链", "加密货币", "Solana"],
        "is_official": True,
        "is_published": True,
    },
    {
        "title": "AI 项目雷达",
        "description": "搜索 X/Twitter 上的 AI 和机器学习开源项目，发现可商业化机会。",
        "tool_type": "alpha",
        "prompt_content": """Search X (Twitter) for the latest AI and Machine Learning open source projects related to: {query}.

Find projects from 2025-2026 only. Focus on:
- LLM tools and frameworks
- AI agents and automation
- Computer vision applications
- NLP and text processing

For each project, provide:
1. Project name
2. Brief description (what it does)
3. GitHub URL (if available)
4. Stars/Forks count
5. Monetization potential

Format your response as a structured list. Focus on tools that can be:
- Wrapped as SaaS
- Used as API service
- Integrated into existing products

Output format:
```
## [Project Name]
- Description: ...
- GitHub: ...
- Stars: ...
- Potential: ...
- Monetization: ...
```
""",
        "tags": ["AI", "机器学习", "LLM", "自动化"],
        "is_official": True,
        "is_published": True,
    },

    # ==========================================
    # 营收分析模板 (revenue) - 2 个
    # ==========================================
    {
        "title": "SaaS 商业机会分析",
        "description": "从情报日报中挖掘 SaaS 产品机会，分析市场空白和竞争格局。",
        "tool_type": "revenue",
        "prompt_content": """你是一位资深的 SaaS 产品顾问。请分析以下情报内容，挖掘 SaaS 商业机会。

请重点关注：

## 1. 💰 SaaS 机会 (SaaS Opportunities)
- 可产品化的需求
- 市场空白点
- 竞品弱点

## 2. 🎯 目标用户 (Target Users)
- 谁会付费？
- 痛点有多痛？
- 付费意愿评估

## 3. 💵 定价建议 (Pricing Strategy)
- 免费版功能
- 付费版功能
- 定价区间建议

## 4. 🚀 MVP 建议 (MVP Roadmap)
- 第一版核心功能
- 2周可完成的功能
- 快速验证方案

## 5. ⚠️ 风险提示 (Risks)
- 竞争风险
- 技术风险
- 市场风险

---

**待分析内容：**

{content}
""",
        "tags": ["SaaS", "商业分析", "产品", "定价"],
        "is_official": True,
        "is_published": True,
    },
    {
        "title": "个人品牌机会分析",
        "description": "从情报日报中挖掘个人品牌建设机会，包括内容创作、涨粉策略等。",
        "tool_type": "revenue",
        "prompt_content": """你是一位资深的个人品牌顾问。请分析以下情报内容，挖掘个人品牌建设机会。

请重点关注：

## 1. ✍️ 内容选题 (Content Ideas)
- 高热度话题
- 可系列化的内容
- 差异化角度

## 2. 📈 涨粉机会 (Growth Opportunities)
- 可蹭的热点
- 跨平台分发策略
- 互动诱饵设计

## 3. 💰 变现路径 (Monetization Paths)
- 知识付费
- 广告合作
- 产品带货

## 4. 🤝 背书机会 (Credibility Building)
- 可参与的开源项目
- 可投稿的平台
- 可建立的合作

## 5. 📅 行动计划 (Action Plan)
- 本周可执行的任务
- 本月目标
- 季度规划

---

**待分析内容：**

{content}
""",
        "tags": ["个人品牌", "内容创作", "涨粉", "变现"],
        "is_official": True,
        "is_published": True,
    },
]


def get_official_templates():
    """获取官方模板列表"""
    return OFFICIAL_TEMPLATES


def get_templates_by_tool_type(tool_type: str):
    """按工具类型获取模板"""
    return [t for t in OFFICIAL_TEMPLATES if t["tool_type"] == tool_type]