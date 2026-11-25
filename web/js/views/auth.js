/**
 * Kokogram Auth Views Controller (HLD §1.7, §6)
 *
 * Coordinates:
 *  - Login view (validation, submission, error display).
 *  - Registration view (validation, duplicate checking, error display).
 *  - Authorized profile view stub (initials avatar, @username, online badge, logout).
 *  - Instant seamless view transitions without page reloads.
 */

import { ApiError, isMockEnabled } from '../api.js';
import authService from '../auth.js';

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

  // State
  let currentScreen = 'login'; // 'login' | 'register' | 'profile'

  /* ==========================================================================
     Screen Switching
     ========================================================================== */

  function showScreen(screen) {
    currentScreen = screen;
    clearAllErrors();

    if (viewLogin) viewLogin.classList.toggle('is-active', screen === 'login');
    if (viewRegister) viewRegister.classList.toggle('is-active', screen === 'register');
    if (viewProfile) viewProfile.classList.toggle('is-active', screen === 'profile');
  }

  function clearAllErrors() {
    // Hide form alerts
    if (alertLogin) {
      alertLogin.textContent = '';
      alertLogin.classList.remove('is-visible');
    }
    if (alertRegister) {
      alertRegister.textContent = '';
      alertRegister.classList.remove('is-visible');
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
      if (inp) inp.classList.remove('has-error');
    });
  }

  function setFieldError(inputEl, errorEl, message) {
    if (inputEl) inputEl.classList.add('has-error');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.classList.add('is-visible');
    }
  }

  function setFormAlert(alertEl, message) {
    if (alertEl) {
      alertEl.textContent = message;
      alertEl.classList.add('is-visible');
    }
  }

  /* ==========================================================================
     Profile Rendering (Screen 4)
     ========================================================================== */

  function renderProfile(user) {
    if (!user) return;

    // Compute initials (e.g. alex_psarev -> AP, neo_2026 -> NE)
    const uname = (user.username || 'User').replace(/[^a-zA-Z0-9]/g, '').toUpperCase();
    const initials = uname.length >= 2 ? uname.slice(0, 2) : (uname.slice(0, 1) || 'U');

    if (profileAvatar) profileAvatar.textContent = initials;
    if (profileUsername) profileUsername.textContent = `@${user.username}`;
    if (profileInputUser) profileInputUser.value = user.username;

    const statusText = user.status || 'Делаем жучий свэг 🕷';
    if (profileStatus) profileStatus.textContent = statusText;
    if (profileInputStatus) profileInputStatus.value = statusText;
  }

  /* ==========================================================================
     Client-side Validation Helpers
     ========================================================================== */

  function validateUsername(val) {
    const clean = (val || '').trim();
    if (!clean) return 'Длина 3–12 символов; латиница, цифры, «_»';
    if (clean.length < 3 || clean.length > 12) return 'Длина 3–12 символов; латиница, цифры, «_»';
    if (!/^[a-zA-Z0-9_]+$/.test(clean)) return 'Длина 3–12 символов; латиница, цифры, «_»';
    return null;
  }

  function validatePassword(val) {
    if (!val) return '6–12 символов, буквы и цифры';
    if (val.length < 6 || val.length > 12) return '6–12 символов, буквы и цифры';
    const hasLetter = /[a-zA-Zа-яА-ЯёЁ]/.test(val);
    const hasDigit = /\d/.test(val);
    if (!hasLetter || !hasDigit) return '6–12 символов, буквы и цифры';
    return null;
  }

  function validateContact(val) {
    const clean = (val || '').trim();
    if (!clean) return 'Введите адрес почты или номер телефона';
    if (clean.includes('@')) {
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(clean)) {
        return 'Некорректный адрес электронной почты';
      }
    } else {
      if (!/^\+?[\d\s\-()]+$/.test(clean)) {
        return 'Некорректный формат телефона (например, +79991234567)';
      }
      const digits = clean.replace(/\D/g, '');
      if (digits.length !== 11 || !(digits.startsWith('7') || digits.startsWith('8'))) {
        return 'Некорректный формат телефона (например, +79991234567 или 89991234567)';
      }
    }
    return null;
  }

  /* ==========================================================================
     Event Listeners
     ========================================================================== */

  // Switch to Register
  if (linkToRegister) {
    linkToRegister.addEventListener('click', (e) => {
      e.preventDefault();
      showScreen('register');
    });
  }

  // Switch to Login
  if (linkToLogin) {
    linkToLogin.addEventListener('click', (e) => {
      e.preventDefault();
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

      const userErr = validateUsername(username);
      if (userErr) {
        setFieldError(inputRegUsername, errRegUsername, `Ошибка (username_length): ${userErr}`);
        hasClientError = true;
      }

      const contactErr = validateContact(contact);
      if (contactErr) {
        setFieldError(inputRegContact, errRegContact, `Ошибка: ${contactErr}`);
        hasClientError = true;
      }

      const passErr = validatePassword(password);
      if (passErr) {
        setFieldError(inputRegPass, errRegPass, `Ошибка (password_composition): ${passErr}`);
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
        // Success automatically triggers auto-login and transitions to profile
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.code === 'username_taken') {
            setFieldError(inputRegUsername, errRegUsername, 'Ошибка 409 (username_taken): Username уже используется');
          } else if (err.code === 'email_taken') {
            setFieldError(inputRegContact, errRegContact, 'Ошибка 409 (email_taken): Почта уже зарегистрирована');
          } else if (err.code === 'phone_taken') {
            setFieldError(inputRegContact, errRegContact, 'Ошибка 409 (phone_taken): Номер телефона уже зарегистрирован');
          } else if (err.code === 'validation_error') {
            // Map details to fields
            let handledDetail = false;
            err.details.forEach((d) => {
              if (d.field === 'username') {
                setFieldError(inputRegUsername, errRegUsername, 'Ошибка (username_length): Длина 3–12 символов; латиница, цифры, «_»');
                handledDetail = true;
              } else if (d.field === 'password') {
                setFieldError(inputRegPass, errRegPass, 'Ошибка (password_composition): 6–12 символов, буквы и цифры');
                handledDetail = true;
              } else if (d.field === 'email' || d.field === 'phone' || d.field === 'login') {
                setFieldError(inputRegContact, errRegContact, 'Ошибка: Введите корректный адрес почты или номер телефона');
                handledDetail = true;
              }
            });
            if (!handledDetail) {
              setFormAlert(alertRegister, `Ошибка (${err.code}): ${err.message}`);
            }
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
        btnLogout.disabled = false;
        btnLogout.textContent = 'Выйти';
        // Auth observer will transition to login
      }
    });
  }

  // Subscribe to auth state updates
  authService.onAuthStateChanged((user, isAuth) => {
    if (isAuth && user) {
      renderProfile(user);
      showScreen('profile');
    } else {
      showScreen('login');
    }
  });

  // Display initial active screen
  if (authService.isAuthenticated()) {
    renderProfile(authService.getUser());
    showScreen('profile');
  } else {
    showScreen('login');
  }
}
