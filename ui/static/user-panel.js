/**
 * User Panel Module - Right side user status panel
 * 用户面板模块 - 右侧用户状态面板
 */

// 面板状态缓存
let panelState = {
  isLoggedIn: false,
  isPaid: false,
  user: null,
  usage: null,
  anonymousUsage: null
};

/**
 * 初始化用户面板
 */
async function initUserPanel() {
  await loadUserPanelData();
}

/**
 * 加载用户面板数据
 */
async function loadUserPanelData() {
  const container = document.getElementById('user-panel-content');
  if (!container) return;

  // 检查登录状态
  const isLoggedIn = AuthState.isLoggedIn();
  panelState.isLoggedIn = isLoggedIn;

  if (isLoggedIn) {
    // 已登录：获取用户信息和次数
    panelState.user = AuthState.getCurrentUser();
    await loadLoggedInUserUsage();
  } else {
    // 未登录：获取匿名用户次数
    await loadAnonymousUsage();
  }

  renderUserPanel();
  updateAccountNavLink(isLoggedIn);
}

/**
 * 更新"用户中心"导航链接的显示状态
 */
function updateAccountNavLink(isLoggedIn) {
  const navAccount = document.getElementById('nav-account');
  const mobileNavAccount = document.getElementById('mobile-nav-account');

  if (navAccount) {
    if (isLoggedIn) {
      navAccount.classList.remove('hidden');
    } else {
      navAccount.classList.add('hidden');
    }
  }

  if (mobileNavAccount) {
    if (isLoggedIn) {
      mobileNavAccount.classList.remove('hidden');
    } else {
      mobileNavAccount.classList.add('hidden');
    }
  }
}

/**
 * 加载已登录用户的次数信息
 */
