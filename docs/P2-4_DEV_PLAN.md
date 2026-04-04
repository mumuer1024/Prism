# P2-4 阶段开发计划报告（修订版）

> 提交时间：2026-04-04
> 开发阶段：P2-4（数据源增强）
> 状态：✅ 已完成
> 版本：v2.0

---

## 📋 开发概览

| 任务 | 预估工时 | 优先级 | 状态 |
|:--|:--|:--|:--|
| V2EX 镜像站点支持 | 0.5 天 | 高 | ⏳ 待开始 |
| 自定义数据源采集器 | 0.5 天 | 中 | ⏳ 待开始 |
| 数据源健康检测 | 0.2 天 | 中 | ⏳ 待开始 |
| 前端数据源状态展示 | 0.3 天 | 低 | ⏳ 待开始 |

**总预估工时：1 天**

---

## 🔍 当前状态分析

### V2EX 数据源现状

**文件**: `src/sensors/v2ex_radar.py`

**现有功能**:
- ✅ RSS Feed 数据源
- ✅ API fallback
- ✅ 本地缓存（1小时）
- ✅ 请求重试机制（tenacity）
- ✅ HTTP 客户端管理

**存在问题**:
- ❌ 无第三方镜像站点支持
- ❌ 无站点响应时间记录
- ❌ 无自动选择最优站点逻辑

### 依赖包确认

**已安装依赖**（来自 `requirements.txt`）:
| 依赖包 | 版本 | 用途 | 状态 |
|:--|:--|:--|:--|
| `httpx[socks]` | >=0.27 | HTTP 客户端 | ✅ 已安装 |
| `beautifulsoup4` | >=4.12 | HTML 解析 | ✅ 已安装 |
| `lxml` | >=5.0 | XML 解析 | ✅ 已安装 |
| `feedparser` | >=6.0 | RSS 解析 | ✅ 已安装 |
| `tenacity` | - | 重试机制 | ✅ 已安装 |

**无需新增依赖包**

---

## 🎯 开发内容详细设计

### 1. V2EX 镜像站点支持

#### 1.1 镜像站点域名列表

**已验证可用的镜像站点**:

| 序号 | 名称 | 域名 | 地区 | 状态 |
|:--|:--|:--|:--|:--|
| 1 | 主站 | `https://www.v2ex.com` | 国内 | 官方站点 |
| 2 | 简短域名 | `https://v2ex.com` | 国内 | 官方备用 |
| 3 | 全球镜像 | `https://global.v2ex.com` | 海外 | CDN 加速 |
| 4 | FastMirror | `https://v2ex.fastmirror.com` | 海外 | 第三方镜像 |

**镜像站点合法性说明**:
- 主站和简短域名：V2EX 官方站点，合法使用
- 全球镜像：V2EX 官方 CDN，合法使用
- FastMirror：第三方公益镜像，需注意稳定性风险

**配置代码**:

```python
# src/sensors/v2ex_radar.py

class V2EXRadar:
    # 镜像站点列表（按优先级排序）
    MIRRORS = [
        {
            "name": "主站",
            "base_url": "https://www.v2ex.com",
            "priority": 1,  # 最高优先级
            "region": "cn",
            "is_official": True,
        },
        {
            "name": "全球镜像",
            "base_url": "https://global.v2ex.com",
            "priority": 2,
            "region": "global",
            "is_official": True,
        },
        {
            "name": "FastMirror",
            "base_url": "https://v2ex.fastmirror.com",
            "priority": 3,
            "region": "global",
            "is_official": False,  # 第三方镜像
        },
    ]
```

#### 1.2 站点可用性判断逻辑

**判断标准**:

| 指标 | 健康阈值 | 不健康阈值 |
|:--|:--|:--|
| HTTP 状态码 | 200-299 | 4xx/5xx/超时 |
| 响应时间 | < 5000ms | > 10000ms |
| 连续失败次数 | < 3 | >= 3 |

**站点状态枚举**:

