/**
 * Account Module - User Center Page Logic
 * 用户中心模块 - 用户中心页面逻辑
 */

// ============================================
// Data Loading
// ============================================

/**
 * Load all account data
 */
async function loadAccountData() {
  try {
    // Load profile and usage data in parallel
    const [profileResult, usageResult, inviteResult] = await Promise.all([
      AuthAPI.getProfile(),
      AuthAPI.getUsageBalance(),
      AuthAPI.getInviteStats()
    ]);

    // Hide loading, show content
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('content').classList.remove('hidden');

    // Render profile
    if (profileResult.success && profileResult.data && profileResult.data.user) {
      renderProfile(profileResult.data.user);
    } else {
      console.error('Profile data invalid:', profileResult);
    }

    // Render usage
    if (usageResult.success && usageResult.data) {
      renderUsage(usageResult.data);
    } else {
      console.error('Usage data invalid:', usageResult);
    }

    // Render invite stats
    if (inviteResult.success && inviteResult.data) {
      renderInviteStats(inviteResult.data);
    } else {
      console.error('Invite stats data invalid:', inviteResult);
    }

  } catch (err) {
    console.error('Failed to load account data:', err);

    // Hide loading, show content with error
    document.getElementById('loading-state').classList.add('hidden');
    document.getElementById('content').classList.remove('hidden');

    showToast('加载数据失败: ' + err.message, 'error');

    // If unauthorized, redirect to login
    if (err.message?.includes('401')) {
      setTimeout(() => {
        AuthState.logout();
      }, 1500);
    }
  }
}

// ============================================
// Render Functions
// ============================================

/**
 * Render user profile
 */
function renderProfile(user) {
  // Avatar
  const avatar = document.getElementById('user-avatar');
  if (avatar) {
    const initial = (user.nickname || user.email || 'U')[0].toUpperCase();
    avatar.textContent = initial;
  }
  
  // Name
  const name = document.getElementById('user-name');
  if (name) {
    name.textContent = user.nickname || user.email.split('@')[0];
  }
  
  // Email
  const email = document.getElementById('user-email');
  if (email) {
    email.textContent = user.email;
  }
  
  // Nickname input
  const nicknameInput = document.getElementById('nickname');
  if (nicknameInput) {
    nicknameInput.value = user.nickname || '';
  }
  
  // Created at
  const createdAt = document.getElementById('created-at');
  if (createdAt && user.created_at) {
    createdAt.textContent = formatDate(user.created_at);
  }
}

/**
 * Render usage stats
 */
function renderUsage(data) {
  // Paid count
  const paidCount = document.getElementById('paid-count');
  if (paidCount) {
    paidCount.textContent = data.paid_count || 0;
  }
  
  // Free remaining
  const freeCount = document.getElementById('free-count');
  if (freeCount) {
    freeCount.textContent = `${data.free_remaining || 0} / ${data.free_limit || 3}`;
  }
  
  // User type
  const userType = document.getElementById('user-type');
  if (userType) {
    const typeLabels = {
      'paid': '付费用户',
      'free': '免费用户',
      'anonymous': '匿名用户'
    };
    userType.textContent = typeLabels[data.user_type] || '免费用户';
    userType.className = 'text-2xl font-bold ' + (data.user_type === 'paid' ? 'text-accent' : 'text-success');
  }
}

/**
 * Render invite stats
 */
