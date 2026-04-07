/**
 * Reports Module - Report listing and viewing
 * 报告模块 - 报告列表和查看
 *
 * v2.1 激活码架构：使用 device_id 认证
 */

// 当前选中的报告路径
let selectedReports = new Set();
// 当前查看的报告
let currentReport = null;
// 所有报告数据
let allReports = [];

/**
 * 获取设备 ID
 */
function getDeviceId() {
  return localStorage.getItem('prism_device_id');
}

/**
 * 获取访客 ID
 */
function getVisitorId() {
  let visitorId = localStorage.getItem('prism_visitor_id');
  if (!visitorId) {
    visitorId = 'v_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('prism_visitor_id', visitorId);
  }
  return visitorId;
}

/**
 * 获取认证参数（用于API调用）
 * @returns {URLSearchParams} 包含 device_id 或 visitor_id 的参数
 */
function getReportAuthParams() {
  const params = new URLSearchParams();

  // 添加 device_id（如果已激活）
  const deviceId = getDeviceId();
  if (deviceId) {
    params.append('device_id', deviceId);
  }

  // 添加 visitor_id（用于匿名用户）
  params.append('visitor_id', getVisitorId());

  return params;
}

/**
 * Load reports list
 */
async function loadReports() {
  const list = document.getElementById('report-list');
  if (!list) return;

  list.innerHTML = '<div class="text-center py-8 text-text-muted text-sm">加载中...</div>';

  try {
    const authParams = getReportAuthParams();
    const res = await fetch('/api/reports?' + authParams.toString());
    allReports = await res.json();

    if (!allReports.length) {
      list.innerHTML = '<div class="text-center py-8 text-text-muted text-sm">暂无报告</div>';
      return;
    }

    const folders = groupByFolder(allReports);
    renderReportList(list, folders);
  } catch (e) {
    list.innerHTML = '<div class="text-center py-8 text-sm" style="color: #ff6b6b;">加载失败</div>';
  }
}

/**
 * Group reports by folder
 */
function groupByFolder(reports) {
  const folders = {};
  reports.forEach(r => {
    if (!folders[r.folder]) folders[r.folder] = [];
    folders[r.folder].push(r);
  });
  return folders;
}

/**
 * Render report list HTML
 */
function renderReportList(container, folders) {
  container.innerHTML = '';

  Object.entries(folders).forEach(([folder, items]) => {
    const header = document.createElement('div');
    header.className = 'px-3 py-2 text-xs font-semibold uppercase tracking-wider';
    header.style.color = '#4a4a6a';
    header.textContent = folder || '根目录';
    container.appendChild(header);

    items.forEach(r => {
      const item = createReportItem(r);
      container.appendChild(item);
    });
  });
}

/**
 * Create report item element
 */
function createReportItem(report) {
  const div = document.createElement('div');
  div.className = 'report-item px-3 py-2.5 rounded-lg cursor-pointer transition-colors flex items-start gap-2';
  div.style.cssText = 'background: transparent;';
  div.dataset.path = report.path;

  const date = new Date(report.mtime * 1000).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  div.innerHTML = `
    <input type="checkbox" class="report-checkbox mt-1 flex-shrink-0"
           onchange="toggleReportSelection('${report.path}', this.checked)"
           onclick="event.stopPropagation()">
    <div class="flex-1 min-w-0" onclick="loadReport('${report.path}', this.parentElement)">
      <div class="font-medium text-sm truncate" style="color: #e8e8f0;">${report.name}</div>
      <div class="text-xs mt-0.5" style="color: #8888aa;">${date}</div>
    </div>
  `;

  return div;
}

/**
 * Toggle report selection
 */
function toggleReportSelection(path, checked) {
  if (checked) {
    selectedReports.add(path);
  } else {
    selectedReports.delete(path);
  }
  updateBatchActions();
}

/**
 * Toggle select all
 */
function toggleSelectAll() {
  const checkboxes = document.querySelectorAll('.report-checkbox');
  const allSelected = selectedReports.size === allReports.length && allReports.length > 0;

  if (allSelected) {
    selectedReports.clear();
    checkboxes.forEach(cb => cb.checked = false);
  } else {
    selectedReports.clear();
    allReports.forEach(r => selectedReports.add(r.path));
    checkboxes.forEach(cb => cb.checked = true);
  }
  updateBatchActions();
}

/**
 * Clear all selections
 */
function clearSelection() {
  selectedReports.clear();
  document.querySelectorAll('.report-checkbox').forEach(cb => cb.checked = false);
  updateBatchActions();
}

/**
 * Update batch actions UI
 */
function updateBatchActions() {
  const batchActions = document.getElementById('batch-actions');
  const selectedCount = document.getElementById('selected-count');
  const selectAllBtn = document.getElementById('btn-select-all');

  if (selectedReports.size > 0) {
    batchActions.classList.remove('hidden');
    selectedCount.textContent = selectedReports.size;
  } else {
    batchActions.classList.add('hidden');
  }

  const allSelected = selectedReports.size === allReports.length && allReports.length > 0;
  selectAllBtn.textContent = allSelected ? '取消' : '全选';
}

/**
 * Clear all selected report items
 */
function clearSelectedReportItems() {
  document.querySelectorAll('.report-item').forEach(e => {
    e.classList.remove('selected');
    e.style.cssText = 'background: transparent;';
  });
}

/**
 * Load and display report content
 */
async function loadReport(path, element) {
  clearSelectedReportItems();
  element.classList.add('selected');

  currentReport = path;

  const reportHeader = document.getElementById('report-header');
  const reportTitle = document.getElementById('report-title');
  reportHeader.classList.remove('hidden');
  reportTitle.textContent = path.split('/').pop();

  const content = document.getElementById('report-content');
  if (!content) return;

  content.innerHTML = `
    <div class="flex items-center justify-center h-full" style="color: #8888aa;">
      <svg class="w-5 h-5 animate-spin mr-2" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      加载中...
    </div>
  `;

  try {
    const authParams = getReportAuthParams();
    const res = await fetch('/api/reports/content?path=' + encodeURIComponent(path) + '&' + authParams.toString());
    const data = await res.json();

    const div = document.createElement('div');
    div.className = 'md max-w-4xl mx-auto';
    div.innerHTML = marked.parse(data.content);

    content.innerHTML = '';
    content.appendChild(div);
  } catch (e) {
    content.innerHTML = '<div class="flex items-center justify-center h-full" style="color: #ff6b6b;">加载失败</div>';
  }
}

/**
 * Download current report
 */
function downloadCurrent(format) {
  if (!currentReport) {
    showToast('请先选择报告', 'warn');
    return;
  }

  const authParams = getReportAuthParams();
  const url = `/api/reports/download?path=${encodeURIComponent(currentReport)}&format=${format}&${authParams.toString()}`;
  window.location.href = url;
}

/**
 * Download batch reports
 */
function downloadBatch(format) {
  if (selectedReports.size === 0) {
    showToast('请先选择报告', 'warn');
    return;
  }

  const authParams = getReportAuthParams();
  const paths = Array.from(selectedReports).join(',');
  const url = `/api/reports/batch-download?paths=${encodeURIComponent(paths)}&format=${format}&${authParams.toString()}`;
  window.location.href = url;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  const icon = document.getElementById('toast-icon');
  const msg = document.getElementById('toast-message');

  const icons = {
    success: '✓',
    error: '✕',
    warn: '⚠',
    info: 'ℹ'
  };

  icon.textContent = icons[type] || icons.info;
  msg.textContent = message;

  toast.classList.remove('translate-y-20', 'opacity-0');

  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0');
  }, 3000);
}