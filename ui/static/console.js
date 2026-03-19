/**
 * Console Module - Script execution and log management
 * 控制台模块 - 脚本执行和日志管理
 */

/**
 * Set script card state
 * 设置脚本卡片状态
 */
function setScriptState(id, state) {
  scriptStates[id] = state;

  const dot = document.getElementById('dot-' + id);
  const btn = document.getElementById('btn-' + id);

  if (!dot || !btn) return;

  // Update status dot color
  const colorMap = {
    running: '#00d4aa',
    done: '#00d4aa',
    error: '#ff6b6b',
    default: '#4a4a6a'
  };
  dot.style.background = colorMap[state] || colorMap.default;

  // Update button state
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

  // Toggle pulse animation
  if (config.pulse) {
    dot.classList.add('animate-pulse');
  } else {
    dot.classList.remove('animate-pulse');
  }
}

/**
 * Append log line to console
 * 添加日志行到控制台
 */
function appendLog(line) {
  const body = document.getElementById('log-body');
  if (!body) return;

  const div = document.createElement('div');
  div.className = 'log-line py-0.5';

  // Color based on content
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
 * 清空控制台日志
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
 * 运行脚本并流式输出
 */
function runScript(id) {
  const logBody = document.getElementById('log-body');
  const logTitle = document.getElementById('log-title');
  const logStatus = document.getElementById('log-status');

  // Reset log
  if (logBody) logBody.innerHTML = '';
  if (logTitle) logTitle.textContent = SCRIPTS_META[id] || id;
  if (logStatus) {
    logStatus.textContent = '运行中...';
    logStatus.style.cssText = 'color: #00d4aa;';
  }

  setScriptState(id, 'running');

  // Connect to event source
  const es = new EventSource('/api/run/' + id);

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
