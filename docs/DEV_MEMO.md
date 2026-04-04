# Prism 开发备忘录

> 创建时间：2026-04-04
> 基于项目实际进度分析生成

---

## 📊 项目整体进度

| 版本阶段 | 状态 | 完成度 |
|:--|:--|:--|
| **V1.x 基础功能** | ✅ 已完成 | 100% |
| **V2.0 用户系统** | ✅ 已完成 | 100% |
| **V2.1 商业化增强** | 🔄 进行中 | ~80% |
| **V3.0 高级功能** | 🔄 进行中 | ~40% |

> **商业模式**：次数购买制，支持兑换码充值，在线支付按需开发。

---

## ✅ 已完成功能清单

### V1.x 基础功能

| 功能模块 | 文件/目录 | 状态 |
|:--|:--|:--|
| 情报日报 | `run_mission.py` | ✅ |
| 赏金猎人 | `run_bounty_hunter.py` | ✅ |
| Alpha 雷达 | `run_alpha_radar.py` | ✅ |
| 营收分析师 | `run_revenue_architect.py` | ✅ |
| 统一情报采集器 | `fetch_unified_intel.py` | ✅ |
| LLM 客户端 | `llm_client.py` | ✅ |
| 配置模块 | `config.py` | ✅ |
| Web UI 入口 | `server.py` | ✅ |
| Docker 部署 | `Dockerfile`, `docker-compose.yml` | ✅ |

### 数据源传感器 (11个)

| 传感器 | 文件 | 状态 |
|:--|:--|:--|
| Hacker News | `src/sensors/hacker_news.py` | ✅ |
| GitHub Trending | `src/sensors/github_trending.py` | ✅ |
| ArXiv AI | `src/sensors/arxiv_ai.py` | ✅ |
| Product Hunt | `src/sensors/product_hunt.py` | ✅ |
| V2EX | `src/sensors/v2ex_radar.py` | ✅ |
| X/Twitter (Grok) | `src/sensors/x_grok_sensor.py` | ✅ |
| HN Blogs | `src/sensors/hn_blogs.py` | ✅ |
| Chrome 扩展 | `src/sensors/chrome_radar.py` | ✅ |
| 小红书 | `src/sensors/xhs_radar.py` | ✅ |
| DailyHot | `src/sensors/dailyhot_sensor.py` | ✅ |
| X Twitter | `src/sensors/x_twitter.py` | ✅ |

### V2.0 用户系统

| 里程碑 | 完成内容 | 状态 |
|:--|:--|:--|
| M1: 数据库与基础设施 | `src/database/` (connection.py, models.py, crud.py, migrations/) | ✅ |
| M2: 认证核心 | `src/auth/` (router.py, service.py, schemas.py, dependencies.py) | ✅ |
| M3: OAuth 登录 | `src/auth/oauth/` (github.py, wechat.py, state.py, exceptions.py) | ✅ |
| M4: 用户与兑换 | `src/user/` (router.py, service.py, schemas.py) | ✅ |
| M5: 免费用户系统 | `src/usage/` (router.py, service.py, schemas.py) | ✅ |
| M6: 前端页面 | `ui/` (login.html, register.html, account.html 等 6 个页面) | ✅ |
| M7: 测试与联调 | `tests/` (14 个测试文件) | ✅ |

### 前端 UI 模块

| 模块 | 文件 | 状态 |
|:--|:--|:--|
| 认证模块 | `ui/static/auth.js` | ✅ |
| 用户面板 | `ui/static/user-panel.js` | ✅ |
| 配置管理 | `ui/static/config.js` | ✅ |
| 数据源管理 | `ui/static/sources.js` | ✅ |
| 报告管理 | `ui/static/reports.js` | ✅ |
| 控制台 | `ui/static/console.js` | ✅ |
| 导航 | `ui/static/navigation.js` | ✅ |
| 法律声明 | `ui/static/legal.js` | ✅ |
| 预设广场 | `ui/static/marketplace.js` | ✅ |
| Prompt 配置 | `ui/static/prompt-config.js` | ✅ |

