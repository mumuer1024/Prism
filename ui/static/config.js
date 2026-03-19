/**
 * config.js - 配置管理模块
 * 处理系统配置加载、保存和模型管理
 */

// 配置分组定义（基于 v1.0 原始逻辑）
const CONFIG_SECTIONS = [
  {
    key: "llm",
    title: "通用推理模型",
    desc: "营收分析 / 通用任务",
    fields: [
      { key: "LLM_API_FORMAT", label: "API 格式", type: "select", options: [
        { value: "openai", label: "OpenAI 兼容（NewAPI / OpenRouter 等）" },
        { value: "gemini", label: "Gemini 原生" },
        { value: "claude", label: "Claude 原生" }
      ]},
      { key: "LLM_BASE_URL", label: "API 基础地址", type: "text", placeholder: "https://api.openai.com/v1/chat/completions" },
      { key: "LLM_API_KEY", label: "API 密钥", type: "password", placeholder: "sk-..." },
      { key: "LLM_MODEL", label: "使用的模型", type: "model" }
    ]
  },
  {
    key: "xai",
    title: "X/Twitter 搜索端点",
    desc: "X/Twitter搜索仅支持Grok模型",
    fields: [
      { key: "XAI_API_FORMAT", label: "API 格式", type: "select", options: [
        { value: "openai", label: "OpenAI 兼容（xAI 官方）" },
        { value: "gemini", label: "Gemini 原生" },
        { value: "claude", label: "Claude 原生" }
      ]},
      { key: "XAI_BASE_URL", label: "API 基础地址", type: "text", placeholder: "https://api.x.ai/v1/chat/completions" },
      { key: "XAI_API_KEY", label: "API 密钥", type: "password", placeholder: "sk-..." },
      { key: "XAI_MODEL", label: "使用的模型", type: "model" }
    ]
  },
  {
    key: "translator",
    title: "翻译模型端点",
    desc: "ArXiv 摘要翻译 / 博客摘要",
    fields: [
      { key: "TRANSLATOR_API_FORMAT", label: "API 格式", type: "select", options: [
        { value: "gemini", label: "Gemini 原生" },
        { value: "openai", label: "OpenAI 兼容（NewAPI / OpenRouter 等）" },
        { value: "claude", label: "Claude 原生" }
      ]},
      { key: "TRANSLATOR_BASE_URL", label: "API 基础地址", type: "text", placeholder: "https://generativelanguage.googleapis.com/v1beta/models" },
      { key: "TRANSLATOR_API_KEY", label: "API 密钥", type: "password", placeholder: "..." },
      { key: "TRANSLATOR_MODEL", label: "使用的模型", type: "model" }
    ]
  },
  {
    key: "tokens",
    title: "数据源密钥",
    desc: "外部服务访问令牌",
    fields: [
      { key: "GITHUB_TOKEN", label: "GITHUB_TOKEN", type: "password", placeholder: "ghp_...", desc: "GitHub PAT（必需）" },
      { key: "PRODUCTHUNT_TOKEN", label: "PRODUCTHUNT_TOKEN", type: "password", placeholder: "...", desc: "Product Hunt（可选）" },
      { key: "TAVILY_TOKEN", label: "TAVILY_TOKEN", type: "password", placeholder: "tvly-...", desc: "Tavily AI 搜索（可选）" }
    ]
  }
];

// 存储获取到的模型列表
const modelsCache = {
  llm: [],
  xai: [],
  translator: []
};

/**
 * 初始化配置页面
 */
async function initConfig() {
  await loadConfig();
}

/**
 * 加载配置数据
 */
async function loadConfig() {
  try {
    const cfg = await fetch('/api/config').then(r => r.json());
    renderConfig(cfg);
  } catch (err) {
    console.error('加载配置失败:', err);
    document.getElementById('config-content').innerHTML = `
      <div style="text-align:center;padding:48px 0;color:var(--error)">
        <div style="font-size:36px;margin-bottom:12px">⚠️</div>
        <div>加载配置失败: ${err.message}</div>
        <button onclick="loadConfig()" style="margin-top:16px;padding:8px 16px;background:var(--accent);border:none;border-radius:6px;color:white;cursor:pointer">
          重试
        </button>
      </div>
    `;
  }
}

/**
 * 渲染配置表单（使用 v1.0 样式）
 */
