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
