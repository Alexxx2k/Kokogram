/**
 * Kokogram Auth Service (HLD §4.3, FS F_Auth_*)
 *
 * Manages:
 *  - User session state (token and profile in localStorage).
 *  - Login (POST /auth/login).
 *  - Register (POST /auth/register -> 201 User -> auto-login POST /auth/login).
 *  - Logout (POST /auth/logout with Bearer token, cleanup in finally).
 *  - State change observers (onAuthStateChanged).
 */

import {
  api,
  clearSession,
  getStoredUser,
  getToken,
  setStoredUser,
  setToken,
  setUnauthorizedHandler,
} from './api.js';

export class AutoLoginError extends Error {
  constructor(cause, user, loginIdentifier) {
    super('Аккаунт создан, но автоматический вход не удался');
    this.name = 'AutoLoginError';
    this.cause = cause;
    this.user = user;
    this.loginIdentifier = loginIdentifier;
  }
}

class AuthService {
  constructor() {
    this._listeners = new Set();
    this._initUnauthorizedHandling();
  }

  _initUnauthorizedHandling() {
    setUnauthorizedHandler(() => {
      this._notify(null, false);
    });
  }

  /**
   * Checks whether the user is currently authenticated.
   * @returns {boolean}
   */
  isAuthenticated() {
    return Boolean(getToken());
  }

  /**
   * Returns stored token string or null.
   * @returns {string|null}
   */
  getToken() {
    return getToken();
  }

  /**
   * Returns current logged-in user profile or null.
   * @returns {object|null}
   */
  getUser() {
    return getStoredUser();
  }

  /**
   * Subscribes a listener to auth state changes.
   * @param {function(user: object|null, isAuthenticated: boolean): void} callback
   * @returns {function(): void} Unsubscribe function
   */
  onAuthStateChanged(callback) {
    if (typeof callback !== 'function') return () => {};
    this._listeners.add(callback);
    // Call immediately with current state
    try {
      callback(this.getUser(), this.isAuthenticated());
    } catch (e) {
      console.error('[AuthService] Initial state notification error:', e);
    }
    return () => this._listeners.delete(callback);
  }

  _notify(user, isAuth) {
    for (const listener of this._listeners) {
      try {
        listener(user, isAuth);
      } catch (err) {
        console.error('[AuthService] Listener error:', err);
      }
    }
  }

  /**
   * Logs in a user via email or phone.
   * @param {string} login Email or phone number
   * @param {string} password Password
   * @returns {Promise<{token: string, expires_at: string, user: object}>}
   */
  async login(login, password) {
    const cleanLogin = (login || '').trim();
    const response = await api.post(
      '/auth/login',
      {
        login: cleanLogin,
        password,
      },
      { skipAuth: true },
    );

    if (response?.token && response?.user) {
      setToken(response.token);
      setStoredUser(response.user);
      this._notify(response.user, true);
    }

    return response;
  }

  /**
   * Registers a new user and automatically logs them in.
   * Per HLD §4.3: POST /auth/register returns 201 User (WITHOUT token).
   * We then automatically invoke login() with the same credentials to obtain a session token.
   *
   * @param {object} params
   * @param {string} params.username Username (3-12 characters, alphanumeric + _)
   * @param {string} [params.login] Raw email or phone input
   * @param {string} [params.email] Optional explicit email
   * @param {string} [params.phone] Optional explicit phone
   * @param {string} params.password Password
   * @returns {Promise<{token: string, expires_at: string, user: object}>}
   */
  async register({ username, login, email, phone, password }) {
    const cleanUsername = (username || '').trim();
    let targetEmail = (email || '').trim();
    let targetPhone = (phone || '').trim();

    if (login && !targetEmail && !targetPhone) {
      const rawLogin = login.trim();
      if (rawLogin.includes('@')) {
        targetEmail = rawLogin;
      } else {
        targetPhone = rawLogin;
      }
    }

    const registerPayload = {
      username: cleanUsername,
      password,
    };
    if (targetEmail) registerPayload.email = targetEmail;
    if (targetPhone) registerPayload.phone = targetPhone;

    // 1. Register: returns 201 with User object (strictly without token)
    const createdUser = await api.post('/auth/register', registerPayload, { skipAuth: true });

    // 2. Auto-login: obtain session token and store user (only by email or phone per F_Auth_9, F_Auth_10)
    const loginIdentifier = targetEmail || targetPhone;
    if (!loginIdentifier) {
      throw new AutoLoginError(new Error('Email или телефон не указан'), createdUser, '');
    }

    try {
      return await this.login(loginIdentifier, password);
    } catch (loginErr) {
      throw new AutoLoginError(loginErr, createdUser, loginIdentifier);
    }
  }

  /**
   * Fetches the current user profile via GET /users/me to verify the active
   * session on the server and refresh stored user data.
   * On 401 unauthorized, api.js clears the session and notifies listeners.
   * @returns {Promise<object|null>}
   */
  async refreshSession() {
    if (!this.isAuthenticated()) {
      return null;
    }
    const user = await api.get('/users/me');
    if (user) {
      setStoredUser(user);
      this._notify(user, true);
    }
    return user;
  }

  /**
   * Logs out the current session.
   * Calls POST /auth/logout with Bearer token, then clears localStorage in finally.
   * @returns {Promise<void>}
   */
  async logout() {
    try {
      if (this.isAuthenticated()) {
        await api.post('/auth/logout');
      }
    } catch (err) {
      console.warn('[AuthService] Logout server request failed or expired:', err);
    } finally {
      clearSession();
      this._notify(null, false);
    }
  }
}

export const authService = new AuthService();
export default authService;
