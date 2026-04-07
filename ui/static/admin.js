/**
 * Prism 管理后台 JavaScript
 */

// API 基础路径
const API_BASE = '/api/admin';

// 状态
let currentPage = 1;
let currentSearch = '';
let currentFilter = '';
let selectedUsers = [];  // 批量选择的用户ID
let auditPage = 1;       // 审计日志页码

// ==========================================
// 初始化
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
  // 初始化主题
  initTheme();

  // 检查管理员权限
  checkAdminAuth();

  // 加载概览数据
  loadOverview();

  // 加载审计操作类型
  loadAuditActions();
});

// ==========================================
// 认证检查
// ==========================================

async function checkAdminAuth() {
  const token = AuthState.getToken();
  if (!token) {
    window.location.href = '/login?redirect=/admin';
    return;
  }

  try {
    const response = await fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    });

    if (!response.ok) {
      window.location.href = '/login?redirect=/admin';
      return;
    }

    const data = await response.json();

    // 检查用户是否是管理员
    const user = data.data?.user;
    if (!user || !user.is_admin) {
      alert('您没有管理员权限');
      window.location.href = '/';
      return;
    }
  } catch (error) {
    console.error('Auth check failed:', error);
    window.location.href = '/login?redirect=/admin';
  }
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
  if (tab === 'users') loadUsers();
  if (tab === 'codes') loadBatches();
  if (tab === 'audit') loadAuditLogs();
}

// ==========================================
// API 请求
// ==========================================

async function apiRequest(endpoint, options = {}) {
  const token = AuthState.getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options.headers
  };
  
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers
  });
  
  if (response.status === 401) {
    window.location.href = '/login?redirect=/admin';
    return null;
  }
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(error.detail || '请求失败');
  }
  
  return response.json();
}

// ==========================================
// 概览
// ==========================================

async function loadOverview() {
  try {
    // 并行加载用户统计和充值统计
    const [userStats, revenueStats] = await Promise.all([
      apiRequest('/stats/users'),
      apiRequest('/stats/revenue')
    ]);
    
    if (userStats) {
      document.getElementById('stat-total-users').textContent = userStats.total_users || 0;
      document.getElementById('stat-active-users').textContent = userStats.active_users || 0;
      document.getElementById('stat-new-today').textContent = userStats.new_users_today || 0;
      document.getElementById('stat-banned-users').textContent = userStats.banned_users || 0;
    }
    
    if (revenueStats) {
      document.getElementById('stat-total-topup').textContent = revenueStats.total_topup_count || 0;
      document.getElementById('stat-total-bonus').textContent = revenueStats.total_bonus_count || 0;
      document.getElementById('stat-codes-used').textContent = revenueStats.total_codes_used || 0;
      document.getElementById('stat-codes-unused').textContent = revenueStats.total_codes_unused || 0;
    }
  } catch (error) {
    console.error('Load overview failed:', error);
  }
}

// ==========================================
// 用户管理
// ==========================================

async function loadUsers(page = 1) {
  currentPage = page;
  
  try {
    const params = new URLSearchParams({
      page: page,
      limit: 20
    });
    
    if (currentSearch) params.append('search', currentSearch);
    if (currentFilter) params.append('is_banned', currentFilter);
    
    const data = await apiRequest(`/users?${params}`);
    
    if (data) {
      renderUsersTable(data.users);
      renderUsersPagination(data.total, page);
    }
  } catch (error) {
    console.error('Load users failed:', error);
    document.getElementById('users-table-body').innerHTML = 
      `<tr><td colspan="7" class="text-center text-error py-8">加载失败: ${error.message}</td></tr>`;
  }
}

function renderUsersTable(users) {
  const tbody = document.getElementById('users-table-body');

  if (!users || users.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-text-muted py-8">暂无数据</td></tr>`;
    return;
  }

  tbody.innerHTML = users.map(user => `
    <tr>
      <td>
        <input type="checkbox"
               class="user-select-checkbox"
               data-user-id="${user.id}"
               data-user-email="${user.email}"
               ${user.is_banned ? 'disabled' : ''}
               ${selectedUsers.includes(user.id) ? 'checked' : ''}
               onchange="toggleUserSelect(${user.id}, '${user.email}', this.checked)">
      </td>
      <td class="font-mono">${user.id}</td>
      <td>${user.email}</td>
      <td>${user.nickname || '-'}</td>
      <td class="font-mono">${user.usage_count}</td>
      <td>
        ${user.is_banned
          ? `<span class="badge badge-error">已封禁</span>`
          : `<span class="badge badge-success">正常</span>`
        }
      </td>
      <td class="text-sm text-text-muted">${formatDate(user.created_at)}</td>
      <td>
        <div class="flex gap-2">
          <button onclick="viewUser(${user.id})" class="text-sm text-accent hover:underline">详情</button>
          ${user.is_banned
            ? `<button onclick="unbanUserConfirm(${user.id})" class="text-sm text-success hover:underline">解禁</button>`
            : `<button onclick="showBanModal(${user.id})" class="text-sm text-error hover:underline">封禁</button>`
          }
        </div>
      </td>
    </tr>
  `).join('');

  // 更新全选复选框状态
  updateSelectAllState();
}

