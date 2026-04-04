/**
 * payment.js - 支付模块
 * 处理套餐展示、订单创建、支付流程
 */

// 状态
let packages = [];
let currentOrder = null;
let pollInterval = null;

/**
 * 初始化支付页面
 */
async function initPaymentPage() {
  await loadPackages();
  await loadAvailableChannels();
}

/**
 * 加载套餐列表
 */
async function loadPackages() {
  const container = document.getElementById('packages-container');
  if (!container) return;

  try {
    const res = await fetch('/api/payment/packages');
    if (!res.ok) throw new Error('加载失败');

    const data = await res.json();
    packages = data.packages || [];

    if (packages.length === 0) {
      container.innerHTML = `
        <div class="payment-empty">
          <div class="empty-icon">📦</div>
          <div class="empty-text">暂无可购买的套餐</div>
          <div class="empty-hint">请稍后再试或联系管理员</div>
        </div>
      `;
      return;
    }

    renderPackages(container);
  } catch (err) {
    console.error('加载套餐失败:', err);
    container.innerHTML = `
      <div class="payment-error">
        <div class="error-icon">⚠️</div>
        <div class="error-text">加载失败: ${err.message}</div>
        <button onclick="loadPackages()" class="retry-btn">重试</button>
      </div>
    `;
  }
}

/**
 * 渲染套餐卡片
 */
function renderPackages(container) {
  const html = `
    <div class="packages-header">
      <h2>选择套餐</h2>
      <p>购买使用次数，解锁更多功能</p>
    </div>
    <div class="packages-grid">
      ${packages.map((pkg, index) => `
        <div class="package-card ${pkg.is_recommended ? 'recommended' : ''}" data-package-id="${pkg.id}">
          ${pkg.is_recommended ? '<div class="recommended-badge">推荐</div>' : ''}
          <div class="package-name">${pkg.name}</div>
          <div class="package-count">
            <span class="count-number">${pkg.total_count}</span>
            <span class="count-unit">次</span>
          </div>
          ${pkg.bonus_count > 0 ? `
            <div class="package-bonus">含赠送 ${pkg.bonus_count} 次</div>
          ` : ''}
          <div class="package-price">
            <span class="price-symbol">¥</span>
            <span class="price-number">${pkg.price_yuan}</span>
          </div>
          ${pkg.description ? `<div class="package-desc">${pkg.description}</div>` : ''}
          <button class="buy-btn" onclick="selectPackage(${pkg.id})">
            立即购买
          </button>
        </div>
      `).join('')}
    </div>
    <div class="payment-notice">
      <strong>提示：</strong>支付功能即将上线，当前仅支持兑换码充值。
      <a href="/user">前往充值</a>
    </div>
  `;
  container.innerHTML = html;
}

/**
 * 加载可用支付渠道
 */
async function loadAvailableChannels() {
  try {
    const res = await fetch('/api/payment/channels');
    if (!res.ok) return;

    const data = await res.json();
    const channels = data.channels || [];

    // 更新支付方式选择
    const methodSelect = document.getElementById('payment-method');
    if (methodSelect) {
      methodSelect.innerHTML = channels.map(ch => `
        <option value="${ch.name}" ${!ch.available ? 'disabled' : ''}>
          ${ch.display_name} ${!ch.available ? '(即将上线)' : ''}
        </option>
      `).join('');
    }
  } catch (err) {
    console.error('加载支付渠道失败:', err);
  }
}

/**
 * 选择套餐
 */
function selectPackage(packageId) {
  const pkg = packages.find(p => p.id === packageId);
  if (!pkg) return;

  // 显示支付确认弹窗
  showPaymentModal(pkg);
}

/**
 * 显示支付确认弹窗
 */
function showPaymentModal(pkg) {
  const modal = document.createElement('div');
  modal.id = 'payment-modal';
  modal.className = 'payment-modal';
  modal.innerHTML = `
    <div class="payment-modal-overlay" onclick="closePaymentModal()"></div>
    <div class="payment-modal-content">
      <div class="payment-modal-header">
        <h3>确认购买</h3>
        <button class="close-btn" onclick="closePaymentModal()">✕</button>
      </div>
      <div class="payment-modal-body">
        <div class="order-summary">
          <div class="summary-item">
            <span class="label">套餐</span>
            <span class="value">${pkg.name}</span>
          </div>
          <div class="summary-item">
            <span class="label">次数</span>
            <span class="value">${pkg.total_count} 次${pkg.bonus_count > 0 ? ` (含赠送 ${pkg.bonus_count} 次)` : ''}</span>
          </div>
          <div class="summary-item total">
            <span class="label">支付金额</span>
            <span class="value">¥${pkg.price_yuan}</span>
          </div>
        </div>

        <div class="payment-method-select">
          <label>支付方式</label>
          <select id="payment-method">
            <option value="mock">模拟支付（测试）</option>
            <option value="wechat" disabled>微信支付（即将上线）</option>
            <option value="alipay" disabled>支付宝（即将上线）</option>
          </select>
        </div>

        <div class="payment-qr" id="payment-qr" style="display: none;">
          <div class="qr-placeholder">
            <div class="qr-icon">📱</div>
            <div class="qr-text">支付二维码将在此显示</div>
          </div>
        </div>
      </div>
      <div class="payment-modal-footer">
        <button class="btn-cancel" onclick="closePaymentModal()">取消</button>
        <button class="btn-confirm" onclick="createOrder(${pkg.id})">
          确认支付
        </button>
      </div>
    </div>
  `;

  document.body.appendChild(modal);
  requestAnimationFrame(() => modal.classList.add('show'));
}

