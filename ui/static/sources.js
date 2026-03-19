/**
 * Sources Module - Data source management
 * 数据源模块 - 数据源管理
 */

/**
 * Load data sources list
 * 加载数据源列表
 */
async function loadSources() {
  const list = document.getElementById('sources-list');
  if (!list) return;

  try {
    const res = await fetch('/api/sources');
    const sources = await res.json();

    renderSources(list, sources);
  } catch (e) {
    list.innerHTML = '<div class="text-center py-8" style="color: #ff6b6b;">加载失败</div>';
  }
}

/**
 * Render sources list
 * 渲染数据源列表
 */
function renderSources(container, sources) {
  container.innerHTML = '';

  // Sort sources: tavily first, then others
  const sortedSources = [...sources].sort((a, b) => {
    if (a.key === 'tavily') return -1;
    if (b.key === 'tavily') return 1;
    return 0;
  });

  // Apply saved Tavily state from localStorage
  const savedTavilyEnabled = localStorage.getItem('tavily-enabled');
  if (savedTavilyEnabled !== null) {
    const tavilySource = sortedSources.find(s => s.key === 'tavily');
    if (tavilySource) {
      tavilySource.enabled = savedTavilyEnabled === 'true';
    }
  }

  sortedSources.forEach(src => {
    const card = createSourceCard(src);
    container.appendChild(card);
  });
}

/**
 * Create source card element
 * 创建数据源卡片元素
 */
function createSourceCard(src) {
  const card = document.createElement('div');
  card.className = 'source-card card-hover';
  card.id = `source-card-${src.key}`;

  const warning = createWarningBadge(src);
  const tokenNotice = createTokenNotice(src);
  const keywordsSection = src.key === 'tavily' ? createTavilyKeywordsSection(src) : '';

  card.innerHTML = `
    <div class="source-icon">${src.icon}</div>
    <div class="source-info">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="source-name">${src.name}</span>
        ${warning}
      </div>
      <p class="source-desc">${src.desc}</p>
      ${tokenNotice}
      ${keywordsSection}
    </div>
    <div class="toggle ${src.enabled ? 'enabled' : ''}" onclick="${src.key === 'tavily' ? `toggleTavilySource(this)` : `toggleSource('${src.key}', ${!src.enabled})`}"></div>
  `;

  return card;
}

/**
 * Create Tavily keywords section
 * 创建 Tavily 关键词编辑区域
 */
function createTavilyKeywordsSection(src) {
  const savedKeywords = localStorage.getItem('tavily-keywords') || '';
  const displayStyle = src.enabled ? 'display: block;' : 'display: none;';

  return `
    <div class="tavily-keywords" id="tavily-keywords-section" style="${displayStyle}">
      <div class="tavily-keywords-label">自定义搜索关键词（用逗号分隔）</div>
      <input type="text" id="tavily-keywords-input" class="tavily-keywords-input" placeholder="例如：AI, 区块链, 创业" value="${savedKeywords}">
      <div class="flex gap-2 mt-2">
        <button class="config-btn config-btn-primary text-xs" onclick="saveTavilyKeywords()">保存</button>
        <button class="config-btn config-btn-primary text-xs" onclick="resetTavilyKeywords()">重置</button>
      </div>
    </div>
  `;
}

/**
 * Toggle Tavily source (frontend only)
 * 切换 Tavily 信息源（仅前端存储）
 */
async function toggleTavilySource(toggleEl) {
  const isEnabled = toggleEl.classList.toggle('enabled');
  const keywordsSection = document.getElementById('tavily-keywords-section');

  if (keywordsSection) {
    keywordsSection.style.display = isEnabled ? 'block' : 'none';
  }

  // Save to localStorage
  localStorage.setItem('tavily-enabled', isEnabled ? 'true' : 'false');

  // Also update backend via API
  try {
    await fetch('/api/sources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: 'tavily', enabled: isEnabled })
    });
  } catch (e) {
    console.warn('Failed to update Tavily backend state:', e);
  }

  showToast(isEnabled ? 'Tavily 搜索已启用' : 'Tavily 搜索已禁用', 'ok');
}

/**
 * Save Tavily keywords (frontend only)
 * 保存 Tavily 关键词（仅前端存储）
 */
function saveTavilyKeywords() {
  const keywordsInput = document.getElementById('tavily-keywords-input');
  if (keywordsInput) {
    const keywords = keywordsInput.value.trim();
    localStorage.setItem('tavily-keywords', keywords);
    showToast('关键词已保存', 'ok');
  }
}

/**
 * Reset Tavily keywords (frontend only)
 * 重置 Tavily 关键词（仅前端存储）
 */
function resetTavilyKeywords() {
  const keywordsInput = document.getElementById('tavily-keywords-input');
  if (keywordsInput) {
    keywordsInput.value = '';
    localStorage.removeItem('tavily-keywords');
    showToast('关键词已重置', 'ok');
  }
}

/**
 * Create warning badge if needed
 * 创建警告标签（如果需要）
 */
function createWarningBadge(src) {
  if (!src.requires_key || src.key_configured) {
    return '';
  }

  return `<span class="text-xs px-2 py-1 rounded-md" style="color: #ffaa44; background: rgba(255,170,68,0.1);">需配置 ${src.requires_key}</span>`;
}

/**
 * Create token required notice
 * 创建 Token 必需提示
 */
function createTokenNotice(src) {
  if (!src.requires_key) {
    return '';
  }

  return `
    <div class="source-warning mt-2">
      <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
      需token配置，如不配置则不支持搜索本平台
    </div>
  `;
}

/**
 * Toggle source enabled state
 * 切换数据源启用状态
 */
async function toggleSource(key, enabled) {
  try {
    await fetch('/api/sources', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key, enabled })
    });

    loadSources();
    showToast(enabled ? '已启用' : '已禁用', 'ok');
  } catch (e) {
    showToast('操作失败', 'err');
  }
}
