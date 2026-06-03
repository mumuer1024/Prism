**English** | **[中文](README_zh.md)**

<div align="center">

# 🕵️ Prism - AI Intelligence Aggregation System

**Your industry, your signal.**

AI-powered intelligence system that automatically collects, translates, and analyzes data from 13+ sources to generate Chinese daily briefings.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Version](https://img.shields.io/badge/Version-2.1.0-blue.svg)](https://github.com/mumuer1024/Prism)

</div>

---

## 🙏 Acknowledgements

This project is built on top of [77AutumN/Intel_Briefing](https://github.com/77AutumN/Intel_Briefing).

- **Original Author:** [@77AutumN](https://github.com/77AutumN)
- **Original Repository:** https://github.com/77AutumN/Intel_Briefing

Building on the original data collection core, this project adds Web UI, activation code system, three analysis tools (Bounty Hunter / Alpha Radar / Revenue Architect), data source management, and separated multi-LLM endpoint configuration.

Note: *Bounty Hunter, Alpha Radar, and Revenue Architect* were included in the original project but never published by the original author, so the author of these three tools is the current maintainer.

---

## 🤔 What Is This?

A **ready-to-use intelligence collection + analysis engine**. Think of it as an AI assistant that automatically "scrolls" through tech news across the web, then organizes it into a Chinese daily report.

> 💡 **Product Positioning:** This product only provides tool access. All AI features use API keys you provide directly — we don't proxy, store, or touch your API keys or AI request content.

**V2.1 Features:**
- ✅ Activation code system (replaces user registration)
- ✅ Device binding & usage quota management
- ✅ Referral code system with mutual rewards
- ✅ Anonymous visitor free tier (3 uses/day)
- ✅ Web UI with visual interface
- ✅ 4 analysis tools (Daily Briefing / Bounty Hunter / Alpha Radar / Revenue Architect)
- ✅ 13 data sources (individually toggleable, including Tavily AI Search)
- ✅ Multi-LLM endpoint configuration (general reasoning / X search / translation)
- ✅ Real-time streaming log output
- ✅ Online report browsing & download (Markdown/Word)
- ✅ Dark/Light theme toggle
- ✅ Privacy Policy / Terms of Service / Data Source Disclosure
- ✅ AI-generated content labeling (regulatory compliance)
- ✅ Admin dashboard (activation code management, audit logs)
- ✅ Prompt template marketplace
- ✅ Custom Prompt configuration
- ✅ Data source health monitoring
- ✅ Payment interface (reserved)

**Who is this for?**
- Users who want a quick daily overview of industry trends
- Product managers / content creators doing competitive analysis or industry research
- Indie developers / entrepreneurs looking for inspiration and opportunities

---

## ✨ Features

### 🎫 Activation Code System (V2.1)

| Feature | Description |
|:--|:--|
| 🔑 Code Activation | Activate with codes (PRISM-XXXX-XXXX-XXXX format) |
| 📱 Device Binding | Each code binds up to 3 devices |
| 💎 Quota Tiers | S=3, M=6, L=10, XL=20, XXL=50, XXXL=100 uses |
| 🤝 Referral Rewards | Referral codes (REF-XXXXXX) give +3 uses to both parties |
| 👻 Anonymous Access | Visitors get 3 free uses per day |

### 🔧 Admin Dashboard

| Feature | Description |
|:--|:--|
| 🎫 Activation Code Mgmt | Generate, view, export activation codes |
| 📝 Audit Logs | Admin operation tracking |
| 📊 Statistics | Usage and system metrics |

### 🏪 Prompt Template Marketplace

| Feature | Description |
|:--|:--|
| 📚 Official Templates | Preset prompts for each tool |
| 🔍 Browse & Filter | Filter templates by tool type |
| 📥 One-click Import | Import templates to personal config |
| ⭐ Featured | Highlighted popular templates |

### ✏️ Custom Prompts

| Feature | Description |
|:--|:--|
| 📝 Online Editor | Edit prompts in the Web UI |
| 📜 Version History | Track prompt changes |
| ↩️ Rollback | Revert to previous versions |
| ✅ Live Validation | Placeholder detection & syntax checking |
| 💡 Autocomplete | Suggest supported placeholders |

### 📡 Data Source Management

| Feature | Description |
|:--|:--|
| 🔌 Independent Toggles | 13 data sources individually controllable |
| 📊 Health Monitoring | Real-time source status checks |
| 🔄 V2EX Mirrors | Auto-failover across mirror sites |
| 📥 Custom Sources | Add custom RSS/webpage sources |
| ⚙️ DailyHot Config | Customizable hot-list categories |

### 📊 Daily Intelligence Briefing (`run_mission.py`)
Collects latest info from 10+ sources, generates a Chinese daily report with 8 sections:

| Section | Data Source | What You'll See |
|:--|:--|:--|
| 🛠️ Industry Trends | Hacker News, GitHub Trending | What leaders are talking about |
| 💰 Capital Moves | 36Kr, WallStreetCN | Funding rounds, M&A activity |
| 📚 Academic Frontier | ArXiv AI/ML | Latest papers with auto-translated abstracts |
| 🚀 Product Picks | Product Hunt | New product launches |
| 💬 Community Buzz | V2EX | Chinese developer community discussions |
| 🐦 Social Sentiment | X (Twitter) via Grok | Trending industry topics on Twitter |
| 📖 Deep Insights | HN Top Blogs | Full-text analysis of popular blogs |
| 🔍 AI Search | Tavily | Real-time AI search with custom keywords |
| 🔗 Link Verification | Auto-check | Every link verified for validity |

### 💰 Bounty Hunter (`run_bounty_hunter.py`)
Scans market demand signals and discovers real opportunity gaps. Defaults to tracking V2EX urgent jobs and HN hiring trends.

### ⛏️ Alpha Radar (`run_alpha_radar.py`)
Searches X/Twitter via Grok for latest open-source projects, focusing on:
- Solana / Web3 CLI tools
- Open-source code with "wrap-and-monetize" potential
- Auto-verifies GitHub link validity (prevents AI hallucination)

### 🏗️ Revenue Architect (`run_revenue_architect.py`)
Reads the daily report, uses LLM to analyze 5 types of opportunities:

| Category | Description |
|:--|:--|
| 💰 Monetization | Projects/needs that can directly generate revenue |
| 🧠 Learning | Technologies worth deep study |
| ✍️ Content | Topics with high engagement potential |
| 📈 Growth | Trending topics to leverage for audience growth |
| 🤝 Credibility | Open-source projects where contributing builds reputation |

---

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/mumuer1024/Prism.git
cd Prism
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Keys

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 5. Start Web UI (Recommended)

```bash
python server.py
```

Then open http://localhost:8680 in your browser.

### 6. Or Run from Command Line

```bash
# 📊 Generate daily intelligence briefing
python run_mission.py

# 💰 Find bounty opportunities
python run_bounty_hunter.py

# ⛏️ Scan Web3 open-source tools
python run_alpha_radar.py

# 🏗️ Analyze opportunities and generate action plans
python run_revenue_architect.py
```

Reports are saved in the `reports/` directory.

### 7. Docker Deployment (Recommended for Production)

```bash
# 1. Copy config
cp .env.example .env
# Edit .env and fill in your API keys

# 2. Build and start
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop services
docker-compose down
```

Access at: http://localhost:8680

> 💡 **Tip:** Port can be changed via the `PORT` variable in `.env` (default: 8680)

---

## 🔌 API Documentation

After starting the server, visit:

- **Swagger UI**: http://localhost:8680/docs
- **ReDoc**: http://localhost:8680/redoc

### Key API Endpoints

| Module | Prefix | Description |
|:--|:--|:--|
| Activation | `/api/activation` | Code activation, device binding |
| Usage | `/api/usage` | Balance, permission check, consumption |
| User Config | `/api/user-config` | Prompt & source configuration |
| Marketplace | `/api/marketplace` | Template listing, import |
| Admin | `/api/admin` | Activation code mgmt, audit logs |
| Source Health | `/api/sources/health` | Data source status |
| Payment | `/api/payment` | Plans, orders, payment (reserved) |

---

## 🔑 API Key Requirements

| Key | Purpose | Required | Cost |
|:--|:--|:--|:--|
| `GITHUB_TOKEN` | GitHub Trending (GraphQL API) | **Yes** (minimum) | ✅ [Free PAT](https://github.com/settings/tokens) |
| `LLM_API_KEY` | General LLM reasoning | Recommended | Any OpenAI-compatible endpoint |
| `XAI_API_KEY` | Grok API (X/Twitter search) | Optional | ([Apply](https://console.x.ai/)) |
| `PRODUCTHUNT_TOKEN` | Product Hunt data | Optional | ✅ [Free](https://www.producthunt.com/v2/oauth/applications) |
| `TAVILY_TOKEN` | Tavily AI Search | Optional | ✅ [Free](https://tavily.com/) |
| `TRANSLATOR_API_KEY` | Chinese translation (Gemini/OpenAI) | Optional | ✅ Generous free tier |

> ⚠️ **Minimum requirement:** Get a `GITHUB_TOKEN` to run the basic daily briefing (HN, GitHub Trending, ArXiv, V2EX, 36Kr, etc.). Other keys are optional — skip the corresponding sources if not configured.

---

## 📁 Project Structure

```
Prism/
├── server.py                   # 🌐 Web UI entry (FastAPI)
├── ui/
│   ├── index.html              # Frontend page
│   └── static/                 # Static assets
├── run_mission.py              # 🎯 Daily Intelligence Briefing
├── run_bounty_hunter.py        # 💰 Bounty Hunter
├── run_alpha_radar.py          # ⛏️ Alpha Radar
├── run_revenue_architect.py    # 🏗️ Revenue Architect
├── llm_client.py               # Unified LLM client
├── config.py                   # Configuration module
├── fetch_unified_intel.py      # Unified intelligence collector
├── src/
│   ├── activation/             # Activation code module
│   ├── usage/                  # Usage tracking module
│   ├── admin/                  # Admin module
│   ├── marketplace/            # Prompt template marketplace
│   ├── config_router.py        # User config API
│   ├── database/               # Database (SQLite)
│   ├── sensors/                # Data source sensors
│   │   ├── arxiv_ai.py
│   │   ├── github_trending.py
│   │   ├── hacker_news.py
│   │   ├── product_hunt.py
│   │   ├── v2ex_radar.py
│   │   ├── x_grok_sensor.py
│   │   ├── tavily_search.py
│   │   ├── dailyhot_sensor.py
│   │   ├── custom_source.py
│   │   └── source_health.py
│   ├── defaults/               # Default configs
│   └── utils/                  # Utilities
├── tests/                      # 🧪 Tests
├── reports/                    # 📄 Generated reports
├── docs/                       # 📚 Documentation
├── .env.example                # API key template
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── LICENSE                     # GPL-3.0
```

---

## 🗺️ Roadmap

### V1.x ✅

- [x] **Web UI** — Modern design, dark mode, mobile-responsive
- [x] **API Configuration** — Key management, model testing, connectivity check
- [x] **Tavily Search** — Custom search keywords
- [x] **Report Management** — Categorize, search, batch download
- [x] **Docker Deployment** — One-click containerized deployment
- [x] **Legal Pages** — Privacy policy, terms, data source disclosure
- [x] **AI Content Labeling** — Mark all AI-generated content

### V2.0 ✅

- [x] **User System** — Registration, login, OAuth, password management
- [x] **Usage Quota System** — Paid quota, free tier, anonymous access
- [x] **Redemption Code System** — Activation codes, batch management, expiry
- [x] **Referral System** — Referral codes, rewards, first-use bonus
- [x] **Report Cache** — Caching for paid users
- [x] **Database Migration** — SQLite with version management

### V2.1 ✅

- [x] **Admin Dashboard** — User management, audit logs, statistics
- [x] **Batch Code Generation** — CLI tool, batch management, export
- [x] **Prompt Marketplace** — Official templates, one-click import
- [x] **Custom Prompts** — Online editor, version history, rollback
- [x] **Prompt Validation** — Placeholder detection, live validation, autocomplete
- [x] **Source Health Monitoring** — Real-time status, error tracking
- [x] **V2EX Mirror Support** — Auto-failover across mirrors
- [x] **Custom Data Sources** — RSS/webpage collectors
- [x] **Payment Interface (Reserved)** — Plan management, order system, channel abstraction

### V2.2 Planned

- [ ] **Payment Integration** — WeChat Pay / Alipay
- [ ] **Multi-language Support** — English UI

### V3.0 Vision

- [ ] Stay tuned

> 💡 **Product Positioning:** Prism only provides tool access. All AI features use API keys you provide directly.

---

## 🔧 Advanced Configuration

### Proxy / VPN

If you need a proxy to access external APIs:

```bash
export HTTP_PROXY=http://127.0.0.1:7890
export HTTPS_PROXY=http://127.0.0.1:7890
```

> [!IMPORTANT]
> `httpx` does not support SOCKS proxies by default. If your proxy only provides a SOCKS port:
> ```bash
> pip install httpx[socks]
> ```

### LLM Endpoint Separation

`.env` supports three independent LLM configurations:

```bash
# General LLM endpoint (reasoning tasks like revenue analysis)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_key
LLM_MODEL=gpt-4
LLM_API_FORMAT=openai  # openai | gemini | claude

# X/Twitter search (must be xAI official — only Grok can access X real-time data)
XAI_BASE_URL=https://api.x.ai/v1/chat/completions
XAI_API_KEY=your_xai_key
XAI_MODEL=grok-3

# Translation
TRANSLATOR_BASE_URL=https://generativelanguage.googleapis.com/v1beta
TRANSLATOR_API_KEY=your_gemini_key
TRANSLATOR_MODEL=gemini-1.5-flash
TRANSLATOR_API_FORMAT=gemini
```

### Activation Code System Configuration

```bash
# Admin credentials (default: admin/admin123)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

---

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_auth_unit.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

---

## ⚠️ Disclaimer

### AI-Generated Content

🤖 **This product uses AI to summarize, translate, and analyze public information. All AI-generated content is labeled accordingly, complying with China's "AI-Generated Synthetic Content Labeling Management Measures" (effective September 1, 2025).**

AI-generated content may contain hallucinations, inaccuracies, or outdated information. It is for reference only, does not represent the views of the original authors, and does not constitute investment, legal, or professional advice. Users should independently verify information accuracy and bear full responsibility for decisions made based on this product's content.

### API Key Security

- Your API keys are stored in your browser's localStorage and never uploaded to our servers
- AI requests are sent directly from your browser to your chosen AI service provider
- Keep your API keys secure and do not share them with others
- Data transmission between you and AI service providers follows that provider's privacy policy

---

## 📄 License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

### What You Can Do ✅

- **Free Use** — Personal, educational, or open-source projects
- **Modify & Distribute** — Modifications and distribution allowed, including commercial use
- **Patent License** — Receive patent license from contributors

### Obligations ⚠️

- **Open Source Requirement** — When distributing or providing network services, you must open-source your modifications under GPL-3.0
- **Preserve Copyright** — Must retain original author copyright notices
- **Same License** — Derivative works must use GPL-3.0 or a compatible license

### Original Project License

The original project [77AutumN/Intel_Briefing](https://github.com/77AutumN/Intel_Briefing) uses the MIT license. This project retains the MIT-licensed portions while new code uses GPL-3.0, distributed as a whole under GPL-3.0.

---

<div align="center">

**If you find this useful, a ⭐ is the best support.**

[Report Bug](https://github.com/mumuer1024/Prism/issues) · [Feature Request](https://github.com/mumuer1024/Prism/discussions)

</div>