function renderInviteStats(data) {
  // Invite code
  const inviteCode = document.getElementById('invite-code');
  if (inviteCode) {
    inviteCode.textContent = data.invite_code || '-';
  }

  // Invite count
  const inviteCount = document.getElementById('invite-count');
  if (inviteCount) {
    inviteCount.textContent = data.total_invited || 0;
  }

  // Total reward
  const inviteReward = document.getElementById('invite-reward');
  if (inviteReward) {
    inviteReward.textContent = `${data.total_bonus || 0} 次`;
  }

  // Invite records
  const recordsContainer = document.getElementById('invite-records');
  if (recordsContainer && data.invite_records && data.invite_records.length > 0) {
    recordsContainer.innerHTML = `
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-border" style="background: var(--bg-tertiary);">
            <th class="text-left px-4 py-3 font-medium" style="color: var(--text);">邮箱</th>
            <th class="text-left px-4 py-3 font-medium" style="color: var(--text);">注册时间</th>
            <th class="text-right px-4 py-3 font-medium" style="color: var(--text);">奖励</th>
          </tr>
        </thead>
        <tbody>
          ${data.invite_records.map(record => `
            <tr class="border-b border-border last:border-0 hover:bg-bg-tertiary transition-colors">
              <td class="px-4 py-3" style="color: var(--text-secondary);">${maskEmail(record.invitee_email)}</td>
              <td class="px-4 py-3" style="color: var(--text-secondary);">${formatDate(record.created_at)}</td>
              <td class="px-4 py-3 text-right text-success font-medium">+${record.bonus_count || 0} 次</td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    `;
  }
}

// ============================================
// Action Handlers
// ============================================

/**
 * Update nickname
 */
async function updateNickname() {
  const nicknameInput = document.getElementById('nickname');
  const nickname = nicknameInput?.value?.trim();
  
  if (!nickname) {
    showToast('请输入昵称', 'error');
    return;
  }
  
  try {
    const result = await AuthAPI.updateProfile({ nickname });
    
    if (result.success) {
      showToast('昵称已更新', 'ok');
      
      // Update local storage
      const user = AuthState.getCurrentUser();
      if (user) {
        user.nickname = nickname;
        AuthState.updateUser(user);
      }
      
      // Update UI
      const nameEl = document.getElementById('user-name');
      if (nameEl) {
        nameEl.textContent = nickname;
      }
      
      const avatar = document.getElementById('user-avatar');
      if (avatar) {
        avatar.textContent = nickname[0].toUpperCase();
      }
    } else {
      showToast(result.message || '更新失败', 'error');
    }
  } catch (err) {
    showToast('网络错误', 'error');
  }
}

/**
 * Redeem activation code
 */
async function redeemCode() {
  const codeInput = document.getElementById('redeem-code');
  const code = codeInput?.value?.trim();
  
  if (!code) {
    showToast('请输入激活码', 'error');
    return;
  }
  
  const messageEl = document.getElementById('redeem-message');
  
  try {
    const result = await AuthAPI.redeemCode(code);
    
    if (result.success) {
      showToast(`充值成功！获得 ${result.data.added_count} 次使用次数`, 'ok');
      
      // Clear input
      if (codeInput) codeInput.value = '';
      
      // Update usage display
      const paidCount = document.getElementById('paid-count');
      if (paidCount) {
        paidCount.textContent = result.data.new_count;
      }
      
      // Hide message
      if (messageEl) messageEl.classList.add('hidden');
    } else {
      // Show error message
      if (messageEl) {
        messageEl.textContent = result.message || '激活码无效';
        messageEl.className = 'text-xs mt-2 text-error';
        messageEl.classList.remove('hidden');
      }
    }
  } catch (err) {
    showToast('网络错误', 'error');
  }
}

/**
 * Copy invite code to clipboard
 */
async function copyInviteCode() {
  const codeEl = document.getElementById('invite-code');
  const code = codeEl?.textContent;
  
  if (!code || code === '-') {
    showToast('暂无邀请码', 'error');
    return;
  }
  
  try {
    await navigator.clipboard.writeText(code);
    showToast('邀请码已复制', 'ok');
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = code;
    document.body.appendChild(textArea);
    textArea.select();
    document.execCommand('copy');
    document.body.removeChild(textArea);
    showToast('邀请码已复制', 'ok');
  }
}

/**
 * Logout user
 */
function logout() {
  AuthState.logout();
}

// ============================================
// Utility Functions
// ============================================

/**
 * Format date
 */
function formatDate(dateStr) {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
}

/**
 * Mask email for privacy
 */
function maskEmail(email) {
  if (!email) return '-';
  const [localPart, domain] = email.split('@');
  if (!domain) return email;
  
  const maskedLocal = localPart[0] + '***' + (localPart.length > 1 ? localPart[localPart.length - 1] : '');
  return `${maskedLocal}@${domain}`;
}

// ============================================
// Export for global access
// ============================================

window.loadAccountData = loadAccountData;
window.updateNickname = updateNickname;
window.redeemCode = redeemCode;
window.copyInviteCode = copyInviteCode;
window.logout = logout;