/**
 * 关闭支付弹窗
 */
function closePaymentModal() {
  const modal = document.getElementById('payment-modal');
  if (modal) {
    modal.classList.remove('show');
    setTimeout(() => modal.remove(), 300);
  }

  // 停止轮询
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
}

/**
 * 创建订单
 */
async function createOrder(packageId) {
  const methodSelect = document.getElementById('payment-method');
  const paymentMethod = methodSelect?.value || 'mock';

  const confirmBtn = document.querySelector('.btn-confirm');
  const originalText = confirmBtn.innerHTML;
  confirmBtn.innerHTML = '处理中...';
  confirmBtn.disabled = true;

  try {
    const token = AuthState?.getToken();
    if (!token) {
      showToast('请先登录', 'err');
      window.location.href = '/login?redirect=' + encodeURIComponent(window.location.pathname);
      return;
    }

    const res = await fetch('/api/payment/orders', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        package_id: packageId,
        payment_method: paymentMethod
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '创建订单失败');
    }

    const order = await res.json();
    currentOrder = order;

    // 显示支付二维码
    showPaymentQR(order);

    // 开始轮询订单状态
    startPolling(order.order_no);

  } catch (err) {
    showToast(`✗ ${err.message}`, 'err');
  } finally {
    confirmBtn.innerHTML = originalText;
    confirmBtn.disabled = false;
  }
}

/**
 * 显示支付二维码
 */
function showPaymentQR(order) {
  const qrContainer = document.getElementById('payment-qr');
  if (!qrContainer) return;

  qrContainer.style.display = 'block';
  qrContainer.innerHTML = `
    <div class="qr-info">
      <div class="order-no">订单号: ${order.order_no}</div>
      <div class="qr-placeholder">
        <div class="qr-icon">💳</div>
        <div class="qr-text">
          ${order.payment_method === 'mock'
            ? '测试模式：点击下方按钮模拟支付'
            : '请使用手机扫描二维码支付'}
        </div>
      </div>
    </div>
  `;

  // 如果是模拟支付，显示模拟支付按钮
  if (order.payment_method === 'mock') {
    const footer = document.querySelector('.payment-modal-footer');
    if (footer) {
      footer.innerHTML = `
        <button class="btn-cancel" onclick="closePaymentModal()">取消</button>
        <button class="btn-mock-pay" onclick="mockPay('${order.order_no}')">
          模拟支付成功
        </button>
      `;
    }
  }
}

/**
 * 开始轮询订单状态
 */
function startPolling(orderNo) {
  if (pollInterval) {
    clearInterval(pollInterval);
  }

  pollInterval = setInterval(async () => {
    try {
      const token = AuthState?.getToken();
      const res = await fetch(`/api/payment/orders/${orderNo}/status`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (!res.ok) return;

      const status = await res.json();

      if (status.is_paid) {
        clearInterval(pollInterval);
        pollInterval = null;
        showPaymentSuccess(status);
      }
    } catch (err) {
      console.error('轮询订单状态失败:', err);
    }
  }, 2000);
}

/**
 * 模拟支付
 */
async function mockPay(orderNo) {
  const btn = document.querySelector('.btn-mock-pay');
  if (btn) {
    btn.innerHTML = '处理中...';
    btn.disabled = true;
  }

  try {
    const token = AuthState?.getToken();
    const res = await fetch('/api/payment/mock/pay', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ order_no: orderNo })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || '支付失败');
    }

    const result = await res.json();

    if (result.success) {
      showPaymentSuccess({ order_no: orderNo, usage_count: currentOrder?.usage_count || 0 });
    } else {
      throw new Error(result.message || '支付失败');
    }
  } catch (err) {
    showToast(`✗ ${err.message}`, 'err');
    if (btn) {
      btn.innerHTML = '模拟支付成功';
      btn.disabled = false;
    }
  }
}

/**
 * 显示支付成功
 */
function showPaymentSuccess(status) {
  const modal = document.getElementById('payment-modal');
  if (!modal) return;

  const content = modal.querySelector('.payment-modal-content');
  if (!content) return;

  content.innerHTML = `
    <div class="payment-success">
      <div class="success-icon">✓</div>
      <div class="success-title">支付成功</div>
      <div class="success-info">
        已充值 <strong>${status.usage_count}</strong> 次使用次数
      </div>
      <button class="btn-done" onclick="closePaymentModalAndRefresh()">完成</button>
    </div>
  `;
}

/**
 * 关闭弹窗并刷新页面
 */
function closePaymentModalAndRefresh() {
  closePaymentModal();
  // 刷新用户信息
  if (typeof loadUserInfo === 'function') {
    loadUserInfo();
  }
  showToast('✓ 充值成功', 'ok');
}

// 导出模块
window.initPaymentPage = initPaymentPage;
window.loadPackages = loadPackages;
window.selectPackage = selectPackage;
window.closePaymentModal = closePaymentModal;
window.createOrder = createOrder;
window.mockPay = mockPay;
window.closePaymentModalAndRefresh = closePaymentModalAndRefresh;