// Centralized API client with Bearer token handling and auto-refresh

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Storage keys
const TOKEN_KEY = 'authToken';
const REFRESH_TOKEN_KEY = 'refreshToken';
const PROFILE_ID_KEY = 'currentProfileId';
const REMEMBER_ME_KEY = 'rememberMe';

// Get the appropriate storage based on "remember me" preference
function getStorage(): Storage {
  const rememberMe = localStorage.getItem(REMEMBER_ME_KEY) === 'true';
  return rememberMe ? localStorage : sessionStorage;
}

export function getStoredToken(): string | null {
  // Check both storages (user might have switched)
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || sessionStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setStoredTokens(accessToken: string, refreshToken?: string): void {
  const storage = getStorage();
  storage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    storage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

export function removeStoredTokens(): void {
  // Clear from both storages
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function setRememberMe(remember: boolean): void {
  if (remember) {
    localStorage.setItem(REMEMBER_ME_KEY, 'true');
  } else {
    localStorage.removeItem(REMEMBER_ME_KEY);
  }
}

export function getRememberMe(): boolean {
  return localStorage.getItem(REMEMBER_ME_KEY) === 'true';
}

function getStoredProfileId(): string | null {
  return localStorage.getItem(PROFILE_ID_KEY) || sessionStorage.getItem(PROFILE_ID_KEY);
}

function setStoredProfileId(profileId: string): void {
  const storage = getStorage();
  storage.setItem(PROFILE_ID_KEY, profileId);
}

function removeStoredProfileId(): void {
  localStorage.removeItem(PROFILE_ID_KEY);
  sessionStorage.removeItem(PROFILE_ID_KEY);
}

// Event to notify about session expiration
const SESSION_EXPIRED_EVENT = 'session:expired';

export function onSessionExpired(callback: () => void): () => void {
  window.addEventListener(SESSION_EXPIRED_EVENT, callback);
  return () => window.removeEventListener(SESSION_EXPIRED_EVENT, callback);
}

function dispatchSessionExpired(): void {
  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
}

// Token refresh state
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    setStoredTokens(data.access_token, data.refresh_token);
    return data.access_token;
  } catch {
    return null;
  }
}

// Ensure only one refresh happens at a time
async function getValidToken(): Promise<string | null> {
  const token = getStoredToken();
  if (!token) return null;

  // If already refreshing, wait for the result
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  return token;
}

interface RequestOptions extends Omit<RequestInit, 'headers'> {
  headers?: Record<string, string>;
  skipAuth?: boolean;
  retryOnUnauthorized?: boolean;
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, retryOnUnauthorized = true, headers = {}, ...fetchOptions } = options;
  
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // Add Bearer token if available and not skipping auth
  if (!skipAuth) {
    const token = await getValidToken();
    if (token) {
      requestHeaders['Authorization'] = `Bearer ${token}`;
    }
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers: requestHeaders,
  });

  // Handle 401 - try refresh token first
  if (response.status === 401 && retryOnUnauthorized && !skipAuth) {
    // Try to refresh the token
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = refreshAccessToken();
    }

    const newToken = await refreshPromise;
    isRefreshing = false;
    refreshPromise = null;

    if (newToken) {
      // Retry the request with new token
      requestHeaders['Authorization'] = `Bearer ${newToken}`;
      const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...fetchOptions,
        headers: requestHeaders,
      });

      if (retryResponse.ok) {
        const text = await retryResponse.text();
        if (!text) return {} as T;
        return JSON.parse(text);
      }
    }

    // Refresh failed or retry failed - session expired
    removeStoredTokens();
    removeStoredProfileId();
    dispatchSessionExpired();
    throw new Error('Sessão expirada. Faça login novamente.');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Erro desconhecido' }));
    throw new Error(error.message || error.detail || 'Erro na requisição');
  }

  // Handle empty responses
  const text = await response.text();
  if (!text) {
    return {} as T;
  }

  return JSON.parse(text);
}