function renderConfig(cfg) {
  const container = document.getElementById('config-content');
  
  const html = CONFIG_SECTIONS.map(section => `
    <div class="config-group">
      <div class="config-group-header">${section.title}</div>
      ${section.desc ? `<div style="padding:8px 20px;font-size:11px;color:var(--text-secondary);border-bottom:1px solid var(--border)">${section.desc}</div>` : ''}
      
      ${section.fields.map(field => renderField(field, cfg, section.key)).join('')}
      
      ${section.key !== 'tokens' ? `
        <div style="padding:16px 20px;border-top:1px solid var(--border);display:flex;gap:8px;align-items:center">
          <button onclick="fetchModels('${section.key}')" 
                  style="background:rgba(124,92,252,0.15);border:1px solid rgba(124,92,252,0.3);border-radius:8px;color:var(--accent);font-family:'Syne',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;padding:8px 14px;cursor:pointer;transition:all 0.2s;white-space:nowrap">
            拉取模型
          </button>
          <button onclick="testConnection('${section.key}')"
                  style="background:rgba(0,212,170,0.15);border:1px solid rgba(0,212,170,0.3);border-radius:8px;color:var(--success);font-family:'Syne',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;padding:8px 14px;cursor:pointer;transition:all 0.2s;white-space:nowrap">
            测试连通性
          </button>
          <span id="status-${section.key}" style="margin-left:auto;font-size:12px"></span>
        </div>
      ` : ''}
    </div>
  `).join('');
  
  container.innerHTML = html;
}

/**
 * 渲染单个配置字段（使用 v1.0 样式）
 */
function renderField(field, cfg, sectionKey) {
  const value = cfg[field.key] || '';
  const desc = field.desc || '';
  
  if (field.type === 'select') {
    return `
      <div class="config-row">
        <div>
          <div class="config-key">${field.key}</div>
          <div class="config-key-desc">${field.label}</div>
        </div>
        <select class="config-input" id="cfg-${field.key}">
          ${field.options.map(opt => `
            <option value="${opt.value}" ${value === opt.value ? 'selected' : ''}>${opt.label}</option>
          `).join('')}
        </select>
      </div>
    `;
  }
  
  if (field.type === 'password') {
    return `
      <div class="config-row">
        <div>
          <div class="config-key">${field.key}</div>
          <div class="config-key-desc">${desc || field.label}</div>
        </div>
        <div style="position:relative">
          <input type="password" id="cfg-${field.key}" value="${value}" 
                 class="config-input" style="padding-right:36px" placeholder="${field.placeholder || ''}">
          <button type="button" onclick="togglePassword('cfg-${field.key}')" 
                  style="position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--text2);cursor:pointer;padding:4px">
            <i class="fas fa-eye" style="font-size:12px">👁</i>
          </button>
        </div>
      </div>
    `;
  }
  
  if (field.type === 'model') {
    // 模型选择：下拉框 + 手动输入
    const cache = modelsCache[sectionKey] || [];
    return `
      <div class="config-row">
        <div>
          <div class="config-key">${field.key}</div>
          <div class="config-key-desc">${field.label}</div>
        </div>
        <div class="model-row">
          <select id="cfg-${field.key}-select" onchange="document.getElementById('cfg-${field.key}').value = this.value"
                  class="config-input" style="flex:1">
            <option value="">-- 先拉取模型列表 --</option>
            ${cache.map(m => `<option value="${m}" ${value === m ? 'selected' : ''}>${m}</option>`).join('')}
          </select>
          <input type="text" id="cfg-${field.key}" value="${value}" 
                 class="config-input" style="flex:1" placeholder="或手动输入模型名称">
        </div>
      </div>
    `;
  }
  
  // 普通文本输入
  return `
    <div class="config-row">
      <div>
        <div class="config-key">${field.key}</div>
        <div class="config-key-desc">${field.label}</div>
      </div>
      <input type="text" id="cfg-${field.key}" value="${value}" 
             class="config-input" placeholder="${field.placeholder || ''}">
    </div>
  `;
}

/**
 * 切换密码显示/隐藏
 */
function togglePassword(inputId) {
  const input = document.getElementById(inputId);
  const btn = input.nextElementSibling;
  const icon = btn.querySelector('i');
  
  if (input.type === 'password') {
    input.type = 'text';
    icon.textContent = '🙈';
  } else {
    input.type = 'password';
    icon.textContent = '👁';
  }
}

/**
 * 获取模型列表（基于 v1.0 逻辑）
 */
