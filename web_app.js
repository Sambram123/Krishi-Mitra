// Krishi Mitra — Shared Authentication & Web App Helper
// Provides in-memory JWT storage, silent refresh on 401, phone+OTP login modal, and auth UI bindings.
const KrishiAuth = (() => {
  let _accessToken = null;
  let _currentUser = null;
  let _isRefreshing = false;
  let _refreshSubscribers = [];
  let _loginSuccessCallback = null;
  let _pendingPhone = '';

  const i18n = {
    kn: {
      loginTitle: 'ರೈತರ ಸುರಕ್ಷಿತ ಲಾಗಿನ್',
      loginSubtitle: 'ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ಮತ್ತು ಸಂವಾದಕ್ಕಾಗಿ ನಿಮ್ಮ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ.',
      phoneLabel: 'ಮೊಬೈಲ್ ಸಂಖ್ಯೆ (10 ಅಂಕಿಗಳು)',
      phonePlaceholder: '9876543210',
      nameLabel: 'ರೈತರ ಹೆಸರು (ಐಚ್ಛಿಕ)',
      namePlaceholder: 'ಉದಾ: ಬಸವರಾಜ',
      sendOtpBtn: 'ಒಟಿಪಿ ಪಡೆಯಿರಿ (Send OTP)',
      sendingOtp: 'ಒಟಿಪಿ ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ...',
      otpLabel: '6-ಅಂಕಿಯ ಒಟಿಪಿ ಕೋಡ್',
      otpPlaceholder: '123456',
      verifyBtn: 'ದೃಢೀಕರಿಸಿ ಮತ್ತು ಮುಂದುವರಿಯಿರಿ',
      verifying: 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...',
      changePhone: 'ಸಂಖ್ಯೆ ಬದಲಿಸಿ',
      resendOtp: 'ಮತ್ತೆ ಒಟಿಪಿ ಕಳುಹಿಸಿ',
      otpSentTo: 'ಒಟಿಪಿಯನ್ನು ಈ ಸಂಖ್ಯೆಗೆ ಕಳುಹಿಸಲಾಗಿದೆ:',
      loginSuccess: 'ಲಾಗಿನ್ ಯಶಸ್ವಿಯಾಗಿದೆ!',
      logoutBtn: 'ಲಾಗ್‌ಔಟ್',
      loginBtn: 'ರೈತರ ಲಾಗಿನ್',
      devNotice: 'ಡೆವಲಪ್‌ಮೆಂಟ್ ಮೋಡ್: ಒಟಿಪಿ ಕೋಡ್ ಸರ್ವರ್ ಟರ್ಮಿನಲ್‌ನಲ್ಲಿ ಪ್ರಿಂಟ್ ಆಗುತ್ತದೆ.',
      errPhone: 'ದಯವಿಟ್ಟು ಮಾನ್ಯವಾದ 10-ಅಂಕಿಯ ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ.',
      errOtp: 'ದಯವಿಟ್ಟು 6-ಅಂಕಿಯ ಒಟಿಪಿ ಕೋಡ್ ನಮೂದಿಸಿ.',
      sessionExpired: 'ಅಧಿವೇಶನ ಮುಕ್ತಾಯಗೊಂಡಿದೆ. ದಯವಿಟ್ಟು ಪುನಃ ಲಾಗಿನ್ ಆಗಿ.'
    },
    en: {
      loginTitle: 'Farmer Secure Login',
      loginSubtitle: 'Enter your mobile phone number to check government schemes and consult Krishi Mitra.',
      phoneLabel: 'Mobile Number (10 digits)',
      phonePlaceholder: '9876543210',
      nameLabel: 'Farmer Name (Optional)',
      namePlaceholder: 'e.g. Basavaraj',
      sendOtpBtn: 'Send OTP',
      sendingOtp: 'Sending OTP...',
      otpLabel: '6-Digit OTP Code',
      otpPlaceholder: '123456',
      verifyBtn: 'Verify & Continue',
      verifying: 'Verifying OTP...',
      changePhone: 'Change Number',
      resendOtp: 'Resend OTP',
      otpSentTo: 'OTP has been dispatched to:',
      loginSuccess: 'Logged in successfully!',
      logoutBtn: 'Logout',
      loginBtn: 'Farmer Login',
      devNotice: 'Dev Mode: The 6-digit OTP is printed to the backend server terminal.',
      errPhone: 'Please enter a valid 10-digit mobile number.',
      errOtp: 'Please enter the 6-digit OTP code.',
      sessionExpired: 'Session expired. Please log in again.'
    }
  };

  function getLang() {
    if (typeof currentLanguage !== 'undefined' && currentLanguage) return currentLanguage;
    if (typeof currentLang !== 'undefined' && currentLang) return currentLang;
    return 'kn';
  }

  function getToken() {
    return _accessToken;
  }

  function setToken(token) {
    _accessToken = token;
  }

  function getUser() {
    return _currentUser;
  }

  function setUser(user) {
    _currentUser = user;
    renderAuthUI();
  }

  async function requestOtp(phone) {
    const res = await fetch('/api/auth/request-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phone }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'Failed to request OTP');
    }
    return data;
  }

  async function verifyOtp(phone, otp, name = '', preferredLanguage = '') {
    const lang = preferredLanguage || getLang();
    const res = await fetch('/api/auth/verify-otp', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        phone,
        otp,
        name: name || undefined,
        preferred_language: lang,
      }),
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || 'OTP verification failed');
    }
    _accessToken = data.access_token;
    _currentUser = data.user;
    renderAuthUI();
    return data;
  }

  async function refreshToken() {
    try {
      const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
      });
      if (!res.ok) {
        _accessToken = null;
        _currentUser = null;
        renderAuthUI();
        return null;
      }
      const data = await res.json();
      _accessToken = data.access_token;
      return _accessToken;
    } catch (e) {
      _accessToken = null;
      _currentUser = null;
      renderAuthUI();
      return null;
    }
  }

  async function logout() {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
      });
    } catch (e) {
      console.warn('Logout error', e);
    }
    _accessToken = null;
    _currentUser = null;
    if (window.KrishiOffline) {
      try { await window.KrishiOffline.clearAllData(); } catch (e) {}
    }
    renderAuthUI();
  }

  async function getMe() {
    if (!_accessToken) return null;
    try {
      const res = await fetchWithAuth('/api/auth/me');
      if (res.ok) {
        _currentUser = await res.json();
        renderAuthUI();
        return _currentUser;
      }
    } catch (e) {
      console.warn('getMe error', e);
    }
    return null;
  }

  async function checkAuth() {
    const token = await refreshToken();
    if (token) {
      await getMe();
    } else {
      renderAuthUI();
    }
    return _currentUser;
  }

  async function fetchWithAuth(url, options = {}) {
    options = { ...options };
    options.headers = new Headers(options.headers || {});
    options.credentials = 'same-origin';

    if (_accessToken) {
      options.headers.set('Authorization', `Bearer ${_accessToken}`);
    }

    let response = await fetch(url, options);

    if (response.status === 401) {
      if (!_isRefreshing) {
        _isRefreshing = true;
        const newToken = await refreshToken();
        _isRefreshing = false;
        if (newToken) {
          _refreshSubscribers.forEach(cb => cb(newToken));
          _refreshSubscribers = [];
          options.headers.set('Authorization', `Bearer ${newToken}`);
          response = await fetch(url, options);
          return response;
        } else {
          _refreshSubscribers.forEach(cb => cb(null));
          _refreshSubscribers = [];
          showLoginModal();
          return response;
        }
      } else {
        const retryPromise = new Promise(resolve => {
          _refreshSubscribers.push(async (newToken) => {
            if (newToken) {
              options.headers.set('Authorization', `Bearer ${newToken}`);
              resolve(await fetch(url, options));
            } else {
              showLoginModal();
              resolve(response);
            }
          });
        });
        return await retryPromise;
      }
    }

    return response;
  }

  function injectModalHTML() {
    if (document.getElementById('krishi-auth-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'krishi-auth-modal';
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm hidden';
    modal.innerHTML = `
      <div class="bg-[#FAF8F5] text-slate-900 rounded-3xl shadow-2xl max-w-md w-full p-6 sm:p-8 border border-emerald-900/10 relative">
        <button id="auth-modal-close" type="button" class="absolute top-5 right-5 text-slate-400 hover:text-slate-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-200/60 transition-colors">
          <span class="material-symbols-outlined text-lg">close</span>
        </button>

        <div class="flex items-center gap-3 mb-4">
          <div class="w-12 h-12 rounded-2xl bg-[#1B5E20] text-white flex items-center justify-center shadow-md shrink-0">
            <span class="material-symbols-outlined text-2xl">eco</span>
          </div>
          <div>
            <h2 id="auth-modal-title" class="font-heading font-extrabold text-xl text-slate-900 tracking-tight leading-snug">
              ರೈತರ ಸುರಕ್ಷಿತ ಲಾಗಿನ್
            </h2>
            <p id="auth-modal-subtitle" class="text-xs text-slate-600 mt-0.5 leading-relaxed">
              ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ಮಾಹಿತಿ ಮತ್ತು ಸಂವಾದಕ್ಕಾಗಿ ನಿಮ್ಮ ಮೊಬೈಲ್ ಸಂಖ್ಯೆ ನಮೂದಿಸಿ.
            </p>
          </div>
        </div>

        <div id="auth-modal-error" class="hidden mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center gap-2">
          <span class="material-symbols-outlined text-sm shrink-0">error</span>
          <span id="auth-modal-error-text"></span>
        </div>

        <div id="auth-modal-success" class="hidden mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium flex items-center gap-2">
          <span class="material-symbols-outlined text-sm shrink-0">check_circle</span>
          <span id="auth-modal-success-text"></span>
        </div>

        <div id="auth-step-phone" class="space-y-4">
          <div>
            <label id="auth-label-phone" for="auth-phone-input" class="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
              ಮೊಬೈಲ್ ಸಂಖ್ಯೆ (10 ಅಂಕಿಗಳು)
            </label>
            <div class="relative flex items-center">
              <span class="absolute left-3.5 text-xs font-bold text-slate-500 font-mono select-none">+91</span>
              <input id="auth-phone-input" type="tel" maxlength="10" inputmode="numeric" placeholder="9876543210"
                class="w-full pl-12 pr-4 py-3.5 bg-white border-2 border-slate-200 focus:border-[#1B5E20] focus:ring-2 focus:ring-[#1B5E20]/20 rounded-xl text-base font-semibold text-slate-900 tracking-wider placeholder:text-slate-400 outline-none transition-all shadow-inner" />
            </div>
          </div>

          <div>
            <label id="auth-label-name" for="auth-name-input" class="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
              ರೈತರ ಹೆಸರು (ಐಚ್ಛಿಕ)
            </label>
            <input id="auth-name-input" type="text" placeholder="ಉದಾ: ಬಸವರಾಜ"
              class="w-full px-4 py-3 bg-white border border-slate-200 focus:border-[#1B5E20] focus:ring-1 focus:ring-[#1B5E20] rounded-xl text-sm font-medium text-slate-900 placeholder:text-slate-400 outline-none transition-all" />
          </div>

          <button id="auth-send-otp-btn" type="button"
            class="w-full min-h-[52px] py-3.5 px-4 rounded-xl bg-[#1B5E20] hover:bg-[#2E7D32] text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99]">
            <span class="material-symbols-outlined text-lg">send</span>
            <span id="auth-send-otp-text">ಒಟಿಪಿ ಪಡೆಯಿರಿ (Send OTP)</span>
          </button>
        </div>

        <div id="auth-step-otp" class="space-y-4 hidden">
          <div class="p-3 bg-slate-100/80 rounded-xl border border-slate-200/80 flex items-center justify-between">
            <div class="text-xs text-slate-700">
              <span id="auth-otp-sent-to-label">ಒಟಿಪಿಯನ್ನು ಈ ಸಂಖ್ಯೆಗೆ ಕಳುಹಿಸಲಾಗಿದೆ:</span>
              <span id="auth-target-phone" class="font-bold font-mono ml-1 text-slate-900">+91 ******</span>
            </div>
            <button id="auth-change-phone-btn" type="button" class="text-xs text-[#1B5E20] hover:underline font-bold">
              ಸಂಖ್ಯೆ ಬದಲಿಸಿ
            </button>
          </div>

          <div>
            <label id="auth-label-otp" for="auth-otp-input" class="block text-xs font-bold text-slate-700 mb-1.5 uppercase tracking-wider">
              6-ಅಂಕಿಯ ಒಟಿಪಿ ಕೋಡ್
            </label>
            <input id="auth-otp-input" type="text" maxlength="6" inputmode="numeric" placeholder="123456"
              class="w-full px-4 py-3.5 bg-white border-2 border-slate-200 focus:border-[#1B5E20] focus:ring-2 focus:ring-[#1B5E20]/20 rounded-xl text-center text-2xl font-bold font-mono tracking-[0.4em] text-slate-900 placeholder:text-slate-300 outline-none transition-all shadow-inner" />
          </div>

          <button id="auth-verify-otp-btn" type="button"
            class="w-full min-h-[52px] py-3.5 px-4 rounded-xl bg-[#1B5E20] hover:bg-[#2E7D32] text-white font-bold text-sm shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99]">
            <span class="material-symbols-outlined text-lg">verified_user</span>
            <span id="auth-verify-otp-text">ದೃಢೀಕರಿಸಿ ಮತ್ತು ಮುಂದುವರಿಯಿರಿ</span>
          </button>

          <div class="text-center pt-1">
            <button id="auth-resend-otp-btn" type="button" class="text-xs text-slate-500 hover:text-slate-800 font-semibold hover:underline">
              ಮತ್ತೆ ಒಟಿಪಿ ಕಳುಹಿಸಿ (Resend OTP)
            </button>
          </div>
        </div>

        <div class="mt-4 pt-3 border-t border-slate-200 text-[11px] text-slate-400 flex items-center gap-1.5">
          <span class="material-symbols-outlined text-xs text-amber-600">info</span>
          <span id="auth-dev-notice">ಡೆವಲಪ್‌ಮೆಂಟ್ ಮೋಡ್: ಒಟಿಪಿ ಕೋಡ್ ಸರ್ವರ್ ಟರ್ಮಿನಲ್‌ನಲ್ಲಿ ಪ್ರಿಂಟ್ ಆಗುತ್ತದೆ.</span>
        </div>
      </div>
    `;

    document.body.appendChild(modal);

    const closeBtn = document.getElementById('auth-modal-close');
    const sendBtn = document.getElementById('auth-send-otp-btn');
    const verifyBtn = document.getElementById('auth-verify-otp-btn');
    const changeBtn = document.getElementById('auth-change-phone-btn');
    const resendBtn = document.getElementById('auth-resend-otp-btn');

    closeBtn.addEventListener('click', hideLoginModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) hideLoginModal();
    });

    sendBtn.addEventListener('click', handleSendOtpClick);
    verifyBtn.addEventListener('click', handleVerifyOtpClick);
    changeBtn.addEventListener('click', () => showStep(1));
    resendBtn.addEventListener('click', handleSendOtpClick);

    document.getElementById('auth-phone-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleSendOtpClick();
    });
    document.getElementById('auth-otp-input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleVerifyOtpClick();
    });
  }

  function showStep(step) {
    const step1 = document.getElementById('auth-step-phone');
    const step2 = document.getElementById('auth-step-otp');
    const errBox = document.getElementById('auth-modal-error');
    const succBox = document.getElementById('auth-modal-success');
    if (errBox) errBox.classList.add('hidden');
    if (succBox) succBox.classList.add('hidden');

    if (step === 1) {
      if (step1) step1.classList.remove('hidden');
      if (step2) step2.classList.add('hidden');
      setTimeout(() => document.getElementById('auth-phone-input')?.focus(), 100);
    } else {
      if (step1) step1.classList.add('hidden');
      if (step2) step2.classList.remove('hidden');
      setTimeout(() => document.getElementById('auth-otp-input')?.focus(), 100);
    }
  }

  function showModalError(msg) {
    const errBox = document.getElementById('auth-modal-error');
    const errText = document.getElementById('auth-modal-error-text');
    if (errBox && errText) {
      errText.textContent = msg;
      errBox.classList.remove('hidden');
    }
  }

  function showModalSuccess(msg) {
    const succBox = document.getElementById('auth-modal-success');
    const succText = document.getElementById('auth-modal-success-text');
    if (succBox && succText) {
      succText.textContent = msg;
      succBox.classList.remove('hidden');
    }
  }

  async function handleSendOtpClick() {
    const phoneInput = document.getElementById('auth-phone-input');
    const raw = (phoneInput?.value || '').trim().replace(/\D/g, '');
    const lang = getLang();
    const t = i18n[lang] || i18n.kn;

    if (raw.length !== 10) {
      showModalError(t.errPhone);
      return;
    }

    _pendingPhone = '+91' + raw;
    const sendBtn = document.getElementById('auth-send-otp-btn');
    const sendText = document.getElementById('auth-send-otp-text');
    if (sendBtn) sendBtn.disabled = true;
    if (sendText) sendText.textContent = t.sendingOtp;

    try {
      const result = await requestOtp(_pendingPhone);
      document.getElementById('auth-target-phone').textContent = result.phone || _pendingPhone;
      showStep(2);
      showModalSuccess(t.otpSentTo + ' ' + (result.phone || _pendingPhone));
    } catch (err) {
      showModalError(err.message || 'Failed to send OTP. Please check your connection.');
    } finally {
      if (sendBtn) sendBtn.disabled = false;
      if (sendText) sendText.textContent = t.sendOtpBtn;
    }
  }

  async function handleVerifyOtpClick() {
    const otpInput = document.getElementById('auth-otp-input');
    const nameInput = document.getElementById('auth-name-input');
    const otp = (otpInput?.value || '').trim();
    const lang = getLang();
    const t = i18n[lang] || i18n.kn;

    if (otp.length !== 6) {
      showModalError(t.errOtp);
      return;
    }

    const verifyBtn = document.getElementById('auth-verify-otp-btn');
    const verifyText = document.getElementById('auth-verify-otp-text');
    if (verifyBtn) verifyBtn.disabled = true;
    if (verifyText) verifyText.textContent = t.verifying;

    try {
      const name = nameInput?.value?.trim() || '';
      await verifyOtp(_pendingPhone, otp, name, lang);
      showModalSuccess(t.loginSuccess);
      window.dispatchEvent(new CustomEvent('krishi:auth-success', {
        detail: { user: _currentUser, phone: _pendingPhone }
      }));
      setTimeout(() => {
        hideLoginModal();
        if (_loginSuccessCallback) {
          const cb = _loginSuccessCallback;
          _loginSuccessCallback = null;
          cb();
        }
      }, 600);
    } catch (err) {
      showModalError(err.message || 'Invalid OTP code. Please try again.');
    } finally {
      if (verifyBtn) verifyBtn.disabled = false;
      if (verifyText) verifyText.textContent = t.verifyBtn;
    }
  }

  function updateModalLang() {
    const lang = getLang();
    const t = i18n[lang] || i18n.kn;

    const elTitle = document.getElementById('auth-modal-title');
    const elSubtitle = document.getElementById('auth-modal-subtitle');
    const elPhoneLabel = document.getElementById('auth-label-phone');
    const elNameLabel = document.getElementById('auth-label-name');
    const elSendText = document.getElementById('auth-send-otp-text');
    const elOtpSentTo = document.getElementById('auth-otp-sent-to-label');
    const elChangePhone = document.getElementById('auth-change-phone-btn');
    const elOtpLabel = document.getElementById('auth-label-otp');
    const elVerifyText = document.getElementById('auth-verify-otp-text');
    const elResend = document.getElementById('auth-resend-otp-btn');
    const elDevNotice = document.getElementById('auth-dev-notice');

    if (elTitle) elTitle.textContent = t.loginTitle;
    if (elSubtitle) elSubtitle.textContent = t.loginSubtitle;
    if (elPhoneLabel) elPhoneLabel.textContent = t.phoneLabel;
    if (elNameLabel) elNameLabel.textContent = t.nameLabel;
    if (elSendText) elSendText.textContent = t.sendOtpBtn;
    if (elOtpSentTo) elOtpSentTo.textContent = t.otpSentTo;
    if (elChangePhone) elChangePhone.textContent = t.changePhone;
    if (elOtpLabel) elOtpLabel.textContent = t.otpLabel;
    if (elVerifyText) elVerifyText.textContent = t.verifyBtn;
    if (elResend) elResend.textContent = t.resendOtp;
    if (elDevNotice) elDevNotice.textContent = t.devNotice;
  }

  function showLoginModal(onSuccess) {
    injectModalHTML();
    _loginSuccessCallback = onSuccess || null;
    updateModalLang();
    showStep(1);
    const modal = document.getElementById('krishi-auth-modal');
    if (modal) modal.classList.remove('hidden');
  }

  function hideLoginModal() {
    const modal = document.getElementById('krishi-auth-modal');
    if (modal) modal.classList.add('hidden');
  }

  function renderAuthUI() {
    const lang = getLang();
    const t = i18n[lang] || i18n.kn;
    const containers = document.querySelectorAll('.krishi-auth-container, #auth-header-container');

    containers.forEach(container => {
      container.innerHTML = '';
      if (_currentUser) {
        const pill = document.createElement('div');
        pill.className = 'flex items-center gap-2 bg-emerald-50 text-emerald-950 border border-emerald-300/80 px-3 py-1.5 rounded-full text-xs font-semibold shadow-xs';
        const displayName = _currentUser.name || _currentUser.phone;
        pill.innerHTML = `
          <span class="material-symbols-outlined text-emerald-700 text-sm">account_circle</span>
          <span class="truncate max-w-[130px] font-bold">${displayName}</span>
          ${_currentUser.role === 'admin' ? '<span class="bg-amber-100 text-amber-800 border border-amber-300 px-1 rounded text-[9px] font-bold uppercase font-mono">ADMIN</span>' : ''}
        `;

        const logoutBtn = document.createElement('button');
        logoutBtn.type = 'button';
        logoutBtn.className = 'flex items-center gap-1 bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-full text-xs font-semibold transition-colors cursor-pointer border border-slate-200';
        logoutBtn.innerHTML = `
          <span class="material-symbols-outlined text-sm">logout</span>
          <span>${t.logoutBtn}</span>
        `;
        logoutBtn.onclick = () => logout();

        container.append(pill, logoutBtn);
      } else {
        const loginBtn = document.createElement('button');
        loginBtn.type = 'button';
        loginBtn.className = 'flex items-center gap-1.5 bg-[#1B5E20] hover:bg-[#2E7D32] text-white px-4 py-2 rounded-full text-xs font-bold shadow-sm transition-all cursor-pointer';
        loginBtn.innerHTML = `
          <span class="material-symbols-outlined text-sm">login</span>
          <span>${t.loginBtn}</span>
        `;
        loginBtn.onclick = () => showLoginModal();
        container.appendChild(loginBtn);
      }
    });
  }

  function init() {
    injectModalHTML();
    renderAuthUI();
    checkAuth();
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  return {
    getToken,
    setToken,
    getUser,
    setUser,
    getLang,
    setLang: (lang) => { updateModalLang(); renderAuthUI(); },
    fetchWithAuth,
    requestOtp,
    verifyOtp,
    refreshToken,
    logout,
    getMe,
    checkAuth,
    showLoginModal,
    hideLoginModal,
    renderAuthUI,
    init,
  };
})();

