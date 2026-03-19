/**
 * Core Module - Constants and Utilities
 * 核心模块 - 常量和工具函数
 */

// Script metadata
const SCRIPTS_META = {
  mission: '情报日报',
  bounty: '赏金猎人',
  alpha: 'Alpha 雷达',
  revenue: '营收分析师',
};

// Configuration keys
const CONFIG_KEYS = [
  'LLM_API_FORMAT', 'LLM_BASE_URL', 'LLM_API_KEY', 'LLM_MODEL',
  'XAI_API_FORMAT', 'XAI_BASE_URL', 'XAI_API_KEY', 'XAI_MODEL',
  'TRANSLATOR_API_FORMAT', 'TRANSLATOR_BASE_URL', 'TRANSLATOR_API_KEY', 'TRANSLATOR_MODEL',
  'GITHUB_TOKEN', 'PRODUCTHUNT_TOKEN', 'TAVILY_TOKEN',
];

// State
let currentTab = 'console';
const scriptStates = {};

/**
 * Initialize theme on page load
 * 页面加载时初始化主题
 */
function initTheme() {
  const savedTheme = localStorage.getItem('prism-theme');
  const html = document.documentElement;
  
  if (savedTheme === 'dark') {
    html.classList.add('dark');
    updateThemeIcon(true);
  } else if (savedTheme === 'light') {
    html.classList.remove('dark');
    updateThemeIcon(false);
  } else {
    // Check system preference
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (prefersDark) {
      html.classList.add('dark');
      updateThemeIcon(true);
    } else {
      html.classList.remove('dark');
      updateThemeIcon(false);
    }
  }
}

/**
 * Toggle between light and dark theme
 * 切换浅色/深色主题
 */
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.classList.toggle('dark');
  
  localStorage.setItem('prism-theme', isDark ? 'dark' : 'light');
  updateThemeIcon(isDark);
}

/**
 * Update theme toggle icon
 * 更新主题切换图标
 */
function updateThemeIcon(isDark) {
  const sunIcon = document.getElementById('theme-icon-sun');
  const moonIcon = document.getElementById('theme-icon-moon');
  
  if (sunIcon && moonIcon) {
    if (isDark) {
      sunIcon.classList.remove('hidden');
      moonIcon.classList.add('hidden');
    } else {
      sunIcon.classList.add('hidden');
      moonIcon.classList.remove('hidden');
    }
  }
}

/**
 * Show toast notification
 * 显示提示通知
 */
function showToast(msg, type = 'ok') {
  const toast = document.getElementById('toast');
  const icon = document.getElementById('toast-icon');
  const message = document.getElementById('toast-message');

  if (!toast || !icon || !message) return;

  message.textContent = msg;

  if (type === 'ok') {
    icon.innerHTML = '<svg class="w-5 h-5 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>';
    toast.style.borderColor = '#00d4aa';
  } else {
    icon.innerHTML = '<svg class="w-5 h-5 text-error" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>';
    toast.style.borderColor = '#ff6b6b';
  }

  toast.classList.remove('translate-y-20', 'opacity-0');
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0');
  }, 2500);
}

/**
 * Toggle mobile menu
 * 切换移动端菜单
 */
function toggleMobileMenu() {
  const menu = document.getElementById('mobile-menu');
  const icon = document.getElementById('menu-icon');

  if (!menu || !icon) return;

  menu.classList.toggle('hidden');
  if (menu.classList.contains('hidden')) {
    icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>';
  } else {
    icon.innerHTML = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>';
  }
}

/**
 * Toggle password visibility
 * 切换密码可见性
 */
function togglePassword(id) {
  const input = document.getElementById(id);
  if (input) {
    input.type = input.type === 'password' ? 'text' : 'password';
  }
}

// Export functions
window.initTheme = initTheme;
window.toggleTheme = toggleTheme;
