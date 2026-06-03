/**
 * prompt-config.js - Prompt 配置模块
 * 处理用户自定义 Prompt 的加载、编辑和保存
 * 支持占位符提示、实时验证和自动补全
 */

// 工具类型配置
const PROMPT_TOOLS = [
  { key: 'mission', name: '情报日报', icon: '📊', desc: '从 10+ 数据源抓取，生成 8 大板块中文日报' },
  { key: 'bounty_v2ex', name: '赏金猎人 - V2EX', icon: '💰', desc: 'V2EX 急单筛选规则和关键词' },
  { key: 'alpha', name: 'Alpha 雷达', icon: '⛏️', desc: 'Web3/Solana 开源项目搜索 Prompt' },
  { key: 'revenue', name: '营收分析师', icon: '🏗️', desc: '商业机会分析 Prompt' }
];

// 当前编辑状态
let currentPromptData = {};
let editingToolType = null;
let currentPlaceholders = [];
let validationTimeout = null;

/**
 * 获取设备 ID
 */
function getDeviceId() {
  return localStorage.getItem('prism_device_id');
}

/**
 * 检查是否已激活
 */
function isActivated() {
  return !!getDeviceId();
}

/**
 * 初始化 Prompt 配置
 */
async function initPromptConfig() {
  await loadPromptConfigs();
}

/**
 * 加载所有 Prompt 配置
 */
async function loadPromptConfigs() {
  const container = document.getElementById('prompt-config-content');
  if (!container) return;

  // 检查激活状态
  const deviceId = getDeviceId();
  if (!deviceId) {
    container.innerHTML = `
      <div class="prompt-login-notice">
        <div class="notice-icon">🔐</div>
        <div class="notice-text">请先激活以配置自定义 Prompt</div>
      </div>
    `;
    return;
  }

  try {
    const res = await fetch('/api/user-config/prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    if (res.status === 401) {
      container.innerHTML = `
        <div class="prompt-login-notice">
          <div class="notice-icon">🔐</div>
          <div class="notice-text">设备未激活，请先激活</div>
        </div>
      `;
      return;
    }

    if (!res.ok) throw new Error('加载失败');

    const { prompts } = await res.json();
    currentPromptData = {};
    prompts.forEach(p => { currentPromptData[p.tool_type] = p; });

    renderPromptList(container);
  } catch (err) {
    console.error('加载 Prompt 配置失败:', err);
    container.innerHTML = `
      <div class="prompt-error">
        <div class="error-icon">⚠️</div>
        <div class="error-text">加载失败: ${err.message}</div>
        <button onclick="loadPromptConfigs()" class="retry-btn">重试</button>
      </div>
    `;
  }
}

/**
 * 渲染 Prompt 列表
 */
function renderPromptList(container) {
  const html = `
    <div class="prompt-list-header">
      <h3>功能模块配置</h3>
      <p>自定义各功能的 Prompt，修改后运行对应功能时将使用新配置</p>
    </div>
    <div class="prompt-cards">
      ${PROMPT_TOOLS.map(tool => {
        const data = currentPromptData[tool.key] || {};
        const hasCustom = data.has_custom || false;
        return `
          <div class="prompt-card ${hasCustom ? 'has-custom' : ''}" onclick="openPromptEditor('${tool.key}')">
            <div class="prompt-card-icon">${tool.icon}</div>
            <div class="prompt-card-info">
              <div class="prompt-card-title">
                ${tool.name}
                ${hasCustom ? '<span class="custom-badge">已自定义</span>' : ''}
              </div>
              <div class="prompt-card-desc">${tool.desc}</div>
            </div>
            <div class="prompt-card-action">
              <span class="action-text">${hasCustom ? '编辑' : '配置'}</span>
              <span class="action-arrow">→</span>
            </div>
          </div>
        `;
      }).join('')}
    </div>
  `;
  container.innerHTML = html;
}

/**
 * 加载工具支持的占位符
 */
async function loadPlaceholders(toolType) {
  try {
    const res = await fetch(`/api/user-config/prompt/${toolType}/placeholders`);
    if (!res.ok) return [];

    const { placeholders } = await res.json();
    currentPlaceholders = placeholders;
    return placeholders;
  } catch (err) {
    console.error('加载占位符失败:', err);
    return [];
  }
}

