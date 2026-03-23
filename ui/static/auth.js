/**
 * Auth Module - Authentication and User State Management
 * 认证模块 - 用户认证和状态管理
 */

// ============================================
// Auth State Management
// ============================================

const AuthState = {
  /**
   * Get current user from localStorage
   */
  getCurrentUser() {
    const user = localStorage.getItem('prism_user');
    if (user) {
      try {
        return JSON.parse(user);
      } catch (e) {
        return null;
      }
    }
    return null;
  },

  /**
   * Get JWT token
   */
  getToken() {
    return localStorage.getItem('prism_token');
  },

  /**
   * Check if user is logged in
   */
  isLoggedIn() {
    return !!localStorage.getItem('prism_token');
  },

  /**
   * Set authentication data
   */
  setAuth(token, user) {
    localStorage.setItem('prism_token', token);
    localStorage.setItem('prism_user', JSON.stringify(user));
  },

  /**
   * Clear authentication data
   */
  clearAuth() {
    localStorage.removeItem('prism_token');
    localStorage.removeItem('prism_user');
  },

  /**
   * Logout user
   */
  logout() {
    this.clearAuth();
    window.location.href = '/login';
  },

  /**
   * Update user data in localStorage
   */
  updateUser(user) {
    localStorage.setItem('prism_user', JSON.stringify(user));
  }
};

// ============================================
// API Helpers
// ============================================

const AuthAPI = {
  /**
   * Login with email and password
   */
  async login(email, password) {
    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    return resp.json();
  },

  /**
   * Register new user
   */
  async register(email, password, invite_code = null) {
    const body = { email, password };
    if (invite_code) body.invite_code = invite_code;
    
    const resp = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    return resp.json();
  },

  /**
   * Send password reset email
   */
  async forgotPassword(email) {
    const resp = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    return resp.json();
  },

  /**
   * Get current user profile
   */
  async getProfile() {
    const token = AuthState.getToken();
    const resp = await fetch('/api/user/profile', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return resp.json();
  },

  /**
   * Update user profile
   */
  async updateProfile(data) {
    const token = AuthState.getToken();
    const resp = await fetch('/api/user/profile', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(data)
    });
    return resp.json();
  },

  /**
   * Redeem activation code
   */
  async redeemCode(code) {
    const token = AuthState.getToken();
    const resp = await fetch('/api/user/redeem', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ code })
    });
    return resp.json();
  },

  /**
   * Get invite stats
   */
  async getInviteStats() {
    const token = AuthState.getToken();
    const resp = await fetch('/api/user/invite-stats', {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    return resp.json();
  },

  /**
   * Get usage balance
   */
  async getUsageBalance() {
    const token = AuthState.getToken();
    const headers = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const resp = await fetch('/api/usage/balance', { headers });
    return resp.json();
  },

  /**
   * Handle OAuth callback
   */
  async handleOAuthCallback(code, state) {
    const resp = await fetch(`/api/auth/oauth/github/callback?code=${encodeURIComponent(code)}&state=${encodeURIComponent(state || '')}`);
    return resp.json();
  }
};

// ============================================
// Form Handlers
// ============================================

/**
 * Handle login form submission
 */
async function handleLogin(event) {
  event.preventDefault();
  
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const remember = document.getElementById('remember')?.checked;
  
  // Show loading state
  setFormLoading(true);
  hideError();
  
  try {
    const result = await AuthAPI.login(email, password);
    
    if (result.success) {
      // Save auth data
      AuthState.setAuth(result.data.token, result.data.user);
      
      // Show success message
      showToast('登录成功', 'ok');
      
      // Redirect
      setTimeout(() => {
        const redirect = new URLSearchParams(window.location.search).get('redirect') || '/';
        window.location.href = redirect;
      }, 500);
    } else {
      showError(result.message || '登录失败，请检查邮箱和密码');
    }
  } catch (err) {
    showError('网络错误，请稍后重试');
  } finally {
    setFormLoading(false);
  }
}

/**
 * Handle register form submission
 */
async function handleRegister(event) {
  event.preventDefault();
  
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const confirmPassword = document.getElementById('confirm-password').value;
  const inviteCode = document.getElementById('invite-code')?.value || null;
  const terms = document.getElementById('terms')?.checked;
  
  // Validation
  if (password !== confirmPassword) {
    showError('两次密码不一致');
    return;
  }
  
  if (!terms) {
    showError('请先同意用户协议和隐私政策');
    return;
  }
  
  // Show loading state
  setFormLoading(true);
  hideError();
  
  try {
    const result = await AuthAPI.register(email, password, inviteCode);
    
    if (result.success) {
      // Save auth data
      AuthState.setAuth(result.data.token, result.data.user);
      
      // Show success message
      showToast('注册成功', 'ok');
      
      // Redirect
      setTimeout(() => {
        window.location.href = '/';
      }, 500);
    } else {
      showError(result.message || '注册失败，请稍后重试');
    }
  } catch (err) {
    showError('网络错误，请稍后重试');
  } finally {
    setFormLoading(false);
  }
}

/**
 * Handle forgot password form submission
 */
async function handleForgotPassword(event) {
  event.preventDefault();
  
  const email = document.getElementById('email').value;
  
  // Show loading state
  setFormLoading(true);
  hideError();
  
  try {
    const result = await AuthAPI.forgotPassword(email);
    
    if (result.success) {
      // Show success message
      document.getElementById('success-message').classList.remove('hidden');
      document.getElementById('submit-btn').classList.add('hidden');
    } else {
      showError(result.message || '发送失败，请检查邮箱地址');
    }
  } catch (err) {
    showError('网络错误，请稍后重试');
  } finally {
    setFormLoading(false);
  }
}

/**
 * Handle OAuth callback
 */
async function handleOAuthCallback(code, state) {
  try {
    const result = await AuthAPI.handleOAuthCallback(code, state);
    
    if (result.success) {
      AuthState.setAuth(result.data.token, result.data.user);
      return { success: true };
    } else {
      return { success: false, message: result.message || 'OAuth 认证失败' };
    }
  } catch (err) {
    return { success: false, message: err.message || '网络错误' };
  }
}

// ============================================
// UI Helpers
// ============================================

/**
 * Set form loading state
 */
function setFormLoading(loading) {
  const submitBtn = document.getElementById('submit-btn');
  const submitText = document.getElementById('submit-text');
  const submitSpinner = document.getElementById('submit-spinner');
  
  if (submitBtn) {
    submitBtn.disabled = loading;
  }
  
  if (submitText) {
    submitText.textContent = loading ? '处理中...' : (submitText.dataset.original || '提交');
  }
  
  if (submitSpinner) {
    submitSpinner.classList.toggle('hidden', !loading);
  }
}

/**
 * Show error message
 */
function showError(message) {
  const errorDiv = document.getElementById('error-message');
  const errorText = document.getElementById('error-text');
  
  if (errorDiv && errorText) {
    errorText.textContent = message;
    errorDiv.classList.remove('hidden');
  }
}

/**
 * Hide error message
 */
function hideError() {
  const errorDiv = document.getElementById('error-message');
  if (errorDiv) {
    errorDiv.classList.add('hidden');
  }
}

/**
 * Toggle password visibility
 */
function togglePasswordVisibility(inputId) {
  const input = document.getElementById(inputId);
  if (input) {
    input.type = input.type === 'password' ? 'text' : 'password';
  }
}

/**
 * Check password strength
 */
function checkPasswordStrength() {
  const password = document.getElementById('password')?.value || '';
  const strengthBars = document.querySelectorAll('#password-strength > div');
  const hint = document.getElementById('password-hint');
  
  let strength = 0;
  if (password.length >= 6) strength++;
  if (password.length >= 10) strength++;
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) strength++;
  if (/[0-9]/.test(password) && /[^A-Za-z0-9]/.test(password)) strength++;
  
  const colors = ['#ff6b6b', '#ffaa44', '#7c5cfc', '#00d4aa'];
  const labels = ['弱', '一般', '良好', '强'];
  
  strengthBars.forEach((bar, i) => {
    if (i < strength) {
      bar.style.background = colors[strength - 1];
    } else {
      bar.style.background = 'var(--border)';
    }
  });
  
  if (hint) {
    hint.textContent = `密码强度：${labels[Math.max(0, strength - 1)] || '弱'}`;
    hint.style.color = colors[strength - 1] || 'var(--text-muted)';
  }
}