function renderUsersPagination(total, current) {
  const totalPages = Math.ceil(total / 20);
  const info = document.getElementById('users-pagination-info');
  const pagination = document.getElementById('users-pagination');
  
  info.textContent = `共 ${total} 条`;
  
  if (totalPages <= 1) {
    pagination.innerHTML = '';
    return;
  }
  
  let html = '';
  
  if (current > 1) {
    html += `<button onclick="loadUsers(${current - 1})" class="px-3 py-1 rounded border border-border text-sm">上一页</button>`;
  }
  
  for (let i = Math.max(1, current - 2); i <= Math.min(totalPages, current + 2); i++) {
    if (i === current) {
      html += `<button class="px-3 py-1 rounded bg-accent text-accent-text text-sm font-medium">${i}</button>`;
    } else {
      html += `<button onclick="loadUsers(${i})" class="px-3 py-1 rounded border border-border text-sm">${i}</button>`;
    }
  }
  
  if (current < totalPages) {
    html += `<button onclick="loadUsers(${current + 1})" class="px-3 py-1 rounded border border-border text-sm">下一页</button>`;
  }
  
  pagination.innerHTML = html;
}

function searchUsers() {
  currentSearch = document.getElementById('user-search').value.trim();
  currentFilter = document.getElementById('user-filter').value;
  loadUsers(1);
}

async function viewUser(userId) {
  try {
    const data = await apiRequest(`/users/${userId}`);
    if (data && data.data) {
      const user = data.data;
      const stats = user.invite_stats || {};
      
      showResult('用户详情', `
        <div class="space-y-3">
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">ID:</div>
            <div class="font-mono">${user.id}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">邮箱:</div>
            <div>${user.email}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">昵称:</div>
            <div>${user.nickname || '-'}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">使用次数:</div>
            <div class="font-mono">${user.usage_count}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">邀请码:</div>
            <div class="font-mono">${user.invite_code || '-'}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">状态:</div>
            <div>${user.is_banned ? '已封禁' : '正常'}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">注册时间:</div>
            <div>${formatDate(user.created_at)}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">最后登录:</div>
            <div>${formatDate(user.last_login_at)}</div>
          </div>
          <hr class="border-border my-2">
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">总充值次数:</div>
            <div class="font-mono">${user.total_topup_count || 0}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">总赠送次数:</div>
            <div class="font-mono">${user.total_bonus_count || 0}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">邀请人数:</div>
            <div class="font-mono">${stats.total_invited || 0}</div>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <div class="text-text-muted">邀请奖励:</div>
            <div class="font-mono">${stats.total_bonus || 0}</div>
          </div>
        </div>
      `);
    }
  } catch (error) {
    alert('获取用户详情失败: ' + error.message);
  }
}

function showBanModal(userId) {
  document.getElementById('ban-user-id').value = userId;
  document.getElementById('ban-reason').value = '';
  document.getElementById('ban-modal').classList.remove('hidden');
}

function hideBanModal() {
  document.getElementById('ban-modal').classList.add('hidden');
}

async function banUser() {
  const userId = document.getElementById('ban-user-id').value;
  const reason = document.getElementById('ban-reason').value.trim() || '违规操作';
  
  try {
    await apiRequest(`/users/${userId}/ban`, {
      method: 'PATCH',
      body: JSON.stringify({ reason })
    });
    
    hideBanModal();
    loadUsers(currentPage);
    alert('用户已封禁');
  } catch (error) {
    alert('封禁失败: ' + error.message);
  }
}

async function unbanUserConfirm(userId) {
  if (!confirm('确定要解禁该用户吗？')) return;
  
  try {
    await apiRequest(`/users/${userId}/unban`, { method: 'PATCH' });
    loadUsers(currentPage);
    alert('用户已解禁');
  } catch (error) {
    alert('解禁失败: ' + error.message);
  }
}

