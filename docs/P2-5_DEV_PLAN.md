# P2-5 阶段开发计划

> 创建时间：2026-04-04
> 开发阶段：P2-5（Prompt 验证增强）
> 状态：✅ 已完成

---

## 📋 开发概览

| 任务 | 预估工时 | 状态 |
|:--|:--|:--|
| Prompt 验证器实现 | 0.3 天 | ⏳ 待开始 |
| API 路由集成 | 0.2 天 | ⏳ 待开始 |
| 前端提示增强 | 0.3 天 | ⏳ 待开始 |
| 测试编写 | 0.2 天 | ⏳ 待开始 |

**总预估工时：1 天**

---

## 🎯 功能目标

### 当前状态

- ✅ 长度验证（1-50000字符）
- ❌ 无占位符验证
- ❌ 无语法检查
- ❌ 前端提示不完整

### 目标状态

- ✅ 长度验证（保持）
- ✅ 占位符存在性验证
- ✅ 未知占位符检测
- ✅ 前端实时验证提示
- ✅ 占位符自动补全
- ✅ 占位符列表展示

---

## 🔧 技术方案

### 1. Prompt 验证器

创建 `src/utils/prompt_validator.py`：

```python
from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    used_placeholders: List[str]
    missing_placeholders: List[str]
    unknown_placeholders: List[str]

class PromptValidator:
    """Prompt 验证器"""

    # 各工具支持的占位符
    PLACEHOLDERS = {
        "mission": ["{date_str}", "{time_str}"],
        "bounty_v2ex": [],  # 无占位符
        "bounty_chrome": [],  # 无占位符
        "alpha": ["{query}"],
        "revenue": ["{content}"],
    }

    # 占位符描述
    PLACEHOLDER_DESC = {
        "{date_str}": "日期字符串（如 2026-04-04）",
        "{time_str}": "时间字符串（如 10:30:00）",
        "{query}": "搜索查询词（Alpha雷达专用）",
        "{content}": "日报内容（营收分析师专用）",
    }

    MIN_LENGTH = 1
    MAX_LENGTH = 50000

    def validate(self, tool_type: str, prompt: str) -> ValidationResult:
        """
        验证 Prompt

        Args:
            tool_type: 工具类型
            prompt: Prompt 内容

        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        used = []
        missing = []
        unknown = []

        # 1. 验证工具类型
        if tool_type not in self.PLACEHOLDERS:
            errors.append(f"无效的工具类型: {tool_type}")
            return ValidationResult(False, errors, warnings, used, missing, unknown)

        # 2. 验证长度
        if len(prompt) < self.MIN_LENGTH:
            errors.append(f"Prompt 长度不能为空")
        elif len(prompt) > self.MAX_LENGTH:
            errors.append(f"Prompt 长度超过限制 ({self.MAX_LENGTH} 字符)")

        # 3. 提取使用的占位符
        pattern = r'\{[a-zA-Z_][a-zA-Z0-9_]*\}'
        found = re.findall(pattern, prompt)
        used = list(set(found))

        # 4. 检查必需占位符（可选）
        required = self.PLACEHOLDERS.get(tool_type, [])
        for p in required:
            if p not in used:
                missing.append(p)
                # 占位符缺失是警告而非错误（某些 Prompt 可能不需要）
                warnings.append(f"缺少占位符 {p}: {self.PLACEHOLDER_DESC.get(p, '')}")

        # 5. 检查未知占位符
        all_known = set(self.PLACEHOLDER_DESC.keys())
        for p in used:
            if p not in all_known:
                unknown.append(p)
                warnings.append(f"未知占位符 {p}，运行时可能无法替换")

        is_valid = len(errors) == 0

        return ValidationResult(is_valid, errors, warnings, used, missing, unknown)

    def get_supported_placeholders(self, tool_type: str) -> List[dict]:
        """
        获取工具支持的占位符列表

        Returns:
            List[dict]: 占位符信息列表
        """
        if tool_type not in self.PLACEHOLDERS:
            return []

        result = []
        for p in self.PLACEHOLDERS[tool_type]:
            result.append({
                "placeholder": p,
                "description": self.PLACEHOLDER_DESC.get(p, ""),
                "required": False,  # 所有占位符都是可选的
            })
        return result
```

### 2. API 路由集成

在 `src/config_router.py` 中添加验证端点：

```python
# 新增端点
@router.get(
    "/prompt/{tool_type}/placeholders",
    summary="获取支持的占位符",
)
async def get_placeholders(tool_type: str):
    """获取指定工具支持的占位符列表"""
    validator = PromptValidator()
    placeholders = validator.get_supported_placeholders(tool_type)
    return {"tool_type": tool_type, "placeholders": placeholders}

@router.post(
    "/prompt/{tool_type}/validate",
    summary="验证 Prompt",
)
async def validate_prompt(
    tool_type: str,
    request: PromptUpdateRequest,
):
    """验证 Prompt 内容"""
    validator = PromptValidator()
    result = validator.validate(tool_type, request.content)
    return {
        "is_valid": result.is_valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "used_placeholders": result.used_placeholders,
        "missing_placeholders": result.missing_placeholders,
        "unknown_placeholders": result.unknown_placeholders,
    }
```

