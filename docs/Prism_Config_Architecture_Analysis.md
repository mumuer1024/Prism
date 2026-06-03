# Prism v2.1 配置读取链路分析与改造方案

> 文档创建时间：2026-04-06
> 用途：记录现状、问题和改造方向，供开发参考

---

## 一、现状总览

### 1.1 配置隔离现状

| 配置类型 | 存储位置 | 用户隔离 | 说明 |
|------|------|------|------|
| LLM API Key | `.env` 文件 | ❌ 共享 | 所有用户使用同一套LLM配置 |
| 数据源Token（GitHub/Tavily等） | `.env` 文件 | ❌ 共享 | 所有用户使用同一套Token |
| 用户自定义Prompt | `user_prompts` 表 | ✅ 隔离 | 每用户独立配置 |
| 用户自定义数据源 | `user_sources` 表 | ✅ 隔离 | 每用户独立配置 |
| 用户专属Token | `user_configs` 表 | ✅ 隔离 | 表结构已支持，但前端未使用 |
| 报告文件 | `reports/` 目录 | ❌ 共享 | CLI生成，无用户区分 |
| 报告缓存 | `reports` 数据库表 | ✅ 隔离 | Web API生成时存储，有user_id |

---

### 1.2 任务脚本配置读取现状

| 脚本 | LLM API Key | 数据源Token | 用户Prompt | 多用户支持 |
|------|------|------|------|------|
| run_mission.py | 全局.env | 全局.env | ✅ user_id参数 | 仅Prompt隔离 |
| run_bounty_hunter.py | 全局.env | 无需Token | ✅ user_id参数 | 仅Prompt隔离 |
| run_alpha_radar.py | 全局.env (XAI) | 无需Token | ✅ user_id参数 | 仅Prompt隔离 |
| run_revenue_architect.py | 全局.env | 无需Token | ✅ user_id参数 | 仅Prompt隔离 |

---

### 1.3 关键文件位置

| 功能 | 文件 | 关键位置 |
|------|------|------|
| 全局配置读取API | `server.py` | 第191行 GET /api/config，第197行 POST /api/config |
| 全局配置定义 | `config.py` | 全文件，从os.getenv()读取 |
| 用户配置API | `src/config_router.py` | 第864-920行 /api/user-config/keys |
| 用户配置数据库模型 | `src/database/models.py` | UserConfig类 |
| LLM客户端 | `llm_client.py` | chat()函数，支持api_key动态传入 |
| 报告存储目录 | 各任务脚本第17-21行 | `reports/daily_briefings/`等 |

---

### 1.4 重要发现

**`llm_client.py`已经支持动态传入API Key：**
```python
def chat(
    prompt: str,
    ...
    api_key: str = "",  # 可由调用者传入
    ...
):
```
这意味着改造时不需要重写LLM客户端，只需要修改调用层。

**`user_configs`表已存在：**
数据库中已有按user_id隔离的配置表，只是前端配置页没有使用它，
仍然在往`.env`写。

---

## 二、存在的问题

### P0 阻塞上线的问题

#### 问题1：配置页API Key写入.env（全局共享）
- **现象**：所有用户共用同一套API Key，A用户配置的Key会覆盖B用户的配置
- **根因**：`config.js`前端把配置POST到`/api/config`，后端写入`.env`文件
- **影响**：多用户场景下配置互相覆盖，数据不隔离

#### 问题2：报告文件无用户隔离
- **现象**：所有用户的报告混在同一目录下，报告列表显示所有人的报告
- **根因**：任务脚本的REPORT_DIR没有按user_id分目录
- **影响**：用户能看到其他用户的报告内容

#### 问题3：任务脚本使用全局Key执行
- **现象**：无论哪个用户触发任务，都使用同一个LLM API Key
- **根因**：任务脚本从`config.py`读取全局配置
- **影响**：无法实现用户自带Key的产品定位，成本无法按用户控制

---

### P1 影响体验但不阻塞上线

#### 问题4：GitHub Token健康检测关联失效
- **现象**：用户在配置页填写GitHub Token后，健康检测仍提示"需要填入Token"
- **根因**：健康检测读取`user_configs`表，但配置页写入的是`.env`，两套系统不通

#### 问题5：HN健康状态401误报
- **现象**：Hacker News数据源显示401需要认证
- **根因**：HN是公开API不需要认证，健康检测逻辑有误

#### 问题6：用户中心页顶部Tab未同步
- **现象**：`account.html`顶部导航没有其他页面的Tab
- **根因**：只改了`index.html`，忘了同步`account.html`

---

### P2 上线后迭代

#### 问题7：管理后台缺少删除用户功能
需要支持删除用户及其全部数据

