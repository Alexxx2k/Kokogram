/**
 * Kokogram API Client & Mock Subsystem (HLD §1.7, §4.1, §4.3)
 *
 * Provides:
 *  - REST client with automatic Bearer token injection and X-Request-ID header.
 *  - Unified error handling: translates { error: { code, message, details } } to ApiError.
 *  - Automatic session cleanup on 401 'unauthorized' with listener notification.
 *  - Complete Mock Mode (USE_MOCK = true) emulating /auth/register, /auth/login, /auth/logout,
 *    and HTTP 401, 409, 422 error states according to FS and HLD contracts.
 */

export const TOKEN_STORAGE_KEY = 'kokogram_token';
export const USER_STORAGE_KEY = 'kokogram_user';
export const MOCK_STORAGE_KEY = 'kokogram_mock';
export const DEFAULT_API_BASE = '/api/v1';

/**
 * Standard Application Error representation.
 */
export class ApiError extends Error {
  constructor(status, errorPayload) {
    const error = errorPayload?.error || {};
    const message = error.message || (typeof errorPayload === 'string' ? errorPayload : `HTTP ${status}`);
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = error.code || (status === 401 ? 'unauthorized' : 'unknown_error');
    this.message = message;
    this.details = Array.isArray(error.details) ? error.details : [];
    this.raw = errorPayload;
  }
}

/* ==========================================================================
   Session & Storage Utilities
   ========================================================================== */

export function getToken() {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setStoredUser(user) {
  if (user) {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_STORAGE_KEY);
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
  localStorage.removeItem(USER_STORAGE_KEY);
}

let unauthorizedHandler = null;

export function setUnauthorizedHandler(callback) {
  unauthorizedHandler = callback;
}

function notifyUnauthorized() {
  clearSession();
  if (typeof unauthorizedHandler === 'function') {
    try {
      unauthorizedHandler();
    } catch (e) {
      console.error('[API] Error in unauthorizedHandler:', e);
    }
  }
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('kokogram:unauthorized'));
  }
}

/* ==========================================================================
   Mock Mode Switch & Mock Data Repository
   ========================================================================== */

export function isMockEnabled() {
  const val = localStorage.getItem(MOCK_STORAGE_KEY);
  return val === null ? true : val === 'true';
}

export function setMockEnabled(enabled) {
  localStorage.setItem(MOCK_STORAGE_KEY, String(enabled));
}

const MOCK_DB_STORAGE_KEY = 'kokogram_mock_users';

const INITIAL_MOCK_USERS = [
  {
    id: '11111111-1111-4111-8111-111111111111',
    username: 'alex_psarev',
    email: 'alex@mail.ru',
    phone: '+79991234567',
    password: 'alex123',
    status: 'Делаем жучий свэг 🕷',
    avatar_url: null,
    created_at: '2026-01-01T00:00:00Z',
  },
  {
    id: '22222222-2222-4222-8222-222222222222',
    username: 'maisha_sob',
    email: 'misha@mail.ru',
    phone: '+79990001122',
    password: 'misha123',
    status: 'На связи',
    avatar_url: null,
    created_at: '2026-01-02T00:00:00Z',
  },
];

function getMockUsers() {
  const raw = localStorage.getItem(MOCK_DB_STORAGE_KEY);
  if (!raw) {
    localStorage.setItem(MOCK_DB_STORAGE_KEY, JSON.stringify(INITIAL_MOCK_USERS));
    return [...INITIAL_MOCK_USERS];
  }
  try {
    return JSON.parse(raw);
  } catch {
    return [...INITIAL_MOCK_USERS];
  }
}

function saveMockUsers(users) {
  localStorage.setItem(MOCK_DB_STORAGE_KEY, JSON.stringify(users));
}

function normalizePhone(phone) {
  if (!phone) return '';
  const digits = phone.replace(/\D/g, '');
  if (digits.length === 11 && (digits.startsWith('7') || digits.startsWith('8'))) {
    return '+7' + digits.slice(1);
  }
  return phone.trim();
}

function normalizeEmail(email) {
  return email ? email.trim().toLowerCase() : '';
}

function generateUuid() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

const delay = (ms = 180) => new Promise((resolve) => setTimeout(resolve, ms));

/* ==========================================================================
   Mock Request Handler
   ========================================================================== */

