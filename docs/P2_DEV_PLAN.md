# P2 阶段开发计划

> 创建时间：2026-04-04
> 开发阶段：P2（预设广场完善 + 测试补充 + 监控告警 + 数据源增强）
> 状态：✅ 已完成

---

## 📋 开发概览

| 模块 | 预估工时 | 优先级 | 状态 |
|:--|:--|:--|:--|
| P2-1: 预设广场完善 | 1 天 | 高 | ✅ 已完成 |
| P2-2: 测试补充 | 2 天 | 高 | ✅ 已完成 |
| P2-3: 监控告警 | 1 天 | 高 | ✅ 已完成 |
| P2-4: 数据源增强 | 1 天 | 中 | ⏳ 待开始 |
| P2-5: Prompt 验证增强 | 1 天 | 中 | ⏳ 待开始 |

**总预估工时：6 天**

---

## ✅ P2-1: 预设广场完善

### 当前状态

- ✅ 后端 API 已完成（列表、详情、导入）
- ✅ 前端 JS 模块已完成
- ❌ 官方模板数据为空
- ❌ 前端页面入口不明显

### 开发内容

#### 1.1 填充官方模板数据

为 5 个工具类型各创建 2-3 个官方预设模板：

| 工具类型 | 模板数量 | 示例模板 |
|:--|:--|:--|
| mission（情报日报） | 3 | 科技日报、商业日报、开发者日报 |
| bounty_v2ex（V2EX赏金） | 2 | 技术外包、设计外包 |
| bounty_chrome（Chrome扩展） | 2 | 效率工具、开发者工具 |
| alpha（Alpha雷达） | 2 | Web3项目、AI项目 |
| revenue（营收分析） | 2 | SaaS分析、电商分析 |

**实现方式：**
- 创建数据库迁移脚本插入官方模板
- 或通过 CLI 工具批量导入

#### 1.2 前端优化

- 在主页「广场」Tab 中突出预设广场入口
- 添加模板分类筛选功能
- 添加模板预览功能
- 优化模板导入确认流程

### 预期成果

- 预设广场包含 10+ 官方模板
- 用户可一键导入模板到自己的配置
- 前端体验流畅

---

## ✅ P2-2: 测试补充

### 当前状态

- ✅ `tests/test_admin_api.py` - 19 个测试
- ✅ `tests/test_marketplace_api.py` - 已创建
- ❌ 测试覆盖不完整
- ❌ 缺少 Prompt 版本历史测试
- ❌ 缺少预设广场完整测试

### 开发内容

#### 2.1 管理后台 API 测试补充

新增测试用例：

| 测试类 | 测试内容 |
|:--|:--|
| TestBatchBan | 批量封禁用户 |
| TestAuditLogs | 审计日志查询、筛选 |
| TestAuditActions | 审计操作类型列表 |

#### 2.2 预设广场 API 测试补充

新增测试文件 `tests/test_marketplace_full.py`：

| 测试类 | 测试内容 |
|:--|:--|
| TestTemplateList | 模板列表、分页、筛选 |
| TestTemplateDetail | 模板详情查询 |
| TestTemplateImport | 模板导入、导入计数 |
| TestTemplateNotFound | 模板不存在处理 |

#### 2.3 Prompt 版本历史测试

新增测试文件 `tests/test_prompt_history.py`：

| 测试类 | 测试内容 |
|:--|:--|
| TestPromptSave | 保存时自动创建历史版本 |
| TestPromptHistory | 历史版本查询 |
| TestPromptRollback | 版本回滚功能 |

### 预期成果

- 测试覆盖率提升至 80%+
- 所有新增 API 都有对应测试
- 测试全部通过

---

## ✅ P2-3: 监控告警

### 当前状态

- ❌ 无 API 调用失败告警
- ❌ 无错误日志聚合
- ❌ 无运行状态监控

### 开发内容

#### 3.1 错误日志聚合

创建 `src/utils/error_tracker.py`：

```python
class ErrorTracker:
    """错误追踪器"""
    
    def track_error(
        self,
        error_type: str,
        error_message: str,
        context: dict = None,
    ):
        """记录错误"""
        
    def get_error_stats(self, hours: int = 24) -> dict:
        """获取错误统计"""
        
    def get_recent_errors(self, limit: int = 100) -> list:
        """获取最近错误"""
```

#### 3.2 API 调用监控

创建 `src/utils/api_monitor.py`：

```python
class APIMonitor:
    """API 调用监控"""
    
    def record_call(
        self,
        api_name: str,
        success: bool,
        response_time_ms: int,
        error: str = None,
    ):
        """记录 API 调用"""
        
    def get_stats(self, hours: int = 24) -> dict:
        """获取调用统计"""
        
    def check_alert(self) -> list:
        """检查是否需要告警"""
```

#### 3.3 告警机制