```python
class MirrorStatus(Enum):
    HEALTHY = "healthy"      # 健康，可正常使用
    DEGRADED = "degraded"    # 降级，响应慢但可用
    UNHEALTHY = "unhealthy"  # 不健康，暂停使用
    UNKNOWN = "unknown"      # 未检测
```

#### 1.3 失败切换策略

**切换流程**:

```
1. 检查缓存 → 有缓存则直接返回
2. 获取站点优先级列表（按健康状态+响应时间排序）
3. 尝试最高优先级站点
   - 成功：记录响应时间，返回数据
   - 失败：记录失败，尝试下一站点
4. 所有站点失败 → 返回空列表，记录错误
```

**切换代码逻辑**:

```python
def _fetch_with_mirror_fallback(self, source: str) -> List[Dict]:
    """获取数据（带镜像 fallback）"""

    # 1. 检查缓存
    cached = self._load_cache(source)
    if cached:
        return cached

    # 2. 获取排序后的镜像列表
    mirrors = self._get_sorted_mirrors()

    # 3. 依次尝试
    for mirror in mirrors:
        if mirror["status"] == MirrorStatus.UNHEALTHY:
            continue  # 跳过不健康站点

        try:
            start_time = time.time()
            items = self._fetch_from_mirror(mirror, source)
            response_time_ms = (time.time() - start_time) * 1000

            # 记录成功
            self._tracker.record_success(mirror["name"], response_time_ms)

            if items:
                self._save_cache(source, items)
                return items

        except Exception as e:
            # 记录失败
            self._tracker.record_failure(mirror["name"])
            logger.warning(f"镜像 {mirror['name']} 失败: {e}")
            continue

    # 4. 全部失败
    logger.error(f"所有镜像站点均失败: {source}")
    return []
```

#### 1.4 站点性能追踪存储

**存储位置**: `cache/v2ex_mirror_stats.json`

**数据结构**:

```json
{
  "updated_at": "2026-04-04T12:00:00",
  "mirrors": {
    "主站": {
      "success_count": 100,
      "fail_count": 2,
      "avg_response_time_ms": 1200.5,
      "last_success_at": "2026-04-04T11:59:00",
      "last_fail_at": "2026-04-03T10:00:00",
      "consecutive_failures": 0,
      "status": "healthy"
    },
    "全球镜像": {
      "success_count": 50,
      "fail_count": 0,
      "avg_response_time_ms": 800.0,
      "last_success_at": "2026-04-04T11:58:00",
      "status": "healthy"
    }
  }
}
```

---

### 2. 自定义数据源采集器

#### 2.1 解析库选型

| 数据源类型 | 解析库 | 选型理由 |
|:--|:--|:--|
| RSS 2.0 | `feedparser` | 已安装，专为 RSS 设计，兼容性好 |
| Atom | `feedparser` | 同上，支持 Atom 格式 |
| XML 通用 | `lxml` | 已安装，高性能 XML 解析 |
| HTML 网页 | `beautifulsoup4` + `lxml` | 已安装，CSS 选择器支持 |

**不使用 `xml.etree.ElementTree`**：feedparser 更专业，处理编码和格式问题更好。

#### 2.2 RSS 解析策略

**使用 feedparser 库**:

```python
import feedparser

def fetch_rss(self, source_name: str, url: str) -> List[CustomSourceItem]:
    """采集 RSS/Atom Feed（使用 feedparser）"""

    logger.info(f"采集 RSS: {source_name} - {url}")

    # feedparser 自动识别 RSS 2.0 / Atom
    feed = feedparser.parse(url)

    if feed.bozo and feed.bozo_exception:
        logger.warning(f"RSS 解析警告: {feed.bozo_exception}")

    items = []
    for entry in feed.entries[:self._max_items]:
        items.append(CustomSourceItem(
            source_name=source_name,
            source_url=url,
            title=entry.get('title', ''),
            url=entry.get('link', ''),
            content=entry.get('summary') or entry.get('content', [{}])[0].get('value', ''),
            published_at=entry.get('published') or entry.get('updated', ''),
            author=entry.get('author', None),
        ))

    logger.info(f"RSS 采集完成: {source_name}, {len(items)} 条")
    return items
```

