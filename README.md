<div align="center">

# 🕵️ Prism - 棱镜情报 - AI 情报聚合系统

**棱镜情报，Your industry, your signal.**

用 AI 自动从 10+ 数据源抓取、翻译、分析情报，生成一份中文日报。

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/Version-1.3.0-blue.svg)](https://github.com/mumuer1024/Prism)

</div>

---

## 🙏 鸣谢

本项目基于 [77AutumN/Intel_Briefing](https://github.com/77AutumN/Intel_Briefing) 进行二次开发。

- **原项目作者:** [@77AutumN](https://github.com/77AutumN)
- **原项目地址:** https://github.com/77AutumN/Intel_Briefing

在原项目的数据采集核心基础上，新增了 Web UI、赏金猎人/Alpha雷达/营收分析师三大工具、数据源管理、多 LLM 端点分离等功能。

备注说明：*赏金猎人/Alpha雷达/营收分析师* 这三个工具原项目自带但原作者并没有发布，所以本项目的这三个工具作者是我。

---

## 🤔 这是什么？

一个**开箱即用的情报采集+分析引擎**。你可以把它理解为：一个帮你自动"刷"全网科技新闻的 AI 助手，刷完以后还会帮你整理成中文报告。

> 💡 **产品定位**：本产品仅提供工具使用权，所有 AI 功能均由用户自备 API Key 直连调用，我们不代理、不存储、不触碰您的 API 密钥和 AI 请求内容。

**V1.3 版本已支持：**
- ✅ Web UI 可视化操作界面
- ✅ 4 大分析工具（日报/赏金猎人/Alpha雷达/营收分析师）
- ✅ 12 个数据源（可开关管理，含 Tavily AI 搜索）
- ✅ 多 LLM 端点配置（通用推理/X搜索/翻译分离）
- ✅ 实时日志流式输出
- ✅ 报告在线浏览与下载（Markdown/Word）
- ✅ 深色/浅色主题切换
- ✅ 隐私政策/用户协议/数据来源声明
- ✅ AI 生成内容标识（符合法规要求）

**适合谁用？**
- 想每天快速了解科技圈动态的开发者
- 做竞品分析、行业研究的产品经理
- 想找灵感和机会的独立开发者 / 创业者
- 任何对"信息不对称套利"感兴趣的人

---

## ✨ 功能特性

### 📊 情报日报 (`run_mission.py`)
从 10+ 数据源抓取最新信息，生成一份包含 8 大板块的中文日报：

| 板块 | 数据源 | 你能看到什么 |
|:--|:--|:--|
| 🛠️ 技术趋势 | Hacker News, GitHub Trending | 今天程序员们在聊什么 |
| 💰 资本动向 | 36Kr, WallStreetCN | 谁在融资、谁在并购 |
| 📚 学术前沿 | ArXiv AI/ML | 最新 AI 论文，自动翻译摘要 |
| 🚀 产品精选 | Product Hunt | 今天发布了什么新产品 |
| 💬 社区热议 | V2EX | 中文开发者社区在讨论什么 |
| 🐦 社交舆情 | X (Twitter) via Grok | Twitter 上的技术热话题 |
| 📖 深度洞察 | HN Top Blogs | 热门技术博客全文分析 |
| 🔍 AI 搜索 | Tavily | 基于自定义关键词的实时 AI 搜索 |
| 🔗 链接验证 | 自动核查 | 每个链接都经过有效性检测 |

### 💰 赏金猎人 (`run_bounty_hunter.py`)
自动扫描 V2EX 和 Chrome 扩展商店，寻找：
- **V2EX 急单** — 筛选"有偿"、"求助"等关键词，按紧急程度打分
- **Chrome 扩展机会** — 找到"用户多但评分差"的扩展（适合重写竞品）

### ⛏️ Alpha 雷达 (`run_alpha_radar.py`)
通过 Grok 搜索 X/Twitter 上最新的开源项目，专注于：
- Solana / Web3 领域的 CLI 工具
- 有"包装变现"潜力的开源代码
- 自动验证 GitHub 链接是否有效（防 AI 幻觉）

### 🏗️ 营收分析师 (`run_revenue_architect.py`)
读取日报内容，用 LLM 自动分析出 5 类机会：

| 类别 | 说明 |
|:--|:--|
| 💰 变现机会 | 能直接赚钱的项目/需求 |
| 🧠 学习机会 | 值得深入研究的技术 |
| ✍️ 创作机会 | 高互动潜力的内容选题 |
| 📈 涨粉机会 | 可以蹭热度的趋势话题 |
| 🤝 背书机会 | 参与贡献能建立信誉的开源项目 |

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/Intel_Briefing.git
cd Intel_Briefing
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

```bash
cp .env.example .env
# 编辑 .env，填入你自己的 API Key
```

### 4. 启动 Web UI（推荐）

```bash
python server.py
```

然后打开浏览器访问 http://localhost:8680

### 5. 或命令行运行

```bash
# 📊 生成情报日报
python run_mission.py

# 💰 寻找赏金机会
python run_bounty_hunter.py

# ⛏️ 扫描 Web3 开源工具
python run_alpha_radar.py

# 🏗️ 分析机会并生成行动计划
python run_revenue_architect.py
```

报告会保存在 `reports/` 目录下。

### 6. Docker 部署（推荐生产环境）

```bash
# 1. 复制配置文件
cp .env.example .env
# 编辑 .env，填入你自己的 API Key

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

访问地址：http://localhost:8680

**Docker 部署优势：**
- 环境隔离，无需配置 Python 环境
- 一键启动，自动安装所有依赖
- 数据持久化，容器重启数据不丢失

> 💡 **提示**：端口可通过 `.env` 中的 `PORT` 变量修改，默认 8680

---

## 🔑 API 密钥说明

| 密钥 | 用途 | 是否必需 | 费用 |
|:--|:--|:--|:--|
| `GITHUB_TOKEN` | GitHub Trending (GraphQL API) | **必需** | ✅ [免费申请 PAT](https://github.com/settings/tokens) |
| `LLM_API_KEY` | 通用 LLM 推理（营收分析等） | 推荐 | 使用任意 OpenAI 兼容端点 |
| `XAI_API_KEY` | Grok API (X/Twitter 搜索) | 可选 |  ([申请](https://console.x.ai/)) |
| `PRODUCTHUNT_TOKEN` | Product Hunt 数据 | 可选 | ✅ [免费申请](https://www.producthunt.com/v2/oauth/applications) |
| `TAVILY_TOKEN` | Tavily AI 搜索 | 可选 | ✅ [免费申请](https://tavily.com/) |
| `TRANSLATOR_API_KEY` | 中文翻译（Gemini/OpenAI） | 可选 | ✅ 免费额度充足 |

> ⚠️ **最低要求：拿到 `GITHUB_TOKEN` 就能跑基础日报**（HN、GitHub Trending、ArXiv、V2EX、36Kr 等）。其他密钥根据需求配置，没有则跳过对应数据源。

---

## 📁 项目结构

```
Intel_Briefing/
├── server.py                   # 🌐 Web UI 入口 (FastAPI)
├── ui/
│   ├── index.html              # 前端页面
│   └── static/                 # 静态资源
│       ├── style.css           # 样式表
│       ├── core.js             # 核心工具函数
│       ├── navigation.js       # 导航模块
│       ├── console.js          # 控制台模块
│       ├── sources.js          # 数据源管理模块
│       ├── config.js           # 配置管理模块
│       ├── reports.js          # 报告模块
│       └── legal.js            # 法律声明模块（隐私政策/用户协议/数据来源）
├── run_mission.py              # 🎯 情报日报
├── run_bounty_hunter.py        # 💰 赏金猎人
├── run_alpha_radar.py          # ⛏️ Alpha 雷达
├── run_revenue_architect.py    # 🏗️ 营收分析师
├── llm_client.py               # 统一 LLM 客户端
├── config.py                   # 配置模块
├── fetch_unified_intel.py      # 统一情报采集器
├── src/
│   ├── sensors/                # 数据源传感器
│   │   ├── arxiv_ai.py
│   │   ├── chrome_radar.py
│   │   ├── github_trending.py
│   │   ├── hacker_news.py
│   │   ├── hn_blogs.py
│   │   ├── product_hunt.py
│   │   ├── v2ex_radar.py
│   │   ├── x_grok_sensor.py
│   │   ├── xhs_radar.py
│   │   └── tavily_search.py    # Tavily AI 搜索
│   ├── generators/
│   ├── utils/
│   └── external/
├── reports/                    # 📄 生成的报告目录
│   ├── daily_briefings/        # 情报日报
│   ├── tactical/               # 赏金猎人报告
│   ├── web3/                   # Alpha 雷达报告
│   └── opportunities/          # 营收分析报告
├── .env.example                # API 密钥模板
├── requirements.txt
├── Dockerfile                  # Docker 镜像构建文件
├── docker-compose.yml          # Docker Compose 编排文件
└── .dockerignore               # Docker 构建排除文件
```

---

## 🎨 Web UI 功能

### 仪表盘
- 一键运行四大分析工具
- 实时查看日志输出
- 在线浏览生成的报告
- 深色/浅色主题切换
- 页脚版本号与作者署名

### 配置管理
- LLM 端点配置（通用推理/X搜索/翻译分离）
- API Key 管理（支持明文查看/隐藏）
- 模型列表自动拉取
- 模型连通性一键测试

### 数据源管理
- 12 个数据源独立开关（包括 Tavily AI 搜索）
- Tavily 搜索支持自定义关键词
- 显示数据源状态和 API Key 配置情况
- 持久化到 `.env` 文件

### 报告管理
- 报告分类浏览（日报/赏金猎人/Alpha雷达/营收分析）
- 关键词搜索过滤
- 批量下载为 Markdown/Word 格式

### 法律声明
- 隐私政策（用户数据保护说明）
- 用户协议（使用条款与免责声明）
- 数据来源（12 个数据源详情）
- AI 生成内容标识（符合法规要求）

---

## 🗺️ 路线图

### V1.1 优化（已完成）

- [x] **优化 WebUI 界面** — 现代化设计，深色模式配色优化，更好的移动端适配
- [x] **API 配置增强** —
  - API Key 明文查看/隐藏切换
  - 模型连通性一键测试
  - 拉取模型列表
- [x] **Tavily 搜索增强** — 支持自定义搜索关键词（前端存储）

### V1.2 优化（已完成）

- [x] **社交热议格式优化** — 统一 X/Twitter 板块输出格式，强制包含标题行和结构化事件列表
- [x] **营收分析师稳定性增强** — 
  - 增加超时重试机制（首次 300 秒，重试 420 秒）
  - 添加超时提示信息
- [x] **配置页面修复** — 添加全局"保存配置"按钮，修复配置无法保存的问题

### V1.3 已完成

- [x] **报告管理和下载** — 支持报告分类、搜索、批量下载为 Markdown/Word
- [x] **Docker 部署支持** — 提供 Dockerfile 和 docker-compose.yml，一键容器化部署
- [x] **法律声明页面** — 隐私政策、用户协议、数据来源声明
- [x] **AI 生成标识** — 所有 AI 输出内容添加「AI 生成」标记，符合法规要求
- [x] **页脚优化** — 版本号、作者署名、声明链接

### V1.4 计划中

- [ ] **自定义 Prompt** — 支持用户编辑各工具的 LLM Prompt
- [ ] **自定义数据源** — 支持用户新增数据源

### V2.0 愿景（规划中）

*预计发布时间：2026 Q4*

> 💡 **产品定位**：棱镜仅提供工具使用权，所有 AI 功能均由用户自备 API Key 直连调用。

#### 付费功能
- [ ] **目标领域及数据源预设广场** — 用户可以购买/订阅特定行业的数据源配置包
  - 例：Web3 赛道包、SaaS 创业包、AI 工具包
  - 一键导入 curated 数据源组合

- [ ] **Prompt 预设广场** — 专业分析师撰写的 Prompt 模板市场
  - 行业专属分析模板
  - 高级营收分析策略

#### 多用户支持
- [ ] **用户注册与登录** — 邮箱+密码+验证码 / 第三方 OAuth（GitHub/Google）
- [ ] **激活码系统** — 支持邀请码、优惠码、邀请返利
- [ ] **数据隔离** — 多租户架构，数据完全隔离
- [ ] **订阅功能** —
  - 免费版：基础数据源 + 每日 1 次运行（无需注册）
  - 专业版：全部数据源 + 无限制运行 + 高级报告
  - 团队版：多席位 + 协作功能
  - 买断版：完整功能部署包，客户自行部署

#### 数据安全
- [ ] **用户 API Key 本地存储** — 不上传服务器，用户直连 AI 服务商
- [ ] **数据自动清理** — 用户数据保留 30 天，到期自动清理
- [ ] **隐私合规** — 完善的隐私政策和用户协议

---

## 🔧 高级配置

### 代理 / VPN 配置

如果你需要通过代理访问外部 API，设置环境变量：

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

> [!IMPORTANT]
> `httpx` 默认不支持 SOCKS 代理。如果你的代理客户端只提供 SOCKS 端口，需要额外安装：
> ```bash
> pip install httpx[socks]
> ```

### LLM 端点分离配置

`.env` 支持三组独立的 LLM 配置：

```bash
# 通用 LLM 端点（营收分析等推理任务）
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_key
LLM_MODEL=gpt-4
LLM_API_FORMAT=openai  # openai | gemini | claude

# X/Twitter 搜索专用（必须 xAI 官方，只有 Grok 能访问 X 实时数据）
XAI_BASE_URL=https://api.x.ai/v1/chat/completions
XAI_API_KEY=your_xai_key
XAI_MODEL=grok-3

# 翻译专用
TRANSLATOR_BASE_URL=https://generativelanguage.googleapis.com/v1beta
TRANSLATOR_API_KEY=your_gemini_key
TRANSLATOR_MODEL=gemini-1.5-flash
TRANSLATOR_API_FORMAT=gemini
```

---

## ⚠️ 免责声明

### AI 生成内容

🤖 **本产品使用 AI 技术对公开资讯进行摘要、翻译和分析。所有 AI 生成的内容均标注「AI 生成」标识，符合《人工智能生成合成内容标识管理办法》（2025 年 9 月 1 日起施行）的要求。**

AI 生成内容可能存在"幻觉"、不准确或过时的情况，仅供参考，不代表原文观点，不构成任何投资、法律或专业决策建议。用户应自行核实信息的准确性，并对基于本产品内容所做的任何决策承担全部责任。

### API Key 安全

- 您的 API Key 存储在浏览器本地，不会上传至我们的服务器
- AI 请求由您的浏览器直接发送至您选择的 AI 服务商
- 请妥善保管您的 API Key，不要分享给他人
- 您与 AI 服务商之间的数据传输遵循该服务商的隐私政策

---

## 📄 License

本项目采用 [GNU General Public License v3.0](LICENSE) 开源协议。

### 你可以做什么 ✅

- **自由使用** — 个人或商业用途
- **修改分发** — 修改后可以分发，但必须开源
- **专利授权** — 获得贡献者的专利授权

### 义务 ⚠️

- **开源义务** — 如果你分发或提供网络服务，必须开源你的修改
- **保留版权声明** — 必须保留原作者版权声明
- **相同协议** — 衍生作品必须使用 GPL-3.0 或兼容协议

### 原项目协议

原项目 [77AutumN/Intel_Briefing](https://github.com/77AutumN/Intel_Briefing) 采用 MIT 协议。本项目在保留 MIT 部分的同时，新增代码采用 GPL-3.0，整体以 GPL-3.0 分发。

---

<div align="center">

**如果觉得有用，给个 ⭐ 就是最大的支持。**

[提交 Bug](https://github.com/mumuer1024/Prism/issues) · [功能建议](https://github.com/mumuer1024/Prism/discussions)

</div>
