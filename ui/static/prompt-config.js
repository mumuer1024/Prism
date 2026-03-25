/**
 * prompt-config.js - Prompt 配置模块
 * 处理用户自定义 Prompt 的加载、编辑和保存
 */

// 工具类型配置
const PROMPT_TOOLS = [
  { key: 'mission', name: '情报日报', icon: '📊', desc: '从 10+ 数据源抓取，生成 8 大板块中文日报' },
  { key: 'bounty_v2ex', name: '赏金猎人 - V2EX', icon: '💰', desc: 'V2EX 急单筛选规则和关键词' },
  { key: 'bounty_chrome', name: '赏金猎人 - Chrome', icon: '🔌', desc: 'Chrome 扩展机会筛选条件' },
  { key: 'alpha', name: 'Alpha 雷达', icon: '⛏️', desc: 'Web3/Solana 开源项目搜索 Prompt' },
  { key: 'revenue', name: '营收分析师', icon: '🏗️', desc: '商业机会分析 Prompt' }
];

// 当前编辑状态
let currentPromptData = {};
let editingToolType = null;

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

  // 检查登录状态（使用 AuthState 统一管理）
  const token = AuthState.getToken();
  if (!token) {
    container.innerHTML = `
      <div class="prompt-login-notice">
        <div class="notice-icon">🔐</div>
        <div class="notice-text">请先登录以配置自定义 Prompt</div>
        <a href="/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}" class="notice-btn">去登录</a>
      </div>
    `;
    return;
  }

  try {
    const res = await fetch('/api/user-config/prompt', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (res.status === 401) {
      container.innerHTML = `
        <div class="prompt-login-notice">
          <div class="notice-icon">🔐</div>
          <div class="notice-text">登录已过期，请重新登录</div>
          <a href="/login?redirect=${encodeURIComponent(window.location.pathname + window.location.search)}" class="notice-btn">去登录</a>
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
 * 打开 Prompt 编辑器
 */
async function openPromptEditor(toolType) {
  const tool = PROMPT_TOOLS.find(t => t.key === toolType);
  if (!tool) return;

  editingToolType = toolType;
  const data = currentPromptData[toolType] || {};

  // 创建编辑器模态框
  const modal = document.createElement('div');
  modal.id = 'prompt-editor-modal';
  modal.className = 'prompt-modal';
  modal.innerHTML = `
    <div class="prompt-modal-overlay" onclick="closePromptEditor()"></div>
    <div class="prompt-modal-content">
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
        <div class="editor-label">Prompt 内容</div>
        <textarea id="prompt-editor-textarea" class="prompt-textarea" placeholder="输入自定义 Prompt...">${data.prompt_content || ''}</textarea>
        <div class="editor-hint">
          <strong>提示：</strong>
          <ul>
            <li>Alpha 雷达支持 <code>{query}</code> 占位符，运行时会替换为实际搜索词</li>
            <li>营收分析师支持 <code>{content}</code> 占位符，运行时会替换为日报内容</li>
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
}

/**
 * 保存 Prompt
 */
async function savePrompt(toolType) {
  const textarea = document.getElementById('prompt-editor-textarea');
  const content = textarea?.value?.trim() || '';

  const token = AuthState.getToken();
  if (!token) {
    showToast('请先登录', 'err');
    return;
  }

  const saveBtn = document.querySelector('.btn-save');
  const originalText = saveBtn.innerHTML;
  saveBtn.innerHTML = '<span>⏳</span> 保存中...';
  saveBtn.disabled = true;

  try {
    const res = await fetch(`/api/user-config/prompt/${toolType}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ content })
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

  const token = AuthState.getToken();
  if (!token) {
    showToast('请先登录', 'err');
    return;
  }

  try {
    const res = await fetch(`/api/user-config/prompt/${toolType}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
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