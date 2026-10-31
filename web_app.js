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

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
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

window.KrishiAuth = KrishiAuth;

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

  if (document.getElementById('chat-input-form')) {
    let profile = profileDefaults();
    farmerProfile = profile;
    let busy = false;
    let voiceStarting = false;
    let recorder = null;
    let mediaStream = null;
    let voiceTimeout = null;
    let recordingInterval = null;
    let audioLevelInterval = null;
    let recordingStartedAt = null;
    let audioContext = null;
    let audioAnalyser = null;
    let preferredAudioInputId = localStorage.getItem('krishi_audio_input') || '';
    let audioInputDevices = [];
    const stream = document.getElementById('chat-stream');
    const input = document.getElementById('user-text-input');
    const micButton = document.getElementById('mic-trigger-btn');
    const micModal = document.getElementById('waveform-modal');
    const audioInputControl = document.getElementById('audio-input-control');
    const audioInputSelect = document.getElementById('audio-input-select');
    const audioInputLabel = document.getElementById('audio-input-label');
    const micIcon = document.getElementById('mic-icon');
    const serviceStatus = document.getElementById('service-status');
    const serviceStatusText = document.getElementById('service-status-text');
    const loadingSpinner = document.getElementById('loading-spinner');
    const form = document.getElementById('chat-input-form');
    const submitButton = form.querySelector('button[type="submit"]');

    function setServiceStatus(text, loading = false) {
      serviceStatusText.textContent = text;
      loadingSpinner.classList.toggle('hidden', !loading);
      serviceStatus.setAttribute('aria-busy', String(loading));
    }

    async function refreshAudioInputs() {
      if (!navigator.mediaDevices?.enumerateDevices || !audioInputSelect) return;
      try {
        const devices = (await navigator.mediaDevices.enumerateDevices())
          .filter(device => device.kind === 'audioinput');
        audioInputDevices = devices;
        audioInputSelect.replaceChildren();
        audioInputLabel.textContent = currentLanguage === 'kn'
          ? 'ಇನ್‌ಪುಟ್ ಮೈಕ್'
          : 'Input microphone';
        devices.forEach((device, index) => {
          const option = document.createElement('option');
          option.value = device.deviceId;
          option.textContent = device.label
            || (currentLanguage === 'kn' ? `ಮೈಕ್ರೊಫೋನ್ ${index + 1}` : `Microphone ${index + 1}`);
          audioInputSelect.appendChild(option);
        });
        const preferredExists = devices.some(device => device.deviceId === preferredAudioInputId);
        if (!preferredExists) preferredAudioInputId = '';
        if (preferredAudioInputId) audioInputSelect.value = preferredAudioInputId;
        audioInputControl.classList.toggle('hidden', devices.length < 2);
      } catch (error) {
        console.warn('[voice] input device enumeration failed', { message: error.message });
      }
    }

    function microphoneSilenceMessage() {
      const selectedLabel = audioInputDevices.find(device =>
        device.deviceId === preferredAudioInputId)?.label
        || audioInputSelect?.selectedOptions?.[0]?.textContent
        || (currentLanguage === 'kn' ? 'ಆಯ್ಕೆ ಮಾಡಿದ ಮೈಕ್' : 'the selected microphone');
      const alternative = audioInputDevices.find(device =>
        device.deviceId !== preferredAudioInputId
        && /microphone array|microphone \(/i.test(device.label));
      const alternativeLabel = alternative?.label;
      if (currentLanguage === 'kn') {
        return alternativeLabel
          ? `"${selectedLabel}" ನಲ್ಲಿ ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. "ಇನ್‌ಪುಟ್ ಮೈಕ್" ನಲ್ಲಿ "${alternativeLabel}" ಆಯ್ಕೆಮಾಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.`
          : `"${selectedLabel}" ನಲ್ಲಿ ಧ್ವನಿ ಕೇಳಿಸಲಿಲ್ಲ. "ಇನ್‌ಪುಟ್ ಮೈಕ್" ನಲ್ಲಿ ಬೇರೆ ಮೈಕ್ ಆಯ್ಕೆಮಾಡಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.`;
      }
      return alternativeLabel
        ? `No sound was detected from "${selectedLabel}". Choose "${alternativeLabel}" in Input microphone and try again.`
        : `No sound was detected from "${selectedLabel}". Choose another input in Input microphone and try again.`;
    }

    function selectAlternativeMicrophone() {
      const alternatives = audioInputDevices.filter(device =>
        device.deviceId && device.deviceId !== preferredAudioInputId);
      const alternative = alternatives.find(device => /microphone array/i.test(device.label))
        || alternatives.find(device => /microphone/i.test(device.label))
        || alternatives[0];
      if (!alternative) return false;
      preferredAudioInputId = alternative.deviceId;
      if (preferredAudioInputId) {
        localStorage.setItem('krishi_audio_input', preferredAudioInputId);
      }
      if (audioInputSelect) audioInputSelect.value = preferredAudioInputId;
      return true;
    }

    function renderMessage(sender, text, evaluations = []) {
      const row = makeElement('div', sender === 'user'
        ? 'flex items-start justify-end gap-3 text-sm'
        : 'flex items-start gap-4 text-sm');
      row.dataset.chatMessage = 'true';
      row.dataset.chatRole = sender === 'user' ? 'user' : 'assistant';
      const avatar = makeElement('div', sender === 'user'
        ? 'w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center text-white shrink-0 mt-0.5'
        : 'w-10 h-10 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 flex items-center justify-center text-white shrink-0 shadow-md',
      sender === 'user' ? 'person' : 'smart_toy');
      avatar.classList.add('material-symbols-outlined');
      const bubble = makeElement(sender === 'user' ? 'p' : 'div', sender === 'user'
        ? 'bg-emerald-600 text-white rounded-3xl rounded-tr-sm px-5 py-3.5 max-w-[85%] shadow-md text-xs sm:text-sm whitespace-pre-wrap'
        : 'space-y-3 bg-[#151E2E] border border-slate-800/80 rounded-3xl rounded-tl-sm p-5 max-w-[90%] shadow-md text-slate-200',
      text);
      bubble.dataset.chatText = text;
      if (sender === 'user') row.append(bubble, avatar);
      else {
        row.append(avatar, bubble);
        evaluations.forEach(result => bubble.appendChild(schemeCard(result, currentLanguage)));
      }
      stream.appendChild(row);
      stream.scrollTop = stream.scrollHeight;
      return bubble;
    }

    function recentChatHistory() {
      return [...stream.querySelectorAll('[data-chat-message]')]
        .slice(-8)
        .map(row => ({
          role: row.dataset.chatRole,
          content: row.querySelector('[data-chat-text]')?.dataset.chatText || '',
        }));
    }

    function playGeneratedReply(bubble, result) {
      if (!result.audio || !result.mime_type) return false;
      try {
        const audioBytes = Uint8Array.from(
          atob(result.audio),
          character => character.charCodeAt(0),
        );
        const audioUrl = URL.createObjectURL(
          new Blob([audioBytes], { type: result.mime_type }),
        );
        const player = makeElement('audio', 'w-full mt-2');
        player.controls = true;
        player.src = audioUrl;
        player.addEventListener('ended', () => {
          URL.revokeObjectURL(audioUrl);
          setServiceStatus(result.model_mode);
        }, { once: true });
        player.addEventListener('error', () => {
          URL.revokeObjectURL(audioUrl);
          setServiceStatus(currentLanguage === 'kn'
            ? 'ಧ್ವನಿ ಪ್ಲೇ ಆಗಲಿಲ್ಲ. ಕೇಳಲು ಆಡಿಯೊ ನಿಯಂತ್ರಣ ಒತ್ತಿ.'
            : 'Audio could not play. Use the audio controls to retry.');
        }, { once: true });
        bubble.appendChild(player);
        setServiceStatus(
          currentLanguage === 'kn' ? 'ಉತ್ತರಿಸುತ್ತಿದೆ…' : 'Responding…',
          true,
        );
        player.play().catch(() => setServiceStatus(currentLanguage === 'kn'
          ? 'ಉತ್ತರ ಸಿದ್ಧವಾಗಿದೆ. ಕೇಳಲು ಆಡಿಯೊ ನಿಯಂತ್ರಣ ಒತ್ತಿ.'
          : 'Reply ready. Press the audio controls to hear it.'));
        return true;
      } catch (error) {
        console.error('[chat] audio playback setup failed', { message: error.message });
        return false;
      }
    }

    async function processFarmerQuery(message) {
      const text = message.trim();
      if (!text || busy) return;
      busy = true;
      const history = recentChatHistory();
      renderMessage('user', text);
      submitButton.disabled = true;
      submitButton.classList.add('opacity-50', 'cursor-wait');
      setServiceStatus(
        currentLanguage === 'kn' ? 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ…' : 'Thinking…',
        true,
      );
      try {
        const result = await postJson('/api/chat', {
          message: text,
          language: currentLanguage,
          profile,
          history,
        });
        profile = result.profile;
        farmerProfile = profile;
        const replyBubble = renderMessage(
          'bot',
          result.reply,
          result.show_evaluations ? result.evaluations : [],
        );
        setServiceStatus(result.model_mode);
        updateProfileBar();
        if (!playGeneratedReply(replyBubble, result)) {
          speakReply(result.reply, () => setServiceStatus(result.model_mode));
        }
      } catch (error) {
        renderMessage('bot', `${currentLanguage === 'kn' ? 'ದೋಷ' : 'Error'}: ${error.message}`);
        setServiceStatus(
          currentLanguage === 'kn' ? 'ಸೇವೆ ಲಭ್ಯವಿಲ್ಲ' : `Service unavailable: ${error.message}`,
        );
      } finally {
        busy = false;
        submitButton.disabled = false;
        submitButton.classList.remove('opacity-50', 'cursor-wait');
      }
    }

    function speakReply(text, onComplete) {
      if (!('speechSynthesis' in window) || !text) {
        onComplete?.();
        return;
      }
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = currentLanguage === 'kn' ? 'kn-IN' : 'en-IN';
      utterance.rate = 0.92;
      const languagePrefix = currentLanguage === 'kn' ? 'kn' : 'en';
      const voice = window.speechSynthesis.getVoices()
        .find(candidate => candidate.lang.toLowerCase().startsWith(languagePrefix));
      if (voice) utterance.voice = voice;
      else if (currentLanguage === 'kn') {
        setServiceStatus('ಕನ್ನಡ ಧ್ವನಿ ಲಭ್ಯವಿಲ್ಲ. ಬರಹದ ಉತ್ತರವನ್ನು ಓದಬಹುದು.');
        onComplete?.();
        return;
      }
      setServiceStatus(
        currentLanguage === 'kn' ? 'ಉತ್ತರಿಸುತ್ತಿದೆ…' : 'Responding…',
        true,
      );
      utterance.onend = () => onComplete?.();
      utterance.onerror = () => onComplete?.();
      window.speechSynthesis.speak(utterance);
    }

    function updateProfileBar() {
      document.getElementById('pill-district').textContent = profile.district || '—';
      document.getElementById('pill-land').textContent = profile.land_acres === null
        ? '—'
        : `${profile.land_acres}${currentLanguage === 'kn' ? ' ಎಕರೆ' : ' Acres'}`;
      document.getElementById('pill-crop').textContent = profile.crops.join(', ') || '—';
      document.getElementById('pill-status').textContent =
        profile.district || profile.land_acres !== null || profile.crops.length
          ? (currentLanguage === 'kn' ? 'ಪೂರ್ಣವಲ್ಲ' : 'Incomplete')
          : (currentLanguage === 'kn' ? 'ವಿವರಗಳಿಲ್ಲ' : 'No details');
    }

    function clearProfile() {
      profile = profileDefaults();
      farmerProfile = profile;
      stream.querySelectorAll('[data-chat-message="true"]').forEach(message => message.remove());
      updateProfileBar();
      setServiceStatus('');
    }

    function resetVoice() {
      clearTimeout(voiceTimeout);
      voiceTimeout = null;
      clearInterval(recordingInterval);
      recordingInterval = null;
      clearInterval(audioLevelInterval);
      audioLevelInterval = null;
      audioAnalyser = null;
      if (audioContext) {
        audioContext.close().catch(error => {
          console.warn('[voice] audio context close failed', { message: error.message });
        });
        audioContext = null;
      }
      recordingStartedAt = null;
      if (mediaStream) mediaStream.getTracks().forEach(track => track.stop());
      recorder = mediaStream = null;
      micModal.classList.add('hidden');
      micButton.classList.remove('bg-red-600', 'pulsing-ring');
      micButton.classList.add('bg-gradient-to-tr', 'from-emerald-600', 'to-teal-500');
      micButton.disabled = false;
      micIcon.textContent = 'mic';
    }

    function stopVoiceRecording(activeRecorder, reason, startedAt) {
      if (activeRecorder?.state !== 'recording') return;
      clearTimeout(voiceTimeout);
      voiceTimeout = null;
      clearInterval(recordingInterval);
      recordingInterval = null;
      console.info('[voice] recording stop requested', {
        reason,
        recordingDurationMs: startedAt ? Date.now() - startedAt : null,
      });
      if (reason === 'max_duration') {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಗರಿಷ್ಠ ಸಮಯ ಮುಗಿದಿದೆ. ಧ್ವನಿಯನ್ನು ಕಳುಹಿಸಲಾಗುತ್ತಿದೆ…'
          : 'Recording limit reached. Sending your audio…', true);
      }
      activeRecorder.stop();
    }

    async function blobToBase64(blob) {
      const bytes = new Uint8Array(await blob.arrayBuffer());
      let binary = '';
      for (let i = 0; i < bytes.length; i += 0x8000) {
        binary += String.fromCharCode(...bytes.subarray(i, Math.min(i + 0x8000, bytes.length)));
      }
      return btoa(binary);
    }

    async function processVoiceClip(blob, recordingDurationMs) {
      if (busy) return;
      busy = true;
      submitButton.disabled = true;
      micButton.disabled = true;
      submitButton.classList.add('opacity-50', 'cursor-wait');
      setServiceStatus(
        currentLanguage === 'kn' ? 'ಧ್ವನಿಯನ್ನು ಪ್ರಕ್ರಿಯೆಗೊಳಿಸಲಾಗುತ್ತಿದೆ…' : 'Processing your voice…',
        true,
      );
      try {
        const mimeType = blob.type.split(';')[0].toLowerCase();
        console.info('[voice] upload started', {
          mimeType,
          audioBytes: blob.size,
          recordingDurationMs,
        });
        const result = await postJson('/api/voice-turn', {
          audio: await blobToBase64(blob),
          mime_type: mimeType,
          recording_duration_ms: recordingDurationMs,
          language: currentLanguage,
          profile,
          history: recentChatHistory(),
        });
        console.info('[voice] turn completed', {
          requestId: result.requestId,
          transcriptChars: result.transcript.length,
          replyChars: result.reply.length,
          audioBase64Chars: result.audio.length,
        });
        setServiceStatus(
          currentLanguage === 'kn' ? 'ಉತ್ತರ ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ…' : 'Preparing your reply…',
          true,
        );
        profile = result.profile;
        farmerProfile = profile;
        renderMessage('user', result.transcript);
        const replyBubble = renderMessage(
          'bot',
          result.reply,
          result.show_evaluations ? result.evaluations : [],
        );
        updateProfileBar();

        const audioBytes = Uint8Array.from(atob(result.audio), character => character.charCodeAt(0));
        const audioUrl = URL.createObjectURL(new Blob([audioBytes], { type: result.mime_type }));
        const player = makeElement('audio', 'w-full mt-2');
        player.controls = true;
        player.src = audioUrl;
        player.addEventListener('ended', () => URL.revokeObjectURL(audioUrl), { once: true });
        player.addEventListener('error', () => {
          URL.revokeObjectURL(audioUrl);
          setServiceStatus(currentLanguage === 'kn'
            ? 'ಆಡಿಯೊ ಪ್ಲೇ ಆಗಲಿಲ್ಲ. ಮೇಲಿನ ನಿಯಂತ್ರಣವನ್ನು ಬಳಸಿ.'
            : 'Audio could not play. Use the audio controls to retry.');
        }, { once: true });
        replyBubble.appendChild(player);
        setServiceStatus(result.model_mode, true);
        try {
          await player.play();
        } catch {
          setServiceStatus(currentLanguage === 'kn'
            ? 'ಉತ್ತರ ಸಿದ್ಧವಾಗಿದೆ. ಕೇಳಲು ಆಡಿಯೊ ನಿಯಂತ್ರಣವನ್ನು ಒತ್ತಿ.'
            : 'Reply ready. Press the audio controls to hear it.');
        }
        player.addEventListener('ended', () => setServiceStatus(result.model_mode), { once: true });
      } catch (error) {
        console.error('[voice] turn failed', { message: error.message });
        if (error.status === 422 && selectAlternativeMicrophone()) {
          const nextInputLabel = audioInputDevices.find(device =>
            device.deviceId === preferredAudioInputId)?.label;
          setServiceStatus(currentLanguage === 'kn'
            ? `ಮಾತು ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. "${nextInputLabel}" ಆಯ್ಕೆ ಮಾಡಿದೆ; ಮತ್ತೆ ಮಾತನಾಡಿ ಪ್ರಯತ್ನಿಸಿ.`
            : `No speech was recognized. Switched to "${nextInputLabel}". Try speaking again.`);
        } else {
          setServiceStatus(error.message || 'Voice chat failed. Please try again.');
        }
      } finally {
        busy = false;
        micButton.disabled = false;
        submitButton.disabled = false;
        submitButton.classList.remove('opacity-50', 'cursor-wait');
      }
    }

    async function startVoice() {
      if (busy || voiceStarting) return;
      if (!navigator.mediaDevices?.getUserMedia) {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಮೈಕ್‌ಗೆ ಸುರಕ್ಷಿತ HTTPS ಅಥವಾ localhost ಅಗತ್ಯ.'
          : 'Microphone needs HTTPS or localhost. Type your question instead.');
        return;
      }
      if (typeof MediaRecorder === 'undefined') {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಈ ಬ್ರೌಸರ್‌ನಲ್ಲಿ ಆಡಿಯೊ ದಾಖಲಿಸುವಿಕೆ ಲಭ್ಯವಿಲ್ಲ.'
          : 'Audio recording is not supported in this browser. Try a current version of Chrome or Edge.');
        return;
      }
      voiceStarting = true;
      micButton.disabled = true;
      try {
        const permissionStatus = await navigator.permissions?.query({ name: 'microphone' })
          .catch(() => null);
        if (permissionStatus?.state === 'denied') {
          const error = new Error('Microphone permission was denied.');
          error.name = 'NotAllowedError';
          throw error;
        }
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿಗಾಗಿ ಕಾಯಲಾಗುತ್ತಿದೆ…'
          : 'Waiting for microphone permission…', true);
        const audioConstraints = {
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: false,
          autoGainControl: true,
        };
        if (preferredAudioInputId) {
          audioConstraints.deviceId = { exact: preferredAudioInputId };
        }
        const streamRequest = navigator.mediaDevices.getUserMedia({ audio: audioConstraints });
        let permissionTimedOut = false;
        let permissionTimeout;
        streamRequest.then(stream => {
          if (permissionTimedOut) stream.getTracks().forEach(track => track.stop());
        }, () => {});
        try {
          mediaStream = await Promise.race([
            streamRequest,
            new Promise((resolve, reject) => {
              permissionTimeout = setTimeout(() => {
                permissionTimedOut = true;
                const error = new Error('Microphone permission request timed out.');
                error.name = 'MicrophoneTimeoutError';
                reject(error);
              }, 12000);
            }),
          ]);
        } finally {
          clearTimeout(permissionTimeout);
        }
        await refreshAudioInputs();
        const microphoneTrack = mediaStream.getAudioTracks()[0];
        const microphoneSettings = microphoneTrack?.getSettings?.() || {};
        console.info('[voice] microphone track ready', {
          input: microphoneTrack?.label || 'unknown',
          sampleRate: microphoneSettings.sampleRate || 'unknown',
          channelCount: microphoneSettings.channelCount || 'unknown',
          noiseSuppression: microphoneSettings.noiseSuppression ?? 'unknown',
          autoGainControl: microphoneSettings.autoGainControl ?? 'unknown',
          echoCancellation: microphoneSettings.echoCancellation ?? 'unknown',
        });
        const mimeType = typeof MediaRecorder.isTypeSupported === 'function'
          ? [
            'audio/webm;codecs=opus',
            'audio/ogg;codecs=opus',
            'audio/mp4',
          ].find(type => MediaRecorder.isTypeSupported(type))
          : undefined;
        const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
        let peakInputLevel = 0;
        if (AudioContextConstructor) {
          try {
            audioContext = new AudioContextConstructor();
            const source = audioContext.createMediaStreamSource(mediaStream);
            audioAnalyser = audioContext.createAnalyser();
            audioAnalyser.fftSize = 1024;
            source.connect(audioAnalyser);
            await audioContext.resume();
          } catch (error) {
            console.warn('[voice] microphone level monitor unavailable', {
              message: error.message,
            });
            audioAnalyser = null;
          }
        }
        recorder = mimeType
          ? new MediaRecorder(mediaStream, { mimeType })
          : new MediaRecorder(mediaStream);
        const activeRecorder = recorder;
        const recordedChunks = [];
        const selectedInputLabel = microphoneTrack?.label
          || audioInputDevices.find(device => device.deviceId === preferredAudioInputId)?.label
          || audioInputSelect?.selectedOptions?.[0]?.textContent
          || 'default microphone';
        activeRecorder.ondataavailable = event => {
          if (event.data.size) {
            recordedChunks.push(event.data);
          }
        };
        activeRecorder.onerror = event => {
          resetVoice();
          const message = event.error?.message || 'Could not record microphone audio.';
          console.error('[voice] recording failed', { message });
          setServiceStatus(message);
        };
        activeRecorder.onstop = () => {
          const blob = new Blob(recordedChunks, { type: activeRecorder.mimeType || 'audio/webm' });
          const recordingDurationMs = recordingStartedAt ? Date.now() - recordingStartedAt : 0;
          console.info('[voice] recording stopped', {
            mimeType: blob.type,
            audioBytes: blob.size,
            recordingDurationMs,
            chunks: recordedChunks.length,
            peakInputLevel: Number(peakInputLevel.toFixed(4)),
            input: selectedInputLabel,
          });
          resetVoice();
          if (!blob.size) {
            setServiceStatus(currentLanguage === 'kn'
              ? 'ಧ್ವನಿ ದಾಖಲಾಗಲಿಲ್ಲ. ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'
              : 'No audio was recorded. Please try again.');
            return;
          }
          if (audioAnalyser && peakInputLevel < microphoneSoundThreshold) {
            console.warn('[voice] input meter detected no sound; sending recording for transcription', {
              input: selectedInputLabel,
              audioBytes: blob.size,
            });
          }
          processVoiceClip(blob, recordingDurationMs);
        };
        recordingStartedAt = Date.now();
        activeRecorder.start(250);
        voiceStarting = false;
        micButton.disabled = false;
        console.info('[voice] recording started', { mimeType: activeRecorder.mimeType });
        let recordingSeconds = 0;
        micModal.classList.remove('hidden');
        micButton.classList.remove('from-emerald-600', 'to-teal-500');
        micButton.classList.add('bg-red-600', 'pulsing-ring');
        micIcon.textContent = 'stop';
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಮಾತನಾಡಿ, ಮುಗಿದಾಗ ಮೈಕ್ ಒತ್ತಿ ಕಳುಹಿಸಿ (ಗರಿಷ್ಠ 25 ಸೆಕೆಂಡು).'
          : 'Speak, then tap the mic to send (up to 25 seconds).');
        const micStatusLabel = document.getElementById('mic-status-label');
        const micSubtextLabel = document.getElementById('mic-subtext-label');
        let soundDetected = false;
        const samples = audioAnalyser ? new Uint8Array(audioAnalyser.fftSize) : null;
        if (audioAnalyser && samples) {
          audioLevelInterval = setInterval(() => {
            audioAnalyser.getByteTimeDomainData(samples);
            let sumSquares = 0;
            for (const sample of samples) {
              const normalized = (sample - 128) / 128;
              sumSquares += normalized * normalized;
            }
            const level = Math.sqrt(sumSquares / samples.length);
            peakInputLevel = Math.max(peakInputLevel, level);
            if (level >= microphoneSoundThreshold) {
              soundDetected = true;
              if (micStatusLabel) {
                micStatusLabel.textContent = currentLanguage === 'kn'
                  ? 'ಧ್ವನಿ ಕೇಳಿಸುತ್ತಿದೆ…'
                  : 'Microphone is picking up sound…';
              }
              if (micSubtextLabel) {
                micSubtextLabel.textContent = currentLanguage === 'kn'
                  ? 'ಮುಗಿದಾಗ ಮೈಕ್ ಒತ್ತಿ ಕಳುಹಿಸಿ'
                  : 'Tap the microphone when you are done to send';
              }
            } else if (!soundDetected && Date.now() - recordingStartedAt > 3000) {
              if (micStatusLabel) {
                micStatusLabel.textContent = currentLanguage === 'kn'
                  ? 'ಧ್ವನಿ ಕೇಳಿಸುತ್ತಿಲ್ಲ'
                  : 'No sound detected yet';
              }
              if (micSubtextLabel) {
                micSubtextLabel.textContent = microphoneSilenceMessage();
              }
            }
          }, 120);
        }
        recordingInterval = setInterval(() => {
          recordingSeconds = Math.floor((Date.now() - recordingStartedAt) / 1000);
          if (recordingSeconds >= 25) {
            stopVoiceRecording(activeRecorder, 'max_duration', recordingStartedAt);
            return;
          }
          setServiceStatus(currentLanguage === 'kn'
            ? `ದಾಖಲಿಸಲಾಗುತ್ತಿದೆ… ${recordingSeconds} ಸೆಕೆಂಡು`
            : `Recording… ${recordingSeconds}s`);
        }, 1000);
        voiceTimeout = setTimeout(() => {
          stopVoiceRecording(activeRecorder, 'max_duration', recordingStartedAt);
        }, 25000);
      } catch (error) {
        voiceStarting = false;
        resetVoice();
        console.error('[voice] microphone setup failed', { message: error.message });
        const microphoneErrorMessages = {
          NotAllowedError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿ ನಿರಾಕರಿಸಲಾಗಿದೆ. ಬ್ರೌಸರ್ ಸೈಟ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಮೈಕ್ ಅನುಮತಿಸಿ.'
            : 'Microphone permission was denied. Allow microphone access in your browser site settings.',
          NotFoundError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ರೊಫೋನ್ ಕಂಡುಬಂದಿಲ್ಲ. ಮೈಕ್ ಸಂಪರ್ಕಿಸಿ ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'
            : 'No microphone was found. Connect a microphone and try again.',
          NotReadableError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ರೊಫೋನ್ ಬಳಸಲಾಗುತ್ತಿಲ್ಲ. ಬೇರೆ ಆಪ್ ಮೈಕ್ ಬಳಸುತ್ತಿದೆಯೇ ನೋಡಿ.'
            : 'The microphone is unavailable. Check whether another app is using it.',
          MicrophoneTimeoutError: currentLanguage === 'kn'
            ? 'ಮೈಕ್ ಅನುಮತಿ ಸಿಗಲಿಲ್ಲ. ವಿಳಾಸ ಪಟ್ಟಿಯಲ್ಲಿರುವ ಸೈಟ್ ಸೆಟ್ಟಿಂಗ್‌ಗಳಲ್ಲಿ ಮೈಕ್ರೊಫೋನ್ ಅನುಮತಿಸಿ.'
            : 'Microphone permission did not respond. Allow microphone access in the site settings beside your browser address bar.',
        };
        setServiceStatus(
          microphoneErrorMessages[error.name] || error.message || 'Could not start voice input.',
        );
      }
    }

    audioInputSelect?.addEventListener('change', () => {
      preferredAudioInputId = audioInputSelect.value;
      if (preferredAudioInputId) localStorage.setItem('krishi_audio_input', preferredAudioInputId);
      else localStorage.removeItem('krishi_audio_input');
      setServiceStatus(currentLanguage === 'kn'
        ? 'ಆಯ್ಕೆ ಮಾಡಿದ ಮೈಕ್ ಮುಂದಿನ ದಾಖಲಿಸುವಿಕೆಗೆ ಬಳಸಲಾಗುತ್ತದೆ.'
        : 'Selected microphone will be used for the next recording.');
    });

    document.addEventListener('click', event => {
      if (event.target.closest('#mic-trigger-btn')) {
        event.preventDefault();
        event.stopImmediatePropagation();
        if (recorder?.state === 'recording') {
          stopVoiceRecording(recorder, 'manual', recordingStartedAt);
        }
        else startVoice();
      }
    }, true);

    document.getElementById('chat-lang-btn').addEventListener('click', updateProfileBar);
    document.getElementById('mobile-lang-btn').addEventListener('click', updateProfileBar);

    form.addEventListener('submit', event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      const message = input.value.trim();
      if (message) {
        input.value = '';
        processFarmerQuery(message);
      }
    }, true);

    window.processFarmerQuery = processFarmerQuery;
    window.appendChatMsg = (sender, text, evaluations = []) => renderMessage(sender, text, evaluations);
    window.updateLiveProfileBar = updateProfileBar;
    window.clearActiveProfile = clearProfile;
    window.startNewChat = clearProfile;
    window.loadPersonaQuery = type => {
      const samples = {
        crop_health: currentLanguage === 'kn'
          ? 'ನನ್ನ ಬೆಳೆ ಆರೋಗ್ಯವಾಗಿದೆಯೇ ಎಂದು ಹೇಗೆ ತಿಳಿಯಲಿ?'
          : 'What should I check first if my crop looks unhealthy?',
        irrigation: currentLanguage === 'kn'
          ? 'ನನ್ನ ಹೊಲದಲ್ಲಿ ನೀರನ್ನು ಮಿತವಾಗಿ ಹೇಗೆ ಬಳಸಬಹುದು?'
          : 'How can I use water more efficiently on my farm?',
        soil: currentLanguage === 'kn'
          ? 'ನನ್ನ ಹೊಲದ ಮಣ್ಣಿನ ಗುಣಮಟ್ಟವನ್ನು ಹೇಗೆ ಸುಧಾರಿಸಬಹುದು?'
          : 'How can I improve the soil in my field?',
      };
      processFarmerQuery(samples[type] || samples.crop_health);
    };

    updateProfileBar();
    fetch('/api/health')
      .then(response => {
        if (!response.ok) throw new Error('Backend is unavailable.');
        return response.json();
      })
      .then(data => {
        setServiceStatus(`${data.model_mode} · ${data.voice_mode}`);
      })
      .catch(() => {
        setServiceStatus(currentLanguage === 'kn'
          ? 'ಹಿಂಬದಿ ಸೇವೆ ಲಭ್ಯವಿಲ್ಲ — python -m backend.web_server ಚಾಲನೆ ಮಾಡಿ.'
          : 'Backend unavailable — start it with: python -m backend.web_server');
      });
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