修改保存逻辑，在保存前进行验证：

```python
@router.put("/prompt/{tool_type}")
async def update_prompt(...):
    # 新增：验证 Prompt
    validator = PromptValidator()
    result = validator.validate(tool_type, request.content)

    if not result.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": result.errors, "warnings": result.warnings}
        )

    # 保存逻辑...
```

### 3. 前端提示增强

修改 `ui/static/prompt-config.js`：

```javascript
// 新增：占位符提示组件
function renderPlaceholderHints(toolType) {
  // 获取支持的占位符
  fetch(`/api/user-config/prompt/${toolType}/placeholders`)
    .then(res => res.json())
    .then(data => {
      // 渲染占位符列表
      const html = data.placeholders.map(p => `
        <div class="placeholder-item">
          <code class="placeholder-code">${p.placeholder}</code>
          <span class="placeholder-desc">${p.description}</span>
          <button onclick="insertPlaceholder('${p.placeholder}')">插入</button>
        </div>
      `).join('');
      // ...
    });
}

// 新增：实时验证
function validatePromptContent(toolType, content) {
  fetch(`/api/user-config/prompt/${toolType}/validate`, {
    method: 'POST',
    body: JSON.stringify({ content })
  })
    .then(res => res.json())
    .then(result => {
      // 显示验证结果
      if (result.errors.length > 0) {
        showValidationErrors(result.errors);
      }
      if (result.warnings.length > 0) {
        showValidationWarnings(result.warnings);
      }
    });
}

// 新增：占位符自动补全
function setupAutocomplete(textarea) {
  textarea.addEventListener('input', (e) => {
    const value = e.target.value;
    const cursorPos = e.target.selectionStart;

    // 检测是否正在输入占位符
    const beforeCursor = value.substring(0, cursorPos);
    const match = beforeCursor.match(/\{[a-zA-Z_]*$/);

    if (match) {
      showAutocompleteDropdown(match[0]);
    }
  });
}
```

---

## 📁 文件变更清单

| 文件 | 变更类型 | 说明 |
|:--|:--|:--|
| `src/utils/prompt_validator.py` | 新建 | Prompt 验证器 |
| `src/utils/__init__.py` | 修改 | 导出验证器 |
| `src/config_router.py` | 修改 | 新增验证端点，集成验证逻辑 |
| `ui/static/prompt-config.js` | 修改 | 增强前端提示和验证 |
| `ui/static/style.css` | 修改 | 新增验证提示样式 |
| `tests/test_prompt_validator.py` | 新建 | 验证器测试 |

---

## 🧪 测试用例

### 后端测试

| 测试类 | 测试内容 |
|:--|:--|
| TestPromptValidator | 验证器核心功能测试 |
| TestPlaceholderValidation | 占位符验证测试 |
| TestLengthValidation | 长度验证测试 |
| TestUnknownPlaceholder | 未知占位符检测测试 |
| TestValidateAPI | API 端点测试 |

### 测试用例详情

```python
class TestPromptValidator:
    def test_valid_prompt(self):
        """测试有效的 Prompt"""

    def test_empty_prompt(self):
        """测试空 Prompt"""

    def test_too_long_prompt(self):
        """测试超长 Prompt"""

    def test_invalid_tool_type(self):
        """测试无效工具类型"""

class TestPlaceholderValidation:
    def test_used_placeholders_detected(self):
        """测试已使用占位符检测"""

    def test_missing_placeholders_warning(self):
        """测试缺失占位符警告"""

    def test_unknown_placeholders_warning(self):
        """测试未知占位符警告"""

    def test_no_placeholders_required(self):
        """测试无占位符工具（bounty_v2ex）"""

class TestValidateAPI:
    def test_validate_endpoint(self):
        """测试验证端点"""

    def test_placeholders_endpoint(self):
        """测试占位符列表端点"""

    def test_save_with_invalid_prompt(self):
        """测试保存无效 Prompt 被拒绝"""
```

---

## 📊 预期成果

| 成果 | 说明 |
|:--|:--|
| 占位符验证 | 检测缺失和未知占位符 |
| 实时提示 | 前端编辑时实时验证 |
| 占位符列表 | 显示各工具支持的占位符 |
| 自动补全 | 输入 `{` 时显示补全选项 |
| API 端点 | 验证和占位符查询端点 |

---

## ⚠️ 注意事项

1. **占位符可选性**：所有占位符都是可选的，缺失只产生警告而非错误
2. **向后兼容**：现有 Prompt 保存逻辑不受影响
3. **前端性能**：实时验证使用防抖，避免频繁请求

---

## ✅ 审核确认

请审核人员确认以下内容：

- [ ] 功能范围合理
- [ ] 技术方案可行
- [ ] 测试覆盖完整

**审核人**：________________
**审核日期**：________________