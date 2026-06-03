/**
 * marketplace.js - Prompt广场模块
 * v2.1 激活码架构：使用 device_id 认证
 */

// 频道配置
const MARKETPLACE_CHANNELS = [
  { key: 'mission', name: '情报日报', icon: '📊' },
  { key: 'alpha', name: 'Alpha雷达', icon: '⛏️' },
  { key: 'bounty_v2ex', name: '赏金·V2EX', icon: '💰' },
  { key: 'revenue', name: '营收分析', icon: '🏗️' }
];

// 当前状态
let currentChannel = 'my_prompts';
let templatesCache = {};
let expandedTemplateId = null;

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
 * 初始化广场
 */
async function initMarketplace() {
  await loadChannelContent(currentChannel);
}

/**
 * 切换频道
 */
function switchMarketplaceChannel(channel) {
  if (currentChannel === channel) return;
  currentChannel = channel;

  // 更新 Tab 样式
  const myPromptsTab = document.getElementById('marketplace-tab-my_prompts');
  if (myPromptsTab) {
    if (channel === 'my_prompts') {
      myPromptsTab.classList.add('active');
      myPromptsTab.style.borderColor = 'var(--accent)';
      myPromptsTab.style.color = 'var(--text)';
    } else {
      myPromptsTab.classList.remove('active');
      myPromptsTab.style.borderColor = 'transparent';
      myPromptsTab.style.color = 'var(--text-secondary)';
    }
  }

  MARKETPLACE_CHANNELS.forEach(ch => {
    const tab = document.getElementById(`marketplace-tab-${ch.key}`);
    if (tab) {
      if (ch.key === channel) {
        tab.classList.add('active');
        tab.style.borderColor = 'var(--accent)';
        tab.style.color = 'var(--text)';
      } else {
        tab.classList.remove('active');
        tab.style.borderColor = 'transparent';
        tab.style.color = 'var(--text-secondary)';
      }
    }
  });

  loadChannelContent(channel);
}

/**
 * 加载频道内容
 */
async function loadChannelContent(channel) {
  if (channel === 'my_prompts') {
    await loadMyPrompts();
  } else {
    await loadTemplates(channel);
  }
}

/**
 * 加载"我的Prompt"
 */