if (typeof window !== 'undefined') window.KrishiAuth = KrishiAuth;

// Krishi Mitra — Voice Consent & DPDP Privacy Manager
const KrishiConsent = (() => {
  let _hasVoiceConsent = null;
  let _saveHistory = false;
  let _currentPolicy = null;
  let _activeStream = null;
  let _consentDecisionCallback = null;

  const i18n = {
    kn: {
      modalTitle: 'ಧ್ವನಿ ಗೌಪ್ಯತೆ ಮತ್ತು ಅನುಮತಿ (Voice Privacy Consent)',
      modalSubtitle: 'ಕೃಷಿ ಮಿತ್ರದೊಂದಿಗೆ ಕನ್ನಡದಲ್ಲಿ ಧ್ವನಿಯ ಮೂಲಕ ಮಾತನಾಡಲು ಡಿಪಿಡಿಪಿ (DPDP 2023) ಕಾಯ್ದೆಯನ್ವಯ ನಿಮ್ಮ ಸ್ಪಷ್ಟ ಒಪ್ಪಿಗೆ ಅಗತ್ಯವಿದೆ.',
      whatTitle: 'ಏನು ರೆಕಾರ್ಡ್ ಮಾಡಲಾಗುತ್ತದೆ?',
      whatDesc: 'ಮೈಕ್ರೊಫೋನ್ ಬಟನ್ ಒತ್ತಿದಾಗ ನೀವು ಮಾತನಾಡುವ ಧ್ವನಿ ಆಡಿಯೋ ಮಾತ್ರ.',
      whyTitle: 'ಏಕೆ ಬಳಸಲಾಗುತ್ತದೆ?',
      whyDesc: 'ನಿಮ್ಮ ಆಡುಭಾಷೆಯ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳನ್ನು ಅರ್ಥಮಾಡಿಕೊಂಡು ಯೋಜನೆಗಳ ಅರ್ಹತೆ ಪರಿಶೀಲಿಸಲು.',
      thirdPartiesTitle: 'ಪ್ರಕ್ರಿಯೆಗೊಳಿಸುವವರು ಯಾರು?',
      thirdPartiesDesc: 'ಸರ್ವಮ್ ಎಐ (Sarvam AI — ಕನ್ನಡ ASR/TTS) ಮತ್ತು ಗ್ರೋಕ್ (Groq — ಭಾಷಾ ಮಾದರಿ).',
      retentionTitle: 'ಡೇಟಾ ಉಳಿಸುವಿಕೆ & ಭದ್ರತೆ:',
      retentionDesc: 'ಆಡಿಯೋವನ್ನು ತಾತ್ಕಾಲಿಕ ಮೆಮೊರಿಯಲ್ಲಿ ಮಾತ್ರ ಸಂಸ್ಕರಿಸಲಾಗುತ್ತದೆ. ಎಂದಿಗೂ ಡಿಸ್ಕ್ ಅಥವಾ ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಉಳಿಸುವುದಿಲ್ಲ.',
      revocationTitle: 'ಹಿಂಪಡೆಯುವ ಹಕ್ಕು:',
      revocationDesc: 'ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ಸೆಟ್ಟಿಂಗ್ಸ್‌ನಲ್ಲಿ ಈ ಅನುಮತಿಯನ್ನು ಹಿಂಪಡೆಯಬಹುದು ಅಥವಾ ಡೇಟಾ ಅಳಿಸಬಹುದು.',
      allowBtn: 'ಒಪ್ಪಿಗೆ ನೀಡಿ (Allow Voice)',
      denyBtn: 'ಬೇಡ (No thanks)',
      settingsTitle: 'ಗೌಪ್ಯತೆ ಮತ್ತು ಸೆಟ್ಟಿಂಗ್ಸ್ (Privacy Settings)',
      voiceStatusLabel: 'ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್ ಸ್ಥಿತಿ:',
      voiceStatusActive: 'ಸಕ್ರಿಯವಾಗಿದೆ (Active)',
      voiceStatusInactive: 'ಹಿಂಪಡೆಯಲಾಗಿದೆ / ನಿಷ್ಕ್ರಿಯ (Withdrawn)',
      withdrawBtn: 'ಧ್ವನಿ ಅನುಮತಿ ಹಿಂಪಡೆಯಿರಿ',
      historyLabel: 'ಸಂಭಾಷಣಾ ಇತಿಹಾಸ ಉಳಿಸಿ (Save Conversation History)',
      historyHint: 'ಪೂರ್ವನಿಯೋಜಿತವಾಗಿ ಆಫ್ ಆಗಿದೆ. ಆನ್ ಮಾಡಿದರೆ ಮಾತ್ರ ಸಂಭಾಷಣಾ ವಿವರಗಳನ್ನು ಉಳಿಸಲಾಗುತ್ತದೆ.',
      deleteDataBtn: 'ನನ್ನ ಎಲ್ಲಾ ಡೇಟಾ ಅಳಿಸಿ (Delete My Data)',
      deleteConfirm: 'ಖಚಿತಪಡಿಸಿ: ನಿಮ್ಮ ಎಲ್ಲಾ ಸಕ್ರಿಯ ಸಂಭಾಷಣೆ, ಇತಿಹಾಸ ಮತ್ತು ಡೇಟಾವನ್ನು ಶಾಶ್ವತವಾಗಿ ಅಳಿಸಲಾಗುವುದೇ?',
      deleteSuccess: 'ನಿಮ್ಮ ಎಲ್ಲಾ ಡೇಟಾ ಮತ್ತು ಸಂಭಾಷಣೆಗಳನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಅಳಿಸಲಾಗಿದೆ.',
      withdrawnSuccess: 'ಧ್ವನಿ ಅನುಮತಿಯನ್ನು ಹಿಂಪಡೆಯಲಾಗಿದೆ. ಮೈಕ್ರೊಫೋನ್ ಸಂಪರ್ಕ ಕಡಿತಗೊಂಡಿದೆ.',
      consentRequired: 'ಧ್ವನಿ ಬಳಸಲು ಅನುಮತಿ ಅಗತ್ಯವಿದೆ. ದಯವಿಟ್ಟು ಅನುಮತಿ ನೀಡಿ.'
    },
    en: {
      modalTitle: 'Voice Privacy & Informed Consent',
      modalSubtitle: 'Under DPDP 2023, explicit and informed consent is required to process your voice with Krishi Mitra.',
      whatTitle: 'What is recorded?',
      whatDesc: 'Your microphone audio only while you are actively speaking after pressing the mic button.',
      whyTitle: 'Why is it processed?',
      whyDesc: 'To transcribe your spoken agricultural queries and determine your government scheme eligibility.',
      thirdPartiesTitle: 'Third-Party Processors:',
      thirdPartiesDesc: 'Sarvam AI (Kannada speech-to-text & TTS) and Groq (language reasoning).',
      retentionTitle: 'Retention & Storage:',
      retentionDesc: 'In-memory processing only. Audio is immediately discarded and never stored on disk or in the database.',
      revocationTitle: 'Your Rights & Revocation:',
      revocationDesc: 'You may withdraw consent at any time from the settings panel or delete your session data.',
      allowBtn: 'Allow Voice Processing',
      denyBtn: 'No thanks',
      settingsTitle: 'Privacy & Data Settings',
      voiceStatusLabel: 'Voice Recording Consent:',
      voiceStatusActive: 'Active & Granted',
      voiceStatusInactive: 'Withdrawn / Inactive',
      withdrawBtn: 'Withdraw Voice Consent',
      historyLabel: 'Save Conversation History',
      historyHint: 'Default is off. Transcripts are only retained if you explicitly turn this on.',
      deleteDataBtn: 'Delete My Data (Right to Erasure)',
      deleteConfirm: 'Are you sure? This will permanently delete all your conversation sessions, history, and active consents.',
      deleteSuccess: 'All your session data and transcripts have been permanently deleted.',
      withdrawnSuccess: 'Voice consent has been withdrawn and the microphone released.',
      consentRequired: 'Voice processing consent is required to use audio features.'
    }
  };

  function getLang() {
    if (typeof currentLanguage !== 'undefined' && currentLanguage) return currentLanguage;
    if (typeof currentLang !== 'undefined' && currentLang) return currentLang;
    return 'kn';
  }

  async function getPolicy() {
    if (_currentPolicy) return _currentPolicy;
    try {
      const res = await fetch('/api/consent/policy');
      if (res.ok) {
        _currentPolicy = await res.json();
      }
    } catch (e) {
      console.warn('Failed to fetch consent policy', e);
    }
    return _currentPolicy;
  }

  async function checkConsents() {
    if (!KrishiAuth.getToken()) {
      _hasVoiceConsent = false;
      return { voice_consent_active: false, save_history: false };
    }
    try {
      const res = await KrishiAuth.fetchWithAuth('/api/me/consents');
      if (res.ok) {
        const data = await res.json();
        _hasVoiceConsent = Boolean(data.voice_consent_active);
        _saveHistory = Boolean(data.save_history);
        renderSettingsUI();
        return data;
      }
    } catch (e) {
      console.warn('Failed to check user consents', e);
    }
    return { voice_consent_active: false, save_history: false };
  }

  async function grantVoiceConsent(saveHistory = null) {
    const policy = await getPolicy();
    const version = policy?.version || '1.0';
    const payload = {
      purpose: 'voice_recording',
      policy_version: version,
      granted: true,
    };
    if (saveHistory !== null) {
      payload.save_history = saveHistory;
    }
    const res = await KrishiAuth.fetchWithAuth('/api/consent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail?.message || err.detail || 'Consent recording failed');
    }
    const data = await res.json();
    _hasVoiceConsent = true;
    if (data.save_history !== undefined) _saveHistory = data.save_history;
    renderSettingsUI();
    return data;
  }

  async function withdrawVoiceConsent() {
    releaseMicrophone();
    if (window.KrishiOffline) {
      try { await window.KrishiOffline.purgeVoiceQueue(); } catch (e) {}
    }
    const res = await KrishiAuth.fetchWithAuth('/api/consent/voice', {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail?.message || err.detail || 'Failed to withdraw consent');
    }
    _hasVoiceConsent = false;
    renderSettingsUI();
    return await res.json();
  }

  async function updateHistoryPreference(enabled) {
    const res = await KrishiAuth.fetchWithAuth('/api/me/history-preference', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ save_history: enabled }),
    });
    if (res.ok) {
      const data = await res.json();
      _saveHistory = Boolean(data.save_history);
      renderSettingsUI();
    }
  }

  async function deleteUserData() {
    releaseMicrophone();
    if (window.KrishiOffline) {
      try { await window.KrishiOffline.clearAllData(); } catch (e) {}
    }
    const res = await KrishiAuth.fetchWithAuth('/api/me/data', {
      method: 'DELETE',
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail?.message || err.detail || 'Data deletion failed');
    }
    _hasVoiceConsent = false;
    _saveHistory = false;
    renderSettingsUI();
    return await res.json();
  }

  function registerActiveStream(stream) {
    _activeStream = stream;
  }

  function releaseMicrophone() {
    if (_activeStream) {
      try {
        _activeStream.getTracks().forEach(track => {
          track.stop();
          track.enabled = false;
        });
      } catch (e) {}
      _activeStream = null;
    }
    if (typeof stopRecording === 'function' && typeof isRecording !== 'undefined' && isRecording) {
      try { stopRecording(); } catch (e) {}
    }
  }

  function injectConsentModalHTML() {
    if (document.getElementById('krishi-consent-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'krishi-consent-modal';
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/65 backdrop-blur-md hidden';
    modal.innerHTML = `
      <div class="bg-[#FAF8F5] text-slate-900 rounded-3xl shadow-2xl max-w-lg w-full p-6 sm:p-8 border border-emerald-900/10 relative">
        <div class="flex items-start gap-3.5 mb-5">
          <div class="w-12 h-12 rounded-2xl bg-[#1B5E20] text-white flex items-center justify-center shadow-md shrink-0">
            <span class="material-symbols-outlined text-2xl">mic</span>
          </div>
          <div>
            <h2 id="consent-modal-title" class="font-heading font-extrabold text-lg sm:text-xl text-slate-900 tracking-tight leading-snug">
              ಧ್ವನಿ ಗೌಪ್ಯತೆ ಮತ್ತು ಅನುಮತಿ (Voice Privacy Consent)
            </h2>
            <p id="consent-modal-subtitle" class="text-xs text-slate-600 mt-1 leading-relaxed">
              ಕೃಷಿ ಮಿತ್ರದೊಂದಿಗೆ ಕನ್ನಡದಲ್ಲಿ ಧ್ವನಿಯ ಮೂಲಕ ಮಾತನಾಡಲು ಡಿಪಿಡಿಪಿ (DPDP 2023) ಕಾಯ್ದೆಯನ್ವಯ ನಿಮ್ಮ ಸ್ಪಷ್ಟ ಒಪ್ಪಿಗೆ ಅಗತ್ಯವಿದೆ.
            </p>
          </div>
        </div>

        <div class="space-y-3 mb-6 max-h-[55vh] overflow-y-auto pr-1 text-xs">
          <div class="p-3 rounded-2xl bg-white border border-slate-200/90 shadow-2xs">
            <div class="font-bold text-slate-900 flex items-center gap-1.5 mb-0.5">
              <span class="material-symbols-outlined text-emerald-700 text-sm">graphic_eq</span>
              <span id="consent-what-title">ಏನು ರೆಕಾರ್ಡ್ ಮಾಡಲಾಗುತ್ತದೆ?</span>
            </div>
            <p id="consent-what-desc" class="text-slate-600 leading-relaxed">
              ಮೈಕ್ರೊಫೋನ್ ಬಟನ್ ಒತ್ತಿದಾಗ ನೀವು ಮಾತನಾಡುವ ಧ್ವನಿ ಆಡಿಯೋ ಮಾತ್ರ.
            </p>
          </div>

          <div class="p-3 rounded-2xl bg-white border border-slate-200/90 shadow-2xs">
            <div class="font-bold text-slate-900 flex items-center gap-1.5 mb-0.5">
              <span class="material-symbols-outlined text-emerald-700 text-sm">agriculture</span>
              <span id="consent-why-title">ಏಕೆ ಬಳಸಲಾಗುತ್ತದೆ?</span>
            </div>
            <p id="consent-why-desc" class="text-slate-600 leading-relaxed">
              ನಿಮ್ಮ ಆಡುಭಾಷೆಯ ಕೃಷಿ ಪ್ರಶ್ನೆಗಳನ್ನು ಅರ್ಥಮಾಡಿಕೊಂಡು ಯೋಜನೆಗಳ ಅರ್ಹತೆ ಪರಿಶೀಲಿಸಲು.
            </p>
          </div>

          <div class="p-3 rounded-2xl bg-white border border-slate-200/90 shadow-2xs">
            <div class="font-bold text-slate-900 flex items-center gap-1.5 mb-0.5">
              <span class="material-symbols-outlined text-emerald-700 text-sm">hub</span>
              <span id="consent-third-title">ಪ್ರಕ್ರಿಯೆಗೊಳಿಸುವವರು ಯಾರು?</span>
            </div>
            <p id="consent-third-desc" class="text-slate-600 leading-relaxed">
              ಸರ್ವಮ್ ಎಐ (Sarvam AI — ಕನ್ನಡ ASR/TTS) ಮತ್ತು ಗ್ರೋಕ್ (Groq — ಭಾಷಾ ಮಾದರಿ).
            </p>
          </div>

          <div class="p-3 rounded-2xl bg-emerald-50/80 border border-emerald-200 shadow-2xs">
            <div class="font-bold text-emerald-950 flex items-center gap-1.5 mb-0.5">
              <span class="material-symbols-outlined text-emerald-700 text-sm">security</span>
              <span id="consent-retention-title">ಡೇಟಾ ಉಳಿಸುವಿಕೆ & ಭದ್ರತೆ:</span>
            </div>
            <p id="consent-retention-desc" class="text-emerald-900 leading-relaxed">
              ಆಡಿಯೋವನ್ನು ತಾತ್ಕಾಲಿಕ ಮೆಮೊರಿಯಲ್ಲಿ ಮಾತ್ರ ಸಂಸ್ಕರಿಸಲಾಗುತ್ತದೆ. ಎಂದಿಗೂ ಡಿಸ್ಕ್ ಅಥವಾ ಡೇಟಾಬೇಸ್‌ನಲ್ಲಿ ಉಳಿಸುವುದಿಲ್ಲ.
            </p>
          </div>

          <div class="p-3 rounded-2xl bg-white border border-slate-200/90 shadow-2xs">
            <div class="font-bold text-slate-900 flex items-center gap-1.5 mb-0.5">
              <span class="material-symbols-outlined text-emerald-700 text-sm">cancel</span>
              <span id="consent-revocation-title">ಹಿಂಪಡೆಯುವ ಹಕ್ಕು:</span>
            </div>
            <p id="consent-revocation-desc" class="text-slate-600 leading-relaxed">
              ಯಾವುದೇ ಸಮಯದಲ್ಲಿ ಸೆಟ್ಟಿಂಗ್ಸ್‌ನಲ್ಲಿ ಈ ಅನುಮತಿಯನ್ನು ಹಿಂಪಡೆಯಬಹುದು ಅಥವಾ ಡೇಟಾ ಅಳಿಸಬಹುದು.
            </p>
          </div>
        </div>

        <div class="flex items-center gap-3">
          <button id="consent-btn-deny" type="button"
            class="flex-1 min-h-[50px] py-3 px-4 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition-colors flex items-center justify-center cursor-pointer">
            <span id="consent-deny-text">ಬೇಡ (No thanks)</span>
          </button>
          <button id="consent-btn-allow" type="button"
            class="flex-1 min-h-[50px] py-3 px-4 rounded-xl bg-[#1B5E20] hover:bg-[#2E7D32] text-white font-bold text-xs shadow-md hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer active:scale-[0.99]">
            <span class="material-symbols-outlined text-base">check</span>
            <span id="consent-allow-text">ಒಪ್ಪಿಗೆ ನೀಡಿ (Allow Voice)</span>
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('consent-btn-allow').addEventListener('click', handleConsentAllow);
    document.getElementById('consent-btn-deny').addEventListener('click', handleConsentDeny);
  }

  function injectSettingsDrawerHTML() {
    if (document.getElementById('krishi-settings-modal')) return;

    const modal = document.createElement('div');
    modal.id = 'krishi-settings-modal';
    modal.className = 'fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm hidden';
    modal.innerHTML = `
      <div class="bg-[#FAF8F5] text-slate-900 rounded-3xl shadow-2xl max-w-md w-full p-6 sm:p-8 border border-slate-200 relative">
        <button id="settings-modal-close" type="button" class="absolute top-5 right-5 text-slate-400 hover:text-slate-700 w-8 h-8 rounded-full flex items-center justify-center hover:bg-slate-200/60 transition-colors">
          <span class="material-symbols-outlined text-lg">close</span>
        </button>

        <div class="flex items-center gap-3 mb-5">
          <div class="w-10 h-10 rounded-xl bg-[#1B5E20] text-white flex items-center justify-center shadow-md shrink-0">
            <span class="material-symbols-outlined text-xl">tune</span>
          </div>
          <div>
            <h2 id="settings-title" class="font-heading font-extrabold text-lg text-slate-900">
              ಗೌಪ್ಯತೆ ಮತ್ತು ಸೆಟ್ಟಿಂಗ್ಸ್ (Privacy Settings)
            </h2>
          </div>
        </div>

        <div class="space-y-4 text-xs">
          <!-- Voice Consent Status -->
          <div class="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-2xs space-y-2.5">
            <div class="flex items-center justify-between">
              <span id="settings-voice-label" class="font-bold text-slate-800">ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್ ಸ್ಥಿತಿ:</span>
              <span id="settings-voice-badge" class="px-2 py-0.5 rounded text-[11px] font-bold"></span>
            </div>
            <button id="settings-withdraw-btn" type="button"
              class="w-full py-2 px-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors flex items-center justify-center gap-1.5">
              <span class="material-symbols-outlined text-sm">block</span>
              <span id="settings-withdraw-text">ಧ್ವನಿ ಅನುಮತಿ ಹಿಂಪಡೆಯಿರಿ</span>
            </button>
          </div>

          <!-- History Saving Toggle -->
          <div class="p-3.5 rounded-2xl bg-white border border-slate-200 shadow-2xs space-y-1.5">
            <div class="flex items-center justify-between">
              <label for="settings-history-toggle" id="settings-history-label" class="font-bold text-slate-800 cursor-pointer">
                ಸಂಭಾಷಣಾ ಇತಿಹಾಸ ಉಳಿಸಿ
              </label>
              <input id="settings-history-toggle" type="checkbox"
                class="w-5 h-5 rounded text-[#1B5E20] focus:ring-[#1B5E20] border-slate-300 cursor-pointer" />
            </div>
            <p id="settings-history-hint" class="text-[11px] text-slate-500 leading-relaxed">
              ಪೂರ್ವನಿಯೋಜಿತವಾಗಿ ಆಫ್ ಆಗಿದೆ. ಆನ್ ಮಾಡಿದರೆ ಮಾತ್ರ ಸಂಭಾಷಣಾ ವಿವರಗಳನ್ನು ಉಳಿಸಲಾಗುತ್ತದೆ.
            </p>
          </div>

          <!-- Delete My Data -->
          <div class="p-3.5 rounded-2xl bg-rose-50/70 border border-rose-200/80 shadow-2xs space-y-2">
            <div class="font-bold text-rose-950 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-sm text-rose-700">delete_forever</span>
              <span>ಡಿಪಿಡಿಪಿ ಡೇಟಾ ಅಳಿಸುವಿಕೆ (Right to Erasure)</span>
            </div>
            <button id="settings-delete-btn" type="button"
              class="w-full py-2.5 px-3 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs transition-colors shadow-xs flex items-center justify-center gap-1.5 cursor-pointer">
              <span class="material-symbols-outlined text-sm">delete</span>
              <span id="settings-delete-text">ನನ್ನ ಎಲ್ಲಾ ಡೇಟಾ ಅಳಿಸಿ (Delete My Data)</span>
            </button>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('settings-modal-close').addEventListener('click', hideSettingsPanel);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) hideSettingsPanel();
    });

    document.getElementById('settings-withdraw-btn').addEventListener('click', async () => {
      const lang = getLang();
      const t = i18n[lang] || i18n.kn;
      try {
        await withdrawVoiceConsent();
        alert(t.withdrawnSuccess);
      } catch (e) {
        alert(e.message);
      }
    });

    document.getElementById('settings-history-toggle').addEventListener('change', async (e) => {
      await updateHistoryPreference(e.target.checked);
    });

    document.getElementById('settings-delete-btn').addEventListener('click', async () => {
      const lang = getLang();
      const t = i18n[lang] || i18n.kn;
      if (confirm(t.deleteConfirm)) {
        try {
          await deleteUserData();
          alert(t.deleteSuccess);
          hideSettingsPanel();
          if (typeof startNewChat === 'function') startNewChat();
        } catch (e) {
          alert(e.message);
        }
      }
    });
  }

  function updateConsentModalLang() {
    const lang = getLang();
    const t = i18n[lang] || i18n.kn;

    const elTitle = document.getElementById('consent-modal-title');
    const elSub = document.getElementById('consent-modal-subtitle');
    const elWhatT = document.getElementById('consent-what-title');
    const elWhatD = document.getElementById('consent-what-desc');
    const elWhyT = document.getElementById('consent-why-title');
    const elWhyD = document.getElementById('consent-why-desc');
    const elThirdT = document.getElementById('consent-third-title');
    const elThirdD = document.getElementById('consent-third-desc');
    const elRetT = document.getElementById('consent-retention-title');
    const elRetD = document.getElementById('consent-retention-desc');
    const elRevT = document.getElementById('consent-revocation-title');
    const elRevD = document.getElementById('consent-revocation-desc');
    const elAllow = document.getElementById('consent-allow-text');
    const elDeny = document.getElementById('consent-deny-text');

    if (elTitle) elTitle.textContent = t.modalTitle;
    if (elSub) elSub.textContent = t.modalSubtitle;
    if (elWhatT) elWhatT.textContent = t.whatTitle;
    if (elWhatD) elWhatD.textContent = t.whatDesc;
    if (elWhyT) elWhyT.textContent = t.whyTitle;
    if (elWhyD) elWhyD.textContent = t.whyDesc;
    if (elThirdT) elThirdT.textContent = t.thirdPartiesTitle;
    if (elThirdD) elThirdD.textContent = t.thirdPartiesDesc;
    if (elRetT) elRetT.textContent = t.retentionTitle;
    if (elRetD) elRetD.textContent = t.retentionDesc;
    if (elRevT) elRevT.textContent = t.revocationTitle;
    if (elRevD) elRevD.textContent = t.revocationDesc;
    if (elAllow) elAllow.textContent = t.allowBtn;
    if (elDeny) elDeny.textContent = t.denyBtn;
  }

  function renderSettingsUI() {
    const lang = getLang();
    const t = i18n[lang] || i18n.kn;

    const badge = document.getElementById('settings-voice-badge');
    const withdrawBtn = document.getElementById('settings-withdraw-btn');
    const historyToggle = document.getElementById('settings-history-toggle');

    if (badge) {
      if (_hasVoiceConsent) {
        badge.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-300';
        badge.textContent = t.voiceStatusActive;
        if (withdrawBtn) withdrawBtn.disabled = false;
      } else {
        badge.className = 'px-2 py-0.5 rounded text-[11px] font-bold bg-slate-100 text-slate-600 border border-slate-300';
        badge.textContent = t.voiceStatusInactive;
        if (withdrawBtn) withdrawBtn.disabled = true;
      }
    }
    if (historyToggle) {
      historyToggle.checked = Boolean(_saveHistory);
    }
  }

  function showConsentModal(callback) {
    injectConsentModalHTML();
    updateConsentModalLang();
    _consentDecisionCallback = callback || null;
    const modal = document.getElementById('krishi-consent-modal');
    if (modal) modal.classList.remove('hidden');
  }

  function hideConsentModal() {
    const modal = document.getElementById('krishi-consent-modal');
    if (modal) modal.classList.add('hidden');
  }

  function showSettingsPanel() {
    injectSettingsDrawerHTML();
    checkConsents();
    renderSettingsUI();
    const modal = document.getElementById('krishi-settings-modal');
    if (modal) modal.classList.remove('hidden');
  }

  function hideSettingsPanel() {
    const modal = document.getElementById('krishi-settings-modal');
    if (modal) modal.classList.add('hidden');
  }

  function handleConsentAllow() {
    hideConsentModal();
    if (_consentDecisionCallback) {
      const cb = _consentDecisionCallback;
      _consentDecisionCallback = null;
      cb(true);
    }
  }

  function handleConsentDeny() {
    hideConsentModal();
    if (_consentDecisionCallback) {
      const cb = _consentDecisionCallback;
      _consentDecisionCallback = null;
      cb(false);
    }
  }

  async function ensureVoiceConsent() {
    // 1. If already authenticated and active consent is granted, return true
    if (KrishiAuth.getToken()) {
      if (_hasVoiceConsent === null) {
        await checkConsents();
      }
      if (_hasVoiceConsent) {
        return true;
      }
    }

    // 2. Prompt consent modal FIRST (as required: "Before the FIRST call to getUserMedia, show a consent modal")
    return new Promise((resolve) => {
      showConsentModal(async (granted) => {
        if (!granted) {
          // User declined; text chat remains fully usable with no mic access
          resolve(false);
          return;
        }

        // User clicked "Allow"
        // Ensure user is authenticated to record consent on the server
        if (!KrishiAuth.getToken()) {
          KrishiAuth.showLoginModal(async () => {
            try {
              await grantVoiceConsent();
              resolve(true);
            } catch (err) {
              console.error('Consent grant failed after login:', err);
              alert(err.message || 'Failed to record consent');
              resolve(false);
            }
          });
        } else {
          try {
            await grantVoiceConsent();
            resolve(true);
          } catch (err) {
            console.error('Consent grant failed:', err);
            alert(err.message || 'Failed to record consent');
            resolve(false);
          }
        }
      });
    });
  }

  function init() {
    injectConsentModalHTML();
    injectSettingsDrawerHTML();
    checkConsents();
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  return {
    ensureVoiceConsent,
    showConsentModal,
    hideConsentModal,
    showSettingsPanel,
    hideSettingsPanel,
    grantVoiceConsent,
    withdrawVoiceConsent,
    updateHistoryPreference,
    deleteUserData,
    checkConsents,
    registerActiveStream,
    releaseMicrophone,
    hasVoiceConsent: () => Boolean(_hasVoiceConsent),
    init,
  };
})();