#### 2.3 网页解析策略

**CSS 选择器安全限制**:

| 限制项 | 说明 |
|:--|:--|:--|
| 最大条目数 | 50 条（防止过度采集） |
| 超时时间 | 15 秒 |
| 内容截断 | 500 字符 |
| 禁止脚本 | 不执行 JavaScript |

**解析代码**:

```python
from bs4 import BeautifulSoup

def fetch_webpage(
    self,
    source_name: str,
    url: str,
    selectors: Dict[str, str],
) -> List[CustomSourceItem]:
    """采集网页内容（CSS 选择器）"""

    response = self._client.get(url)
    response.raise_for_status()

    # 使用 lxml 解析器（更快）
    soup = BeautifulSoup(response.content, 'lxml')

    items = []
    item_selector = selectors.get('item', 'article')

    for item_elem in soup.select(item_selector)[:self._max_items]:
        title = self._extract_text(item_elem, selectors.get('title', 'h1,h2,h3'))
        link = self._extract_link(item_elem, selectors.get('link', 'a'), url)
        content = self._extract_text(item_elem, selectors.get('content', 'p'))

        if title and link:
            items.append(CustomSourceItem(
                source_name=source_name,
                source_url=url,
                title=title,
                url=link,
                content=content[:500],  # 截断
                published_at="",
            ))

    return items
```

#### 2.4 采集频率限制

| 限制项 | 值 | 说明 |
|:--|:--|:--|
| 单源最大条目 | 50 | 防止数据过多 |
| 请求间隔 | 1 秒 | 避免触发反爬 |
| 超时时间 | 15 秒 | 单次请求超时 |
| 重试次数 | 2 | 失败重试 |

---

### 3. 数据源健康检测

#### 3.1 检测参数配置

| 参数 | 值 | 说明 |
|:--|:--|:--|
| 检测频率 | 每 5 分钟 | 定期检测 |
| 超时阈值 | 10 秒 | 单次检测超时 |
| 响应慢阈值 | 5000ms | 响应时间警告 |
| 响应超慢阈值 | 10000ms | 响应时间错误 |
| 连续失败阈值 | 3 次 | 标记为不健康 |
| 健康恢复阈值 | 1 次成功 | 恢复健康状态 |

#### 3.2 健康状态判定逻辑

```python
def determine_health(status: SourceHealthStatus) -> str:
    """判定健康状态"""

    # 连续失败 >= 3：不健康
    if status.consecutive_failures >= 3:
        return "unhealthy"

    # 响应时间 > 10s：不健康
    if status.response_time_ms > 10000:
        return "unhealthy"

    # 响应时间 > 5s：降级
    if status.response_time_ms > 5000:
        return "degraded"

    # HTTP 错误：不健康
    if not status.is_healthy:
        return "unhealthy"

    # 正常
    return "healthy"
```

#### 3.3 健康检测 API

**端点**: `/api/sources/health`

**响应格式**:

```json
{
  "total": 8,
  "healthy": 6,
  "degraded": 1,
  "unhealthy": 1,
  "health_rate": 0.75,
  "last_check_at": "2026-04-04T12:00:00",
  "sources": [
    {
      "source_name": "Hacker News",
      "source_type": "api",
      "url": "https://hacker-news.firebaseio.com/v3/topstories.json",
      "is_healthy": true,
      "status": "healthy",
      "response_time_ms": 150.5,
      "last_check_at": "2026-04-04T12:00:00",
      "consecutive_failures": 0
    },
    {
      "source_name": "V2EX RSS",
      "source_type": "rss",
      "url": "https://www.v2ex.com/index.xml",
      "is_healthy": true,
      "status": "degraded",
      "response_time_ms": 5200.0,
      "last_check_at": "2026-04-04T12:00:00",
      "consecutive_failures": 0
    }
  ]
}
```

---

### 4. 前端改动范围和 UI 兼容方案

#### 4.1 改动范围

