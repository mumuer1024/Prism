/**
 * Sources Module - Data source management
 * 数据源模块 - 数据源管理
 */

// DailyHotApi 分类配置缓存
let dailyhotConfig = {
  enabled: ['tech', 'dev'],
  available: []
};

// 用户状态缓存
let userSourceState = {
  isLoggedIn: false,
  isPaid: false,
  paidCount: 0
};

/**
 * Load data sources list
 * 加载数据源列表
 */
async function loadSources() {
  const list = document.getElementById('sources-list');
  if (!list) return;

  // 初始化用户状态
  userSourceState.isLoggedIn = AuthState.isLoggedIn();

  try {
    // 并行加载数据源、DailyHotApi 配置和用户次数
    const [sourcesRes, dailyhotRes, usageRes] = await Promise.all([
      fetch('/api/sources'),
      // 使用公开 API 获取分类映射（无需登录）
      fetch('/api/user-config/dailyhot/category-map').catch(() => null),
      // 获取用户次数（用于判断付费状态）
      userSourceState.isLoggedIn ? fetch('/api/usage/balance', {
        headers: getAuthHeaders()
      }).catch(() => null) : Promise.resolve(null)
    ]);

    const sources = await sourcesRes.json();

    // 解析用户次数
    if (usageRes && usageRes.ok) {
      const usageData = await usageRes.json();
      if (usageData.success && usageData.data) {
        userSourceState.paidCount = usageData.data.paid_count || 0;
        userSourceState.isPaid = userSourceState.paidCount > 0;
      }
    }

    // 解析 DailyHotApi 分类映射
    if (dailyhotRes && dailyhotRes.ok) {
      const categoryData = await dailyhotRes.json();
      if (categoryData.categories) {
        dailyhotConfig.available = categoryData.categories.map(cat => ({
          key: cat.key,
          label: cat.label,
          platforms: cat.platforms ? cat.platforms.map(p => p.name || p) : []
        }));
      }
    }

    // 如果已登录，获取用户的启用配置
    if (userSourceState.isLoggedIn) {
      try {
        const userConfigRes = await fetch('/api/user-config/dailyhot/categories', {
          headers: getAuthHeaders()
        });
        if (userConfigRes.ok) {
          const userConfig = await userConfigRes.json();
          dailyhotConfig.enabled = userConfig.enabled || ['tech', 'dev'];
        }
      } catch (e) {
        console.warn('获取用户分类配置失败，使用默认值');
      }
    } else {
      // 未登录用户：尝试从 localStorage 读取，否则使用默认值
      const savedCategories = localStorage.getItem('dailyhot-categories');
      if (savedCategories) {
        try {
          dailyhotConfig.enabled = JSON.parse(savedCategories);
        } catch (e) {
          dailyhotConfig.enabled = ['tech', 'dev'];
        }
      } else {
        dailyhotConfig.enabled = ['tech', 'dev'];
      }
    }

    renderSources(list, sources);
  } catch (e) {
    list.innerHTML = '<div class="text-center py-8" style="color: #ff6b6b;">加载失败</div>';
  }
}

/**
 * 获取认证头
 */