async function handleMockRequest(method, path, body, headers = {}) {
  await delay(120 + Math.random() * 100);

  const cleanPath = path.replace(/^\/api\/v1/, '').replace(/\/$/, '') || '/';
  const upperMethod = method.toUpperCase();

  // POST /auth/register
  if (upperMethod === 'POST' && cleanPath === '/auth/register') {
    const { username, password, email, phone } = body || {};
    const validationDetails = [];

    // F_Prof_2, F_Prof_3: username checks
    if (!username || typeof username !== 'string' || !username.trim()) {
      validationDetails.push({ field: 'username', reason: 'username_required' });
    } else {
      const cleanUsername = username.trim();
      if (cleanUsername.length < 3 || cleanUsername.length > 12) {
        validationDetails.push({ field: 'username', reason: 'username_length' });
      } else if (!/^[a-zA-Z0-9_]+$/.test(cleanUsername)) {
        validationDetails.push({ field: 'username', reason: 'username_format' });
      }
    }

    // F_Auth_7, F_Auth_8: password checks
    if (!password || typeof password !== 'string') {
      validationDetails.push({ field: 'password', reason: 'password_length' });
    } else {
      if (password.length < 6 || password.length > 12) {
        validationDetails.push({ field: 'password', reason: 'password_length' });
      }
      const hasLetter = /[a-zA-Zа-яА-ЯёЁ]/.test(password);
      const hasDigit = /\d/.test(password);
      if (!hasLetter || !hasDigit) {
        validationDetails.push({ field: 'password', reason: 'password_composition' });
      }
    }

    // F_Auth_1, F_Auth_2, F_Auth_12: email or phone
    const normEmail = normalizeEmail(email);
    const normPhone = normalizePhone(phone);

    if (!normEmail && !normPhone) {
      validationDetails.push({ field: 'login', reason: 'contact_required' });
    } else {
      if (normEmail && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(normEmail)) {
        validationDetails.push({ field: 'email', reason: 'invalid_email' });
      }
      if (normPhone && !/^\+7\d{10}$/.test(normPhone)) {
        validationDetails.push({ field: 'phone', reason: 'invalid_phone' });
      }
    }

    if (validationDetails.length > 0) {
      throw new ApiError(422, {
        error: {
          code: 'validation_error',
          message: 'Некорректные данные',
          details: validationDetails,
        },
      });
    }

    const users = getMockUsers();
    const cleanUsername = username.trim();

    // F_Prof_4: username_taken
    if (users.some((u) => u.username.toLowerCase() === cleanUsername.toLowerCase())) {
      throw new ApiError(409, {
        error: {
          code: 'username_taken',
          message: 'Username уже используется другим пользователем',
          details: [{ field: 'username', reason: 'username_taken' }],
        },
      });
    }

    // F_Auth_4: email_taken
    if (normEmail && users.some((u) => normalizeEmail(u.email) === normEmail)) {
      throw new ApiError(409, {
        error: {
          code: 'email_taken',
          message: 'Этот адрес электронной почты уже зарегистрирован',
          details: [{ field: 'email', reason: 'email_taken' }],
        },
      });
    }

    // F_Auth_6: phone_taken
    if (normPhone && users.some((u) => normalizePhone(u.phone) === normPhone)) {
      throw new ApiError(409, {
        error: {
          code: 'phone_taken',
          message: 'Этот номер телефона уже зарегистрирован',
          details: [{ field: 'phone', reason: 'phone_taken' }],
        },
      });
    }

    // Create user
    const newUser = {
      id: generateUuid(),
      username: cleanUsername,
      email: normEmail || null,
      phone: normPhone || null,
      password,
      status: null,
      avatar_url: null,
      created_at: new Date().toISOString(),
    };

    users.push(newUser);
    saveMockUsers(users);

    // HLD §4.3: 201 Created returns User object strictly WITHOUT token!
    return {
      id: newUser.id,
      username: newUser.username,
      status: newUser.status,
      avatar_url: newUser.avatar_url,
      email: newUser.email,
      phone: newUser.phone,
    };
  }

  // POST /auth/login
  if (upperMethod === 'POST' && cleanPath === '/auth/login') {
    const { login, password } = body || {};

    if (!login || !password) {
      throw new ApiError(401, {
        error: {
          code: 'invalid_credentials',
          message: 'Неверный логин или пароль',
          details: [],
        },
      });
    }

    const normInput = String(login).trim();
    const isEmailInput = normInput.includes('@');
    const normEmail = isEmailInput ? normalizeEmail(normInput) : '';
    const normPhone = !isEmailInput ? normalizePhone(normInput) : '';

    const users = getMockUsers();
    const user = users.find((u) => {
      if (isEmailInput) {
        return normalizeEmail(u.email) === normEmail;
      }
      return normalizePhone(u.phone) === normPhone;
    });

    if (!user || user.password !== String(password)) {
      throw new ApiError(401, {
        error: {
          code: 'invalid_credentials',
          message: 'Неверный логин или пароль',
          details: [],
        },
      });
    }

    const token = `mock-token-${user.id.slice(0, 8)}-${Date.now()}`;
    const expiresAt = new Date(Date.now() + 30 * 24 * 3600 * 1000).toISOString();

    return {
      token,
      expires_at: expiresAt,
      user: {
        id: user.id,
        username: user.username,
        status: user.status,
        avatar_url: user.avatar_url,
        email: user.email,
        phone: user.phone,
      },
    };
  }

  // POST /auth/logout
  if (upperMethod === 'POST' && cleanPath === '/auth/logout') {
    const authHeader = headers['Authorization'] || headers['authorization'];
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new ApiError(401, {
        error: {
          code: 'unauthorized',
          message: 'Требуется авторизация',
          details: [],
        },
      });
    }
    return null; // 204 No Content
  }

  // GET /users/me
  if (upperMethod === 'GET' && cleanPath === '/users/me') {
    const authHeader = headers['Authorization'] || headers['authorization'];
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new ApiError(401, {
        error: {
          code: 'unauthorized',
          message: 'Требуется авторизация',
          details: [],
        },
      });
    }

    const storedUser = getStoredUser();
    if (!storedUser) {
      throw new ApiError(401, {
        error: {
          code: 'unauthorized',
          message: 'Сессия не найдена',
          details: [],
        },
      });
    }

    return storedUser;
  }

  throw new ApiError(404, {
    error: {
      code: 'not_found',
      message: `Mock endpoint ${upperMethod} ${cleanPath} not found`,
      details: [],
    },
  });
}

