# Prism 下一步开发计划

> 提交时间：2026-04-04
> 提交人：开发团队
> 审核状态：待审核
> 预计开发周期：约 15 人天

---

## 📋 计划概述

本计划基于项目当前进度（V2.1 完成度 ~80%）制定，聚焦于完善商业化功能和提升系统稳定性。主要包含以下模块：

| 模块 | 优先级 | 预估工时 | 说明 |
|:--|:--|:--|:--|
| 用户管理后台 | P0 | 3 天 | 管理员用户管理界面 |
| 兑换码批量生成 | P0 | 2 天 | 管理员批量生成激活码工具 |
| 测试补充 | P0 | 2 天 | 管理后台/预设广场 API 测试 |
| Grok 调用优化 | P1 | 1 天 | 减少舆情核查调用次数 |
| V2EX 扫描器优化 | P1 | 1 天 | 提高抓取成功率 |
| 自定义 Prompt 完善 | P1 | 2 天 | 后端保存/加载逻辑 |
| 自定义数据源完善 | P2 | 3 天 | 用户自定义 RSS/API 接入 |
| 在线支付（可选） | P3 | 3 天 | 微信/支付宝购买次数 |

**总计**：约 15 人天（不含可选模块）

---

## 🎯 模块一：用户管理后台（P0）

### 1.1 功能描述

为管理员提供完整的用户管理界面，包括：

| 功能 | 说明 |
|:--|:--|
| 用户列表 | 分页展示所有用户，支持搜索/筛选 |
| 用户详情 | 查看用户信息、使用次数、充值记录 |
| 用户封禁 | 禁用/解禁用户账户 |
| 使用统计 | 用户活跃度、充值金额统计 |
| 邀请统计 | 邀请关系、返利记录查看 |

### 1.2 技术方案

#### 后端 API

```
src/admin/
├── router.py          # 扩展现有路由
├── service.py         # 新增：用户管理业务逻辑
└── schemas.py         # 新增：请求/响应模型
```

**新增 API 端点**：

| 端点 | 方法 | 说明 |
|:--|:--|:--|
| `/admin/users` | GET | 用户列表（分页、搜索） |
| `/admin/users/{id}` | GET | 用户详情 |
| `/admin/users/{id}/ban` | PATCH | 封禁用户 |
| `/admin/users/{id}/unban` | PATCH | 解禁用户 |
| `/admin/stats/users` | GET | 用户统计概览 |
| `/admin/stats/revenue` | GET | 充值统计概览 |

#### 数据库扩展

```sql
-- 用户表添加封禁字段
ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN banned_at DATETIME;
ALTER TABLE users ADD COLUMN banned_reason TEXT;
```

#### 前端页面

```
ui/
├── admin.html         # 新增：管理后台主页
└── static/
    └── admin.js       # 新增：管理后台交互逻辑
```

### 1.3 工时分解

| 任务 | 工时 |
|:--|:--|
| 后端 API 开发 | 1 天 |
| 数据库迁移脚本 | 0.5 天 |
| 前端页面开发 | 1 天 |
| 联调测试 | 0.5 天 |
| **合计** | **3 天** |

### 1.4 交付物

- `src/admin/service.py`
- `src/admin/schemas.py`
- `src/database/migrations/v2.1_add_banned_fields.sql`
- `ui/admin.html`
- `ui/static/admin.js`
- `tests/test_admin_api.py`

---

## 🎯 模块二：兑换码批量生成（P0）

### 2.1 功能描述

为管理员提供批量生成兑换码的工具：

| 功能 | 说明 |
|:--|:--|:--|
| 批量生成 | 一次性生成 N 个兑换码 |
| 批次管理 | 按批次号管理兑换码 |
| 导出功能 | 导出为 CSV/Excel 格式 |
| 有效期设置 | 可设置统一过期时间 |
| 使用统计 | 查看批次兑换情况 |

### 2.2 技术方案

#### CLI 工具扩展

```python
# admin.py 扩展

def generate_codes(count: int, usage_count: int, batch: str, 
                   expire_days: int = None, note: str = None):
    """
    批量生成兑换码
    
    Args:
        count: 生成数量
        usage_count: 每个码可充值次数
        batch: 批次号
        expire_days: 有效期天数（可选）
        note: 备注信息
    """
    codes = []
    for _ in range(count):
        code = generate_unique_code()
        codes.append({
            "code": code,
            "usage_count": usage_count,
            "batch": batch,
            "expires_at": calculate_expiry(expire_days),
            "note": note
        })
    batch_insert_codes(codes)
    return codes
```

#### API 端点

| 端点 | 方法 | 说明 |
|:--|:--|:--|
| `/admin/codes/generate` | POST | 批量生成兑换码 |
| `/admin/codes/batches` | GET | 批次列表 |
| `/admin/codes/batches/{batch}` | GET | 批次详情 |
| `/admin/codes/batches/{batch}/export` | GET | 导出兑换码 |