#### 问题8：用户缓存时效性未实现
目标：
- 匿名用户及免费用户：不保存缓存数据
- 付费用户：保存30天，到期自动清理
- 缓存范围：自定义数据源、报告（不包含API Key和Token）
- API Key和Token只保留在用户本地浏览器缓存

---

## 三、改造方案

### 方向：用户自带Key（BYOK）

**核心原则：**
- API Key和Token只存在用户本地浏览器（localStorage）
- 服务器不持久化用户的Key
- 用户触发任务时，前端把Key随请求一起发给后端
- 后端用完即丢，不存数据库

**符合产品定位：**
> "不代理、不中转、不存储用户API Key和请求内容"

---

### 阶段一：上线前必须完成

#### 改造1：配置页改为只存localStorage

**前端改动（`ui/static/config.js`）：**
- 保存配置时：改为只写`localStorage`，不POST到`/api/config`
- 读取配置时：从`localStorage`读取，回填表单
- 删除所有向`/api/config`发请求的逻辑

**后端改动：**
- `/api/config` GET/POST端点可以保留（供自部署用户用），但Web UI不再使用它
- 或者在官方托管版关闭此端点

---

#### 改造2：任务运行时前端传Key给后端

**前端改动（`ui/static/console.js`）：**
- 点击"运行"时，从localStorage读取所有Key
- 随任务请求一起POST给后端

**后端改动（`server.py` 运行任务的端点）：**
- 接收前端传来的Key参数
- 传给对应的任务脚本

**任务脚本改动（四个run_*.py）：**
- 增加接收Key参数的入口
- 调用`llm_client.chat()`时传入用户的Key（已支持动态传入）
- 不再从`config.py`读取全局Key

**`llm_client.py`：**
- 已支持`api_key`动态传入，无需改动

---

#### 改造3：报告按user_id目录隔离

**任务脚本改动：**
```python
# 修改前
REPORT_DIR = BASE_DIR / "reports" / "daily_briefings"

# 修改后
REPORT_DIR = BASE_DIR / "reports" / f"user_{user_id}" / "daily_briefings"
```

**后端API改动（`server.py`）：**
- `/api/reports` 列表端点：只返回当前用户目录下的报告
- `/api/reports/content` 读取端点：验证报告属于当前用户
- 匿名用户：使用`visitor_id`作为目录标识，或不保存报告

---

### 阶段二：上线后迭代

#### 改造4：修复健康检测关联（GitHub Token）
- 健康检测时从localStorage读取用户配置的Token
- 或通过API端点检查（前端发Token给后端做检测）

#### 改造5：修复HN健康状态401
- 检查`source_health.py`中HN的检测逻辑
- HN公开API无需认证，修正检测方式

#### 改造6：用户中心页Tab同步
- `account.html`顶部导航同步添加其他页面的Tab

#### 改造7：管理后台删除用户功能
- 后端新增`DELETE /api/admin/users/{user_id}`端点
- 级联删除用户相关数据（prompts/sources/configs/reports）

#### 改造8：用户缓存时效性
- 报告表增加到期时间字段
- 定时任务清理过期报告
- 按用户类型设置不同保留策略

---

## 四、改造优先级和顺序

```
阶段一（上线前）：
  改造1（配置页改localStorage）✅ 已完成
    ↓
  改造2（运行时传Key）✅ 已完成
    ↓
  改造3（报告目录隔离）✅ 已完成（与改造2合并完成）
    ↓
  同时修复：
    P1问题5 HN健康状态401误报 ✅ 已完成
    P1问题6 用户中心页顶部Tab ✅ 已完成
    P1问题4 GitHub Token健康检测 ⏳ 待完成

阶段二（上线后迭代）：
  改造4-8 按需排期
```

## 五、额外完成项（2026-04-06）

- ✅ localStorage按用户账号隔离（不同账号Key互不干扰）
- ✅ 报告页面认证参数修复（报告按用户正确显示）
- ✅ 用户中心页交互激活问题修复（legal-modal遮罩问题）
- ✅ account.html支持URL参数?tab=xxx跳转

---

## 五、注意事项

1. **自部署用户兼容性**：改造后自部署用户仍可通过`.env`配置全局Key作为默认值，前端localStorage为空时回退到`.env`

2. **测试覆盖**：改造2（运行时传Key）需要新增测试用例，验证Key传递链路

3. **迁移问题**：现有用户在`.env`里配置的Key改造后会失效，需要提示用户重新在配置页填写

4. **安全注意**：localStorage存储的Key不加密，属于行业惯例（类似OpenAI官网），在隐私政策中说明即可