// ==========================================
// 兑换码管理
// ==========================================

async function loadBatches() {
  try {
    const data = await apiRequest('/codes/batches');
    
    if (data) {
      renderBatchesTable(data.batches);
    }
  } catch (error) {
    console.error('Load batches failed:', error);
    document.getElementById('batches-table-body').innerHTML = 
      `<tr><td colspan="7" class="text-center text-error py-8">加载失败: ${error.message}</td></tr>`;
  }
}

function renderBatchesTable(batches) {
  const tbody = document.getElementById('batches-table-body');
  
  if (!batches || batches.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center text-text-muted py-8">暂无数据</td></tr>`;
    return;
  }
  
  tbody.innerHTML = batches.map(batch => `
    <tr>
      <td class="font-mono text-sm">${batch.batch_id}</td>
      <td class="font-mono">${batch.total_codes}</td>
      <td>
        <span class="text-text-muted">${batch.used_codes}</span>
        <span class="text-text-muted">/</span>
        <span class="text-success">${batch.unused_codes}</span>
      </td>
      <td class="font-mono">${batch.total_count}</td>
      <td class="text-sm text-text-muted">${formatDate(batch.created_at)}</td>
      <td class="text-sm text-text-muted">${formatDate(batch.expires_at)}</td>
      <td>
        <div class="flex gap-2">
          <button onclick="viewBatch('${batch.batch_id}')" class="text-sm text-accent hover:underline">详情</button>
          <button onclick="exportBatch('${batch.batch_id}')" class="text-sm text-success hover:underline">导出</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function showGenerateModal() {
  document.getElementById('gen-count').value = 10;
  document.getElementById('gen-usage').value = 10;
  document.getElementById('gen-expire').value = 365;
  document.getElementById('gen-note').value = '';
  document.getElementById('generate-modal').classList.remove('hidden');
}

function hideGenerateModal() {
  document.getElementById('generate-modal').classList.add('hidden');
}

async function generateCodes() {
  const count = parseInt(document.getElementById('gen-count').value);
  const usageCount = parseInt(document.getElementById('gen-usage').value);
  const expireDays = parseInt(document.getElementById('gen-expire').value);
  const note = document.getElementById('gen-note').value.trim();
  
  if (count < 1 || count > 1000) {
    alert('生成数量需在 1-1000 之间');
    return;
  }
  
  if (usageCount < 1 || usageCount > 1000) {
    alert('使用次数需在 1-1000 之间');
    return;
  }
  
  try {
    const data = await apiRequest('/codes/generate', {
      method: 'POST',
      body: JSON.stringify({
        count,
        usage_count: usageCount,
        expire_days: expireDays,
        note: note || null
      })
    });
    
    if (data) {
      hideGenerateModal();
      
      // 显示生成的兑换码
      const codesList = data.codes.map(code => `<div class="font-mono text-sm">${code}</div>`).join('');
      showResult('生成成功', `
        <div class="mb-2 text-text-muted">
          批次号: <span class="font-mono">${data.batch_id}</span><br>
          数量: ${data.count} 个<br>
          每个次数: ${data.usage_count_per_code} 次<br>
          过期时间: ${formatDate(data.expires_at)}
        </div>
        <div class="mt-4 max-h-64 overflow-y-auto border border-border rounded p-2">
          ${codesList}
        </div>
      `);
      
      loadBatches();
    }
  } catch (error) {
    alert('生成失败: ' + error.message);
  }
}

async function viewBatch(batchId) {
  try {
    const data = await apiRequest(`/codes/batches/${batchId}`);
    
    if (data && data.data) {
      const batch = data.data;
      const codesHtml = batch.codes.map(code => `
        <tr>
          <td class="font-mono text-sm">${code.code}</td>
          <td class="font-mono">${code.count}</td>
          <td>${code.used ? '<span class="badge badge-error">已使用</span>' : '<span class="badge badge-success">未使用</span>'}</td>
          <td class="text-sm">${code.used_by_email || '-'}</td>
          <td class="text-sm text-text-muted">${formatDate(code.used_at)}</td>
        </tr>
      `).join('');
      
      showResult(`批次详情: ${batchId}`, `
        <div class="mb-4 text-sm text-text-muted">
          总数: ${batch.total_codes} | 已用: ${batch.used_codes} | 未用: ${batch.unused_codes}<br>
          总次数: ${batch.total_count} | 过期: ${formatDate(batch.expires_at)}
        </div>
        <div class="max-h-64 overflow-y-auto">
          <table class="admin-table text-sm">
            <thead>
              <tr>
                <th>兑换码</th>
                <th>次数</th>
                <th>状态</th>
                <th>使用者</th>
                <th>使用时间</th>
              </tr>
            </thead>
            <tbody>${codesHtml}</tbody>
          </table>
        </div>
      `);
    }
  } catch (error) {
    alert('获取批次详情失败: ' + error.message);
  }
}

async function exportBatch(batchId) {
  try {
    const data = await apiRequest(`/codes/batches/${batchId}/export`);
    
    if (data && data.codes) {
      // 创建 CSV 内容
      const headers = ['兑换码', '次数', '状态', '使用者', '使用时间', '过期时间', '创建时间'];
      const rows = data.codes.map(code => [
        code.code,
        code.count,
        code.used,
        code.used_by || '',
        code.used_at || '',
        code.expires_at || '',
        code.created_at || ''
      ]);
      
      const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
      
      // 下载文件
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `codes_${batchId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    }
  } catch (error) {
    alert('导出失败: ' + error.message);
  }
}