#### 数据库扩展

```sql
-- 激活码表添加过期时间
ALTER TABLE activation_codes ADD COLUMN expires_at DATETIME;
```

### 2.3 工时分解

| 任务 | 工时 |
|:--|:--|
| CLI 工具开发 | 0.5 天 |
| API 端点开发 | 0.5 天 |
| 数据库迁移 | 0.25 天 |
| 导出功能 | 0.5 天 |
| 前端集成 | 0.25 天 |
| **合计** | **2 天** |

### 2.4 交付物

- `admin.py` 扩展
- `src/admin/router.py` 扩展
- `src/database/migrations/v2.1_add_code_expiry.sql`
- `tests/test_admin_codes.py`

---

## 🎯 模块三：测试补充（P0）

### 3.1 功能描述

补充管理后台和预设广场的 API 测试：

| 测试模块 | 说明 |
|:--|:--|:--|
| 管理后台 API 测试 | 用户管理、兑换码管理端点测试 |
| 预设广场 API 测试 | 模板列表、详情、导入端点测试 |
| 边界条件测试 | 权限校验、参数验证、异常处理 |

### 3.2 技术方案

#### 测试文件结构

```
tests/
├── test_admin_api.py      # 新增：管理后台 API 测试
├── test_marketplace_api.py # 新增：预设广场 API 测试
└── conftest.py            # 扩展：添加 admin fixture
```

#### 测试覆盖要点

```python
# test_admin_api.py 示例

class TestAdminUserAPI:
    def test_list_users_pagination(self, admin_client):
        """测试用户列表分页"""
        
    def test_list_users_search(self, admin_client):
        """测试用户搜索"""
        
    def test_ban_user(self, admin_client):
        """测试封禁用户"""
        
    def test_unban_user(self, admin_client):
        """测试解禁用户"""
        
    def test_non_admin_access_denied(self, user_client):
        """测试非管理员访问被拒绝"""

class TestAdminCodesAPI:
    def test_generate_codes(self, admin_client):
        """测试批量生成兑换码"""
        
    def test_export_codes(self, admin_client):
        """测试导出兑换码"""
```

### 3.3 工时分解

| 任务 | 工时 |
|:--|:--|
| 管理后台 API 测试 | 1 天 |
| 预设广场 API 测试 | 0.5 天 |
| conftest.py 扩展 | 0.25 天 |
| 测试运行验证 | 0.25 天 |
| **合计** | **2 天** |

### 3.4 交付物

- `tests/test_admin_api.py`
- `tests/test_marketplace_api.py`
- `tests/conftest.py` 扩展

---

## 🎯 模块四：Grok 调用优化（P1）

### 4.1 功能描述

减少舆情核查的 Grok API 调用次数，降低成本：

| 优化项 | 当前 | 目标 |
|:--|:--|:--|
| PH 舆情核查 | 10 次/报告 | 可选（默认关闭） |
| 战略情报总结 | 1 次 | 保持 |
| Alpha Radar | 1-2 次 | 保持 |
| **总计** | ~12 次 | ~2-3 次 |

### 4.2 技术方案

#### 配置项新增

```python
# config.py

# 舆情核查开关（默认关闭）
ENABLE_SENTIMENT_CHECK: bool = False

# 舆情核查产品数量限制（启用时生效）
SENTIMENT_CHECK_LIMIT: int = 5
```

#### 代码修改

```python
# src/sensors/product_hunt.py

def fetch_product_hunt(enable_sentiment: bool = False):
    """
    获取 Product Hunt 数据
    
    Args:
        enable_sentiment: 是否启用舆情核查
    """
    products = fetch_via_official_api()
    
    if enable_sentiment:
        # 仅对前 N 个产品进行舆情核查
        for product in products[:SENTIMENT_CHECK_LIMIT]:
            product.sentiment = check_sentiment_via_grok(product)
    
    return products
```

### 4.3 工时分解

| 任务 | 工时 |
|:--|:--|:--|
| 配置项添加 | 0.25 天 |
| 代码逻辑修改 | 0.5 天 |
| 前端开关集成 | 0.25 天 |
| **合计** | **1 天** |

### 4.4 交付物

- `config.py` 扩展
- `src/sensors/product_hunt.py` 修改
- `ui/static/sources.js` 扩展（添加开关）

---

## 🎯 模块五：V2EX 扫描器优化（P1）

### 5.1 功能描述

提高 V2EX 数据抓取成功率：

| 问题 | 原因 | 解决方案 |
|:--|:--|:--|
| 经常返回 0 结果 | 反爬机制 | 添加请求头模拟、延迟策略 |
| 数据解析失败 | 页面结构变化 | 更新解析逻辑 |