/**
 * Check if passwords match
 */
function checkPasswordMatch() {
  const password = document.getElementById('password')?.value || '';
  const confirmPassword = document.getElementById('confirm-password')?.value || '';
  const matchHint = document.getElementById('password-match');
  
  if (matchHint && confirmPassword) {
    if (password !== confirmPassword) {
      matchHint.classList.remove('hidden');
    } else {
      matchHint.classList.add('hidden');
    }
  }
}

/**
 * Login with GitHub OAuth
 */
function loginWithGitHub() {
  window.location.href = '/api/auth/oauth/github';
}

// ============================================
// Initialize Forms
// ============================================

document.addEventListener('DOMContentLoaded', () => {
  // Login form
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    // Store original button text
    const submitText = document.getElementById('submit-text');
    if (submitText) {
      submitText.dataset.original = submitText.textContent;
    }
    loginForm.addEventListener('submit', handleLogin);
  }
  
  // Register form
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    const submitText = document.getElementById('submit-text');
    if (submitText) {
      submitText.dataset.original = submitText.textContent;
    }
    registerForm.addEventListener('submit', handleRegister);
  }
  
  // Forgot password form
  const forgotForm = document.getElementById('forgot-form');
  if (forgotForm) {
    const submitText = document.getElementById('submit-text');
    if (submitText) {
      submitText.dataset.original = submitText.textContent;
    }
    forgotForm.addEventListener('submit', handleForgotPassword);
  }
});

// Export for global access
window.AuthState = AuthState;
window.AuthAPI = AuthAPI;
window.loginWithGitHub = loginWithGitHub;
window.handleOAuthCallback = handleOAuthCallback;
window.togglePasswordVisibility = togglePasswordVisibility;
window.checkPasswordStrength = checkPasswordStrength;
window.checkPasswordMatch = checkPasswordMatch;