/* ==========================================================================
   HTTP Client Core (fetch + interceptor)
   ========================================================================== */

export async function request(endpoint, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const base = options.baseUrl || (typeof window !== 'undefined' && window.__API_BASE__) || DEFAULT_API_BASE;

  let urlPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  if (!urlPath.startsWith(base) && !urlPath.startsWith('http')) {
    urlPath = `${base}${urlPath}`;
  }

  const token = options.token || getToken();
  const headers = {
    Accept: 'application/json',
    ...(options.headers || {}),
  };

  if (token && !headers['Authorization'] && !headers['authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    headers['X-Request-ID'] = crypto.randomUUID();
  }

  let body = options.body;
  if (body && typeof body === 'object' && !(body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(body);
  }

  // Mock interception
  if (isMockEnabled()) {
    const parsedBody = typeof options.body === 'string' ? JSON.parse(options.body) : options.body;
    try {
      return await handleMockRequest(method, urlPath, parsedBody, headers);
    } catch (err) {
      if (err instanceof ApiError && err.status === 401 && err.code === 'unauthorized') {
        notifyUnauthorized();
      }
      throw err;
    }
  }

  // Real fetch execution
  let response;
  try {
    response = await fetch(urlPath, {
      method,
      headers,
      body,
      ...options,
    });
  } catch (networkErr) {
    throw new ApiError(503, {
      error: {
        code: 'service_unavailable',
        message: 'Сервер недоступен. Проверьте подключение к сети.',
        details: [{ reason: networkErr.message }],
      },
    });
  }

  if (response.status === 204) {
    return null;
  }

  let data = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch {
      data = null;
    }
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const apiError = new ApiError(response.status, data);
    if (apiError.status === 401 && apiError.code === 'unauthorized') {
      notifyUnauthorized();
    }
    throw apiError;
  }

  return data;
}

export const api = {
  get: (url, opts = {}) => request(url, { ...opts, method: 'GET' }),
  post: (url, body, opts = {}) => request(url, { ...opts, method: 'POST', body }),
  put: (url, body, opts = {}) => request(url, { ...opts, method: 'PUT', body }),
  patch: (url, body, opts = {}) => request(url, { ...opts, method: 'PATCH', body }),
  delete: (url, opts = {}) => request(url, { ...opts, method: 'DELETE' }),
};

export default api;