async function loadLoggedInUserUsage() {
  try {
    const token = AuthState.getToken();
    const resp = await fetch('/api/usage/balance', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (resp.ok) {
      const result = await resp.json();
      if (result.success && result.data) {
        panelState.usage = result.data;
        panelState.isPaid = (result.data.paid_count > 0);
      }
    }
  } catch (err) {
    console.error('加载用户次数失败:', err);
  }
}

/**
 * 加载匿名用户次数信息
 */
async function loadAnonymousUsage() {
  try {
    // 获取或创建匿名用户标识
    let visitorId = localStorage.getItem('prism_visitor_id');
    if (!visitorId) {
      visitorId = 'visitor_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('prism_visitor_id', visitorId);
    }

    // 使用 /api/usage/balance 端点，传入 visitor_id 参数
    const resp = await fetch(`/api/usage/balance?visitor_id=${encodeURIComponent(visitorId)}`);

    if (resp.ok) {
      const data = await resp.json();
      if (data.success && data.data) {
        panelState.anonymousUsage = {
          free_remaining: data.data.free_remaining || 0,
          free_limit: data.data.free_limit || 3
        };
      }
    }
  } catch (err) {
    console.error('加载匿名用户次数失败:', err);
    // 设置默认值
    panelState.anonymousUsage = {
      free_remaining: 3,
      free_limit: 3
    };
  }
}

/**
 * 渲染用户面板
 */
function renderUserPanel() {
  const container = document.getElementById('user-panel-content');
  if (!container) return;

  if (panelState.isLoggedIn) {
    if (panelState.isPaid) {
      container.innerHTML = renderPaidUserPanel();
    } else {
      container.innerHTML = renderFreeUserPanel();
    }
  } else {
    container.innerHTML = renderAnonymousPanel();
  }
}

/**
 * 渲染匿名用户面板
 */
function renderAnonymousPanel() {
  const usage = panelState.anonymousUsage || { free_remaining: 3, free_limit: 3 };
  const remaining = usage.free_remaining || 0;
  const limit = usage.free_limit || 3;
  const percentage = Math.round((remaining / limit) * 100);
  const progressClass = getProgressClass(percentage);

  return `
    <div class="user-panel-section">
      <div class="user-panel-anonymous">
        <div class="user-panel-anonymous-icon">🔒</div>
        <div class="user-panel-anonymous-title">游客模式</div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-usage">
        <div class="usage-label">今日免费次数</div>
        <div class="usage-progress-container">
          <div class="usage-progress-bar">
            <div class="usage-progress-fill ${progressClass}" style="width: ${percentage}%"></div>
          </div>
          <div class="usage-count">${remaining} / ${limit} 次</div>
        </div>
        ${remaining === 0 ? '<div class="usage-warning">今日次数已用完，明日重置</div>' : ''}
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-btn-group">
        <a href="/login" class="user-panel-btn user-panel-btn-outline">登录</a>
        <a href="/register" class="user-panel-btn user-panel-btn-primary">注册</a>
      </div>

      <div class="user-panel-divider"></div>

      <ul class="user-panel-features">
        <li>配置自定义 Prompt</li>
        <li>更多数据源选择</li>
        <li>历史报告保存</li>
        <li>解锁付费功能</li>
      </ul>
    </div>
  `;
}

/**
 * 渲染免费用户面板
 */
function renderFreeUserPanel() {
  const user = panelState.user || {};
  const usage = panelState.usage || { free_remaining: 0, free_limit: 3, paid_count: 0 };

  const freeRemaining = usage.free_remaining || 0;
  const freeLimit = usage.free_limit || 3;
  const freePercentage = Math.round((freeRemaining / freeLimit) * 100);
  const freeProgressClass = getProgressClass(freePercentage);

  const paidCount = usage.paid_count || 0;

  const displayName = user.nickname || user.email?.split('@')[0] || '用户';
  const initial = displayName[0].toUpperCase();

  return `
    <div class="user-panel-section">
      <div class="user-panel-user-info">
        <div class="user-avatar">${initial}</div>
        <div class="user-details">
          <div class="user-name">${displayName}</div>
          <div class="user-type-badge free">免费账户</div>
        </div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-usage">
        <div class="usage-label">今日免费次数</div>
        <div class="usage-progress-container">
          <div class="usage-progress-bar">
            <div class="usage-progress-fill ${freeProgressClass}" style="width: ${freePercentage}%"></div>
          </div>
          <div class="usage-count">${freeRemaining} / ${freeLimit} 次</div>
        </div>
        ${freeRemaining === 0 ? '<div class="usage-warning">今日次数已用完，明日重置</div>' : ''}
      </div>

      <div class="user-panel-usage">
        <div class="usage-label">付费次数</div>
        <div class="usage-count-static">${paidCount} 次</div>
      </div>

      <div class="user-panel-divider"></div>

      ${user.is_admin ? '<div class="user-panel-actions"><a href="/admin" class="user-panel-btn user-panel-btn-admin">🛡️ 管理后台</a></div><div class="user-panel-divider"></div>' : ''}

      <div class="user-panel-actions">
        <a href="/account#usage" class="user-panel-btn user-panel-btn-upgrade">升级解锁全功能</a>
      </div>

      <div class="user-panel-link">
        <a href="/account#redeem">兑换激活码 →</a>
      </div>
    </div>
  `;
}

/**
 * 渲染付费用户面板
 */
function renderPaidUserPanel() {
  const user = panelState.user || {};
  const usage = panelState.usage || { free_remaining: 0, free_limit: 3, paid_count: 0 };

  const paidCount = usage.paid_count || 0;
  const paidPercentage = paidCount > 0 ? 100 : 0; // 付费次数不设上限，直接显示是否有余
  const paidProgressClass = getProgressClass(paidPercentage);

  const freeRemaining = usage.free_remaining || 0;
  const freeLimit = usage.free_limit || 3;
  const freePercentage = Math.round((freeRemaining / freeLimit) * 100);
  const freeProgressClass = getProgressClass(freePercentage);

  const displayName = user.nickname || user.email?.split('@')[0] || '用户';
  const initial = displayName[0].toUpperCase();

  return `
    <div class="user-panel-section">
      <div class="user-panel-user-info">
        <div class="user-avatar paid">${initial}</div>
        <div class="user-details">
          <div class="user-name">${displayName}</div>
          <div class="user-type-badge paid">💎 付费用户</div>
        </div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-usage">
        <div class="usage-label">剩余付费次数</div>
        <div class="usage-progress-container">
          <div class="usage-progress-bar">
            <div class="usage-progress-fill ${paidProgressClass}" style="width: ${paidPercentage}%"></div>
          </div>
          <div class="usage-count">${paidCount} 次</div>
        </div>
        ${paidCount === 0 ? '<div class="usage-warning">付费次数已耗尽</div>' : ''}
      </div>

      <div class="user-panel-usage">
        <div class="usage-label">今日免费次数</div>
        <div class="usage-progress-container">
          <div class="usage-progress-bar">
            <div class="usage-progress-fill ${freeProgressClass}" style="width: ${freePercentage}%"></div>
          </div>
          <div class="usage-count">${freeRemaining} / ${freeLimit} 次</div>
        </div>
      </div>

      <div class="user-panel-divider"></div>

      ${user.is_admin ? '<div class="user-panel-actions column"><a href="/admin" class="user-panel-btn user-panel-btn-admin">🛡️ 管理后台</a></div><div class="user-panel-divider"></div>' : ''}

      <div class="user-panel-actions column">
        <a href="/account" class="user-panel-btn user-panel-btn-outline">前往用户中心</a>
        <a href="/account#redeem" class="user-panel-btn user-panel-btn-primary">兑换激活码</a>
      </div>
    </div>
  `;
}

/**
 * 获取进度条颜色类名
 * @param {number} percentage - 剩余百分比
 * @returns {string} - CSS 类名
 */
function getProgressClass(percentage) {
  if (percentage > 50) {
    return 'normal';
  } else if (percentage > 20) {
    return 'warn';
  } else {
    return 'danger';
  }
}

/**
 * 获取进度条颜色（兼容旧代码）
 * @param {number} percentage - 剩余百分比
 * @returns {string} - 颜色值
 */
function getProgressColor(percentage) {
  if (percentage > 50) {
    return 'var(--accent)';
  } else if (percentage > 20) {
    return 'var(--warn)';
  } else {
    return 'var(--error)';
  }
}

/**
 * 刷新用户面板
 */
async function refreshUserPanel() {
  await loadUserPanelData();
}

// 导出模块
window.initUserPanel = initUserPanel;
window.refreshUserPanel = refreshUserPanel;