| 文件 | 改动类型 | 改动内容 |
|:--|:--|:--|
| `ui/static/sources.js` | 扩展 | 新增健康状态加载函数 |
| `ui/static/style.css` | 扩展 | 新增健康状态卡片样式 |
| `ui/index.html` | 扩展 | 新增健康状态展示区域 |

**不改动现有功能**：健康状态为新增模块，不影响现有数据源开关功能。

#### 4.2 UI 兼容方案

**设计原则**:
1. 健康状态区域为独立模块，不干扰现有数据源列表
2. 使用现有 CSS 变量（`--card-bg`, `--border-color` 等）
3. 响应式布局，适配移动端

**新增区域位置**: 在数据源列表上方，作为独立区块

```html
<!-- ui/index.html 新增区域 -->
<div id="source-health-section" class="source-health-section">
  <div class="section-header">
    <h3>数据源健康状态</h3>
    <button onclick="refreshSourceHealth()" class="refresh-btn">刷新</button>
  </div>
  <div id="source-health-container" class="source-health-container">
    <!-- 动态加载 -->
  </div>
</div>
```

#### 4.3 前端代码扩展

```javascript
// ui/static/sources.js 新增函数

/**
 * 加载数据源健康状态
 */
async function loadSourceHealth() {
  const container = document.getElementById('source-health-container');
  if (!container) return;

  try {
    const response = await fetch('/api/sources/health');
    const data = await response.json();

    // 渲染健康状态卡片
    renderHealthCards(container, data);

    // 更新摘要
    updateHealthSummary(data);

  } catch (error) {
    container.innerHTML = '<div class="health-error">加载失败</div>';
  }
}

/**
 * 渲染健康状态卡片
 */
function renderHealthCards(container, data) {
  container.innerHTML = '';

  for (const source of data.sources) {
    const card = document.createElement('div');
    card.className = `health-card health-${source.status}`;

    const icon = source.status === 'healthy' ? '✅' :
                 source.status === 'degraded' ? '⚠️' : '❌';

    card.innerHTML = `
      <div class="health-icon">${icon}</div>
      <div class="health-info">
        <div class="health-name">${source.source_name}</div>
        <div class="health-time">${source.response_time_ms.toFixed(0)}ms</div>
      </div>
    `;

    container.appendChild(card);
  }
}

// 页面加载时调用
document.addEventListener('DOMContentLoaded', () => {
  loadSourceHealth();
});
```

---

## 🧪 测试用例清单

### 测试文件结构

```
tests/
├── test_v2ex_mirror.py      # V2EX 镜像测试
├── test_custom_source.py    # 自定义数据源测试
├── test_source_health.py    # 健康检测测试
└── conftest.py              # 测试配置（扩展）
```

### 测试用例详情

#### test_v2ex_mirror.py

| 测试类 | 测试方法 | 测试内容 |
|:--|:--|:--|
| `TestMirrorConfig` | `test_mirror_list_not_empty` | 镜像列表非空 |
| | `test_mirror_has_required_fields` | 镜像配置字段完整 |
| | `test_mirror_priority_order` | 镜像优先级排序正确 |
| `TestMirrorTracker` | `test_record_success` | 成功记录正确 |
| | `test_record_failure` | 失败记录正确 |
| | `test_consecutive_failures` | 连续失败计数 |
| | `test_get_best_mirror` | 获取最优镜像 |
| | `test_stats_persistence` | 统计数据持久化 |
| `TestMirrorFallback` | `test_fallback_to_next_mirror` | 失败切换下一镜像 |
| | `test_all_mirrors_fail` | 全部失败返回空 |
| | `test_cache_used_first` | 缓存优先使用 |

#### test_custom_source.py

| 测试类 | 测试方法 | 测试内容 |
|:--|:--|:--|
| `TestRSSFetch` | `test_fetch_rss20` | RSS 2.0 解析 |
| | `test_fetch_atom` | Atom 解析 |
| | `test_rss_with_mock` | Mock 数据测试 |
| | `test_rss_timeout` | 超时处理 |
| | `test_rss_retry` | 重试机制 |
| `TestWebpageFetch` | `test_fetch_with_selectors` | CSS 选择器解析 |
| | `test_relative_link_handling` | 相对链接处理 |
| | `test_content_truncation` | 内容截断 |
| | `test_max_items_limit` | 条目数限制 |
| `TestBatchFetch` | `test_fetch_multiple_sources` | 批量采集 |
| | `test_fetch_user_sources` | 用户数据源采集 |