### 5.2 技术方案

```python
# src/sensors/v2ex_radar.py

def fetch_v2ex_topics():
    """
    优化后的 V2EX 抓取
    """
    headers = {
        "User-Agent": "Mozilla/5.0 ...",
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://www.v2ex.com/",
    }
    
    # 添加请求延迟，避免触发反爬
    time.sleep(random.uniform(1, 3))
    
    # 多节点尝试
    nodes = ["go", "jobs", "programmer", "share"]
    results = []
    for node in nodes:
        try:
            data = fetch_node(node, headers)
            results.extend(data)
        except Exception as e:
            logger.warning(f"Node {node} fetch failed: {e}")
    
    return results
```

### 5.3 工时分解

| 任务 | 工时 |
|:--|:--|
| 请求头优化 | 0.25 天 |
| 多节点尝试逻辑 | 0.25 天 |
| 解析逻辑更新 | 0.25 天 |
| 测试验证 | 0.25 天 |
| **合计** | **1 天** |

### 5.4 交付物

- `src/sensors/v2ex_radar.py` 优化
- `tests/test_sensors.py` 扩展

---

## 🎯 模块六：自定义 Prompt 完善（P1）

### 6.1 功能描述

完善自定义 Prompt 的后端保存/加载逻辑：

| 功能 | 说明 |
|:--|:--|:--|
| Prompt 保存 | 用户自定义 Prompt 存储到数据库 |
| Prompt 加载 | 运行工具时加载用户自定义 Prompt |
| Prompt 管理 | 查看/编辑/删除自定义 Prompt |

### 6.2 技术方案

#### 数据库新增

```sql
-- 用户自定义 Prompt 表
CREATE TABLE user_prompts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    tool_type TEXT NOT NULL,       -- mission / bounty_hunter / alpha_radar / revenue_architect
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_prompts_user ON user_prompts(user_id);
CREATE INDEX idx_user_prompts_tool ON user_prompts(tool_type);
```

#### API 端点

| 端点 | 方法 | 说明 |
|:--|:--|:--|
| `/api/prompts` | GET | 获取用户 Prompt 列表 |
| `/api/prompts` | POST | 创建自定义 Prompt |
| `/api/prompts/{id}` | PUT | 更新 Prompt |
| `/api/prompts/{id}` | DELETE | 删除 Prompt |
| `/api/prompts/{id}/default` | PATCH | 设为默认 |

### 6.3 工时分解

| 任务 | 工时 |
|:--|:--|
| 数据库迁移脚本 | 0.25 天 |
| API 端点开发 | 0.5 天 |
| 工具集成（加载逻辑） | 0.5 天 |
| 前端完善 | 0.5 天 |
| 测试 | 0.25 天 |
| **合计** | **2 天** |

### 6.4 交付物

- `src/database/migrations/v2.1_user_prompts.sql`
- `src/prompts/router.py`
- `src/prompts/service.py`
- `src/prompts/schemas.py`
- `run_mission.py` 等工具文件扩展
- `ui/static/prompt-config.js` 完善
- `tests/test_prompts_api.py`

---

## 🎯 模块七：自定义数据源完善（P2）

### 7.1 功能描述

支持用户自定义数据源接入：

| 功能 | 说明 |
|:--|:--|:--|
| RSS 接入 | 用户添加自定义 RSS 源 |
| API 接入 | 用户添加自定义 API 数据源 |
| 数据源管理 | 查看/编辑/删除自定义数据源 |
| 数据采集 | 运行时采集自定义数据源 |

### 7.2 技术方案

#### 数据库新增

```sql
-- 用户自定义数据源表
CREATE TABLE user_data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,           -- rss / api
    url TEXT NOT NULL,
    config TEXT,                  -- JSON 格式配置
    is_active BOOLEAN DEFAULT TRUE,
    last_fetch_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_user_datasources_user ON user_data_sources(user_id);
```

#### 采集器扩展

```python
# src/sensors/custom_sensor.py

def fetch_custom_sources(user_id: int):
    """
    采集用户自定义数据源
    """
    sources = get_user_data_sources(user_id)
    results = []
    
    for source in sources:
        if source.type == "rss":
            data = fetch_rss(source.url, source.config)
        elif source.type == "api":
            data = fetch_api(source.url, source.config)
        results.extend(data)
    
    return results
```

### 7.3 工时分解

| 任务 | 工时 |
|:--|:--|
| 数据库迁移脚本 | 0.25 天 |
| API 端点开发 | 0.5 天 |
| RSS 采集器 | 1 天 |
| API 采集器 | 0.5 天 |
| 前端完善 | 0.5 天 |
| 测试 | 0.25 天 |
| **合计** | **3 天** |

### 7.4 交付物

