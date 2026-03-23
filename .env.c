# Intel Briefing - 环境变量配置示例
# 复制此文件为 .env 并填入你的实际值

# ═══════════════════════════════════════════════════════════
# 通用推理模型端点（营收分析 / 通用任务）
# 支持任意 OpenAI 兼容端点（NewAPI / OpenRouter / 官方等）
# ═══════════════════════════════════════════════════════════
LLM_API_FORMAT='openai'
LLM_BASE_URL='https://api.deepseek.com'
LLM_API_KEY='sk-384e2f9b3c4a44e8b7502f43ee9d3a0d'
LLM_MODEL='deepseek-reasoner'

# ═══════════════════════════════════════════════════════════
# X/Twitter 搜索端点（仅用于 Grok，必须 xAI 官方）
# 因为只有 Grok 能访问 X 实时数据，必须使用 xAI 官方 API
# ═══════════════════════════════════════════════════════════
XAI_API_FORMAT='openai'
XAI_BASE_URL='https://api.nicoblog.top/v1/chat/completions'
XAI_API_KEY='sk-nadaeKjQl0UnMklN3rqsf6wwdErRVGgGXG0GAwdaG4Evr3iu'
XAI_MODEL='AIGC2D-grok-4.2'

# ═══════════════════════════════════════════════════════════
# 翻译模型端点（ArXiv 摘要翻译 / 博客摘要）
# 支持 OpenAI 兼容 / Gemini 原生 / Claude 原生 三种格式
# ═══════════════════════════════════════════════════════════
TRANSLATOR_API_FORMAT='openai'
TRANSLATOR_BASE_URL='https://api.nicoblog.top/v1/chat/completions'
TRANSLATOR_API_KEY='sk-nadaeKjQl0UnMklN3rqsf6wwdErRVGgGXG0GAwdaG4Evr3iu'
TRANSLATOR_MODEL='deepseek-chat'

# 向后兼容：TRANSLATOR_API_KEY 也接受 GEMINI_API_KEY 作为 fallback
# GEMINI_API_KEY=your-gemini-api-key-here

# ═══════════════════════════════════════════════════════════
# 数据源 API Keys
# ═══════════════════════════════════════════════════════════

# GitHub Personal Access Token（必需，用于 GitHub Trending）
# 创建地址：https://github.com/settings/tokens
GITHUB_TOKEN='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'

# Product Hunt Token（可选，用于 Product Hunt 数据）
# 创建地址：https://www.producthunt.com/v2/oauth/applications
PRODUCTHUNT_TOKEN='qB4rpVSbKXZvLqxiz9zenFv8VE408HADaLoPwAzOUzM'

# ═══════════════════════════════════════════════════════════
# 数据源开关配置（可选，默认全部启用）
# 设置为 false 可禁用对应数据源
# ═══════════════════════════════════════════════════════════
SOURCE_ENABLED_HACKERNEWS=true
SOURCE_ENABLED_GITHUB_TRENDING=true
SOURCE_ENABLED_ARXIV=true
SOURCE_ENABLED_PRODUCTHUNT=true
SOURCE_ENABLED_V2EX=true
SOURCE_ENABLED_36KR=true
SOURCE_ENABLED_WALLSTREET=true
SOURCE_ENABLED_X_GROK=true
SOURCE_ENABLED_HN_BLOGS=true
SOURCE_ENABLED_CHROME=true
SOURCE_ENABLED_XHS=true

# ═══════════════════════════════════════════════════════════
# 代理配置（可选，用于中国大陆网络环境）
# ═══════════════════════════════════════════════════════════
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890
SOURCE_ENABLED_TAVILY='true'
TAVILY_TOKEN='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'