/**
 * 打开 Prompt 编辑器
 */
async function openPromptEditor(toolType) {
  const tool = PROMPT_TOOLS.find(t => t.key === toolType);
  if (!tool) return;

  editingToolType = toolType;
  const data = currentPromptData[toolType] || {};

  // 加载占位符
  const placeholders = await loadPlaceholders(toolType);

  // 创建编辑器模态框
  const modal = document.createElement('div');
  modal.id = 'prompt-editor-modal';
  modal.className = 'prompt-modal';
  modal.innerHTML = `
    <div class="prompt-modal-overlay" onclick="closePromptEditor()"></div>
    <div class="prompt-modal-content prompt-editor-wide">
      <div class="prompt-modal-header">
        <div class="header-left">
          <span class="tool-icon">${tool.icon}</span>
          <h3>${tool.name} Prompt</h3>
        </div>
        <button class="close-btn" onclick="closePromptEditor()">✕</button>
      </div>
      <div class="prompt-modal-body">
        <div class="editor-status">
          ${data.has_custom
            ? '<span class="status-custom">✓ 使用自定义配置</span>'
            : '<span class="status-default">使用默认配置</span>'}
        </div>

        ${placeholders.length > 0 ? `
          <div class="placeholder-panel">
            <div class="placeholder-panel-header">
              <span class="placeholder-icon">📝</span>
              <span>支持的占位符</span>
              <span class="placeholder-count">${placeholders.length} 个</span>
            </div>
            <div class="placeholder-list">
              ${placeholders.map(p => `
                <div class="placeholder-item" onclick="insertPlaceholder('${p.placeholder}')">
                  <code class="placeholder-code">${p.placeholder}</code>
                  <span class="placeholder-desc">${p.description}</span>
                  ${p.example ? `<span class="placeholder-example">示例: ${p.example}</span>` : ''}
                  <button class="placeholder-insert-btn" title="插入">+</button>
                </div>
              `).join('')}
            </div>
          </div>
        ` : `
          <div class="placeholder-panel placeholder-none">
            <div class="placeholder-panel-header">
              <span class="placeholder-icon">📝</span>
              <span>此工具无占位符</span>
            </div>
            <div class="placeholder-empty-text">
              该工具的 Prompt 不需要占位符，可直接编辑内容。
            </div>
          </div>
        `}

        <div class="editor-label">Prompt 内容</div>
        <div class="textarea-wrapper">
          <textarea
            id="prompt-editor-textarea"
            class="prompt-textarea"
            placeholder="输入自定义 Prompt..."
            oninput="onPromptInput()"
          >${data.prompt_content || ''}</textarea>
          <div id="autocomplete-dropdown" class="autocomplete-dropdown hidden"></div>
        </div>

        <div id="validation-result" class="validation-result hidden"></div>

        <div class="editor-hint">
          <strong>提示：</strong>
          <ul>
            <li>点击上方占位符可快速插入</li>
            <li>输入 <code>{</code> 会触发占位符自动补全</li>
            <li>留空或重置将使用默认 Prompt</li>
          </ul>
        </div>
      </div>
      <div class="prompt-modal-footer">
        <button class="btn-reset" onclick="resetPrompt('${toolType}')">
          <span>↺</span> 重置为默认
        </button>
        <div class="footer-right">
          <button class="btn-cancel" onclick="closePromptEditor()">取消</button>
          <button class="btn-save" onclick="savePrompt('${toolType}')">
            <span>💾</span> 保存
          </button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(modal);

  // 添加动画
  requestAnimationFrame(() => {
    modal.classList.add('show');
  });

  // 初始验证
  validatePromptDebounced();
}

/**
 * 处理 Prompt 输入
 */
function onPromptInput() {
  const textarea = document.getElementById('prompt-editor-textarea');
  const value = textarea.value;
  const cursorPos = textarea.selectionStart;

  // 检测占位符自动补全
  const beforeCursor = value.substring(0, cursorPos);
  const match = beforeCursor.match(/\{[a-zA-Z_]*$/);

  if (match && currentPlaceholders.length > 0) {
    showAutocompleteDropdown(match[0], cursorPos);
  } else {
    hideAutocompleteDropdown();
  }

  // 实时验证（防抖）
  validatePromptDebounced();
}

/**
 * 显示自动补全下拉框
 */
function showAutocompleteDropdown(partial, cursorPos) {
  const dropdown = document.getElementById('autocomplete-dropdown');
  if (!dropdown) return;

  const search = partial.toLowerCase();
  const suggestions = currentPlaceholders.filter(p =>
    p.placeholder.toLowerCase().startsWith(search)
  );

  if (suggestions.length === 0) {
    hideAutocompleteDropdown();
    return;
  }

  dropdown.innerHTML = suggestions.map(p => `
    <div class="autocomplete-item" onclick="selectAutocomplete('${p.placeholder}', ${cursorPos})">
      <code>${p.placeholder}</code>
      <span class="autocomplete-desc">${p.description}</span>
    </div>
  `).join('');

  dropdown.classList.remove('hidden');
}

/**
 * 隐藏自动补全下拉框
 */
function hideAutocompleteDropdown() {
  const dropdown = document.getElementById('autocomplete-dropdown');
  if (dropdown) {
    dropdown.classList.add('hidden');
  }
}

/**
 * 选择自动补全项
 */
function selectAutocomplete(placeholder, cursorPos) {
  const textarea = document.getElementById('prompt-editor-textarea');
  if (!textarea) return;

  const value = textarea.value;
  const beforeCursor = value.substring(0, cursorPos);
  const afterCursor = value.substring(cursorPos);

  // 找到 { 的位置
  const bracePos = beforeCursor.lastIndexOf('{');
  const newValue = value.substring(0, bracePos) + placeholder + afterCursor;

  textarea.value = newValue;

  // 设置光标位置
  const newPos = bracePos + placeholder.length;
  textarea.setSelectionRange(newPos, newPos);
  textarea.focus();

  hideAutocompleteDropdown();
  validatePromptDebounced();
}

/**
 * 插入占位符
 */
function insertPlaceholder(placeholder) {
  const textarea = document.getElementById('prompt-editor-textarea');
  if (!textarea) return;

  const cursorPos = textarea.selectionStart;
  const value = textarea.value;

  const newValue = value.substring(0, cursorPos) + placeholder + value.substring(cursorPos);
  textarea.value = newValue;

  // 设置光标位置
  const newPos = cursorPos + placeholder.length;
  textarea.setSelectionRange(newPos, newPos);
  textarea.focus();

  validatePromptDebounced();
}

/**
 * 防抖验证
 */
function validatePromptDebounced() {
  if (validationTimeout) {
    clearTimeout(validationTimeout);
  }

  validationTimeout = setTimeout(() => {
    validatePromptContent();
  }, 500);
}

/**
 * 验证 Prompt 内容
 */
async function validatePromptContent() {
  if (!editingToolType) return;

  const textarea = document.getElementById('prompt-editor-textarea');
  const content = textarea?.value?.trim() || '';
  const resultDiv = document.getElementById('validation-result');

  if (!resultDiv) return;

  // 空内容不显示验证结果
  if (!content) {
    resultDiv.classList.add('hidden');
    return;
  }

  try {
    const res = await fetch(`/api/user-config/prompt/${editingToolType}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });

    if (!res.ok) {
      resultDiv.classList.add('hidden');
      return;
    }

    const result = await res.json();

    // 渲染验证结果
    let html = '';

    if (result.is_valid) {
      if (result.warnings.length === 0 && result.used_placeholders.length === 0) {
        resultDiv.classList.add('hidden');
        return;
      }

      html = '<div class="validation-valid">';

      if (result.used_placeholders.length > 0) {
        html += `
          <div class="validation-used">
            <span class="validation-icon">✓</span>
            已使用占位符: ${result.used_placeholders.map(p => `<code>${p}</code>`).join(', ')}
          </div>
        `;
      }

      if (result.warnings.length > 0) {
        html += `
          <div class="validation-warnings">
            <span class="validation-icon">⚠️</span>
            <div class="warnings-list">
              ${result.warnings.map(w => `<div class="warning-item">${w}</div>`).join('')}
            </div>
          </div>
        `;
      }

      html += '</div>';
    } else {
      html = `
        <div class="validation-invalid">
          <span class="validation-icon">✗</span>
          <div class="errors-list">
            ${result.errors.map(e => `<div class="error-item">${e}</div>`).join('')}
          </div>
          ${result.warnings.length > 0 ? `
            <div class="validation-warnings">
              <span class="validation-icon">⚠️</span>
              <div class="warnings-list">
                ${result.warnings.map(w => `<div class="warning-item">${w}</div>`).join('')}
              </div>
            </div>
          ` : ''}
        </div>
      `;
    }

    resultDiv.innerHTML = html;
    resultDiv.classList.remove('hidden');

  } catch (err) {
    console.error('验证失败:', err);
    resultDiv.classList.add('hidden');
  }
}