function getAuthHeaders() {
  const token = AuthState.getToken();
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

/**
 * Render sources list
 * 渲染数据源列表
 */
function renderSources(container, sources) {
  container.innerHTML = '';

  // 1. 免费层：DailyHotApi 热榜数据源（所有用户可见）
  const dailyhotSection = createDailyHotSection();
  container.appendChild(dailyhotSection);

  // 2. 根据用户状态显示不同的数据源
  if (!userSourceState.isLoggedIn) {
    // 未登录用户：只显示热榜数据源 + 登录引导
    const loginPrompt = document.createElement('div');
    loginPrompt.className = 'sources-login-prompt';
    loginPrompt.innerHTML = `
      <div class="login-prompt-content">
        <div class="login-prompt-icon">🔐</div>
        <div class="login-prompt-text">登录后解锁更多数据源</div>
        <div class="login-prompt-actions">
          <a href="/login" class="login-prompt-btn">登录</a>
          <a href="/register" class="login-prompt-btn primary">注册</a>
        </div>
      </div>
    `;
    container.appendChild(loginPrompt);
  } else {
    // 已登录用户：显示其他数据源
    const freeSourcesHeader = document.createElement('div');
    freeSourcesHeader.className = 'sources-section-header';
    freeSourcesHeader.innerHTML = `
      <h3 class="sources-section-title">📡 其他数据源</h3>
      <p class="sources-section-desc">免费数据源，开箱即用</p>
    `;
    container.appendChild(freeSourcesHeader);

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

    // 3. 付费层：精准搜索数据源
    if (userSourceState.isPaid) {
      // 付费用户：解锁状态
      const paidSection = createPaidSourcesSectionUnlocked();
      container.appendChild(paidSection);
    } else {
      // 免费用户：锁定状态 + 升级引导
      const paidSection = createPaidSourcesSection();
      container.appendChild(paidSection);
    }
  }
}

/**
 * Create DailyHotApi section
 * 创建 DailyHotApi 热榜数据源区域
 */
function createDailyHotSection() {
  const section = document.createElement('div');
  section.className = 'dailyhot-section';

  const available = dailyhotConfig.available || [];
  const enabled = dailyhotConfig.enabled || ['tech', 'dev'];

  section.innerHTML = `
    <div class="dailyhot-header">
      <div class="dailyhot-title">
        <span class="dailyhot-icon">📦</span>
        <div>
          <h3>热榜数据源</h3>
          <span class="dailyhot-badge">DailyHotApi</span>
        </div>
      </div>
      <p class="dailyhot-desc">选择你关注的行业分类（可多选，至少选一个）</p>
    </div>
    <div class="dailyhot-categories">
      ${available.map(cat => `
        <label class="dailyhot-category ${enabled.includes(cat.key) ? 'enabled' : ''}" data-key="${cat.key}">
          <input type="checkbox" 
                 class="dailyhot-checkbox" 
                 ${enabled.includes(cat.key) ? 'checked' : ''}
                 onchange="toggleDailyHotCategory('${cat.key}', this.checked)">
          <div class="dailyhot-category-content">
            <div class="dailyhot-category-header">
              <span class="dailyhot-category-check">${enabled.includes(cat.key) ? '☑' : '☐'}</span>
              <span class="dailyhot-category-label">${cat.label}</span>
            </div>
            <div class="dailyhot-category-platforms">
              ${cat.platforms.join(' / ')}
            </div>
          </div>
        </label>
      `).join('')}
    </div>
  `;

  return section;
}

/**
 * Toggle DailyHotApi category
 * 切换 DailyHotApi 分类启用状态
 */
async function toggleDailyHotCategory(category, isEnabled) {
  // 获取当前启用的分类
  let enabled = [...dailyhotConfig.enabled];

  if (isEnabled) {
    if (!enabled.includes(category)) {
      enabled.push(category);
    }
  } else {
    // 允许全部取消，表示不使用热榜数据源
    enabled = enabled.filter(c => c !== category);
  }

  // 更新 UI
  const label = document.querySelector(`.dailyhot-category[data-key="${category}"]`);
  if (label) {
    label.classList.toggle('enabled', isEnabled);
    const check = label.querySelector('.dailyhot-category-check');
    if (check) check.textContent = isEnabled ? '☑' : '☐';
  }

  // 更新本地缓存
  dailyhotConfig.enabled = enabled;

  // 如果已登录，保存到后端
  if (AuthState.isLoggedIn()) {
    try {
      const res = await fetch('/api/user-config/dailyhot/categories', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders()
        },
        body: JSON.stringify({ categories: enabled })
      });

      if (res.ok) {
        showToast(isEnabled ? `已启用「${getCategoryLabel(category)}」` : `已禁用「${getCategoryLabel(category)}」`, 'ok');
      } else {
        const data = await res.json();
        showToast(data.detail || '保存失败', 'err');
        // 恢复状态
        loadSources();
      }
    } catch (e) {
      showToast('保存失败', 'err');
      loadSources();
    }
  } else {
    // 未登录用户保存到 localStorage
    localStorage.setItem('dailyhot-categories', JSON.stringify(enabled));
    showToast(isEnabled ? `已启用「${getCategoryLabel(category)}」` : `已禁用「${getCategoryLabel(category)}」`, 'ok');
  }
}

/**
 * Get category label
 * 获取分类标签名称
 */