- `src/database/migrations/v2.1_user_data_sources.sql`
- `src/datasources/router.py`
- `src/datasources/service.py`
- `src/sensors/custom_sensor.py`
- `ui/static/sources.js` 完善
- `tests/test_datasources_api.py`

---

## 🎯 模块八：在线支付（P3 - 可选）

### 8.1 功能描述

微信/支付宝在线购买使用次数：

| 功能 | 说明 |
|:--|:--|:--|
| 微信支付 | 微信扫码/公众号支付 |
| 支付宝支付 | 支付宝扫码支付 |
| 订单管理 | 订单创建、查询、回调处理 |
| 次数充值 | 支付成功后自动充值次数 |

### 8.2 技术方案

#### 数据库新增

```sql
-- 支付订单表
CREATE TABLE payment_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    order_no TEXT UNIQUE NOT NULL,
    amount INTEGER NOT NULL,        -- 金额（分）
    usage_count INTEGER NOT NULL,   -- 购买次数
    payment_method TEXT NOT NULL,   -- wechat / alipay
    status TEXT DEFAULT 'pending',  -- pending / paid / failed / refunded
    paid_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_payment_orders_user ON payment_orders(user_id);
CREATE INDEX idx_payment_orders_status ON payment_orders(status);
```

#### API 端点

| 端点 | 方法 | 说明 |
|:--|:--|:--|
| `/api/payment/create` | POST | 创建支付订单 |
| `/api/payment/query` | GET | 查询订单状态 |
| `/api/payment/wechat/callback` | POST | 微信支付回调 |
| `/api/payment/alipay/callback` | POST | 支付宝回调 |

### 8.3 工时分解

| 任务 | 工时 |
|:--|:--|
| 数据库迁移脚本 | 0.25 天 |
| 微信支付集成 | 1 天 |
| 支付宝支付集成 | 1 天 |
| 前端支付页面 | 0.5 天 |
| 测试 | 0.25 天 |
| **合计** | **3 天** |

### 8.4 交付物

- `src/database/migrations/v2.1_payment_orders.sql`
- `src/payment/router.py`
- `src/payment/service.py`
- `src/payment/wechat.py`
- `src/payment/alipay.py`
- `ui/payment.html`
- `ui/static/payment.js`
- `tests/test_payment_api.py`

### 8.5 备注

此模块为**可选模块**，根据业务需求决定是否开发。当前兑换码充值方式已能满足基本需求。

---

## 📅 开发排期建议

### 第一阶段（P0 模块）- 约 7 天

| Day | 任务 |
|:--|:--|
| 1-2 | 用户管理后台开发 |
| 3 | 用户管理后台联调 |
| 4-5 | 兑换码批量生成开发 |
| 6-7 | 测试补充 |

### 第二阶段（P1 模块）- 约 4 天

| Day | 任务 |
|:--|:--|
| 8 | Grok 调用优化 |
| 9 | V2EX 扫描器优化 |
| 10-11 | 自定义 Prompt 完善 |

### 第三阶段（P2 模块）- 约 3 天

| Day | 任务 |
|:--|:--|
| 12-14 | 自定义数据源完善 |

### 第四阶段（P3 可选）- 约 3 天

| Day | 任务 |
|:--|:--|
| 15-17 | 在线支付开发（如需要） |

---

## 📊 风险评估

| 风险项 | 影响 | 缓解措施 |
|:--|:--|:--|
| V2EX 反爬升级 | 数据源失效 | 多节点尝试、请求头模拟 |
| 微信支付审核 | 上线延迟 | 提前申请、预留缓冲时间 |
| 数据库迁移兼容 | 数据丢失 | 编写回滚脚本、测试环境验证 |
| API 权限漏洞 | 安全风险 | 严格权限校验、测试覆盖 |

---

## ✅ 审核要点

请审核人员重点关注以下内容：

1. **功能必要性**：各模块是否符合业务需求？
2. **技术方案**：技术实现是否合理可行？
3. **工时估算**：工作量评估是否准确？
4. **优先级排序**：开发顺序是否合理？
5. **风险评估**：风险缓解措施是否充分？

---

## 📝 审核意见

| 审核项 | 审核意见 | 备注 |
|:--|:--|:--|
| 功能必要性 | | |
| 技术方案 | | |
| 工时估算 | | |
| 优先级排序 | | |
| 风险评估 | | |
| **整体结论** | | |

**审核人**：________________
**审核日期**：________________
**审核签字**：________________

---

## 📚 相关文档

| 文档 | 说明 |
|:--|:--|:--|
| `DEV_MEMO.md` | 项目当前进度备忘录 |
| `V2.0_ROADMAP.md` | V2.0 开发规划（已完成） |
| `README.md` | 项目说明文档 |
| `技术提升指南.md` | 技术改进建议 |