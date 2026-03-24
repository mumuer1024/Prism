/**
 * marketplace.js - 预设广场模块
 * 提供 Prompt 模板的浏览和导入功能
 */

// 频道配置
const MARKETPLACE_CHANNELS = [
  { key: 'mission', name: '情报日报', icon: '📊' },
  { key: 'alpha', name: 'Alpha雷达', icon: '⛏️' },
  { key: 'bounty_v2ex', name: '赏金·V2EX', icon: '💰' },
  { key: 'bounty_chrome', name: '赏金·Chrome', icon: '🔌' },
  { key: 'revenue', name: '营收分析', icon: '🏗️' }
];

// 当前状态
let currentChannel = 'mission';
let templatesCache = {};
let expandedTemplateId = null;

/**
 * 初始化广场
 */
async function initMarketplace() {
  await loadTemplates(currentChannel);
}

/**
 * 切换频道
 */
function switchMarketplaceChannel(channel) {
  if (currentChannel === channel) return;
  
  currentChannel = channel;
  
  // 更新 Tab 样式
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
  
  // 加载模板
  loadTemplates(channel);
}

/**
 * 加载模板列表
 */
async function loadTemplates(toolType) {
  const container = document.getElementById('marketplace-content');
  if (!container) return;
  
  // 显示加载状态
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
        <div class="empty-hint">该频道暂无官方模板，敬请期待</div>
      </div>
    `;
    return;
  }
  
  const html = `
    <div class="marketplace-grid">
      ${templates.map(t => renderTemplateCard(t)).join('')}
    </div>
  `;
  
  container.innerHTML = html;
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
 * 渲染导入按钮（根据用户权限）
 */
function renderImportButton(template) {
  const token = localStorage.getItem('access_token');
  const userStr = localStorage.getItem('user');
  
  // 未登录
  if (!token) {
    return `
      <button class="import-btn login-required" onclick="window.location.href='/login'">
        <span>🔐</span> 登录后导入
      </button>
    `;
  }
  
  // 解析用户信息
  let user = null;
  try {
    user = userStr ? JSON.parse(userStr) : null;
  } catch (e) {}
  
  // 免费/次数用光
  if (!user || (user.usage_count !== undefined && user.usage_count <= 0)) {
    return `
      <button class="import-btn upgrade-required" onclick="showUpgradeTip()">
        <span>🔒</span> 升级后可用
      </button>
    `;
  }
  
  // 付费用户
  return `
    <button class="import-btn can-import" onclick="importTemplate(${template.id}, '${template.title}')">
      <span>📥</span> 一键导入
    </button>
  `;
}

/**
 * 展开/收起模板详情
 */
async function toggleTemplateExpand(templateId) {
  const container = document.getElementById('marketplace-content');
  const templates = templatesCache[currentChannel] || [];
  
  if (expandedTemplateId === templateId) {
    // 收起
    expandedTemplateId = null;
  } else {
    // 展开
    expandedTemplateId = templateId;
    
    // 异步加载 Prompt 内容
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
    const content = template.prompt_content || '';
    
    // 格式化显示
    previewEl.innerHTML = `<pre class="prompt-text">${escapeHtml(content)}</pre>`;
  } catch (err) {
    previewEl.innerHTML = `<div class="error-text">加载失败: ${err.message}</div>`;
  }
}

/**
 * 导入模板
 */
async function importTemplate(templateId, templateTitle) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    showToast('请先登录', 'err');
    window.location.href = '/login';
    return;
  }
  
  // 显示加载状态
  const btn = document.querySelector(`.template-card[data-id="${templateId}"] .import-btn`);
  const originalText = btn?.innerHTML;
  if (btn) {
    btn.innerHTML = '<span>⏳</span> 导入中...';
    btn.disabled = true;
  }
  
  try {
    const res = await fetch(`/api/marketplace/templates/${templateId}/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await res.json();
    
    if (!res.ok) {
      if (res.status === 403) {
        showToast('使用次数不足，请充值后使用', 'err');
        showUpgradeTip();
      } else {
        showToast(data.detail || '导入失败', 'err');
      }
      return;
    }
    
    showToast(`✓ 已导入「${templateTitle}」，前往配置页查看`, 'ok');
    
    // 更新按钮状态
    if (btn) {
      btn.innerHTML = '<span>✓</span> 已导入';
      btn.classList.remove('can-import');
      btn.classList.add('imported');
      btn.onclick = () => showToast('已导入，前往配置页查看', 'ok');
    }
    
  } catch (err) {
    showToast(`导入失败: ${err.message}`, 'err');
  } finally {
    // 恢复按钮（如果失败）
    if (btn && originalText && btn.innerHTML.includes('导入中')) {
      btn.innerHTML = originalText;
      btn.disabled = false;
    }
  }
}

/**
 * 显示升级提示
 */
function showUpgradeTip() {
  const modal = document.createElement('div');
  modal.className = 'upgrade-modal';
  modal.innerHTML = `
    <div class="upgrade-modal-overlay" onclick="this.parentElement.remove()"></div>
    <div class="upgrade-modal-content">
      <div class="upgrade-icon">💎</div>
      <h3>升级解锁完整功能</h3>
      <p>充值使用次数后即可导入预设模板</p>
      <div class="upgrade-actions">
        <button class="btn-cancel" onclick="this.closest('.upgrade-modal').remove()">稍后再说</button>
        <a href="/account#usage" class="btn-upgrade">立即充值</a>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
  
  // 添加动画
  requestAnimationFrame(() => modal.classList.add('show'));
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
window.showUpgradeTip = showUpgradeTip;