async function loadMyPrompts() {
  const container = document.getElementById('marketplace-content');
  if (!container) return;

  const deviceId = getDeviceId();
  if (!deviceId) {
    container.innerHTML = `
      <div class="my-prompts-notice">
        <div class="notice-icon">🔐</div>
        <div class="notice-title">请先激活</div>
        <div class="notice-text">激活后可配置自定义 Prompt，个性化情报生成</div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="flex items-center justify-center py-12 text-text-secondary">
      <svg class="w-5 h-5 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      加载中...
    </div>
  `;

  try {
    const res = await fetch('/api/user-config/prompt', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    if (res.status === 401) {
      container.innerHTML = `
        <div class="my-prompts-notice">
          <div class="notice-icon">🔐</div>
          <div class="notice-title">设备未激活</div>
          <div class="notice-text">请先激活以配置自定义 Prompt</div>
        </div>
      `;
      return;
    }

    if (!res.ok) throw new Error('加载失败');

    const { prompts } = await res.json();
    renderMyPrompts(container, prompts);
  } catch (err) {
    console.error('加载我的 Prompt 失败:', err);
    container.innerHTML = `
      <div class="marketplace-empty">
        <div class="empty-icon">⚠️</div>
        <div class="empty-text">加载失败: ${err.message}</div>
        <button onclick="loadMyPrompts()" class="retry-btn">重试</button>
      </div>
    `;
  }
}

/**
 * 渲染"我的Prompt"列表
 */
function renderMyPrompts(container, prompts) {
  const promptMap = {};
  prompts.forEach(p => { promptMap[p.tool_type] = p; });

  const tools = [
    { key: 'mission', name: '情报日报', icon: '📊', desc: '从 10+ 数据源抓取，生成 8 大板块中文日报' },
    { key: 'bounty_v2ex', name: '赏金猎人 - V2EX', icon: '💰', desc: '扫描市场需求信号，发现真实存在的机会缺口' },
    { key: 'alpha', name: 'Alpha 雷达', icon: '⛏️', desc: '使用 Grok 搜索 X/Twitter 上的行业动态' },
    { key: 'revenue', name: '营收分析师', icon: '🏗️', desc: '基于今日情报日报，由 AI 深度解读行业动态' }
  ];

  const html = `
    <div class="my-prompts-header">
      <h3>自定义 Prompt</h3>
      <p>为各功能模块配置专属 Prompt，运行时将使用您的自定义配置</p>
    </div>
    <div class="prompt-cards">
      ${tools.map(tool => {
        const data = promptMap[tool.key] || {};
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
 * 打开 Prompt 编辑器
 */
async function openPromptEditor(toolType) {
  const tool = [
    { key: 'mission', name: '情报日报', icon: '📊' },
    { key: 'bounty_v2ex', name: '赏金猎人 - V2EX', icon: '💰' },
    { key: 'alpha', name: 'Alpha 雷达', icon: '⛏️' },
    { key: 'revenue', name: '营收分析师', icon: '🏗️' }
  ].find(t => t.key === toolType);

  if (!tool) return;

  const deviceId = getDeviceId();
  if (!deviceId) {
    alert('请先激活');
    return;
  }

  let currentPrompt = '';
  let defaultPromptContent = '';
  try {
    const res = await fetch('/api/user-config/prompt/' + toolType, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });
    if (res.ok) {
      const data = await res.json();
      currentPrompt = data.prompt_content || '';
      defaultPromptContent = data.default_prompt || '';
    }
  } catch (e) {
    console.error('获取 Prompt 失败:', e);
  }

  let placeholders = [];
  try {
    const res = await fetch(`/api/user-config/prompt/${toolType}/placeholders`);
    if (res.ok) {
      const data = await res.json();
      placeholders = data.placeholders || [];
    }
  } catch (e) {
    console.error('获取占位符失败:', e);
  }

  const modal = document.createElement('div');
  modal.id = 'prompt-editor-modal';
  modal.className = 'prompt-modal-overlay';
  modal.dataset.defaultPrompt = defaultPromptContent;
  modal.innerHTML = `
    <div class="prompt-modal-content">
      <div class="prompt-modal-header">
        <h3>${tool.icon} ${tool.name} - Prompt 配置</h3>
        <button onclick="closePromptEditor()" class="close-btn">&times;</button>
      </div>
      <div class="prompt-modal-body">
        ${placeholders.length > 0 ? `
          <div class="placeholder-hints">
            <div class="hint-title">支持的占位符</div>
            <div class="hint-list">
              ${placeholders.map(p => `<span class="hint-tag" title="${p.description}">${p.placeholder}</span>`).join('')}
            </div>
          </div>
        ` : ''}
        <div class="form-group">
          <label>自定义 Prompt</label>
          <textarea id="prompt-editor-textarea" rows="15" placeholder="输入自定义 Prompt...">${currentPrompt}</textarea>
        </div>
      </div>
      <div class="prompt-modal-footer">
        <button onclick="resetPromptToDefault()" class="btn btn-secondary">重置为默认</button>
        <button onclick="closePromptEditor()" class="btn btn-secondary">取消</button>
        <button onclick="savePromptConfig('${toolType}')" class="btn btn-primary">保存</button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
}

/**
 * 重置为默认 Prompt
 */
function resetPromptToDefault() {
  const modal = document.getElementById('prompt-editor-modal');
  const textarea = document.getElementById('prompt-editor-textarea');
  if (!modal || !textarea) return;

  const defaultPrompt = modal.dataset.defaultPrompt || '';
  if (defaultPrompt) {
    textarea.value = defaultPrompt;
    textarea.style.borderColor = 'var(--accent)';
    setTimeout(() => { textarea.style.borderColor = ''; }, 1000);
  } else {
    alert('未找到默认 Prompt');
  }
}

/**
 * 关闭 Prompt 编辑器
 */
function closePromptEditor() {
  const modal = document.getElementById('prompt-editor-modal');
  if (modal) modal.remove();
}

/**
 * 保存 Prompt 配置
 */
async function savePromptConfig(toolType) {
  const textarea = document.getElementById('prompt-editor-textarea');
  if (!textarea) return;

  const content = textarea.value.trim();
  const deviceId = getDeviceId();
  if (!deviceId) {
    alert('请先激活');
    return;
  }

  try {
    const res = await fetch(`/api/user-config/prompt/${toolType}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId, content: content })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '保存失败');
    }

    alert('保存成功');
    closePromptEditor();
    loadMyPrompts();
  } catch (err) {
    alert('保存失败: ' + err.message);
  }
}

/**
 * 加载模板列表
 */
async function loadTemplates(toolType) {
  const container = document.getElementById('marketplace-content');
  if (!container) return;

  container.innerHTML = `
    <div class="flex items-center justify-center py-12 text-text-secondary">
      <svg class="w-5 h-5 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      加载模板中...
    </div>
  `;

  try {
    const res = await fetch(`/api/marketplace/templates?tool_type=${toolType}`);
    if (!res.ok) throw new Error('加载失败');

    const { templates, total } = await res.json();
    templatesCache[toolType] = templates;
    renderTemplates(container, templates, toolType);
  } catch (err) {
    console.error('加载模板失败:', err);
    container.innerHTML = `
      <div class="marketplace-empty">
        <div class="empty-icon">⚠️</div>
        <div class="empty-text">加载失败: ${err.message}</div>
        <button onclick="loadTemplates('${toolType}')" class="retry-btn">重试</button>
      </div>
    `;
  }
}

/**
 * 渲染模板列表
 */
function renderTemplates(container, templates, toolType) {
  if (!templates || templates.length === 0) {
    container.innerHTML = `
      <div class="marketplace-empty">
        <div class="empty-icon">📭</div>
        <div class="empty-text">暂无模板</div>
      </div>
    `;
    return;
  }

  container.innerHTML = `
    <div class="marketplace-grid">
      ${templates.map(t => renderTemplateCard(t)).join('')}
    </div>
  `;
}

/**
 * 渲染单个模板卡片
 */
function renderTemplateCard(template) {
  const isExpanded = expandedTemplateId === template.id;
  const tags = template.tags || [];

  return `
    <div class="template-card ${isExpanded ? 'expanded' : ''}" data-id="${template.id}">
      <div class="template-card-header" onclick="toggleTemplateExpand(${template.id})">
        <div class="template-info">
          <div class="template-title">
            ${template.is_official ? '<span class="official-badge">官方</span>' : ''}
            ${template.title}
          </div>
          <div class="template-desc">${template.description}</div>
          ${tags.length > 0 ? `
            <div class="template-tags">
              ${tags.slice(0, 3).map(tag => `<span class="template-tag">${tag}</span>`).join('')}
            </div>
          ` : ''}
        </div>
        <div class="template-stats">
          <span class="import-count">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
            </svg>
            ${template.import_count || 0}
          </span>
          <span class="expand-icon">${isExpanded ? '▲' : '▼'}</span>
        </div>
      </div>
      ${isExpanded ? `
        <div class="template-expand-content">
          <div class="prompt-preview">
            <div class="preview-label">Prompt 预览</div>
            <div class="prompt-content" id="prompt-preview-${template.id}">
              <div class="loading-prompt">加载中...</div>
            </div>
          </div>
          <div class="template-actions">
            ${renderImportButton(template)}
          </div>
        </div>
      ` : ''}
    </div>
  `;
}

/**
 * 渲染导入按钮
 */
function renderImportButton(template) {
  const deviceId = getDeviceId();
  if (!deviceId) {
    return `<button class="import-btn login-required" onclick="alert('请先激活')">🔐 请先激活</button>`;
  }
  return `<button class="import-btn can-import" onclick="importTemplate(${template.id}, '${template.title}')">📥 一键导入</button>`;
}

/**
 * 展开/收起模板详情
 */
async function toggleTemplateExpand(templateId) {
  const container = document.getElementById('marketplace-content');
  const templates = templatesCache[currentChannel] || [];

  if (expandedTemplateId === templateId) {
    expandedTemplateId = null;
  } else {
    expandedTemplateId = templateId;
    loadPromptPreview(templateId);
  }

  renderTemplates(container, templates, currentChannel);
}

/**
 * 加载 Prompt 预览
 */
async function loadPromptPreview(templateId) {
  const previewEl = document.getElementById(`prompt-preview-${templateId}`);
  if (!previewEl) return;

  try {
    const res = await fetch(`/api/marketplace/templates/${templateId}`);
    if (!res.ok) throw new Error('加载失败');

    const template = await res.json();
    previewEl.innerHTML = `<pre class="prompt-text">${escapeHtml(template.prompt_content || '')}</pre>`;
  } catch (err) {
    previewEl.innerHTML = `<div class="error-text">加载失败: ${err.message}</div>`;
  }
}

/**
 * 导入模板
 */
async function importTemplate(templateId, templateTitle) {
  const deviceId = getDeviceId();
  if (!deviceId) {
    showToast('请先激活', 'err');
    return;
  }

  const btn = document.querySelector(`.template-card[data-id="${templateId}"] .import-btn`);
  const originalText = btn?.innerHTML;
  if (btn) {
    btn.innerHTML = '⏳ 导入中...';
    btn.disabled = true;
  }

  try {
    const res = await fetch(`/api/marketplace/templates/${templateId}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    const data = await res.json();

    if (!res.ok) {
      showToast(data.detail || '导入失败', 'err');
      return;
    }

    showToast(`✓ 已导入「${templateTitle}」`, 'ok');

    if (btn) {
      btn.innerHTML = '✓ 已导入';
      btn.classList.remove('can-import');
      btn.classList.add('imported');
    }
  } catch (err) {
    showToast(`导入失败: ${err.message}`, 'err');
  } finally {
    if (btn && originalText && btn.innerHTML.includes('导入中')) {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  }
}

/**
 * HTML 转义
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// 导出模块
window.initMarketplace = initMarketplace;
window.switchMarketplaceChannel = switchMarketplaceChannel;
window.toggleTemplateExpand = toggleTemplateExpand;
window.importTemplate = importTemplate;
window.openPromptEditor = openPromptEditor;
window.closePromptEditor = closePromptEditor;
window.savePromptConfig = savePromptConfig;
window.resetPromptToDefault = resetPromptToDefault;