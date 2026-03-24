/**
 * Navigation Module - Tab switching and routing
 * 导航模块 - 标签切换和路由
 */

/**
 * Switch to specified tab
 * 切换到指定标签页
 */
function switchTab(tab) {
  currentTab = tab;

  // Update nav buttons
  updateNavButtons(tab);

  // Update panels visibility
  updatePanels(tab);

  // Load data for the tab
  loadTabData(tab);
}

/**
 * Update navigation button states
 * 更新导航按钮状态
 */
function updateNavButtons(activeTab) {
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
    btn.style.color = '#8888aa';
  });

  const activeBtn = document.getElementById('nav-' + activeTab);
  if (activeBtn) {
    activeBtn.classList.add('active');
    activeBtn.style.color = '#7c5cfc';
  }
}

/**
 * Update panel visibility
 * 更新面板可见性
 */
function updatePanels(activeTab) {
  document.querySelectorAll('.panel').forEach(panel => {
    panel.classList.add('hidden');
    panel.classList.remove('active');
  });

  const panel = document.getElementById('panel-' + activeTab);
  if (panel) {
    panel.classList.remove('hidden');
    panel.classList.add('active');
  }
}

/**
 * Load data for the active tab
 * 为活动标签页加载数据
 */
function loadTabData(tab) {
  switch (tab) {
    case 'sources':
      loadSources();
      break;
    case 'prompts':
      loadPromptsPreview();
      break;
    case 'reports':
      loadReports();
      break;
    case 'config':
      loadConfig();
      break;
    default:
      // console tab doesn't need data loading
      break;
  }
}

/**
 * Load prompts preview for the prompts tab
 * 加载 Prompt 预览
 */
async function loadPromptsPreview() {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  // 加载预设模板
  try {
    const presetRes = await fetch('/api/prompts/preset', { headers });
    const presetData = await presetRes.json();
    
    const presetContainer = document.getElementById('preset-prompts-list');
    if (presetData.success && presetData.data.length > 0) {
      presetContainer.innerHTML = presetData.data.slice(0, 5).map(p => `
        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-bg-tertiary transition-colors">
          <div>
            <div class="font-medium text-sm" style="color: var(--text);">${p.name}</div>
            <div class="text-xs text-text-muted">${p.category}</div>
          </div>
          <span class="text-xs px-2 py-0.5 rounded ${p.is_free ? 'bg-success/10 text-success' : 'bg-warn/10 text-warn'}">${p.is_free ? '免费' : '付费'}</span>
        </div>
      `).join('');
    } else {
      presetContainer.innerHTML = '<div class="text-center py-4 text-text-muted text-sm">暂无预设模板</div>';
    }
  } catch (e) {
    console.error('加载预设模板失败:', e);
  }

  // 加载我的模板
  if (!token) {
    return; // 未登录不加载
  }

  try {
    const myRes = await fetch('/api/prompts/custom', { headers });
    const myData = await myRes.json();
    
    const myContainer = document.getElementById('my-prompts-list');
    if (myData.success && myData.data.length > 0) {
      myContainer.innerHTML = myData.data.slice(0, 5).map(p => `
        <div class="flex items-center justify-between p-2 rounded-lg hover:bg-bg-tertiary transition-colors">
          <div>
            <div class="font-medium text-sm" style="color: var(--text);">${p.name}</div>
            <div class="text-xs text-text-muted">${p.category}</div>
          </div>
          <span class="text-xs ${p.is_active ? 'text-success' : 'text-text-muted'}">${p.is_active ? '启用' : '禁用'}</span>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error('加载我的模板失败:', e);
  }
}