/**
 * 关闭 Prompt 编辑器
 */
function closePromptEditor() {
  const modal = document.getElementById('prompt-editor-modal');
  if (modal) {
    modal.classList.remove('show');
    setTimeout(() => modal.remove(), 300);
  }
  editingToolType = null;
  currentPlaceholders = [];

  if (validationTimeout) {
    clearTimeout(validationTimeout);
    validationTimeout = null;
  }
}

/**
 * 保存 Prompt
 */
async function savePrompt(toolType) {
  const textarea = document.getElementById('prompt-editor-textarea');
  const content = textarea?.value?.trim() || '';

  const deviceId = getDeviceId();
  if (!deviceId) {
    showToast('请先激活', 'err');
    return;
  }

  // 先验证
  try {
    const validateRes = await fetch(`/api/user-config/prompt/${toolType}/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content })
    });

    if (validateRes.ok) {
      const validateResult = await validateRes.json();

      if (!validateResult.is_valid) {
        showToast(`✗ ${validateResult.errors[0]}`, 'err');
        return;
      }

      // 有警告时提示用户
      if (validateResult.warnings.length > 0) {
        const proceed = confirm(`存在警告:\n${validateResult.warnings.join('\n')}\n\n是否继续保存?`);
        if (!proceed) return;
      }
    }
  } catch (err) {
    // 验证失败不影响保存流程
    console.warn('验证请求失败:', err);
  }

  const saveBtn = document.querySelector('.btn-save');
  const originalText = saveBtn.innerHTML;
  saveBtn.innerHTML = '<span>⏳</span> 保存中...';
  saveBtn.disabled = true;

  try {
    const res = await fetch(`/api/user-config/prompt/${toolType}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId, content })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '保存失败');
    }

    showToast('✓ Prompt 已保存', 'ok');

    // 更新本地数据
    currentPromptData[toolType] = {
      ...currentPromptData[toolType],
      has_custom: true,
      prompt_content: content
    };

    closePromptEditor();

    // 刷新列表
    const container = document.getElementById('prompt-config-content');
    if (container) renderPromptList(container);

  } catch (err) {
    showToast(`✗ ${err.message}`, 'err');
  } finally {
    saveBtn.innerHTML = originalText;
    saveBtn.disabled = false;
  }
}

/**
 * 重置 Prompt
 */
async function resetPrompt(toolType) {
  if (!confirm('确定要重置为默认 Prompt 吗？')) return;

  const deviceId = getDeviceId();
  if (!deviceId) {
    showToast('请先激活', 'err');
    return;
  }

  try {
    const res = await fetch(`/api/user-config/prompt/${toolType}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '重置失败');
    }

    showToast('✓ 已重置为默认 Prompt', 'ok');

    // 更新本地数据
    currentPromptData[toolType] = {
      ...currentPromptData[toolType],
      has_custom: false
    };

    // 重新加载以获取默认内容
    await loadPromptConfigs();
    closePromptEditor();

  } catch (err) {
    showToast(`✗ ${err.message}`, 'err');
  }
}

// 导出模块
window.initPromptConfig = initPromptConfig;
window.loadPromptConfigs = loadPromptConfigs;
window.openPromptEditor = openPromptEditor;
window.closePromptEditor = closePromptEditor;
window.savePrompt = savePrompt;
window.resetPrompt = resetPrompt;
window.onPromptInput = onPromptInput;
window.insertPlaceholder = insertPlaceholder;
window.selectAutocomplete = selectAutocomplete;