创建 `src/utils/alerting.py`：

```python
class Alerter:
    """告警器"""
    
    def send_alert(
        self,
        level: str,  # info / warning / error
        title: str,
        message: str,
    ):
        """发送告警"""
```

**支持的告警渠道：**
- 邮件告警（SMTP）
- Webhook 告警（通用）
- 日志文件告警（默认）

#### 3.4 管理后台监控面板

在管理后台新增「系统监控」Tab：

- API 调用统计（成功率、响应时间）
- 错误日志列表
- 告警配置

### 预期成果

- API 调用失败自动记录
- 错误率超过阈值自动告警
- 管理后台可查看监控数据

---

## ✅ P2-4: 数据源增强

### 当前状态

- ✅ V2EX RSS + API fallback
- ❌ 无第三方镜像站点支持
- ❌ 无自定义数据源采集逻辑

### 开发内容

#### 4.1 V2EX 镜像站点支持

新增镜像站点配置：

```python
V2EX_MIRRORS = [
    "https://www.v2ex.com",
    "https://v2ex.com",
    "https://global.v2ex.com",  # 海外镜像
    # 可扩展更多镜像
]
```

实现逻辑：
1. 主站点失败时自动尝试镜像
2. 记录各站点响应时间
3. 自动选择最快站点

#### 4.2 用户自定义数据源采集（可选）

实现 `src/sensors/custom_source.py`：

```python
class CustomSourceSensor:
    """自定义数据源采集器"""
    
    def fetch_rss(self, url: str) -> list:
        """采集 RSS 源"""
        
    def fetch_webpage(self, url: str, selector: str) -> list:
        """采集网页源"""
```

### 预期成果

- V2EX 数据获取稳定性进一步提升
- 支持用户自定义数据源（可选）

---

## ✅ P2-5: Prompt 验证增强

### 当前状态

- ✅ 长度验证（1-50000字符）
- ❌ 无占位符验证
- ❌ 无语法检查

### 开发内容

#### 5.1 占位符验证

创建 `src/utils/prompt_validator.py`：

```python
class PromptValidator:
    """Prompt 验证器"""
    
    # 各工具支持的占位符
    PLACEHOLDERS = {
        "mission": ["{date_str}", "{time_str}"],
        "alpha": ["{query}"],
        "revenue": ["{content}"],
        # ...
    }
    
    def validate(self, tool_type: str, prompt: str) -> ValidationResult:
        """验证 Prompt"""
        # 1. 检查长度
        # 2. 检查占位符是否存在
        # 3. 检查未知占位符
        # 4. 返回验证结果
```

#### 5.2 前端提示增强

- 显示各工具支持的占位符列表
- 实时验证占位符使用
- 提供占位符自动补全

### 预期成果

- 用户编辑 Prompt 时有清晰的提示
- 减少因占位符错误导致的运行失败

---

## 📅 开发排期

| 阶段 | 任务 | 工时 | 依赖 |
|:--|:--|:--|:--|
| 第1天 | P2-1: 预设广场完善 | 1天 | 无 |
| 第2-3天 | P2-2: 测试补充 | 2天 | P2-1 |
| 第4天 | P2-3: 监控告警 | 1天 | 无 |
| 第5天 | P2-4: 数据源增强 | 1天 | 无 |
| 第6天 | P2-5: Prompt验证增强 | 1天 | 无 |

---

## 📊 预期成果

### 功能成果

| 成果 | 说明 |
|:--|:--|
| 预设广场可用 | 10+ 官方模板，一键导入 |
| 测试覆盖完整 | 80%+ 覆盖率，全部通过 |
| 监控告警 | API 失败自动告警 |
| 数据源稳定 | V2EX 多镜像支持 |
| Prompt 友好 | 占位符验证 + 提示 |

### 文件变更预估

| 类型 | 数量 |
|:--|:--|
| 新增文件 | 5-8 |
| 修改文件 | 10-15 |
| 新增测试 | 30+ |
| 数据库迁移 | 1 |

---

## ⚠️ 风险与依赖

### 风险

| 风险 | 影响 | 缓解措施 |
|:--|:--|:--|
| V2EX 镜像站点不稳定 | 数据获取失败 | 多镜像 + 缓存 |
| 告警渠道配置复杂 | 功能不可用 | 提供默认日志告警 |
| 测试环境差异 | 测试失败 | 使用内存数据库 |

### 依赖

| 依赖 | 说明 |
|:--|:--|
| tenacity | 已安装（P1阶段） |
| SMTP 服务 | 告警邮件发送（可选） |

---

## ✅ 审核确认

请审核人员确认以下内容：

- [ ] 开发范围合理
- [ ] 工时预估合理
- [ ] 优先级排序合理
- [ ] 无遗漏的重要功能

**审核人**：________________
**审核日期**：________________
**审核签字**：________________