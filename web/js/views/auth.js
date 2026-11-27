/**
 * Kokogram Auth Views Controller (HLD §1.7, §6)
 *
 * Coordinates:
 *  - Login view (validation, submission, error display).
 *  - Registration view (validation, duplicate checking, error display).
 *  - Authorized profile view stub (initials avatar, @username, online badge, logout).
 *  - Instant seamless view transitions without page reloads.
 */

import { ApiError } from '../api.js';
import authService, { AutoLoginError } from '../auth.js';

export function initAuthView() {
  // View containers
  const viewLogin = document.getElementById('view-login');
  const viewRegister = document.getElementById('view-register');
  const viewProfile = document.getElementById('view-profile');

  // Form elements - Login
  const formLogin = document.getElementById('form-login');
  const inputLoginUser = document.getElementById('login-identifier');
  const inputLoginPass = document.getElementById('login-password');
  const alertLogin = document.getElementById('login-alert');
  const btnLoginSubmit = document.getElementById('btn-login-submit');
  const linkToRegister = document.getElementById('link-to-register');

  // Form elements - Register
  const formRegister = document.getElementById('form-register');
  const inputRegUsername = document.getElementById('reg-username');
  const inputRegContact = document.getElementById('reg-contact');
  const inputRegPass = document.getElementById('reg-password');
  const alertRegister = document.getElementById('register-alert');
  const btnRegSubmit = document.getElementById('btn-reg-submit');
  const linkToLogin = document.getElementById('link-to-login');

  // Field error elements - Login
  const errLoginUser = document.getElementById('err-login-user');
  const errLoginPass = document.getElementById('err-login-pass');

  // Field error elements - Register
  const errRegUsername = document.getElementById('err-reg-username');
  const errRegContact = document.getElementById('err-reg-contact');
  const errRegPass = document.getElementById('err-reg-pass');

  // Profile elements
  const profileAvatar = document.getElementById('profile-avatar');
  const profileUsername = document.getElementById('profile-username');
  const profileStatus = document.getElementById('profile-status');
  const profileInputUser = document.getElementById('profile-input-username');
  const profileInputStatus = document.getElementById('profile-input-status');
  const btnLogout = document.getElementById('btn-logout');

  /* ==========================================================================
     Screen Switching
     ========================================================================== */

  function resetAuthForms() {
    if (formLogin) formLogin.reset();
    if (formRegister) formRegister.reset();
  }

  function showScreen(screen) {
    clearAllErrors();

    if (viewLogin) viewLogin.classList.toggle('is-active', screen === 'login');
    if (viewRegister) viewRegister.classList.toggle('is-active', screen === 'register');
    if (viewProfile) viewProfile.classList.toggle('is-active', screen === 'profile');
  }

  function clearAllErrors() {
    // Hide form alerts
    if (alertLogin) {
      alertLogin.textContent = '';
      alertLogin.classList.remove('is-visible', 'is-warning');
    }
    if (alertRegister) {
      alertRegister.textContent = '';
      alertRegister.classList.remove('is-visible', 'is-warning');
    }

    // Hide field errors and remove error borders
    const errEls = [errLoginUser, errLoginPass, errRegUsername, errRegContact, errRegPass];
    errEls.forEach((el) => {
      if (el) {
        el.textContent = '';
        el.classList.remove('is-visible');
      }
    });

    const inputs = [inputLoginUser, inputLoginPass, inputRegUsername, inputRegContact, inputRegPass];
    inputs.forEach((inp) => {
      if (inp) {
        inp.classList.remove('has-error');
        inp.removeAttribute('aria-invalid');
      }
    });
  }

  function setFieldError(inputEl, errorEl, message) {
    if (inputEl) {
      inputEl.classList.add('has-error');
      inputEl.setAttribute('aria-invalid', 'true');
    }
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.add('is-visible');
    }
  }

  function setFormAlert(alertEl, message, variant = 'error') {
    if (alertEl) {
      alertEl.textContent = message;
      alertEl.classList.toggle('is-warning', variant === 'warning');
      alertEl.classList.add('is-visible');
    }
  }

  /* ==========================================================================
     Profile Rendering (Screen 4)
     ========================================================================== */

  function getInitials(username) {
    const raw = (username || '').replace(/[^a-zA-Z0-9_]/g, '');
    const parts = raw.split('_').filter(Boolean);
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    }
    if (parts.length === 1) {
      return parts[0].slice(0, 2).toUpperCase();
    }
    return 'U';
  }

  function renderProfile(user) {
    if (!user) return;

    // Compute initials (e.g. alex_psarev -> AP, misha_sob -> MS, neo -> NE)
    const initials = getInitials(user.username);

    if (profileAvatar) profileAvatar.textContent = initials;
    if (profileUsername) profileUsername.textContent = `@${user.username}`;
    if (profileInputUser) profileInputUser.value = user.username;

    const statusText = user.status || '';
    if (profileStatus) profileStatus.textContent = statusText;
    if (profileInputStatus) profileInputStatus.value = statusText;
  }

  /* ==========================================================================
     Validation Reason Mapping & Client-side Validation Helpers (HLD §4.1)
     ========================================================================== */

  const VALIDATION_MAP = {
    username_required: {
      target: 'username',
      message: 'Ошибка (username_required): Поле обязательно для заполнения',
    },
    username_length: {
      target: 'username',
      message: 'Ошибка (username_length): Длина 3–12 символов; латиница, цифры, «_»',
    },
    username_format: {
      target: 'username',
      message: 'Ошибка (username_format): Допустимы только латиница, цифры, «_»',
    },
    password_length: {
      target: 'password',
      message: 'Ошибка (password_length): Длина пароля от 6 до 12 символов',
    },
    password_composition: {
      target: 'password',
      message: 'Ошибка (password_composition): 6–12 символов, буквы и цифры',
    },
    invalid_email: {
      target: 'contact',
      message: 'Ошибка (invalid_email): Некорректный адрес электронной почты',
    },
    invalid_phone: {
      target: 'contact',
      message: 'Ошибка (invalid_phone): Некорректный формат телефона (например, +79991234567 или 89991234567)',
    },
  };

  function formatValidationReasons(reasons) {
    const messages = new Set();
    for (const reason of reasons) {
      const mapped = VALIDATION_MAP[reason];
      if (mapped) {
        messages.add(mapped.message);
      }
    }
    return [...messages].join('\n');
  }

  function applyServerValidationError(err) {
    const fieldMessages = {
      username: new Set(),
      contact: new Set(),
      password: new Set(),
    };
    const unmappedMessages = new Set();

    for (const d of err.details || []) {
      const reason = d?.reason;
      const field = d?.field;
      const mapped = reason ? VALIDATION_MAP[reason] : null;

      if (mapped) {
        fieldMessages[mapped.target].add(mapped.message);
        continue;
      }

      const fallbackMsg = reason
        ? `Ошибка (${reason}): ${err.message}`
        : `Ошибка (validation_error): ${err.message}`;

      if (field === 'username') {
        fieldMessages.username.add(fallbackMsg);
      } else if (field === 'password') {
        fieldMessages.password.add(fallbackMsg);
      } else if (field === 'email' || field === 'phone') {
        fieldMessages.contact.add(fallbackMsg);
      } else {
        unmappedMessages.add(fallbackMsg);
      }
    }

    let handledAny = false;
    if (fieldMessages.username.size > 0) {
      setFieldError(inputRegUsername, errRegUsername, [...fieldMessages.username].join('\n'));
      handledAny = true;
    }
    if (fieldMessages.contact.size > 0) {
      setFieldError(inputRegContact, errRegContact, [...fieldMessages.contact].join('\n'));
      handledAny = true;
    }
    if (fieldMessages.password.size > 0) {
      setFieldError(inputRegPass, errRegPass, [...fieldMessages.password].join('\n'));
      handledAny = true;
    }

    if (unmappedMessages.size > 0) {
      setFormAlert(alertRegister, [...unmappedMessages].join('\n'));
    } else if (!handledAny) {
      setFormAlert(alertRegister, `Ошибка (${err.code}): ${err.message}`);
    }
  }

  function validateUsername(val) {
    const clean = (val || '').trim();
    if (!clean) return ['username_required'];
    const reasons = [];
    if (clean.length < 3 || clean.length > 12) reasons.push('username_length');
    if (!/^[a-zA-Z0-9_]+$/.test(clean)) reasons.push('username_format');
    return reasons;
  }

  function validatePassword(val) {
    if (!val) return ['password_length'];
    const reasons = [];
    if (val.length < 6 || val.length > 12) reasons.push('password_length');
    const hasLetter = /[a-zA-Zа-яА-ЯёЁ]/.test(val);
    const hasDigit = /\d/.test(val);
    if (!hasLetter || !hasDigit) reasons.push('password_composition');
    return reasons;
  }

  function validateContact(val) {
    const clean = (val || '').trim();
    if (!clean) return [];
    if (clean.includes('@')) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(clean)) {
        return ['invalid_email'];
      }
    } else {
      const compact = clean.replace(/[\s\-()]/g, '');
      if (!/^(?:\+7|7|8)\d{10}$/.test(compact)) {
        return ['invalid_phone'];
      }
    }
    return [];
  }

  /* ==========================================================================
     Event Listeners
     ========================================================================== */

  // Switch to Register
  if (linkToRegister) {
    linkToRegister.addEventListener('click', (e) => {
      e.preventDefault();
      if (formLogin) formLogin.reset();
      showScreen('register');
    });
  }

  // Switch to Login
  if (linkToLogin) {
    linkToLogin.addEventListener('click', (e) => {
      e.preventDefault();
      if (formRegister) formRegister.reset();
      showScreen('login');
    });
  }

  // Handle Login Submit
  if (formLogin) {
    formLogin.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearAllErrors();

      const login = (inputLoginUser?.value || '').trim();
      const password = inputLoginPass?.value || '';

      let hasClientError = false;
      if (!login) {
        setFieldError(inputLoginUser, errLoginUser, 'Поле обязательно для заполнения');
        hasClientError = true;
      }
      if (!password) {
        setFieldError(inputLoginPass, errLoginPass, 'Поле обязательно для заполнения');
        hasClientError = true;
      }
      if (hasClientError) return;

      try {
        if (btnLoginSubmit) {
          btnLoginSubmit.disabled = true;
          btnLoginSubmit.textContent = 'Вход...';
        }

        await authService.login(login, password);
        resetAuthForms();
        // On success auth state change listener automatically triggers showScreen('profile')
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.code === 'invalid_credentials') {
            setFormAlert(alertLogin, 'Ошибка (invalid_credentials): Неверный пароль или логин');
          } else {
            setFormAlert(alertLogin, `Ошибка (${err.code}): ${err.message}`);
          }
        } else {
          setFormAlert(alertLogin, 'Ошибка соединения с сервером. Попробуйте снова.');
        }
      } finally {
        if (btnLoginSubmit) {
          btnLoginSubmit.disabled = false;
          btnLoginSubmit.textContent = 'Войти';
        }
      }
    });
  }

  // Handle Register Submit
  if (formRegister) {
    formRegister.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearAllErrors();

      const username = (inputRegUsername?.value || '').trim();
      const contact = (inputRegContact?.value || '').trim();
      const password = inputRegPass?.value || '';

      let hasClientError = false;

      const userReasons = validateUsername(username);
      if (userReasons.length > 0) {
        setFieldError(inputRegUsername, errRegUsername, formatValidationReasons(userReasons));
        hasClientError = true;
      }

      if (!contact) {
        setFieldError(inputRegContact, errRegContact, 'Введите адрес почты или номер телефона');
        hasClientError = true;
      } else {
        const contactReasons = validateContact(contact);
        if (contactReasons.length > 0) {
          setFieldError(inputRegContact, errRegContact, formatValidationReasons(contactReasons));
          hasClientError = true;
        }
      }

      const passReasons = validatePassword(password);
      if (passReasons.length > 0) {
        setFieldError(inputRegPass, errRegPass, formatValidationReasons(passReasons));
        hasClientError = true;
      }

      if (hasClientError) return;

      try {
        if (btnRegSubmit) {
          btnRegSubmit.disabled = true;
          btnRegSubmit.textContent = 'Регистрация...';
        }

        await authService.register({
          username,
          login: contact,
          password,
        });
        resetAuthForms();
        // Success automatically triggers auto-login and transitions to profile
      } catch (err) {
        if (err instanceof AutoLoginError) {
          if (formRegister) formRegister.reset();
          showScreen('login');
          if (inputLoginUser && err.loginIdentifier) {
            inputLoginUser.value = err.loginIdentifier;
          }
          const reason = err.cause instanceof ApiError ? ` (${err.cause.code})` : '';
          setFormAlert(
            alertLogin,
            `Аккаунт создан, но автоматический вход не выполнен${reason}. Пожалуйста, войдите с указанными данными.`,
            'warning',
          );
        } else if (err instanceof ApiError) {
          if (err.code === 'username_taken') {
            setFieldError(inputRegUsername, errRegUsername, 'Ошибка 409 (username_taken): Username уже используется');
          } else if (err.code === 'email_taken') {
            setFieldError(inputRegContact, errRegContact, 'Ошибка 409 (email_taken): Почта уже зарегистрирована');
          } else if (err.code === 'phone_taken') {
            setFieldError(inputRegContact, errRegContact, 'Ошибка 409 (phone_taken): Номер телефона уже зарегистрирован');
          } else if (err.code === 'validation_error') {
            applyServerValidationError(err);
          } else {
            setFormAlert(alertRegister, `Ошибка (${err.code}): ${err.message}`);
          }
        } else {
          setFormAlert(alertRegister, 'Ошибка соединения с сервером. Попробуйте снова.');
        }
      } finally {
        if (btnRegSubmit) {
          btnRegSubmit.disabled = false;
          btnRegSubmit.textContent = 'Зарегистрироваться';
        }
      }
    });
  }

  // Handle Logout Click
  if (btnLogout) {
    btnLogout.addEventListener('click', async () => {
      try {
        btnLogout.disabled = true;
        btnLogout.textContent = 'Выход...';
        await authService.logout();
      } finally {
        resetAuthForms();
        btnLogout.disabled = false;
        btnLogout.textContent = 'Выйти';
        // Auth observer will transition to login
      }
    });
  }

  // Subscribe to auth state updates (called synchronously with current state)
  authService.onAuthStateChanged((user, isAuth) => {
    if (isAuth && user) {
      resetAuthForms();
      renderProfile(user);
      showScreen('profile');
    } else {
      resetAuthForms();
      showScreen('login');
    }
  });

  // Verify token and refresh user profile via GET /users/me on startup
  if (authService.isAuthenticated()) {
    authService.refreshSession().catch((err) => {
      console.warn('[AuthView] Session verification failed:', err);
    });
  }
}
