/**
 * User Panel Module - Right side user status panel (Activation Code Architecture)
 * 用户面板模块 - 右侧用户状态面板（激活码架构）
 */

// 面板状态缓存
let panelState = {
  isActivated: false,
  activation: null,      // 激活码信息 { code_id, code, quota, remaining, referral_code, device_count }
  anonymousUsage: null,  // 匿名用户次数 { free_remaining, free_limit }
  devices: [],           // 设备列表
  referral: null         // 推荐码信息 { referral_code, referral_count, total_rewarded }
};

// 获取或创建设备 ID
function getOrCreateDeviceId() {
  let deviceId = localStorage.getItem('prism_device_id');
  if (!deviceId) {
    // 优先使用 crypto.randomUUID()（HTTPS 环境可用）
    // 降级方案：手动生成 UUID v4 格式
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      deviceId = crypto.randomUUID();
    } else {
      // 降级：手动生成 UUID v4 格式
      deviceId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
        .replace(/[xy]/g, function(c) {
          const r = Math.random() * 16 | 0;
          const v = c === 'x' ? r : (r & 0x3 | 0x8);
          return v.toString(16);
        });
    }
    localStorage.setItem('prism_device_id', deviceId);
  }
  return deviceId;
}

// 获取或创建访客 ID（匿名用户）
function getOrCreateVisitorId() {
  let visitorId = localStorage.getItem('prism_visitor_id');
  if (!visitorId) {
    visitorId = 'visitor_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('prism_visitor_id', visitorId);
  }
  return visitorId;
}

// 获取设备名称
function getDeviceName() {
  const ua = navigator.userAgent;
  let browser = 'Browser';
  let os = 'Unknown';

  // 检测浏览器
  if (ua.includes('Chrome') && !ua.includes('Edg')) browser = 'Chrome';
  else if (ua.includes('Safari') && !ua.includes('Chrome')) browser = 'Safari';
  else if (ua.includes('Firefox')) browser = 'Firefox';
  else if (ua.includes('Edg')) browser = 'Edge';
  else if (ua.includes('Opera') || ua.includes('OPR')) browser = 'Opera';

  // 检测操作系统
  if (ua.includes('Windows')) os = 'Windows';
  else if (ua.includes('Mac')) os = 'macOS';
  else if (ua.includes('Linux')) os = 'Linux';
  else if (ua.includes('Android')) os = 'Android';
  else if (ua.includes('iPhone') || ua.includes('iPad')) os = 'iOS';

  return `${browser} on ${os}`;
}

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

  const deviceId = getOrCreateDeviceId();

  // 检查激活状态
  try {
    const statusResp = await fetch('/api/activation/status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    if (statusResp.ok) {
      const statusResult = await statusResp.json();
      if (statusResult.success && statusResult.data) {
        panelState.isActivated = true;
        panelState.activation = statusResult.data;

        // 加载设备列表
        await loadDevices(deviceId);

        // 加载推荐码信息
        await loadReferralInfo(deviceId);
      } else {
        panelState.isActivated = false;
        // 加载匿名用户次数
        await loadAnonymousUsage();
      }
    } else {
      panelState.isActivated = false;
      await loadAnonymousUsage();
    }
  } catch (err) {
    console.error('加载激活状态失败:', err);
    panelState.isActivated = false;
    await loadAnonymousUsage();
  }

  renderUserPanel();
}

/**
 * 加载设备列表
 */
async function loadDevices(deviceId) {
  try {
    const resp = await fetch('/api/activation/devices', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    if (resp.ok) {
      const result = await resp.json();
      if (result.success && result.data) {
        panelState.devices = result.data.devices || [];
      }
    }
  } catch (err) {
    console.error('加载设备列表失败:', err);
  }
}

/**
 * 加载推荐码信息
 */
async function loadReferralInfo(deviceId) {
  try {
    const resp = await fetch('/api/activation/referral', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    if (resp.ok) {
      const result = await resp.json();
      if (result.success && result.data) {
        panelState.referral = result.data;
      }
    }
  } catch (err) {
    console.error('加载推荐码信息失败:', err);
  }
}

/**
 * 加载匿名用户次数信息
 */
async function loadAnonymousUsage() {
  try {
    const visitorId = getOrCreateVisitorId();
    const resp = await fetch('/api/usage/balance', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ visitor_id: visitorId })
    });

    if (resp.ok) {
      const result = await resp.json();
      if (result.success && result.data) {
        panelState.anonymousUsage = {
          free_remaining: result.data.free_remaining || 0,
          free_limit: result.data.free_limit || 3
        };
      }
    }
  } catch (err) {
    console.error('加载匿名用户次数失败:', err);
    panelState.anonymousUsage = { free_remaining: 3, free_limit: 3 };
  }
}