// ==========================================
// 工具函数
// ==========================================

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

function showResult(title, content) {
  document.getElementById('result-title').textContent = title;
  document.getElementById('result-content').innerHTML = content;
  document.getElementById('result-modal').classList.remove('hidden');
}

function hideResultModal() {
  document.getElementById('result-modal').classList.add('hidden');
}

// ==========================================
// 批量封禁功能
// ==========================================

function toggleUserSelect(userId, userEmail, checked) {
  if (checked) {
    if (!selectedUsers.includes(userId)) {
      selectedUsers.push(userId);
    }
  } else {
    selectedUsers = selectedUsers.filter(id => id !== userId);
  }
  updateBatchBanButton();
  updateSelectAllState();
}

function toggleSelectAll() {
  const selectAllCheckbox = document.getElementById('select-all-users');
  const checkboxes = document.querySelectorAll('.user-select-checkbox:not(:disabled)');

  checkboxes.forEach(cb => {
    const userId = parseInt(cb.dataset.user_id);
    const userEmail = cb.dataset.user_email;

    if (selectAllCheckbox.checked) {
      if (!selectedUsers.includes(userId)) {
        selectedUsers.push(userId);
      }
      cb.checked = true;
    } else {
      selectedUsers = selectedUsers.filter(id => id !== userId);
      cb.checked = false;
    }
  });

  updateBatchBanButton();
}

function updateSelectAllState() {
  const selectAllCheckbox = document.getElementById('select-all-users');
  const checkboxes = document.querySelectorAll('.user-select-checkbox:not(:disabled)');
  const checkedCount = selectedUsers.length;
  const totalCount = checkboxes.length;

  if (totalCount === 0) {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
  } else if (checkedCount === 0) {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = false;
  } else if (checkedCount === totalCount) {
    selectAllCheckbox.checked = true;
    selectAllCheckbox.indeterminate = false;
  } else {
    selectAllCheckbox.checked = false;
    selectAllCheckbox.indeterminate = true;
  }
}

function updateBatchBanButton() {
  const btn = document.getElementById('batch-ban-btn');
  const countSpan = document.getElementById('selected-count');

  if (selectedUsers.length > 0) {
    btn.classList.remove('hidden');
    countSpan.textContent = selectedUsers.length;
  } else {
    btn.classList.add('hidden');
  }
}

function showBatchBanModal() {
  if (selectedUsers.length === 0) {
    alert('请先选择要封禁的用户');
    return;
  }

  // 获取选中用户的邮箱列表
  const checkboxes = document.querySelectorAll('.user-select-checkbox:checked');
  const userEmails = Array.from(checkboxes).map(cb => `${cb.dataset.user_id}: ${cb.dataset.user_email}`);

  document.getElementById('batch-ban-count').textContent = selectedUsers.length;
  document.getElementById('batch-ban-users-preview').innerHTML = userEmails.join('<br>');
  document.getElementById('batch-ban-modal').classList.remove('hidden');
}

function hideBatchBanModal() {
  document.getElementById('batch-ban-modal').classList.add('hidden');
}