if (typeof window !== 'undefined') window.KrishiConsent = KrishiConsent;

// Krishi Mitra — Resilient Offline Connectivity, IndexedDB Outbox & App Shell Manager
const KrishiOffline = (() => {
  const DB_NAME = 'krishi_mitra_offline_db';
  const DB_VERSION = 1;
  const STORE_OUTBOX = 'outbox';
  const STORE_SESSIONS = 'session_cache';
  const STORE_EVALUATIONS = 'evaluations_cache';
  const STORE_FAQ = 'faq_cache';

  const LIMIT_MAX_DURATION_MS = 60_000;            // max 60s per clip
  const LIMIT_MAX_QUEUE_ITEMS = 10;                // max 10 queued items
  const LIMIT_MAX_TOTAL_BYTES = 20 * 1024 * 1024;  // 20 MB total
  const LIMIT_TTL_MS = 24 * 60 * 60 * 1000;        // 24 hours TTL

  let _db = null;
  let _state = 'online'; // 'online' | 'unstable' | 'offline'
  let _consecutiveHeartbeatFailures = 0;
  let _isProcessingOutbox = false;
  let _heartbeatTimer = null;
  let _faqData = null;

  const i18n = {
    kn: {
      onlineText: 'ಆನ್‌ಲೈನ್ (ಸಂಪರ್ಕಗೊಂಡಿದೆ)',
      unstableText: 'ನೆಟ್‌ವರ್ಕ್ ಅಸ್ಥಿರವಾಗಿದೆ — ಧ್ವನಿ ಸಂಸ್ಕರಣೆಯಲ್ಲಿ ವಿಳಂಬವಾಗಬಹುದು. ಆಫ್‌ಲೈನ್ ಕ್ಯೂ ಸಕ್ರಿಯವಾಗಿದೆ.',
      offlineText: 'ನೀವು ಆಫ್‌ಲೈನ್‌ನಲ್ಲಿದ್ದೀರಿ. ರೆಕಾರ್ಡಿಂಗ್‌ಗಳು ನಿಮ್ಮ ಮೊಬೈಲ್‌ನಲ್ಲಿ ಸುರಕ್ಷಿತವಾಗಿ ಉಳಿಯುತ್ತವೆ, ಇಂಟರ್ನೆಟ್ ಬಂದಾಗ ತಾನಾಗಿಯೇ ಕಳುಹಿಸಲಾಗುತ್ತದೆ.',
      outboxWaiting: 'ಕಳುಹಿಸಲು ಕಾಯಲಾಗುತ್ತಿದೆ (Waiting to send)',
      outboxRetry: 'ಈಗ ಕಳುಹಿಸಿ',
      outboxDelete: 'ಅಳಿಸಿ',
      outboxExpired: '24 ಗಂಟೆ ಮೀರಿದ್ದರಿಂದ ರೆಕಾರ್ಡಿಂಗ್ ರದ್ದಾಗಿದೆ.',
      offlineReadBadge: 'ಆಫ್‌ಲೈನ್ ಓದುವ ಮೋಡ್',
      offlineFaqTitle: 'ಆಫ್‌ಲೈನ್ ಮಾಹಿತಿ (ಹಳೆಯದಾಗಿರಬಹುದು)',
      offlineFaqNotice: 'ಎಐ ವಿಶ್ಲೇಷಣೆಗೆ ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕ ಅಗತ್ಯವಿದೆ. ಆಫ್‌ಲೈನ್‌ನಲ್ಲಿ ಸಂಗ್ರಹವಾಗಿರುವ ಸರ್ಕಾರಿ ಯೋಜನೆಗಳ ವಿವರಗಳನ್ನು ಕೆಳಗೆ ಓದಬಹುದು.',
      errDuration: 'ಧ್ವನಿ ರೆಕಾರ್ಡಿಂಗ್ ಗರಿಷ್ಠ 60 ಸೆಕೆಂಡ್‌ಗಿಂತ ಹೆಚ್ಚಾಗಿದೆ.',
      errQueueFull: 'ಆಫ್‌ಲೈನ್ ಕ್ಯೂ ಮಿತಿ (10 ಐಟಂಗಳು) ತಲುಪಿದೆ. ದಯವಿಟ್ಟು ನೆಟ್‌ವರ್ಕ್ ಬರುವವರೆಗೆ ಕಾಯಿರಿ.',
      errStorageFull: 'ಆಫ್‌ಲೈನ್ ಸಂಗ್ರಹ ಮಿತಿ (20 MB) ಮೀರಿದೆ.',
    },
    en: {
      onlineText: 'Online (Connected)',
      unstableText: 'Network is unstable — audio may experience delays. Offline queue active.',
      offlineText: 'You are offline. Your recording is safely saved on this device and will be sent automatically when online.',
      outboxWaiting: 'Waiting to send',
      outboxRetry: 'Retry Now',
      outboxDelete: 'Delete',
      outboxExpired: 'Queued item expired after 24 hours.',
      offlineReadBadge: 'Offline Read-Only Mode',
      offlineFaqTitle: 'Offline Help (May be outdated)',
      offlineFaqNotice: 'AI generation requires an active network. Stored government scheme reference guidelines are available below.',
      errDuration: 'Voice recording exceeds maximum duration limit of 60 seconds.',
      errQueueFull: 'Offline queue limit reached (maximum 10 items). Please wait for network to clear pending items.',
      errStorageFull: 'Offline storage limit (20 MB) exceeded.',
    }
  };

  function getLang() {
    if (typeof currentLanguage !== 'undefined' && currentLanguage) return currentLanguage;
    if (typeof currentLang !== 'undefined' && currentLang) return currentLang;
    return 'kn';
  }

  function openDB() {
    if (_db) return Promise.resolve(_db);
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(STORE_OUTBOX)) {
          db.createObjectStore(STORE_OUTBOX, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(STORE_SESSIONS)) {
          db.createObjectStore(STORE_SESSIONS, { keyPath: 'session_id' });
        }
        if (!db.objectStoreNames.contains(STORE_EVALUATIONS)) {
          db.createObjectStore(STORE_EVALUATIONS, { keyPath: 'id' });
        }
        if (!db.objectStoreNames.contains(STORE_FAQ)) {
          db.createObjectStore(STORE_FAQ, { keyPath: 'id' });
        }
      };
      request.onsuccess = (e) => {
        _db = e.target.result;
        resolve(_db);
      };
      request.onerror = (e) => reject(e.target.error);
    });
  }

  function putInStore(storeName, item) {
    return openDB().then(db => {
      return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);
        const req = store.put(item);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
    });
  }

  function getFromStore(storeName, key) {
    return openDB().then(db => {
      return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, 'readonly');
        const store = tx.objectStore(storeName);
        const req = store.get(key);
        req.onsuccess = () => resolve(req.result);
        req.onerror = () => reject(req.error);
      });
    });
  }

  function getAllFromStore(storeName) {
    return openDB().then(db => {
      return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, 'readonly');
        const store = tx.objectStore(storeName);
        const req = store.getAll();
        req.onsuccess = () => resolve(req.result || []);
        req.onerror = () => reject(req.error);
      });
    });
  }

  function deleteFromStore(storeName, key) {
    return openDB().then(db => {
      return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);
        const req = store.delete(key);
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
      });
    });
  }

  function clearStore(storeName) {
    return openDB().then(db => {
      return new Promise((resolve, reject) => {
        const tx = db.transaction(storeName, 'readwrite');
        const store = tx.objectStore(storeName);
        const req = store.clear();
        req.onsuccess = () => resolve();
        req.onerror = () => reject(req.error);
      });
    });
  }

  async function checkHeartbeat() {
    const wasOnline = navigator.onLine;
    if (!wasOnline) {
      setConnectivityState('offline');
      return;
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3500);
    const start = performance.now();

    try {
      const res = await fetch('/api/health', {
        method: 'GET',
        cache: 'no-store',
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const latency = performance.now() - start;

      if (res.ok) {
        _consecutiveHeartbeatFailures = 0;
        if (latency > 2500) {
          setConnectivityState('unstable');
        } else {
          setConnectivityState('online');
        }
      } else {
        _consecutiveHeartbeatFailures++;
        setConnectivityState(_consecutiveHeartbeatFailures >= 2 ? 'offline' : 'unstable');
      }
    } catch (e) {
      clearTimeout(timeout);
      _consecutiveHeartbeatFailures++;
      setConnectivityState(_consecutiveHeartbeatFailures >= 2 ? 'offline' : 'unstable');
    }
  }

  function setConnectivityState(newState) {
    if (_state === newState) return;
    const oldState = _state;
    _state = newState;
    renderConnectivityBanner();
    window.dispatchEvent(new CustomEvent('krishi:connectivity', {
      detail: { state: _state, previousState: oldState }
    }));
    if (_state === 'online') {
      processOutbox();
    }
  }

  function injectConnectivityBannerHTML() {
    if (document.getElementById('krishi-connectivity-banner')) return;
    const banner = document.createElement('div');
    banner.id = 'krishi-connectivity-banner';
    banner.className = 'hidden transition-all duration-300 w-full z-40 text-xs px-4 py-2.5 font-medium flex items-center justify-between shadow-xs border-b';
    banner.innerHTML = `
      <div class="flex items-center gap-2 max-w-4xl mx-auto w-full">
        <span id="connectivity-icon" class="material-symbols-outlined text-base"></span>
        <span id="connectivity-text" class="flex-1 font-semibold leading-tight"></span>
        <span id="connectivity-badge" class="px-2 py-0.5 rounded text-[10px] font-bold font-mono"></span>
      </div>
    `;

    const topHeader = document.querySelector('header, .krishi-nav, #chat-top-brand')?.closest('div.border-b');
    if (topHeader && topHeader.parentNode) {
      topHeader.parentNode.insertBefore(banner, topHeader.nextSibling);
    } else {
      document.body.prepend(banner);
    }
  }

  function renderConnectivityBanner() {
    const banner = document.getElementById('krishi-connectivity-banner');
    if (!banner) return;
    const icon = document.getElementById('connectivity-icon');
    const text = document.getElementById('connectivity-text');
    const badge = document.getElementById('connectivity-badge');
    const lang = getLang();
    const t = i18n[lang] || i18n.kn;

    if (_state === 'online') {
      banner.classList.add('hidden');
    } else if (_state === 'unstable') {
      banner.classList.remove('hidden');
      banner.className = 'w-full z-40 text-xs px-4 py-2.5 font-medium flex items-center justify-between shadow-xs border-b bg-amber-500/15 border-amber-500/40 text-amber-950 backdrop-blur-md animate-slide-down';
      if (icon) {
        icon.className = 'material-symbols-outlined text-base text-amber-600 animate-pulse';
        icon.textContent = 'wifi_protected_setup';
      }
      if (text) text.textContent = t.unstableText;
      if (badge) {
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-amber-200 text-amber-900 border border-amber-300';
        badge.textContent = 'UNSTABLE';
      }
    } else {
      banner.classList.remove('hidden');
      banner.className = 'w-full z-40 text-xs px-4 py-2.5 font-medium flex items-center justify-between shadow-xs border-b bg-rose-600/15 border-rose-500/40 text-rose-950 backdrop-blur-md animate-slide-down';
      if (icon) {
        icon.className = 'material-symbols-outlined text-base text-rose-600';
        icon.textContent = 'cloud_off';
      }
      if (text) text.textContent = t.offlineText;
      if (badge) {
        badge.className = 'px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-rose-200 text-rose-900 border border-rose-300';
        badge.textContent = 'OFFLINE';
      }
    }
  }

  function generateUUID() {
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      return crypto.randomUUID();
    }
    return 'km_' + Date.now().toString(36) + '_' + Math.random().toString(36).substring(2, 10);
  }

  async function enqueueVoiceClip({
    id = generateUUID(),
    sessionId,
    audioBase64,
    mimeType = 'audio/webm',
    durationMs = 0,
    language = getLang(),
    transcript = null
  }) {
    const lang = getLang();
    if (durationMs > LIMIT_MAX_DURATION_MS) {
      throw new Error(i18n[lang].errDuration);
    }

    const items = await getAllFromStore(STORE_OUTBOX);
    if (items.length >= LIMIT_MAX_QUEUE_ITEMS) {
      throw new Error(i18n[lang].errQueueFull);
    }

    const itemBytes = (audioBase64 ? audioBase64.length : 0) + 1024;
    const totalBytes = items.reduce((sum, it) => sum + (it.audio_base64 ? it.audio_base64.length : (it.message ? it.message.length : 0)), 0);
    if (totalBytes + itemBytes > LIMIT_MAX_TOTAL_BYTES) {
      throw new Error(i18n[lang].errStorageFull);
    }

    const item = {
      id,
      type: 'voice',
      session_id: sessionId,
      audio_base64: audioBase64,
      mime_type: mimeType,
      duration_ms: durationMs,
      language,
      transcript,
      created_at: Date.now(),
      attempts: 0,
      status: 'pending', // 'pending' | 'sending' | 'pending-confirmation' | 'failed'
      error_message: null
    };

    await putInStore(STORE_OUTBOX, item);
    window.dispatchEvent(new CustomEvent('krishi:outbox-updated', { detail: { item, action: 'enqueue' } }));
    return item;
  }

  async function enqueueChatMessage({
    id = generateUUID(),
    sessionId,
    message,
    language = getLang()
  }) {
    const lang = getLang();
    const items = await getAllFromStore(STORE_OUTBOX);
    if (items.length >= LIMIT_MAX_QUEUE_ITEMS) {
      throw new Error(i18n[lang].errQueueFull);
    }

    const item = {
      id,
      type: 'chat',
      session_id: sessionId,
      message,
      language,
      created_at: Date.now(),
      attempts: 0,
      status: 'pending',
      error_message: null
    };

    await putInStore(STORE_OUTBOX, item);
    window.dispatchEvent(new CustomEvent('krishi:outbox-updated', { detail: { item, action: 'enqueue' } }));
    return item;
  }

  async function processOutbox() {
    if (_isProcessingOutbox || _state !== 'online') return;
    _isProcessingOutbox = true;

    try {
      const allItems = await getAllFromStore(STORE_OUTBOX);
      if (!allItems.length) {
        _isProcessingOutbox = false;
        return;
      }

      const now = Date.now();
      const validItems = [];
      for (const item of allItems) {
        if (now - item.created_at > LIMIT_TTL_MS) {
          await deleteFromStore(STORE_OUTBOX, item.id);
          window.dispatchEvent(new CustomEvent('krishi:outbox-item-expired', { detail: { item } }));
        } else {
          validItems.push(item);
        }
      }

      validItems.sort((a, b) => a.created_at - b.created_at);

      for (const item of validItems) {
        if (_state === 'offline') break;
        if (item.status === 'failed' && item.attempts >= 5) continue;

        // 1. Pre-flight auth check
        if (!KrishiAuth.getToken()) {
          const refreshed = await KrishiAuth.refreshToken();
          if (!refreshed) {
            console.warn('[outbox] User not authenticated; pausing outbox queue');
            break;
          }
        }

        // 2. Pre-flight consent check for voice items
        if (item.type === 'voice') {
          await KrishiConsent.checkConsents();
          if (!KrishiConsent.hasVoiceConsent()) {
            console.warn('[outbox] Voice consent not active; purging voice queue');
            await purgeVoiceQueue();
            break;
          }
        }

        item.status = 'sending';
        await putInStore(STORE_OUTBOX, item);
        window.dispatchEvent(new CustomEvent('krishi:outbox-updated', { detail: { item, action: 'status_change' } }));

        try {
          let responseData = null;
          if (item.type === 'voice') {
            const res = await KrishiAuth.fetchWithAuth('/api/voice-turn', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Idempotency-Key': item.id
              },
              body: JSON.stringify({
                session_id: item.session_id,
                audio: item.audio_base64,
                mime_type: item.mime_type,
                recording_duration_ms: item.duration_ms,
                language: item.language
              })
            });

            if (!res.ok) {
              const errData = await res.json().catch(() => ({}));
              throw new Error(errData.detail?.message || errData.detail || ('Voice API returned status ' + res.status));
            }
            responseData = await res.json();
          } else {
            const res = await KrishiAuth.fetchWithAuth('/api/chat', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Idempotency-Key': item.id
              },
              body: JSON.stringify({
                session_id: item.session_id,
                message: item.message,
                language: item.language
              })
            });

            if (!res.ok) {
              const errData = await res.json().catch(() => ({}));
              throw new Error(errData.detail?.message || errData.detail || ('Chat API returned status ' + res.status));
            }
            responseData = await res.json();
          }

          // Successfully processed!
          await deleteFromStore(STORE_OUTBOX, item.id);
          window.dispatchEvent(new CustomEvent('krishi:outbox-item-sent', {
            detail: { item, response: responseData }
          }));

        } catch (err) {
          console.warn('[outbox] send failed for item', item.id, err);
          item.attempts = (item.attempts || 0) + 1;
          item.status = item.attempts >= 5 ? 'failed' : 'pending';
          item.error_message = err.message || 'Network request failed';
          await putInStore(STORE_OUTBOX, item);
          window.dispatchEvent(new CustomEvent('krishi:outbox-updated', { detail: { item, action: 'error' } }));

          const backoffBase = (typeof window !== 'undefined' && window.__KRISHI_TEST_FAST_RETRY__) ? 10 : 1000;
          const delay = Math.min(backoffBase * Math.pow(2, item.attempts) + Math.random() * (backoffBase / 2), 10000);
          await new Promise(r => setTimeout(r, delay));
        }
      }
    } finally {
      _isProcessingOutbox = false;
    }
  }

  async function retryOutboxItem(id) {
    const item = await getFromStore(STORE_OUTBOX, id);
    if (!item) return;
    item.attempts = 0;
    item.status = 'pending';
    item.error_message = null;
    await putInStore(STORE_OUTBOX, item);
    window.dispatchEvent(new CustomEvent('krishi:outbox-updated', { detail: { item, action: 'retry_queued' } }));
    if (_state === 'online') {
      processOutbox();
    }
  }

  async function deleteOutboxItem(id) {
    await deleteFromStore(STORE_OUTBOX, id);
    window.dispatchEvent(new CustomEvent('krishi:outbox-updated', { detail: { id, action: 'delete' } }));
  }

  async function purgeVoiceQueue() {
    const items = await getAllFromStore(STORE_OUTBOX);
    for (const item of items) {
      if (item.type === 'voice') {
        await deleteFromStore(STORE_OUTBOX, item.id);
      }
    }
    window.dispatchEvent(new CustomEvent('krishi:outbox-purged', { detail: { type: 'voice' } }));
  }

  async function clearAllData() {
    await clearStore(STORE_OUTBOX);
    await clearStore(STORE_SESSIONS);
    await clearStore(STORE_EVALUATIONS);
    window.dispatchEvent(new CustomEvent('krishi:outbox-cleared'));
  }

  async function saveSessionCache(sessionId, turns, profile = {}) {
    if (!sessionId) return;
    await putInStore(STORE_SESSIONS, {
      session_id: sessionId,
      turns: turns || [],
      profile: profile || {},
      cached_at: Date.now()
    });
  }

  async function getSessionCache(sessionId) {
    if (!sessionId) return null;
    return await getFromStore(STORE_SESSIONS, sessionId);
  }

  async function getLatestSessionCache() {
    const sessions = await getAllFromStore(STORE_SESSIONS);
    if (!sessions.length) return null;
    sessions.sort((a, b) => (b.cached_at || 0) - (a.cached_at || 0));
    return sessions[0];
  }

  async function saveEvaluationsCache(evaluations) {
    if (!Array.isArray(evaluations) || !evaluations.length) return;
    for (const ev of evaluations) {
      const id = ev.scheme_id || ev.id || ('ev_' + Math.random().toString(36).substring(2, 9));
      await putInStore(STORE_EVALUATIONS, { id, data: ev, cached_at: Date.now() });
    }
  }

  async function getCachedEvaluations() {
    const items = await getAllFromStore(STORE_EVALUATIONS);
    return items.map(it => it.data);
  }

  async function loadOfflineFAQ() {
    if (_faqData) return _faqData;
    try {
      const res = await fetch('/offline_faq.json');
      if (res.ok) {
        _faqData = await res.json();
        return _faqData;
      }
    } catch (e) {
      console.warn('Failed to fetch offline_faq.json', e);
    }
    return null;
  }

  function init() {
    injectConnectivityBannerHTML();
    openDB().catch(e => console.warn('IndexedDB init warning', e));

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(err => {
        console.warn('[sw] registration failed', err);
      });
    }

    window.addEventListener('online', () => checkHeartbeat());
    window.addEventListener('offline', () => setConnectivityState('offline'));

    checkHeartbeat();
    _heartbeatTimer = setInterval(checkHeartbeat, 5000);
    if (_heartbeatTimer && typeof _heartbeatTimer.unref === 'function') {
      _heartbeatTimer.unref();
    }
  }

  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', init);
    } else {
      init();
    }
  }

  return {
    getState: () => _state,
    setConnectivityState,
    checkHeartbeat,
    openDB,
    enqueueVoiceClip,
    enqueueChatMessage,
    getOutboxItems: () => getAllFromStore(STORE_OUTBOX),
    getOutboxItem: (id) => getFromStore(STORE_OUTBOX, id),
    retryOutboxItem,
    deleteOutboxItem,
    purgeVoiceQueue,
    clearAllData,
    processOutbox,
    saveSessionCache,
    getSessionCache,
    getLatestSessionCache,
    saveEvaluationsCache,
    getCachedEvaluations,
    loadOfflineFAQ,
    renderConnectivityBanner,
    generateUUID,
    init,
  };
})();

