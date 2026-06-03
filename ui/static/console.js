/**
 * Console Module - Script execution and log management
 * 控制台模块 - 脚本执行和日志管理
 *
 * v2.1 激活码架构：使用 device_id 认证
 */

// localStorage key 基础前缀
const CONSOLE_LS_PREFIX_BASE = 'prism_config_';

/**
 * 获取设备 ID（用于认证）
 * @returns {string|null} 设备 ID 或 null
 */
function getDeviceId() {
  return localStorage.getItem('prism_device_id');
}

/**
 * 获取访客 ID（匿名用户标识）
 * @returns {string} 访客 ID
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
 * 获取当前用户标识（用于配置隔离）
 * @returns {string} device_id 或 visitor_id
 */
function getConsoleUserIdentifier() {
  const deviceId = getDeviceId();
  if (deviceId) {
    return deviceId;
  }
  return 'anon_' + getVisitorId();
}

/**
 * 获取带用户标识的 localStorage key 前缀
 * @returns {string} 格式：prism_config_{device_id}_
 */
function getConsoleLSPrefix() {
  return CONSOLE_LS_PREFIX_BASE + getConsoleUserIdentifier() + '_';
}

// 敏感Key列表（需要 base64 编码传输）
const SENSITIVE_KEYS = [
  'LLM_API_KEY',
  'XAI_API_KEY',
  'GITHUB_TOKEN',
  'TAVILY_TOKEN',
  'PRODUCTHUNT_TOKEN',
  'TRANSLATOR_API_KEY'
];

// 所有配置Key列表
const ALL_CONFIG_KEYS = [
  'LLM_API_KEY', 'LLM_BASE_URL', 'LLM_MODEL', 'LLM_API_FORMAT',
  'XAI_API_KEY', 'XAI_BASE_URL', 'XAI_MODEL',
  'GITHUB_TOKEN', 'TAVILY_TOKEN', 'PRODUCTHUNT_TOKEN',
  'TRANSLATOR_API_KEY', 'TRANSLATOR_BASE_URL', 'TRANSLATOR_MODEL'
];

// 脚本必填Key映射
const SCRIPT_REQUIRED_KEYS = {
  'mission': 'LLM_API_KEY',
  'bounty': 'LLM_API_KEY',
  'revenue': 'LLM_API_KEY',
  'alpha': 'XAI_API_KEY'
};

/**
 * 从 localStorage 读取用户配置（按设备隔离）
 * @returns {Object} 配置对象
 */
function getUserConfig() {
  const prefix = getConsoleLSPrefix();
  const cfg = {};
  ALL_CONFIG_KEYS.forEach(key => {
    const value = localStorage.getItem(prefix + key);
    if (value) {
      cfg[key] = value;
    }
  });
  return cfg;
}

/**
 * Base64 编码字符串
 * @param {string} str 原始字符串
 * @returns {string} Base64 编码结果
 */
function encodeBase64(str) {
  try {
    return btoa(unescape(encodeURIComponent(str)));
  } catch (e) {
    return btoa(str);
  }
}

/**
 * Set script card state
 */
function setScriptState(id, state) {
  scriptStates[id] = state;

  const dot = document.getElementById('dot-' + id);
  const btn = document.getElementById('btn-' + id);

  if (!dot || !btn) return;

  const colorMap = {
    running: '#00d4aa',
    done: '#00d4aa',
    error: '#ff6b6b',
    default: '#4a4a6a'
  };
  dot.style.background = colorMap[state] || colorMap.default;

  const stateConfig = {
    running: {
      html: '<svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> 运行中',
      style: 'background: rgba(0,212,170,0.2); border: 1px solid rgba(0,212,170,0.5); color: #00d4aa;',
      disabled: true,
      pulse: true
    },
    done: {
      html: '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"/></svg> 运行',
      style: 'background: rgba(124,92,252,0.1); border: 1px solid rgba(124,92,252,0.3); color: #7c5cfc;',
      disabled: false,
      pulse: false
    },
    error: {
      html: '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/></svg> 出错',
      style: 'background: rgba(255,107,107,0.2); border: 1px solid rgba(255,107,107,0.5); color: #ff6b6b;',
      disabled: false,
      pulse: false
    },
    default: {
      html: '<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"/></svg> 运行',
      style: 'background: rgba(124,92,252,0.1); border: 1px solid rgba(124,92,252,0.3); color: #7c5cfc;',
      disabled: false,
      pulse: false
    }
  };

  const config = stateConfig[state] || stateConfig.default;
  btn.innerHTML = config.html;
  btn.style.cssText = config.style;
  btn.disabled = config.disabled;

  if (config.pulse) {
    dot.classList.add('animate-pulse');
  } else {
    dot.classList.remove('animate-pulse');
  }
}