/**
 * 渲染用户面板
 */
function renderUserPanel() {
  const container = document.getElementById('user-panel-content');
  if (!container) return;

  if (panelState.isActivated && panelState.activation) {
    if (panelState.activation.remaining > 0) {
      container.innerHTML = renderActivatedPanel();
    } else {
      container.innerHTML = renderExhaustedPanel();
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
        <div class="user-panel-anonymous-icon">🎯</div>
        <div class="user-panel-anonymous-title">免费体验</div>
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

      <div class="user-panel-activation">
        <div class="activation-label">激活码</div>
        <input type="text" id="activation-code-input" class="activation-input" placeholder="PRISM-XXXX-XXXX-XXXX">
        <button id="activate-btn" class="user-panel-btn user-panel-btn-primary" onclick="handleActivate()">
          立即激活
        </button>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-link">
        <a href="#" onclick="showBuyActivationCode()">还没有激活码？→ 购买</a>
      </div>
    </div>
  `;
}

/**
 * 渲染已激活用户面板
 */
function renderActivatedPanel() {
  const activation = panelState.activation || {};
  const remaining = activation.remaining || 0;
  const quota = activation.quota || 0;
  const percentage = quota > 0 ? Math.round((remaining / quota) * 100) : 0;
  const progressClass = getProgressClass(percentage);

  const devices = panelState.devices || [];
  const deviceCount = devices.length;
  const currentDeviceId = getOrCreateDeviceId();

  const referral = panelState.referral || {};
  const referralCode = referral.referral_code || '';
  const referralCount = referral.referral_count || 0;
  const totalRewarded = referral.total_rewarded || 0;

  return `
    <div class="user-panel-section">
      <div class="user-panel-activated">
        <div class="user-panel-activated-icon">✅</div>
        <div class="user-panel-activated-title">已激活</div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-usage">
        <div class="usage-label">剩余次数</div>
        <div class="usage-progress-container">
          <div class="usage-progress-bar">
            <div class="usage-progress-fill ${progressClass}" style="width: ${percentage}%"></div>
          </div>
          <div class="usage-count">${remaining} / ${quota} 次</div>
        </div>
      </div>

      <div class="user-panel-usage">
        <div class="usage-label">今日免费次数</div>
        <div class="usage-count-static">已激活用户无限制</div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-referral">
        <div class="referral-header">
          <span class="referral-label">推荐码</span>
          <button class="referral-copy-btn" onclick="copyReferralCode('${referralCode}')">复制</button>
        </div>
        <div class="referral-code">${referralCode}</div>
        <div class="referral-stats">
          已推荐 <strong>${referralCount}</strong> 人 · 累计奖励 <strong>${totalRewarded}</strong> 次
        </div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-devices">
        <div class="devices-header">
          <span class="devices-label">我的设备</span>
          <span class="devices-count">${deviceCount} / 3</span>
        </div>
        <div class="devices-list">
          ${devices.map(d => `
            <div class="device-item ${d.device_id === currentDeviceId ? 'current' : ''}">
              <div class="device-info">
                <span class="device-icon">🖥️</span>
                <span class="device-name">${d.device_name || 'Unknown Device'}</span>
                ${d.is_current ? '<span class="device-current-badge">当前</span>' : ''}
              </div>
              <div class="device-meta">
                <span class="device-last-seen">${formatLastSeen(d.last_seen)}</span>
                ${!d.is_current ? `<button class="device-unbind-btn" onclick="handleUnbindDevice(${d.id})">解绑</button>` : ''}
              </div>
            </div>
          `).join('')}
        </div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-activation">
        <div class="activation-label">输入新激活码叠加次数</div>
        <input type="text" id="add-quota-input" class="activation-input" placeholder="PRISM-XXXX-XXXX-XXXX">
        <button id="add-quota-btn" class="user-panel-btn user-panel-btn-outline" onclick="handleAddQuota()">
          叠加次数
        </button>
      </div>
    </div>
  `;
}

/**
 * 渲染次数耗尽面板
 */
function renderExhaustedPanel() {
  return `
    <div class="user-panel-section">
      <div class="user-panel-exhausted">
        <div class="user-panel-exhausted-icon">⚠️</div>
        <div class="user-panel-exhausted-title">次数已用完</div>
      </div>

      <div class="user-panel-divider"></div>

      <div class="user-panel-actions column">
        <button class="user-panel-btn user-panel-btn-primary" onclick="showBuyActivationCode()">
          购买激活码
        </button>
        <div class="user-panel-activation" style="margin-top: 12px;">
          <input type="text" id="add-quota-input" class="activation-input" placeholder="PRISM-XXXX-XXXX-XXXX">
          <button class="user-panel-btn user-panel-btn-outline" onclick="handleAddQuota()">
            输入新激活码
          </button>
        </div>
      </div>
    </div>
  `;
}

/**
 * 处理激活
 */
async function handleActivate() {
  const input = document.getElementById('activation-code-input');
  const code = input?.value?.trim();

  if (!code) {
    showToast('请输入激活码', 'error');
    return;
  }

  const deviceId = getOrCreateDeviceId();
  const deviceName = getDeviceName();

  try {
    const resp = await fetch('/api/activation/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code,
        device_id: deviceId,
        device_name: deviceName
      })
    });

    const result = await resp.json();

    if (result.success) {
      showToast('激活成功！', 'success');
      // 存储激活码
      localStorage.setItem('prism_activation_code', code);
      // 刷新面板
      await loadUserPanelData();
    } else {
      showToast(result.message || '激活失败', 'error');
    }
  } catch (err) {
    console.error('激活失败:', err);
    showToast('激活失败，请稍后重试', 'error');
  }
}

/**
 * 处理叠加次数
 */
async function handleAddQuota() {
  const input = document.getElementById('add-quota-input');
  const code = input?.value?.trim();

  if (!code) {
    showToast('请输入激活码', 'error');
    return;
  }

  const deviceId = getOrCreateDeviceId();

  try {
    const resp = await fetch('/api/activation/add-quota', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: code,
        device_id: deviceId
      })
    });

    const result = await resp.json();

    if (result.success) {
      showToast(result.message || '叠加成功！', 'success');
      // 刷新面板
      await loadUserPanelData();
    } else {
      showToast(result.message || '叠加失败', 'error');
    }
  } catch (err) {
    console.error('叠加失败:', err);
    showToast('叠加失败，请稍后重试', 'error');
  }
}

/**
 * 处理解绑设备
 */
async function handleUnbindDevice(deviceDbId) {
  if (!confirm('确定要解绑此设备吗？')) return;

  const deviceId = getOrCreateDeviceId();

  try {
    const resp = await fetch(`/api/activation/devices/${deviceDbId}`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ device_id: deviceId })
    });

    const result = await resp.json();

    if (result.success) {
      showToast('设备已解绑', 'success');
      // 刷新设备列表
      await loadDevices(deviceId);
      renderUserPanel();
    } else {
      showToast(result.message || '解绑失败', 'error');
    }
  } catch (err) {
    console.error('解绑失败:', err);
    showToast('解绑失败，请稍后重试', 'error');
  }
}

/**
 * 复制推荐码
 */
function copyReferralCode(code) {
  if (!code) return;

  navigator.clipboard.writeText(code).then(() => {
    showToast('推荐码已复制', 'success');
  }).catch(() => {
    // 降级方案
    const textarea = document.createElement('textarea');
    textarea.value = code;
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand('copy');
    document.body.removeChild(textarea);
    showToast('推荐码已复制', 'success');
  });
}

/**
 * 显示购买激活码提示
 */
function showBuyActivationCode() {
  showToast('请联系管理员购买激活码', 'info');
}

/**
 * 格式化最后活跃时间
 */
function formatLastSeen(lastSeen) {
  if (!lastSeen) return '未知';

  try {
    const date = new Date(lastSeen);
    const now = new Date();
    const diff = now - date;

    if (diff < 60000) return '刚刚';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
    return `${Math.floor(diff / 86400000)} 天前`;
  } catch {
    return '未知';
  }
}

/**
 * 获取进度条颜色类名
 */
function getProgressClass(percentage) {
  if (percentage > 50) return 'normal';
  if (percentage > 20) return 'warn';
  return 'danger';
}

/**
 * 显示 Toast 提示
 */
function showToast(message, type = 'info') {
  // 检查是否有全局的 showToast 函数
  if (typeof window.showToast === 'function' && window.showToast !== showToast) {
    window.showToast(message, type);
    return;
  }

  // 简单的 toast 实现
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.style.cssText = `
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    padding: 12px 24px;
    border-radius: 8px;
    background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
    color: white;
    font-size: 14px;
    z-index: 9999;
    animation: fadeInUp 0.3s ease;
  `;

  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = 'fadeOutDown 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
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
window.handleActivate = handleActivate;
window.handleAddQuota = handleAddQuota;
window.handleUnbindDevice = handleUnbindDevice;
window.copyReferralCode = copyReferralCode;
window.showBuyActivationCode = showBuyActivationCode;