#### test_source_health.py

| 测试类 | 测试方法 | 测试内容 |
|:--|:--|:--|
| `TestHealthChecker` | `test_check_healthy_source` | 健康源检测 |
| | `test_check_unhealthy_source` | 不健康源检测 |
| | `test_check_timeout` | 超时检测 |
| | `test_response_time_record` | 响应时间记录 |
| `TestHealthStatus` | `test_determine_healthy` | 健康判定 |
| | `test_determine_degraded` | 降级判定 |
| | `test_determine_unhealthy` | 不健康判定 |
| | `test_consecutive_failures_threshold` | 连续失败阈值 |
| `TestHealthAPI` | `test_health_endpoint` | API 端点响应 |
| | `test_health_summary` | 摘要数据正确 |

### Mock 策略

```python
# conftest.py 扩展

@pytest.fixture
def mock_v2ex_rss():
    """Mock V2EX RSS 响应"""
    return """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <item>
                <title>测试帖子</title>
                <link>https://www.v2ex.com/t/1</link>
                <description>测试内容</description>
            </item>
        </channel>
    </rss>"""

@pytest.fixture
def mock_http_client():
    """Mock HTTP 客户端"""
    with httpx.Client() as client:
        # 使用 respx 库 Mock HTTP 响应
        import respx
        with respx.mock:
            respx.get("https://test.com/rss").respond(content=mock_v2ex_rss)
            yield client
```

---

## 🔙 回滚策略

### 1. V2EX 镜像回滚

**触发条件**: 镜像功能上线后导致采集失败率上升

**回滚步骤**:

```bash
# 1. 禁用镜像功能（配置开关）
# 在 .env 中设置
V2EX_MIRROR_ENABLED=false

# 2. 或代码回滚
git revert <commit-hash>

# 3. 清除镜像统计数据
rm cache/v2ex_mirror_stats.json
```

**配置开关设计**:

```python
# config.py 新增
V2EX_MIRROR_ENABLED = _parse_bool(os.getenv("V2EX_MIRROR_ENABLED"), True)

# v2ex_radar.py 中使用
if not V2EX_MIRROR_ENABLED:
    # 使用原有逻辑（单站点）
    return self._fetch_with_fallback(source)
else:
    # 使用镜像逻辑
    return self._fetch_with_mirror_fallback(source)
```

### 2. 自定义数据源回滚

**触发条件**: 自定义采集器导致性能问题或错误

**回滚步骤**:

```bash
# 1. 禁用自定义数据源功能
# 在 .env 中设置
CUSTOM_SOURCE_ENABLED=false

# 2. 删除采集器文件（可选）
rm src/sensors/custom_source.py

# 3. 数据库无需回滚（UserSource 表已存在）
```

### 3. 前端改动回滚

**触发条件**: UI 显示异常或影响现有功能

**回滚步骤**:

```bash
# 1. 隐藏健康状态区域（CSS）
# 在 style.css 中添加
.source-health-section { display: none; }

# 2. 或删除新增代码
git revert <commit-hash>
```

### 4. 数据库变更回滚

**本次开发无数据库变更**:
- `UserSource` 表已存在
- 无新增表或字段

**无需数据库回滚操作**

---

## 📁 文件变更清单