function getCategoryLabel(key) {
  const labels = {
    'tech': '科技数字',
    'dev': '开发者',
    'news': '综合资讯',
    'entertainment': '内容娱乐'
  };
  return labels[key] || key;
}

/**
 * Create paid sources section (placeholder)
 * 创建付费数据源区域（占位展示 - 免费用户看到）
 */
function createPaidSourcesSection() {
  const section = document.createElement('div');
  section.className = 'paid-sources-section';

  section.innerHTML = `
    <div class="paid-sources-header">
      <div class="paid-sources-title">
        <span class="paid-sources-icon">🔒</span>
        <div>
          <h3>精准搜索数据源</h3>
          <span class="paid-sources-badge">付费功能</span>
        </div>
      </div>
      <p class="paid-sources-desc">更精准的情报搜索能力</p>
    </div>
    <div class="paid-sources-list">
      <div class="paid-source-item disabled">
        <div class="paid-source-icon">🔍</div>
        <div class="paid-source-info">
          <div class="paid-source-name">RSSHub 关键词搜索</div>
          <div class="paid-source-desc">支持知乎、36kr等平台关键词搜索</div>
        </div>
        <span class="paid-source-status">🔒 锁定</span>
      </div>
      <div class="paid-source-item disabled">
        <div class="paid-source-icon">🌐</div>
        <div class="paid-source-info">
          <div class="paid-source-name">Tavily</div>
          <div class="paid-source-desc">通用网页搜索</div>
        </div>
        <span class="paid-source-status">🔒 锁定</span>
      </div>
      <div class="paid-source-item disabled">
        <div class="paid-source-icon">📡</div>
        <div class="paid-source-info">
          <div class="paid-source-name">自定义 RSS</div>
          <div class="paid-source-desc">添加你自己的 RSS 订阅</div>
        </div>
        <span class="paid-source-status">🔒 锁定</span>
      </div>
    </div>
    <div class="paid-sources-footer">
      <a href="/account#usage" class="paid-sources-upgrade-btn">
        <span>💎</span> 升级解锁
      </a>
    </div>
  `;

  return section;
}

/**
 * Create paid sources section (unlocked for paid users)
 * 创建付费数据源区域（解锁状态 - 付费用户看到）
 */
function createPaidSourcesSectionUnlocked() {
  const section = document.createElement('div');
  section.className = 'paid-sources-section unlocked';

  section.innerHTML = `
    <div class="paid-sources-header">
      <div class="paid-sources-title">
        <span class="paid-sources-icon">✨</span>
        <div>
          <h3>精准搜索数据源</h3>
          <span class="paid-sources-badge unlocked">已解锁</span>
        </div>
      </div>
      <p class="paid-sources-desc">更精准的情报搜索能力</p>
    </div>
    <div class="paid-sources-list">
      <div class="paid-source-item">
        <div class="paid-source-icon">🔍</div>
        <div class="paid-source-info">
          <div class="paid-source-name">RSSHub 关键词搜索</div>
          <div class="paid-source-desc">支持知乎、36kr等平台关键词搜索</div>
        </div>
        <span class="paid-source-status available">可用</span>
      </div>
      <div class="paid-source-item">
        <div class="paid-source-icon">🌐</div>
        <div class="paid-source-info">
          <div class="paid-source-name">Tavily</div>
          <div class="paid-source-desc">通用网页搜索</div>
        </div>
        <span class="paid-source-status available">可用</span>
      </div>
      <div class="paid-source-item">
        <div class="paid-source-icon">📡</div>
        <div class="paid-source-info">
          <div class="paid-source-name">自定义 RSS</div>
          <div class="paid-source-desc">添加你自己的 RSS 订阅</div>
        </div>
        <span class="paid-source-status available">可用</span>
      </div>
    </div>
    <div class="paid-sources-footer">
      <span class="paid-sources-info">💎 剩余次数: ${userSourceState.paidCount} 次</span>
    </div>
  `;

  return section;
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

// 导出函数
window.loadSources = loadSources;
window.toggleDailyHotCategory = toggleDailyHotCategory;
window.toggleTavilySource = toggleTavilySource;
window.saveTavilyKeywords = saveTavilyKeywords;
window.resetTavilyKeywords = resetTavilyKeywords;
window.toggleSource = toggleSource;