// Auth-specific functions
export const authApi = {
  login: async (email: string, password: string, rememberMe: boolean = false) => {
    setRememberMe(rememberMe);
    const response = await apiRequest<{ 
      access_token: string; 
      refresh_token?: string;
      token_type: string 
    }>(
      '/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email, password }),
        skipAuth: true,
      }
    );
    setStoredTokens(response.access_token, response.refresh_token);
    return response;
  },

  signup: async (email: string, password: string, name: string, rememberMe: boolean = false) => {
    setRememberMe(rememberMe);
    const response = await apiRequest<{ 
      access_token: string; 
      refresh_token?: string;
      token_type: string 
    }>(
      '/auth/signup',
      {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
        skipAuth: true,
      }
    );
    setStoredTokens(response.access_token, response.refresh_token);
    return response;
  },

  logout: async () => {
    try {
      await apiRequest('/auth/logout', { method: 'POST', retryOnUnauthorized: false });
    } catch {
      // Ignore errors on logout
    } finally {
      removeStoredTokens();
      removeStoredProfileId();
      localStorage.removeItem(REMEMBER_ME_KEY);
    }
  },

  getMe: async () => {
    return apiRequest<{ id: string; email: string; name: string }>('/auth/me');
  },

  hasToken: () => !!getStoredToken(),

  // Password recovery
  requestPasswordReset: async (email: string) => {
    return apiRequest<{ message: string }>(
      '/auth/request-password-reset',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
        skipAuth: true,
      }
    );
  },

  resetPassword: async (token: string, newPassword: string) => {
    return apiRequest<{ message: string }>(
      '/auth/reset-password',
      {
        method: 'POST',
        body: JSON.stringify({ token, new_password: newPassword }),
        skipAuth: true,
      }
    );
  },

  // Manual token refresh
  refreshToken: async () => {
    const newToken = await refreshAccessToken();
    if (!newToken) {
      throw new Error('Não foi possível atualizar a sessão');
    }
    return newToken;
  },
};

// Profile-specific functions
export const profilesApi = {
  getAll: async () => {
    return apiRequest<Array<{
      id: string;
      user_id: string;
      name: string;
      description: string;
      created_at: string;
      updated_at: string;
    }>>('/auth/profiles');
  },

  create: async (data: { name: string; description?: string }) => {
    return apiRequest<{
      id: string;
      user_id: string;
      name: string;
      description: string;
      created_at: string;
      updated_at: string;
    }>('/auth/profiles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  update: async (id: string, data: { name: string; description?: string }) => {
    return apiRequest<{
      id: string;
      user_id: string;
      name: string;
      description: string;
      created_at: string;
      updated_at: string;
    }>(`/auth/profiles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  delete: async (id: string) => {
    return apiRequest<void>(`/auth/profiles/${id}`, {
      method: 'DELETE',
    });
  },

  setCurrentId: setStoredProfileId,
  getCurrentId: getStoredProfileId,
  clearCurrentId: removeStoredProfileId,
};

// Subscription-specific functions  
export const subscriptionApi = {
  get: async () => {
    return apiRequest<{ subscription: any }>('/subscription');
  },

  getInvoices: async () => {
    return apiRequest<{ invoices: any[] }>('/subscription/invoices');
  },

  cancel: async (immediately: boolean = false) => {
    return apiRequest<{ subscription: any }>('/subscription/cancel', {
      method: 'POST',
      body: JSON.stringify({ immediately }),
    });
  },

  resume: async () => {
    return apiRequest<{ subscription: any }>('/subscription/resume', {
      method: 'POST',
    });
  },

  changePlan: async (planId: string, billingCycle: string) => {
    return apiRequest<{ subscription: any }>('/subscription/change-plan', {
      method: 'POST',
      body: JSON.stringify({ planId, billingCycle }),
    });
  },

  getPortalUrl: async () => {
    return apiRequest<{ url: string }>('/subscription/portal');
  },
};