---

## 🔄 进行中功能

### V2.1 商业化增强

| 功能 | 实现状态 | 文件 | 备注 |
|:--|:--|:--|:--|
| 管理后台 | ✅ 已实现 | `src/admin/router.py` | 模板管理 CRUD 完成 |
| 预设广场 | ✅ 已实现 | `src/marketplace/` | 模板列表/详情/导入完成 |
| 兑换码充值 | ✅ 已实现 | `src/user/service.py` | 第三方平台购买兑换码充值次数 |
| 在线支付 | 📋 按需开发 | - | 微信/支付宝在线购买次数（可选） |

> **商业模式说明**：本项目采用**次数购买制**，不提供月度/年度订阅。用户通过第三方平台（如闲鱼）购买兑换码充值使用次数，后续可按需增加微信/支付宝在线支付功能。

**管理后台已实现功能：**
- 模板创建 (POST `/admin/marketplace/templates`)
- 模板编辑 (PUT `/admin/marketplace/templates/{id}`)
- 模板上架/下架 (PATCH `/admin/marketplace/templates/{id}/publish`)
- 模板删除 (DELETE `/admin/marketplace/templates/{id}`)
- 模板列表 (GET `/admin/marketplace/templates`)

**预设广场已实现功能：**
- 模板列表 (GET `/api/templates`)
- 模板详情 (GET `/api/templates/{id}`)
- 模板导入 (POST `/api/templates/{id}/import`)

### V3.0 高级功能

| 功能 | 实现状态 | 文件 | 备注 |
|:--|:--|:--|:--|
| 自定义 Prompt | 🔄 部分 | `ui/static/prompt-config.js` | 前端已有，后端待完善 |
| 自定义数据源 | 🔄 部分 | `ui/static/sources.js` | 前端已有，后端待完善 |
| 数据源预设广场 | ✅ 已实现 | `src/marketplace/` | 基础结构完成 |
| Prompt 预设广场 | ✅ 已实现 | `src/marketplace/` | 模板导入功能完成 |

---

## 📋 待开发功能

### 高优先级

| 功能 | 描述 | 预估工时 |
|:--|:--|:--|
| 用户管理后台 | 用户列表/封禁/统计 | 2-3 天 |
| 兑换码批量生成 | 管理员批量生成激活码 | 1-2 天 |
| 在线支付（可选） | 微信/支付宝在线购买次数 | 3-5 天 |

### 中优先级

| 功能 | 描述 | 预估工时 |
|:--|:--|:--|
| 自定义 Prompt 完善 | 后端保存/加载逻辑 | 1-2 天 |
| 自定义数据源完善 | 用户自定义 RSS/API | 2-3 天 |
| V2EX 扫描器优化 | 提高抓取成功率 | 1 天 |
| Grok 调用优化 | 减少舆情核查调用次数 | 1 天 |

### 低优先级

| 功能 | 描述 | 预估工时 |
|:--|:--|:--|
| 报告生成时间统计 | 显示各步骤耗时 | 0.5 天 |
| 增量报告功能 | 只显示新增内容 | 1-2 天 |
| 小红书关键词扩展 | 覆盖更多商机 | 0.5 天 |
| 团队协作功能 | 多用户共享报告 | 3-5 天 |

---

## 🧪 测试覆盖情况

| 模块 | 测试文件 | 覆盖度 |
|:--|:--|:--|
| 认证模块 | `test_auth_unit.py`, `test_auth_api.py` | ⭐⭐⭐⭐ 完善 |
| 用户模块 | `test_user_unit.py`, `test_user_api.py` | ⭐⭐⭐⭐ 完善 |
| 使用次数 | `test_usage_unit.py`, `test_usage_api.py` | ⭐⭐⭐⭐ 完善 |
| OAuth | `test_oauth_unit.py` | ⭐⭐⭐⭐ 完善 |
| 传感器 | `test_sensors.py`, `test_dailyhot_sensor.py` | ⭐⭐⭐ 基础 |
| 集成测试 | `test_integration.py` | ⭐⭐⭐ 基础 |
| 管理后台 | 无 | ⭐ 缺失 |
| 预设广场 | 无 | ⭐ 缺失 |

