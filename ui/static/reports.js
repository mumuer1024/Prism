/**
 * Reports Module - Report listing and viewing
 * 报告模块 - 报告列表和查看
 */

/**
 * Load reports list
 * 加载报告列表
 */
async function loadReports() {
  const list = document.getElementById('report-list');
  if (!list) return;

  list.innerHTML = '<div class="text-center py-8 text-text-muted text-sm">加载中...</div>';

  try {
    const res = await fetch('/api/reports');
    const reports = await res.json();

    if (!reports.length) {
      list.innerHTML = '<div class="text-center py-8 text-text-muted text-sm">暂无报告</div>';
      return;
    }

    // Group by folder
    const folders = groupByFolder(reports);

    // Render list
    renderReportList(list, folders);
  } catch (e) {
    list.innerHTML = '<div class="text-center py-8 text-sm" style="color: #ff6b6b;">加载失败</div>';
  }
}

/**
 * Group reports by folder
 * 按文件夹分组报告
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
 * 渲染报告列表HTML
 */
function renderReportList(container, folders) {
  container.innerHTML = '';

  Object.entries(folders).forEach(([folder, items]) => {
    // Folder header
    const header = document.createElement('div');
    header.className = 'px-3 py-2 text-xs font-semibold uppercase tracking-wider';
    header.style.color = '#4a4a6a';
    header.textContent = folder || '根目录';
    container.appendChild(header);

    // Report items
    items.forEach(r => {
      const item = createReportItem(r);
      container.appendChild(item);
    });
  });
}

/**
 * Create report item element
 * 创建报告项元素
 */
function createReportItem(report) {
  const div = document.createElement('div');
  div.className = 'report-item px-3 py-2.5 rounded-lg cursor-pointer transition-colors';
  div.style.cssText = 'background: transparent;';

  const date = new Date(report.mtime * 1000).toLocaleString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });

  div.innerHTML = `
    <div class="font-medium text-sm truncate" style="color: #e8e8f0;">${report.name}</div>
    <div class="text-xs mt-0.5" style="color: #8888aa;">${date}</div>
  `;

  div.onclick = () => loadReport(report.path, div);
  return div;
}

/**
 * Clear all selected report items
 * 清除所有选中的报告项
 */
function clearSelectedReportItems() {
  document.querySelectorAll('.report-item').forEach(e => {
    e.classList.remove('selected');
    e.style.cssText = 'background: transparent;';
  });
}

/**
 * Load and display report content
 * 加载并显示报告内容
 */
async function loadReport(path, element) {
  // Update selection state
  clearSelectedReportItems();
  element.classList.add('selected');

  const content = document.getElementById('report-content');
  if (!content) return;

  // Show loading
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
    const res = await fetch('/api/reports/content?path=' + encodeURIComponent(path));
    const data = await res.json();

    // Render markdown
    const div = document.createElement('div');
    div.className = 'md max-w-4xl mx-auto';
    div.innerHTML = marked.parse(data.content);

    content.innerHTML = '';
    content.appendChild(div);
  } catch (e) {
    content.innerHTML = '<div class="flex items-center justify-center h-full" style="color: #ff6b6b;">加载失败</div>';
  }
}
