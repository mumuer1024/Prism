/**
 * Prism 管理后台 JavaScript (v2.1 激活码架构)
 */

// API 基础路径
const API_BASE = '/api/admin';

// 状态
let adminToken = null;
let codesPage = 1;
let auditPage = 1;

// ==========================================
// 初始化
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
  // 初始化主题
  initTheme();
  
  // 检查登录状态
  checkAdminLogin();
});

// ==========================================
// 管理员认证
// ==========================================

async function checkAdminLogin() {
  // 从 Cookie 或 localStorage 获取 token
  adminToken = getCookie('admin_token') || localStorage.getItem('admin_token');
  
  if (!adminToken) {
    showLoginScreen();
    return;
  }
  
  // 验证 token
  try {
    const resp = await fetch(`${API_BASE}/me`, {
      headers: { 'X-Admin-Token': adminToken }
    });
    
    if (resp.ok) {
      showMainContent();
      loadOverview();
      loadAuditActions();
    } else {
      showLoginScreen();
    }
  } catch (err) {
    console.error('Token validation failed:', err);
    showLoginScreen();
  }
}

function showLoginScreen() {
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('main-content').classList.add('hidden');
}

function showMainContent() {
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('main-content').classList.remove('hidden');
}

async function adminLogin() {
  const username = document.getElementById('admin-username').value.trim();
  const password = document.getElementById('admin-password').value;
  
  if (!username || !password) {
    showLoginError('请输入账号和密码');
    return;
  }
  
  try {
    const resp = await fetch(`${API_BASE}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    });
    
    const data = await resp.json();
    
    if (data.success) {
      adminToken = data.token;
      localStorage.setItem('admin_token', adminToken);
      showMainContent();
      loadOverview();
      loadAuditActions();
    } else {
      showLoginError(data.message || '登录失败');
    }
  } catch (err) {
    console.error('Login failed:', err);
    showLoginError('登录失败，请稍后重试');
  }
}

function showLoginError(msg) {
  const el = document.getElementById('login-error');
  el.textContent = msg;
  el.classList.remove('hidden');
}

async function adminLogout() {
  try {
    await fetch(`${API_BASE}/logout`, {
      method: 'POST',
      headers: { 'X-Admin-Token': adminToken }
    });
  } catch (err) {}
  
  adminToken = null;
  localStorage.removeItem('admin_token');
  showLoginScreen();
}

// ==========================================
// API 请求封装
// ==========================================

async function apiRequest(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'X-Admin-Token': adminToken,
    ...options.headers
  };
  
  const resp = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });
  
  if (resp.status === 401) {
    showLoginScreen();
    throw new Error('Unauthorized');
  }
  
  return resp;
}

// ==========================================
// Tab 切换
// ==========================================

function switchAdminTab(tab) {
  // 更新按钮状态
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(`tab-${tab}`).classList.add('active');
  
  // 更新面板显示
  document.querySelectorAll('.admin-panel').forEach(panel => panel.classList.add('hidden'));
  document.getElementById(`panel-${tab}`).classList.remove('hidden');
  
  // 加载数据
  if (tab === 'overview') loadOverview();
  if (tab === 'codes') loadCodes();
  if (tab === 'audit') loadAuditLogs();
}

// ==========================================
// 概览统计
// ==========================================

async function loadOverview() {
  try {
    const resp = await apiRequest('/stats');
    const data = await resp.json();
    
    document.getElementById('stat-total-codes').textContent = data.total_codes || 0;
    document.getElementById('stat-activated-codes').textContent = data.activated_codes || 0;
    document.getElementById('stat-unused-codes').textContent = data.unused_codes || 0;
    document.getElementById('stat-today-activations').textContent = data.today_activations || 0;
    document.getElementById('stat-total-quota').textContent = data.total_quota || 0;
    document.getElementById('stat-total-remaining').textContent = data.total_remaining || 0;
    document.getElementById('stat-total-devices').textContent = data.total_devices || 0;
    document.getElementById('stat-total-referrals').textContent = data.total_referrals || 0;
  } catch (err) {
    console.error('Load overview failed:', err);
  }
}

// ==========================================
// 激活码管理
// ==========================================

async function loadCodes() {
  const search = document.getElementById('code-search').value.trim();
  const filter = document.getElementById('code-filter').value;
  
  let url = `/codes?page=${codesPage}&limit=20`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (filter) url += `&is_activated=${filter}`;
  
  try {
    const resp = await apiRequest(url);
    const data = await resp.json();
    
    renderCodesTable(data.codes || []);
    renderCodesPagination(data.total || 0, data.page || 1, data.limit || 20);
  } catch (err) {
    console.error('Load codes failed:', err);
    document.getElementById('codes-table-body').innerHTML = '<tr><td colspan="8" class="text-center text-text-muted py-8">加载失败</td></tr>';
  }
}

function renderCodesTable(codes) {
  const tbody = document.getElementById('codes-table-body');
  
  if (!codes.length) {
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-text-muted py-8">暂无数据</td></tr>';
    return;
  }
  
  tbody.innerHTML = codes.map(code => `
    <tr>
      <td>${code.id}</td>
      <td class="font-mono">${code.code}</td>
      <td>${code.quota}</td>
      <td>${code.remaining}</td>
      <td>
        <span class="badge ${code.is_activated ? 'badge-success' : 'badge-info'}">
          ${code.is_activated ? '已激活' : '未激活'}
        </span>
      </td>
      <td>${code.device_count || 0}</td>
      <td>${code.activated_at ? formatDate(code.activated_at) : '-'}</td>
      <td>
        <button onclick="showDevicesModal(${code.id})" class="text-sm text-accent hover:underline mr-2">设备</button>
        ${code.remaining > 0 ? `<button onclick="revokeCode(${code.id})" class="text-sm text-error hover:underline">作废</button>` : ''}
      </td>
    </tr>
  `).join('');
}

function renderCodesPagination(total, page, limit) {
  const totalPages = Math.ceil(total / limit);
  document.getElementById('codes-pagination-info').textContent = `共 ${total} 条`;
  
  let html = '';
  if (page > 1) {
    html += `<button onclick="goToCodesPage(${page - 1})" class="px-3 py-1 rounded-lg border border-border text-text-secondary text-sm">上一页</button>`;
  }
  html += `<span class="text-sm text-text-muted px-2">第 ${page} / ${totalPages} 页</span>`;
  if (page < totalPages) {
    html += `<button onclick="goToCodesPage(${page + 1})" class="px-3 py-1 rounded-lg border border-border text-text-secondary text-sm">下一页</button>`;
  }
  
  document.getElementById('codes-pagination').innerHTML = html;
}

function goToCodesPage(page) {
  codesPage = page;
  loadCodes();
}

// 生成激活码
function showGenerateModal() {
  document.getElementById('generate-modal').classList.remove('hidden');
}

function hideGenerateModal() {
  document.getElementById('generate-modal').classList.add('hidden');
}

async function generateCodes() {
  const count = parseInt(document.getElementById('gen-count').value) || 10;
  const quota = parseInt(document.getElementById('gen-quota').value) || 10;
  const note = document.getElementById('gen-note').value.trim();
  
  if (count < 1 || count > 1000) {
    alert('生成数量必须在 1-1000 之间');
    return;
  }
  
  try {
    const resp = await apiRequest('/codes/generate', {
      method: 'POST',
      body: JSON.stringify({ count, quota, note })
    });
    
    const data = await resp.json();
    
    if (data.success) {
      hideGenerateModal();
      showResult('生成成功', data.codes.join('\n'));
      loadCodes();
      loadOverview();
    } else {
      alert(data.message || '生成失败');
    }
  } catch (err) {
    console.error('Generate codes failed:', err);
    alert('生成失败，请稍后重试');
  }
}

// 作废激活码
async function revokeCode(codeId) {
  if (!confirm('确定要作废此激活码吗？作废后次数将归零，无法恢复。')) return;
  
  try {
    const resp = await apiRequest(`/codes/${codeId}`, { method: 'DELETE' });
    const data = await resp.json();
    
    if (data.success) {
      alert('激活码已作废');
      loadCodes();
      loadOverview();
    } else {
      alert(data.message || '作废失败');
    }
  } catch (err) {
    console.error('Revoke code failed:', err);
    alert('作废失败，请稍后重试');
  }
}

// 查看设备绑定
async function showDevicesModal(codeId) {
  document.getElementById('devices-modal').classList.remove('hidden');
  document.getElementById('devices-content').innerHTML = '<p class="text-text-muted">加载中...</p>';
  
  try {
    const resp = await apiRequest(`/codes/${codeId}/devices`);
    const data = await resp.json();
    
    if (data.success) {
      const devices = data.devices || [];
      if (!devices.length) {
        document.getElementById('devices-content').innerHTML = '<p class="text-text-muted">该激活码暂无绑定设备</p>';
      } else {
        document.getElementById('devices-content').innerHTML = `
          <div class="mb-2 text-sm text-text-muted">激活码: <span class="font-mono text-text">${data.code}</span></div>
          <table class="admin-table text-sm">
            <thead>
              <tr>
                <th>设备ID</th>
                <th>设备名称</th>
                <th>最后活跃</th>
              </tr>
            </thead>
            <tbody>
              ${devices.map(d => `
                <tr>
                  <td class="font-mono text-xs">${d.device_id.substring(0, 16)}...</td>
                  <td>${d.device_name || '-'}</td>
                  <td>${d.last_seen ? formatDate(d.last_seen) : '-'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
      }
    } else {
      document.getElementById('devices-content').innerHTML = '<p class="text-error">加载失败</p>';
    }
  } catch (err) {
    console.error('Load devices failed:', err);
    document.getElementById('devices-content').innerHTML = '<p class="text-error">加载失败</p>';
  }
}

function hideDevicesModal() {
  document.getElementById('devices-modal').classList.add('hidden');
}

// ==========================================
// 审计日志
// ==========================================

async function loadAuditActions() {
  try {
    const resp = await apiRequest('/audit-logs/actions');
    const data = await resp.json();
    
    const select = document.getElementById('audit-action-filter');
    select.innerHTML = '<option value="">全部操作</option>' +
      (data.actions || []).map(a => `<option value="${a.value}">${a.label}</option>`).join('');
  } catch (err) {
    console.error('Load audit actions failed:', err);
  }
}

async function loadAuditLogs() {
  const action = document.getElementById('audit-action-filter').value;
  const startDate = document.getElementById('audit-start-date').value;
  const endDate = document.getElementById('audit-end-date').value;
  
  let url = `/audit-logs?page=${auditPage}&limit=50`;
  if (action) url += `&action=${encodeURIComponent(action)}`;
  if (startDate) url += `&start_date=${startDate}`;
  if (endDate) url += `&end_date=${endDate}`;
  
  try {
    const resp = await apiRequest(url);
    const data = await resp.json();
    
    renderAuditTable(data.logs || []);
    document.getElementById('audit-total').textContent = data.total || 0;
    document.getElementById('audit-page-info').textContent = `第 ${auditPage} 页`;
    
    document.getElementById('audit-prev-btn').disabled = auditPage <= 1;
    document.getElementById('audit-next-btn').disabled = data.logs?.length < 50;
  } catch (err) {
    console.error('Load audit logs failed:', err);
  }
}

function renderAuditTable(logs) {
  const tbody = document.getElementById('audit-table-body');
  
  if (!logs.length) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-text-muted py-8">暂无日志</td></tr>';
    return;
  }
  
  tbody.innerHTML = logs.map(log => `
    <tr>
      <td>${log.id}</td>
      <td>${log.admin_username || '-'}</td>
      <td>${log.action || '-'}</td>
      <td>${log.target_type ? `${log.target_type}:${log.target_id}` : '-'}</td>
      <td class="text-xs">${log.action_detail ? JSON.stringify(log.action_detail) : '-'}</td>
      <td>${log.ip_address || '-'}</td>
      <td>${formatDate(log.created_at)}</td>
    </tr>
  `).join('');
}

function prevAuditPage() {
  if (auditPage > 1) {
    auditPage--;
    loadAuditLogs();
  }
}

function nextAuditPage() {
  auditPage++;
  loadAuditLogs();
}

// ==========================================
// 结果弹窗
// ==========================================

function showResult(title, content) {
  document.getElementById('result-title').textContent = title;
  document.getElementById('result-content').textContent = content;
  document.getElementById('result-modal').classList.remove('hidden');
}

function hideResultModal() {
  document.getElementById('result-modal').classList.add('hidden');
}

/**
 * 复制到剪贴板（支持 HTTP 环境降级）
 */
async function copyToClipboard(text) {
  try {
    // 优先使用 clipboard API（需要 HTTPS）
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      // 降级：使用 execCommand
      const el = document.createElement('textarea');
      el.value = text;
      el.style.position = 'fixed';
      el.style.opacity = '0';
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
    }
    return true;
  } catch (e) {
    console.error('复制失败:', e);
    return false;
  }
}

function copyResult() {
  const content = document.getElementById('result-content').textContent;
  copyToClipboard(content).then(success => {
    if (success) {
      alert('已复制到剪贴板');
    } else {
      alert('复制失败，请手动复制');
    }
  });
}

// ==========================================
// 工具函数
// ==========================================

function getCookie(name) {
  const cookies = document.cookie.split(';');
  for (const cookie of cookies) {
    const [key, value] = cookie.trim().split('=');
    if (key === name) return value;
  }
  return null;
}

function formatDate(dateStr) {
  if (!dateStr) return '-';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
}

// 主题初始化（从 core.js 复制）
function initTheme() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark');
    document.getElementById('theme-icon-sun')?.classList.remove('hidden');
    document.getElementById('theme-icon-moon')?.classList.add('hidden');
  }
}

function toggleTheme() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('theme', isDark ? 'dark' : 'light');
  document.getElementById('theme-icon-sun')?.classList.toggle('hidden', !isDark);
  document.getElementById('theme-icon-moon')?.classList.toggle('hidden', isDark);
}

// 导出函数到 window 对象
window.copyResult = copyResult;
window.copyToClipboard = copyToClipboard;
window.toggleTheme = toggleTheme;
window.initTheme = initTheme;