**待补充测试：**
- [ ] 管理后台 API 测试
- [ ] 预设广场 API 测试
- [ ] 传感器模块完善测试

---

## 📁 项目结构现状

```
Prism/
├── server.py                   # ✅ Web UI 入口
├── run_mission.py              # ✅ 情报日报
├── run_bounty_hunter.py        # ✅ 赏金猎人
├── run_alpha_radar.py          # ✅ Alpha 雷达
├── run_revenue_architect.py    # ✅ 营收分析师
├── llm_client.py               # ✅ LLM 客户端
├── config.py                   # ✅ 配置模块
├── fetch_unified_intel.py      # ✅ 统一情报采集器
├── admin.py                    # CLI 管理工具
├── cli.py                      # CLI 入口
│
├── src/
│   ├── auth/                   # ✅ 认证模块 (完整)
│   ├── user/                   # ✅ 用户模块 (完整)
│   ├── usage/                  # ✅ 使用次数模块 (完整)
│   ├── database/               # ✅ 数据库模块 (完整)
│   ├── sensors/                # ✅ 11 个传感器 (完整)
│   ├── admin/                  # ✅ 管理后台路由 (已实现)
│   ├── marketplace/            # ✅ 预设广场 (已实现)
│   ├── generators/             # ⚠️ 仅 __init__.py (预留)
│   ├── defaults/               # 默认配置
│   ├── external/               # 外部服务
│   └── utils/                  # 工具函数
│
├── ui/
│   ├── index.html              # ✅ 主页
│   ├── login.html              # ✅ 登录页
│   ├── register.html           # ✅ 注册页
│   ├── account.html            # ✅ 用户中心
│   ├── forgot-password.html    # ✅ 忘记密码
│   ├── oauth-callback.html     # ✅ OAuth 回调
│   └── static/                 # ✅ 12 个 JS 模块
│
├── tests/                      # ✅ 14 个测试文件
├── docs/                       # 文档目录
├── reports/                    # 报告输出目录
├── data/                       # 数据目录
│
├── Dockerfile                  # ✅ Docker 镜像
├── docker-compose.yml          # ✅ Docker 编排
├── requirements.txt            # ✅ 依赖清单
├── .env.example                # ✅ 配置模板
└── README.md                   # ✅ 项目文档
```

---

## 🔧 技术债务清单

| 类型 | 问题 | 建议 |
|:--|:--|:--|
| 类型标注 | 大量函数缺少类型提示 | 参考 `docs/技术提升指南.md` |
| 测试覆盖 | 传感器模块测试不足 | 补充单元测试 |
| 性能优化 | 数据采集串行执行 | 实现并行采集 |
| 配置管理 | 配置分散在多处 | 统一使用 Pydantic Settings |
| 文档同步 | V2.0_ROADMAP.md 状态已更新 | ✅ 已完成 |

---

## 📅 下一步计划

### 短期 (1-2 周)

1. **补充测试** - 管理后台和预设广场 API 测试
2. **优化 Grok 调用** - 减少舆情核查次数
3. **V2EX 优化** - 提高抓取成功率

### 中期 (1-2 月)

1. **用户管理后台** - 完整的管理员界面
2. **兑换码批量生成** - 管理员批量生成激活码工具
3. **在线支付（可选）** - 微信/支付宝在线购买次数功能

### 长期 (3-6 月)

1. **自定义数据源** - 用户自定义 RSS/API 接入
2. **团队协作** - 多用户共享报告
3. **API 开放** - 第三方接入接口

---

## 📝 备注

- 本备忘录基于 2026-04-04 项目实际代码分析生成
- 建议定期更新以跟踪开发进度
- 相关文档：`README.md`, `V2.0_ROADMAP.md`, `技术提升指南.md`