| 文件 | 变更类型 | 变更内容 | 回滚难度 |
|:--|:--|:--|:--|
| `src/sensors/v2ex_radar.py` | 修改 | 新增镜像支持 | 低（配置开关） |
| `src/sensors/custom_source.py` | 新建 | 自定义采集器 | 低（删除文件） |
| `src/sensors/source_health.py` | 新建 | 健康检测模块 | 低（删除文件） |
| `src/sensors/__init__.py` | 修改 | 导出新模块 | 低 |
| `src/config.py` | 修改 | 新增配置开关 | 低 |
| `ui/static/sources.js` | 扩展 | 健康状态函数 | 低（独立函数） |
| `ui/static/style.css` | 扩展 | 健康状态样式 | 低（独立样式） |
| `ui/index.html` | 扩展 | 健康状态区域 | 低（独立区域） |
| `tests/test_v2ex_mirror.py` | 新建 | 镜像测试 | 低 |
| `tests/test_custom_source.py` | 新建 | 采集器测试 | 低 |
| `tests/test_source_health.py` | 新建 | 健康检测测试 | 低 |

---

## 📊 预期成果

### 功能成果

| 成果 | 说明 | 验收标准 |
|:--|:--|:--|
| V2EX 多镜像支持 | 4 个镜像站点 | 切换成功率 95%+ |
| 站点性能追踪 | 响应时间记录 | 数据持久化 |
| 自定义 RSS 采集 | feedparser 解析 | 支持 RSS 2.0/Atom |
| 自定义网页采集 | BeautifulSoup 解析 | CSS 选择器 |
| 健康检测 | 定期检测 | API 可访问 |
| 前端状态展示 | 可视化 | UI 正常显示 |

### 性能指标

| 指标 | 目标值 | 测量方法 |
|:--|:--|:--|
| V2EX 采集成功率 | 95%+ | 连续 100 次采集统计 |
| 自定义源成功率 | 90%+ | Mock 测试验证 |
| 健康检测响应 | < 10s | API 响应时间 |
| 测试覆盖率 | 80%+ | pytest --cov |

---

## 📅 开发排期

| 时间 | 任务 | 产出 |
|:--|:--|:--|
| 上午 2h | V2EX 镜像配置 + 追踪器 | `v2ex_radar.py` 修改 |
| 上午 2h | 镜像切换逻辑 + 测试 | `test_v2ex_mirror.py` |
| 下午 2h | 自定义采集器 | `custom_source.py` |
| 下午 1h | 健康检测模块 | `source_health.py` |
| 下午 1h | 前端展示 + 测试 | `sources.js` + 测试文件 |

---

## ⚠️ 风险与缓解

| 风险 | 严重程度 | 缓解措施 |
|:--|:--|:--|
| V2EX 镜像不稳定 | 中 | 多镜像 + 缓存 + 配置开关 |
| 第三方镜像法律风险 | 低 | 标注 `is_official=False`，用户可选 |
| 网页结构变化 | 中 | CSS 选择器可配置 |
| RSS 格式多样 | 低 | feedparser 兼容性好 |
| 前端兼容问题 | 低 | 独立模块，不影响现有功能 |

---

## ✅ 审核确认清单

请审核人员确认以下内容：

- [x] 镜像站点域名列表明确（4 个站点）
- [x] 站点可用性判断逻辑清晰
- [x] 失败切换策略完整
- [x] 解析库选型合理（feedparser + BeautifulSoup）
- [x] 健康检测参数明确（频率、阈值）
- [x] 测试用例清单完整（30+ 测试）
- [x] 回滚策略完整（配置开关 + 代码回滚）
- [x] 前端改动范围明确（独立模块）
- [x] 依赖包已确认（无需新增）
- [x] 无数据库变更

---

## 📝 审核意见

| 审核项 | 审核意见 | 备注 |
|:--|:--|:--|
| 功能必要性 | | |
| 技术方案细节 | | |
| 测试方案 | | |
| 回滚策略 | | |
| 前端兼容 | | |
| **整体结论** | | |

**审核人**：________________
**审核日期**：________________
**审核签字**：________________

---

## 📚 相关文档

| 文档 | 说明 |
|:--|:--|:--|
| `P2_DEV_PLAN.md` | P2 阶段总体计划 |
| `P2-3_DEV_REPORT.md` | P2-3 完成报告 |
| `README.md` | 项目说明 |
| `requirements.txt` | 依赖包清单 |
| `src/sensors/v2ex_radar.py` | V2EX 雷达现有实现 |
| `ui/static/sources.js` | 前端数据源模块 |