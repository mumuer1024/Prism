# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Prism (棱镜情报) is an AI-powered intelligence aggregation system that collects, translates, and analyzes data from 13+ sources to generate Chinese daily briefings. Version 2.1 uses an activation code architecture instead of user registration.

## Common Commands

### Run Web UI (recommended)
```bash
python server.py
```
Access at http://localhost:8680. API docs at `/docs` (Swagger) and `/redoc`.

### Run CLI tools
```bash
python run_mission.py          # Daily intelligence briefing
python run_bounty_hunter.py    # V2EX/HN Hiring opportunity scanner
python run_alpha_radar.py      # Web3/Solana open-source tool scanner
python run_revenue_architect.py # Revenue opportunity analyzer
```

### Testing
```bash
python -m pytest tests/ -v                     # All tests
python -m pytest tests/test_auth_unit.py -v    # Single test file
python -m pytest tests/ --cov=src --cov-report=html  # With coverage
```

### Admin Dashboard (activation codes)
Access `/admin` in browser (default credentials: admin/admin123).
Generate activation codes via Web UI → "激活码管理" → "生成激活码".
Specify count and quota (S=3, M=6, L=10, XL=20, XXL=50, XXXL=100 uses).

Note: The legacy `admin.py` CLI is for the old user registration system and does not work with v2.1 activation code architecture.

### Docker deployment
```bash
docker-compose up -d    # Start
docker-compose logs -f  # View logs
docker-compose down     # Stop
```

## Architecture

### Backend (FastAPI)
- `server.py` - Main FastAPI application, registers all routers
- `src/activation/router.py` - Activation code authentication (v2.1)
- `src/usage/router.py` - Usage tracking and consumption
- `src/config_router.py` - User configuration (prompts, sources)
- `src/admin/router.py` - Admin dashboard APIs
- `src/marketplace/router.py` - Prompt template marketplace

### Activation Code System (v2.1)
- Users activate with codes (PRISM-XXXX-XXXX-XXXX format)
- Each code binds up to 3 devices (by device_id)
- Referral codes (REF-XXXXXX) give +3 uses to both parties on first consumption
- Anonymous visitors get 3 free uses per day

### Data Sources (src/sensors/)
Each sensor fetches from a specific source:
- `hacker_news.py` - HN frontpage/topstories
- `github_trending.py` - GitHub trending repos (requires GITHUB_TOKEN)
- `arxiv_ai.py` - ArXiv AI/ML papers
- `product_hunt.py` - New product launches
- `v2ex_radar.py` - V2EX community (with mirror support)
- `x_grok_sensor.py` - X/Twitter via Grok API (requires XAI_API_KEY)
- `dailyhot_sensor.py` - DailyHotApi aggregating multiple hot lists
- `custom_source.py` - User-defined RSS/webpage sources
- `source_health.py` - Health monitoring for all sources

### LLM Client
`llm_client.py` provides unified chat interface supporting three API formats:
- OpenAI-compatible (default)
- Gemini native API
- Claude native API

Key function: `chat(prompt, system, base_url, api_key, model, api_format, ...)`

### Configuration Flow
1. Frontend stores API keys in localStorage (BYOK - Bring Your Own Key)
2. Keys passed to backend via request params when running tasks
3. Backend passes to subprocess via environment variables (USER_* prefix)
4. Task scripts use user keys, fallback to global `.env` if not provided

### Report Isolation
Reports stored under `reports/{user_id}/`:
- Activated users: `reports/code_{activation_code_id}/`
- Anonymous users: `reports/anon_{visitor_id}/`

### Database (SQLite)
Models in `src/database/models.py`:
- `ActivationCode` - Codes, quota, remaining uses
- `Device` - Device bindings (max 3 per code)
- `ReferralCode` - Referral tracking and rewards
- `AnonymousUsage` - Daily free usage for visitors
- `AdminUser` - Admin accounts (default: admin/admin123)
- `UserPrompt`, `UserSource`, `UserConfig` - Per-user configurations
- `MarketplaceTemplate` - Official prompt templates

## Key Patterns

### Running Tasks with User Config
When `server.py` runs a script, it:
1. Checks usage permission via `UsageService.check_usage()`
2. Consumes quota via `UsageService.consume()`
3. Builds env vars with USER_* prefix for user's API keys
4. Passes USER_ID for report directory isolation

### LLM Endpoint Separation
Three independent LLM configurations:
- `LLM_*` - General reasoning (revenue analysis, etc.)
- `XAI_*` - X/Twitter search (must be xAI official for real-time X access)
- `TRANSLATOR_*` - Translation tasks

### Data Source Toggle
Sources controlled via `SOURCE_ENABLED_*` env vars (default: true).
Parsed by `_parse_bool()` in `config.py`.

### Prompt Validation
`src/utils/prompt_validator.py` validates custom prompts:
- Checks required placeholders: `{date}`, `{content}`, etc.
- Validates syntax and structure
- Provides autocomplete suggestions

## Important Files

- `.env` - Environment configuration (copy from `.env.example`)
- `config.py` - Global config loading from environment
- `src/defaults/prompts.py` - Default prompts for each tool
- `src/defaults/sources.py` - Default data source configurations
- `ui/static/*.js` - Frontend modules (core, navigation, console, sources, config, reports)

## API Key Requirements

| Key | Purpose | Required |
|-----|---------|----------|
| GITHUB_TOKEN | GitHub Trending | **Yes** (minimum) |
| LLM_API_KEY | General reasoning | Recommended |
| XAI_API_KEY | X/Twitter search | Optional |
| PRODUCTHUNT_TOKEN | Product Hunt | Optional |
| TAVILY_TOKEN | AI search | Optional |
| TRANSLATOR_API_KEY | Translation | Optional |

## Known Issues (v2.1)

- **Startup warnings**: Monitoring and Payment routers fail to load due to removed dependencies (`get_user_by_id`, `PaymentOrder`)
- **GitHub Token health check**: Source health monitoring may report false negatives for GitHub Token connectivity

### Fixed Issues ✅

- `/api/usage/balance` - Frontend API mismatch (GET → POST) ✅
- `/api/user-config/dailyhot/categories` - Frontend API mismatch ✅
- `/api/user-config/sources` - Frontend API mismatch ✅

See `docs/Prism_Project_Status.md` for detailed status tracking.

## Notes

- Windows requires `asyncio.WindowsProactorEventLoopPolicy` for subprocess support
- SELF_HOSTED env var controls whether `/api/config` returns/accepts server-side config
- All AI-generated content marked with "🤖 AI 生成" per Chinese regulations
# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