if (typeof window !== 'undefined') window.KrishiOffline = KrishiOffline;



(() => {
  const microphoneSoundThreshold = 0.001;

  const profileDefaults = () => ({
    district: null,
    land_acres: null,
    ownership: null,
    crops: [],
    season: null,
    risk_type: null,
    irrigation_type: null,
    has_water_source: null,
    availed_drip_subsidy_last_3_years: null,
    requested_equipment: null,
    equipment_cost_inr: null,
    has_soil_health_card: null,
    soil_deficiencies: [],
    is_income_tax_payee: null,
    is_institutional_landholder: null,
    is_constitutional_post_holder: null,
    is_government_employee: null,
  });

  function makeElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  }

  function postJson(path, payload) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 50000);
    return KrishiAuth.fetchWithAuth(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    }).then(async response => {
      const data = await response.json();
      const requestId = response.headers.get('X-Request-ID');
      if (!response.ok) {
        const reference = requestId ? ` (reference: ${requestId})` : '';
        const error = new Error(
          `${data.error || `Request failed (${response.status}).`}${reference}`,
        );
        error.status = response.status;
        throw error;
      }
      if (requestId) data.requestId = requestId;
      return data;
    }).catch(error => {
      if (controller.signal.aborted) {
        throw new Error('The request took too long. Check your connection and try again.');
      }
      throw error;
    }).finally(() => clearTimeout(timeout));
  }

  function schemeCard(result, lang) {
    const demo = result.is_demo;
    const ineligible = result.status === 'INELIGIBLE';
    const conditional = result.status === 'CONDITIONALLY_ELIGIBLE';
    const informational = result.status === 'INFORMATIONAL';
    const tone = demo ? 'amber' : ineligible ? 'rose' : conditional || informational ? 'blue' : 'emerald';
    const styles = {
      amber: { border: 'border-amber-500/70', badge: 'bg-amber-950 text-amber-300 border-amber-800', summary: 'text-amber-200' },
      rose: { border: 'border-rose-500/70', badge: 'bg-rose-950 text-rose-300 border-rose-800', summary: 'text-rose-200' },
      blue: { border: 'border-blue-500/70', badge: 'bg-blue-950 text-blue-300 border-blue-800', summary: 'text-blue-200' },
      emerald: { border: 'border-emerald-500/70', badge: 'bg-emerald-950 text-emerald-300 border-emerald-800', summary: 'text-emerald-200' },
    }[tone];
    const card = makeElement('section', `p-4 bg-slate-900 border-2 ${styles.border} rounded-2xl space-y-2`);
    const header = makeElement('div', 'flex justify-between items-start gap-3');
    const title = makeElement('h3', 'font-bold text-sm text-white',
      `${lang === 'kn' ? result.scheme_name_kn : result.scheme_name_en}${demo ? ' [DEMO / TEST CASE]' : ''}`);
    const badge = makeElement('span', `px-2 py-0.5 rounded ${styles.badge} border text-[10px] font-bold shrink-0`,
      result.status.replaceAll('_', ' '));
    header.append(title, badge);
    card.append(header);

    const summary = lang === 'kn' ? result.benefit_summary_kn : result.benefit_summary_en;
    card.appendChild(makeElement('p', `text-xs ${styles.summary} font-semibold`, summary));

    if (result.missing_information?.length) {
      card.appendChild(makeElement('p', 'text-[11px] text-blue-200',
        `${lang === 'kn' ? 'ಮತ್ತಷ್ಟು ಮಾಹಿತಿ ಬೇಕು' : 'Information still needed'}: ${result.missing_information.join(', ')}`));
    }

    for (const [label, items] of [
      [lang === 'kn' ? 'ಕಾರಣಗಳು' : 'Reasons', result.disqualification_reasons],
      [lang === 'kn' ? 'ದಾಖಲೆಗಳು' : 'Documents to prepare',
        (result.required_documents || []).map(doc => lang === 'kn' ? doc.name_kn : doc.name_en)],
      [lang === 'kn' ? 'ನಿಯಮ ಪರಿಶೀಲನೆ' : 'Rule audit', result.audit_trail],
    ]) {
      if (!items?.length) continue;
      const details = makeElement('details', 'text-[11px] text-slate-400');
      details.appendChild(makeElement('summary', 'cursor-pointer', label));
      const list = makeElement('ul', 'list-disc list-inside mt-1 space-y-1');
      items.forEach(item => list.appendChild(makeElement('li', '', item)));
      details.appendChild(list);
      card.appendChild(details);
    }

    const disclaimer = demo
      ? (lang === 'kn' ? result.disclaimer_kn : result.disclaimer_en)
      : (lang === 'kn'
        ? 'ಇದು ಅಧಿಕೃತ ಅರ್ಹತಾ ನಿರ್ಧಾರವಲ್ಲ. ಪ್ರಸ್ತುತ ನಿಯಮಗಳು ಮತ್ತು ಅರ್ಜಿ ಸ್ಥಿತಿಯನ್ನು ಸಂಬಂಧಿತ ಇಲಾಖೆಯಲ್ಲಿ ದೃಢಪಡಿಸಿ.'
        : result.disclaimer_en);
    if (disclaimer) card.appendChild(makeElement('p', 'text-[10px] text-slate-500', disclaimer));

    if (result.last_researched) {
      card.appendChild(makeElement(
        'p',
        'text-[10px] text-slate-500',
        `${lang === 'kn' ? 'ಮೂಲಗಳನ್ನು ಪರಿಶೀಲಿಸಿದ ದಿನಾಂಕ' : 'Sources checked'}: ${result.last_researched}`,
      ));
    }
    if (Array.isArray(result.sources) && result.sources.length) {
      const sourceList = makeElement('div', 'flex flex-wrap gap-x-3 gap-y-1 text-[11px]');
      result.sources.forEach(source => {
        if (typeof source.url !== 'string' || !source.url.startsWith('https://')) return;
        const link = makeElement(
          'a',
          'text-emerald-300 underline underline-offset-2 hover:text-emerald-200',
          source.label,
        );
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        sourceList.appendChild(link);
      });
      if (sourceList.childElementCount) card.appendChild(sourceList);
    }
    return card;
  }

  if (document.getElementById('form-results-container')) {
    const resultsContainer = document.getElementById('form-results-container');
    const status = makeElement('p', 'text-xs text-slate-400');
    resultsContainer.appendChild(status);

    const evaluateForm = async () => {
      const dist = document.getElementById('form-dist').value;
      const acres = Number(document.getElementById('form-land-slider').value);
      const crop = document.getElementById('form-crop').value;
      const cropIndex = document.getElementById('form-crop').selectedIndex;
      const irrigation = document.getElementById('form-irrig').value;
      const calamity = document.getElementById('form-calamity').value;
      const need = document.getElementById('form-need').value;
      const ownership = document.getElementById('form-ownership')?.value || null;
      const tax = document.getElementById('form-taxpayer')?.value;
      const governmentEmployee = document.getElementById('form-government-employee')?.value;
      const institutional = document.getElementById('form-institutional')?.value;
      const constitutional = document.getElementById('form-constitutional')?.value;
      const hasSoilCard = document.getElementById('form-soil-card')?.value;
      const soilDeficiency = document.getElementById('form-soil-deficiency')?.value;
      const dripCooldown = document.getElementById('form-drip-cooldown')?.value;
      const canonicalCrop = typeof AGRO_DATA !== 'undefined'
        ? (AGRO_DATA[dist]?.cropsEn?.[cropIndex] || crop)
        : crop;
      const profile = {
        district: dist,
        land_acres: acres,
        ownership,
        crops: canonicalCrop ? [canonicalCrop] : [],
        season: document.getElementById('form-season')?.value || null,
        irrigation_type: irrigation,
        has_water_source: irrigation !== 'Rainfed',
        risk_type: calamity === 'None' ? null : calamity,
        requested_equipment: need === 'Equipment' ? 'Power Tiller' : null,
        has_soil_health_card: hasSoilCard === '' || hasSoilCard === undefined
          ? null : hasSoilCard === 'true',
        soil_deficiencies: soilDeficiency ? [soilDeficiency] : [],
        availed_drip_subsidy_last_3_years: dripCooldown === '' || dripCooldown === undefined
          ? null : dripCooldown === 'true',
        is_income_tax_payee: tax === '' ? null : tax === 'true',
        is_government_employee: governmentEmployee === '' ? null : governmentEmployee === 'true',
        is_institutional_landholder: institutional === '' ? null : institutional === 'true',
        is_constitutional_post_holder: constitutional === '' ? null : constitutional === 'true',
      };
      const button = document.getElementById('form-btn-eval');
      button.disabled = true;
      status.textContent = currentLang === 'kn' ? 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ…' : 'Checking with the rule engine…';
      Array.from(resultsContainer.children).forEach(child => {
        if (child !== status) child.remove();
      });
      try {
        const result = await postJson('/api/evaluate', { profile });
        result.evaluations.forEach(evaluation => {
          const card = schemeCard(evaluation, currentLang);
          card.dataset.evaluation = 'true';
          resultsContainer.appendChild(card);
        });
        status.textContent = currentLang === 'kn'
          ? 'ಪ್ರಾಥಮಿಕ ಪರಿಶೀಲನೆ ಮಾತ್ರ. ಇದು ಅಧಿಕೃತ ಅನುಮೋದನೆ ಅಲ್ಲ.'
          : 'Preliminary screening only; not an official approval.';
      } catch (error) {
        status.textContent = `${currentLang === 'kn' ? 'ದೋಷ' : 'Error'}: ${error.message}`;
      } finally {
        button.disabled = false;
      }
    };
    window.triggerManualFormEval = evaluateForm;
    document.getElementById('form-btn-eval').addEventListener('click', evaluateForm);
  }
})();

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    KrishiAuth: typeof KrishiAuth !== 'undefined' ? KrishiAuth : null,
    KrishiConsent: typeof KrishiConsent !== 'undefined' ? KrishiConsent : null,
    KrishiOffline: typeof KrishiOffline !== 'undefined' ? KrishiOffline : null,
  };
}