async function executeBatchBan() {
  const reason = document.getElementById('batch-ban-reason').value.trim() || '违规操作';

  try {
    const result = await apiRequest('/users/batch-ban', {
      method: 'POST',
      body: JSON.stringify({
        user_ids: selectedUsers,
        reason: reason
      })
    });

    hideBatchBanModal();

    // 显示结果
    const detailsHtml = result.details.map(d =>
      `<div class="${d.success ? 'text-success' : 'text-error'}">
        ${d.user_id}: ${d.email} - ${d.message}
      </div>`
    ).join('');

    showResult('批量封禁结果', `
      <p>总计: ${result.total} 个用户</p>
      <p class="text-success">成功: ${result.succeeded} 个</p>
      <p class="text-error">失败: ${result.failed} 个</p>
      <hr class="my-2 border-border">
      ${detailsHtml}
    `);

    // 清空选择并刷新列表
    selectedUsers = [];
    updateBatchBanButton();
    loadUsers();

  } catch (error) {
    alert('批量封禁失败: ' + error.message);
  }
}

// ==========================================
// 审计日志功能
// ==========================================

async function loadAuditActions() {
  try {
    const result = await apiRequest('/audit-logs/actions');

    // 填充操作类型下拉框
    const actionSelect = document.getElementById('audit-action-filter');
    actionSelect.innerHTML = '<option value="">全部操作</option>' +
      result.actions.map(a => `<option value="${a.value}">${a.label}</option>`).join('');

    // 填充操作分类下拉框
    const categorySelect = document.getElementById('audit-category-filter');
    categorySelect.innerHTML = '<option value="">全部分类</option>' +
      result.categories.map(c => `<option value="${c.value}">${c.label}</option>`).join('');

  } catch (error) {
    console.error('加载审计操作类型失败:', error);
  }
}

async function loadAuditLogs() {
  const action = document.getElementById('audit-action-filter').value;
  const category = document.getElementById('audit-category-filter').value;
  const startDate = document.getElementById('audit-start-date').value;
  const endDate = document.getElementById('audit-end-date').value;

  let url = `/audit-logs?page=${auditPage}&limit=50`;
  if (action) url += `&action=${action}`;
  if (category) url += `&action_category=${category}`;
  if (startDate) url += `&start_date=${startDate}`;
  if (endDate) url += `&end_date=${endDate}`;

  try {
    const result = await apiRequest(url);
    renderAuditLogs(result.logs);
    renderAuditPagination(result.total, auditPage);
  } catch (error) {
    console.error('加载审计日志失败:', error);
    document.getElementById('audit-table-body').innerHTML =
      `<tr><td colspan="8" class="text-center text-text-muted py-8">加载失败</td></tr>`;
  }
}

function renderAuditLogs(logs) {
  const tbody = document.getElementById('audit-table-body');

  if (!logs || logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" class="text-center text-text-muted py-8">暂无数据</td></tr>`;
    return;
  }

  // 操作类型映射
  const actionLabels = {
    'ban_user': '封禁用户',
    'unban_user': '解禁用户',
    'batch_ban_users': '批量封禁',
    'generate_codes': '生成兑换码',
    'export_codes': '导出兑换码',
    'create_template': '创建模板',
    'update_template': '更新模板',
    'delete_template': '删除模板',
  };

  // 分类映射
  const categoryLabels = {
    'user_management': '用户管理',
    'code_management': '兑换码管理',
    'template_management': '模板管理',
    'system_config': '系统配置',
  };

  tbody.innerHTML = logs.map(log => `
    <tr>
      <td class="font-mono">${log.id}</td>
      <td>${log.admin_email}</td>
      <td>${actionLabels[log.action] || log.action}</td>
      <td>${categoryLabels[log.action_category] || log.action_category}</td>
      <td>
        ${log.target_type ? `${log.target_type}: ${log.target_id || '-'}` : '-'}
      </td>
      <td class="text-sm text-text-muted max-w-xs truncate">
        ${log.action_detail ? JSON.stringify(log.action_detail).substring(0, 50) + '...' : '-'}
      </td>
      <td class="font-mono text-sm">${log.ip_address || '-'}</td>
      <td class="text-sm text-text-muted">${formatDate(log.created_at)}</td>
    </tr>
  `).join('');
}

function renderAuditPagination(total, current) {
  document.getElementById('audit-total').textContent = total;
  document.getElementById('audit-page-info').textContent = `第 ${current} 页`;

  const prevBtn = document.getElementById('audit-prev-btn');
  const nextBtn = document.getElementById('audit-next-btn');

  prevBtn.disabled = current <= 1;
  nextBtn.disabled = current >= Math.ceil(total / 50);
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