/**
 * Append log line to console
 */
function appendLog(line) {
  const body = document.getElementById('log-body');
  if (!body) return;

  const div = document.createElement('div');
  div.className = 'log-line py-0.5';

  const low = line.toLowerCase();
  if (low.includes('error') || low.includes('fail') || low.includes('exception')) {
    div.style.color = '#ff6b6b';
  } else if (low.includes('success') || low.includes('done') || low.includes('完成') || low.includes('成功')) {
    div.style.color = '#00d4aa';
  } else if (low.includes('[done]')) {
    div.style.cssText = 'color: #ffaa44; font-weight: 500;';
  } else if (low.startsWith('=') || low.includes('===')) {
    div.style.cssText = 'color: #7c5cfc; font-weight: 500;';
  } else {
    div.style.color = '#8888aa';
  }

  div.textContent = line;
  body.appendChild(div);
  body.scrollTop = body.scrollHeight;
}

/**
 * Clear console log
 */
function clearLog() {
  const body = document.getElementById('log-body');
  const logTitle = document.getElementById('log-title');
  const logStatus = document.getElementById('log-status');

  if (body) {
    body.innerHTML = `
      <div class="flex flex-col items-center justify-center h-full text-text-muted gap-3">
        <div class="w-16 h-16 rounded-2xl bg-bg-tertiary flex items-center justify-center text-3xl">⚡</div>
        <p class="text-sm">选择左侧脚本，点击运行</p>
      </div>
    `;
  }

  if (logTitle) logTitle.textContent = '等待运行';
  if (logStatus) {
    logStatus.textContent = '—';
    logStatus.style.color = '#4a4a6a';
  }
}

/**
 * Run script and stream output
 * v2.1：使用 device_id 认证
 */
function runScript(id) {
  const logBody = document.getElementById('log-body');
  const logTitle = document.getElementById('log-title');
  const logStatus = document.getElementById('log-status');

  // 1. 读取用户配置
  const userConfig = getUserConfig();

  // 2. 按脚本类型检查必填Key
  const requiredKey = SCRIPT_REQUIRED_KEYS[id];
  if (requiredKey && !userConfig[requiredKey]) {
    const keyNames = {
      'LLM_API_KEY': 'LLM API Key',
      'XAI_API_KEY': 'XAI API Key'
    };
    const keyName = keyNames[requiredKey] || requiredKey;
    showToast(`请先在配置页填写 ${keyName}`, 'err');
    return;
  }

  // 3. 重置日志
  if (logBody) logBody.innerHTML = '';
  if (logTitle) logTitle.textContent = SCRIPTS_META[id] || id;
  if (logStatus) {
    logStatus.textContent = '运行中...';
    logStatus.style.cssText = 'color: #00d4aa;';
  }

  setScriptState(id, 'running');

  // 4. 构建请求 URL 和参数
  let url = '/api/run/' + id;
  const params = new URLSearchParams();

  // 4.1 添加 device_id 认证
  const deviceId = getDeviceId();
  if (deviceId) {
    params.append('device_id', deviceId);
  }

  // 4.2 添加 visitor_id（匿名用户标识）
  params.append('visitor_id', getVisitorId());

  // 4.3 添加用户配置参数（敏感Key base64编码）
  Object.keys(userConfig).forEach(key => {
    const value = userConfig[key];
    if (value) {
      if (SENSITIVE_KEYS.includes(key)) {
        params.append(key, encodeBase64(value));
      } else {
        params.append(key, value);
      }
    }
  });

  // 5. 连接 EventSource
  url += '?' + params.toString();
  const es = new EventSource(url);

  es.onmessage = (e) => {
    const line = e.data;

    if (line.startsWith('[DONE]')) {
      const ok = line.includes('exit=0');
      setScriptState(id, ok ? 'done' : 'error');

      if (logStatus) {
        logStatus.textContent = ok ? '✓ 完成' : '✗ 出错';
        logStatus.style.color = ok ? '#00d4aa' : '#ff6b6b';
      }
      appendLog(line);
      es.close();
    } else {
      appendLog(line);
    }
  };

  es.onerror = () => {
    setScriptState(id, 'error');
    if (logStatus) {
      logStatus.textContent = '连接断开';
      logStatus.style.color = '#ff6b6b';
    }
    es.close();
  };
}

// 导出模块
window.runScript = runScript;
window.setScriptState = setScriptState;
window.appendLog = appendLog;
window.clearLog = clearLog;
window.getUserConfig = getUserConfig;
window.getDeviceId = getDeviceId;
window.getVisitorId = getVisitorId;