async function fetchModels(sectionKey) {
  const section = CONFIG_SECTIONS.find(s => s.key === sectionKey);
  if (!section) return;
  
  const baseUrlField = section.fields.find(f => f.key.includes('BASE_URL'));
  const apiKeyField = section.fields.find(f => f.key.includes('API_KEY') && !f.key.includes('MODEL'));
  const apiFormatField = section.fields.find(f => f.key.includes('API_FORMAT'));
  const modelField = section.fields.find(f => f.key.includes('MODEL'));
  
  const base = document.getElementById(`cfg-${baseUrlField.key}`).value;
  const key = document.getElementById(`cfg-${apiKeyField.key}`).value;
  const fmt = document.getElementById(`cfg-${apiFormatField.key}`)?.value || 'openai';
  
  if (!base || !key) {
    showToast('请先填写 URL 和 API Key', 'err');
    return;
  }
  
  // 找到按钮并显示加载状态
  const statusEl = document.getElementById(`status-${sectionKey}`);
  statusEl.innerHTML = '<span style="color:var(--accent2)">拉取中...</span>';
  
  try {
    const res = await fetch(`/api/models?base_url=${encodeURIComponent(base)}&api_key=${encodeURIComponent(key)}&api_format=${encodeURIComponent(fmt)}`);
    if (!res.ok) throw new Error(await res.text());
    const { models } = await res.json();
    
    // 更新缓存
    modelsCache[sectionKey] = models;
    
    // 重新渲染以更新下拉框
    const cfg = await fetch('/api/config').then(r => r.json());
    renderConfig(cfg);
    
    statusEl.innerHTML = `<span style="color:var(--success)">✓ 获取到 ${models.length} 个模型</span>`;
    setTimeout(() => { statusEl.innerHTML = ''; }, 3000);
  } catch (err) {
    console.error('获取模型失败:', err);
    statusEl.innerHTML = `<span style="color:var(--error)">✗ ${err.message}</span>`;
    setTimeout(() => { statusEl.innerHTML = ''; }, 5000);
  }
}

/**
 * 测试连通性（新增功能）
 */
async function testConnection(sectionKey) {
  const section = CONFIG_SECTIONS.find(s => s.key === sectionKey);
  if (!section) return;
  
  const baseUrlField = section.fields.find(f => f.key.includes('BASE_URL'));
  const apiKeyField = section.fields.find(f => f.key.includes('API_KEY') && !f.key.includes('MODEL'));
  const apiFormatField = section.fields.find(f => f.key.includes('API_FORMAT'));
  
  const base = document.getElementById(`cfg-${baseUrlField.key}`).value;
  const key = document.getElementById(`cfg-${apiKeyField.key}`).value;
  const fmt = document.getElementById(`cfg-${apiFormatField.key}`)?.value || 'openai';
  
  if (!base || !key) {
    showToast('请先填写 URL 和 API Key', 'err');
    return;
  }
  
  const statusEl = document.getElementById(`status-${sectionKey}`);
  statusEl.innerHTML = '<span style="color:var(--accent2)">测试中...</span>';
  
  try {
    const resp = await fetch('/api/test-connection', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ base_url: base, api_key: key, api_format: fmt })
    });
    
    const data = await resp.json();
    
    if (data.ok) {
      statusEl.innerHTML = `<span style="color:var(--success)">✓ 连接成功 (${data.latency}ms)</span>`;
    } else {
      statusEl.innerHTML = `<span style="color:var(--error)">✗ ${data.error || '连接失败'}</span>`;
    }
  } catch (err) {
    console.error('测试连接失败:', err);
    statusEl.innerHTML = `<span style="color:var(--error)">✗ ${err.message}</span>`;
  }
  
  // 5秒后清除状态
  setTimeout(() => { statusEl.innerHTML = ''; }, 5000);
}

/**
 * 保存配置（基于 v1.0 逻辑）
 */
async function saveConfig() {
  // 收集所有配置值
  const data = {};
  CONFIG_SECTIONS.forEach(section => {
    section.fields.forEach(field => {
      const el = document.getElementById(`cfg-${field.key}`);
      if (el && el.value) {
        data[field.key] = el.value;
      }
    });
  });
  
  try {
    await fetch('/api/config', { 
      method: 'POST', 
      headers: {'Content-Type':'application/json'}, 
      body: JSON.stringify({data}) 
    });
    showToast('✓ 配置已保存', 'ok');
  } catch(e) {
    showToast('✗ 保存失败', 'err');
  }
}

// 导出模块
window.initConfig = initConfig;
window.loadConfig = loadConfig;
window.saveConfig = saveConfig;
window.fetchModels = fetchModels;
window.testConnection = testConnection;
window.togglePassword = togglePassword;