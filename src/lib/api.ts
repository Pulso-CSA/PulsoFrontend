// Centralized API client with Bearer token handling and auto-refresh

// Em dev (Vite localhost): usa mesma origem para o proxy. Electron (file://) ou prod: usa VITE_API_URL.
const _defaultBackend = "https://pulsoapi-production-f227.up.railway.app";

export function getApiBaseUrl(): string {
  if (import.meta.env.DEV && typeof window !== "undefined") {
    const o = window.location.origin;
    // Usa proxy (mesma origem) para localhost, 127.0.0.1 ou [::1] (IPv6)
    if (o && (o.includes("localhost") || o.includes("127.0.0.1") || o.includes("[::1]"))) return o;
  }
  return (import.meta.env.VITE_API_URL || _defaultBackend).toString().trim();
}

const LOG = (tag: string, ...args: unknown[]) => {
  console.log(`[Pulso:${tag}]`, new Date().toISOString(), ...args);
};

/** Mensagem útil quando fetch falha (backend parado, porta errada, offline). */
function networkFailureHint(baseUrl: string, originalMessage: string): string {
  const b = baseUrl.replace(/\/$/, "");
  const isLocalDevOrigin =
    typeof window !== "undefined" &&
    (window.location.origin.includes("localhost") ||
      window.location.origin.includes("127.0.0.1") ||
      window.location.origin.includes("[::1]"));
  const devHint = isLocalDevOrigin
    ? " Em desenvolvimento o Vite faz proxy para o PulsoAPI em 127.0.0.1:8000 — arranque a API (ex.: na pasta PulsoAPI/api: uvicorn ou o comando do projeto) ou defina VITE_DEV_API_PROXY no .env com a URL correta."
    : "";
  return `Não foi possível contactar o servidor (${b}).${devHint} Detalhe: ${originalMessage}`;
}

// Log config no carregamento
if (typeof window !== "undefined") {
  LOG(
    "api",
    "API_BASE_URL=",
    getApiBaseUrl(),
    "VITE_API_URL=",
    import.meta.env.VITE_API_URL ?? "(não definida)",
  );
}

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
  // Lê do mesmo storage onde escrevemos (getStorage), evitando token antigo em outro storage
  return getStorage().getItem(TOKEN_KEY);
}

export function getStoredRefreshToken(): string | null {
  return getStorage().getItem(REFRESH_TOKEN_KEY);
}

export function setStoredTokens(accessToken: string, refreshToken?: string): void {
  const storage = getStorage();
  // Limpa tokens antigos do outro storage (ex: token expirado em localStorage ao signup com rememberMe=false)
  const other = storage === localStorage ? sessionStorage : localStorage;
  other.removeItem(TOKEN_KEY);
  other.removeItem(REFRESH_TOKEN_KEY);

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
    const response = await fetch(`${getApiBaseUrl()}/auth/refresh`, {
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

/** Base URL alternativa (motor local CSA em Electron). */
export type ApiRequestBaseOverride = { baseUrl: string; localToken?: string };

export type LocalApiConfig = { baseUrl: string; token: string };

/** Estado do motor CSA no Electron (painel de diagnóstico). */
export type LocalEngineDiagnostics = {
  engineRunning: boolean;
  config: LocalApiConfig | null;
  lastStartError: string | null;
  apiRoot: string | null;
  allowRootsPath: string | null;
  allowedRootCount: number;
  allowedRootsPreview: string[];
  logFilePath: string | null;
  /** null = pasta ainda não preenchida */
  folderInAllowlist: boolean | null;
  isPackaged: boolean;
  relaxAllowlistInDev: boolean;
  pulsoApiCandidates?: { path: string; exists: boolean }[];
  manualPulsoapiFile?: string | null;
  envPulsoApiRoot?: string | null;
  frontendRoot?: string | null;
};

let _localApiConfigCache: { value: LocalApiConfig | null; at: number } | null = null;
const LOCAL_API_CONFIG_TTL_MS = 1500;

/** Config do FastAPI local (127.0.0.1); null fora do Electron ou se o motor não subiu. */
export async function getLocalApiConfig(): Promise<LocalApiConfig | null> {
  if (typeof window === 'undefined') return null;
  const api = (window as unknown as { electronAPI?: { getLocalApiConfig?: () => Promise<LocalApiConfig | null> } }).electronAPI;
  if (!api?.getLocalApiConfig) return null;
  const now = Date.now();
  if (_localApiConfigCache && now - _localApiConfigCache.at < LOCAL_API_CONFIG_TTL_MS) {
    return _localApiConfigCache.value;
  }
  const value = await api.getLocalApiConfig();
  _localApiConfigCache = { value, at: now };
  return value;
}

/** Diagnóstico motor local + allowlist (só Electron). */
export async function getLocalEngineDiagnostics(
  folderPath?: string,
): Promise<LocalEngineDiagnostics | null> {
  if (typeof window === 'undefined') return null;
  const w = window as unknown as {
    electronAPI?: { getLocalDiagnostics?: (p: string) => Promise<LocalEngineDiagnostics> };
  };
  if (!w.electronAPI?.getLocalDiagnostics) return null;
  return w.electronAPI.getLocalDiagnostics(folderPath ?? '');
}

export async function apiRequest<T>(
  endpoint: string,
  options: RequestOptions = {},
  baseOverride?: ApiRequestBaseOverride | null,
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

  if (baseOverride?.localToken) {
    requestHeaders['X-Pulso-Local-Token'] = baseOverride.localToken;
  }

  const base = (baseOverride?.baseUrl ?? getApiBaseUrl()).replace(/\/$/, '');
  const fullUrl = `${base}${endpoint}`;
  LOG("apiRequest", "→", fetchOptions.method || "GET", fullUrl, {
    hasAuth: !!requestHeaders["Authorization"],
    body: fetchOptions.body ? "(presente)" : "(vazio)",
  });

  let response: Response;
  try {
    response = await fetch(fullUrl, {
      ...fetchOptions,
      headers: requestHeaders,
    });
  } catch (fetchErr) {
    LOG("apiRequest", "FETCH FALHOU (rede/CORS?)", endpoint, fetchErr);
    const raw =
      fetchErr instanceof Error ? fetchErr.message : String(fetchErr ?? "erro de rede");
    if (/failed to fetch|networkerror|load failed|network request failed/i.test(raw)) {
      throw new Error(networkFailureHint(base, raw));
    }
    throw fetchErr;
  }

  LOG("apiRequest", "←", response.status, endpoint, {
    ok: response.ok,
    statusText: response.statusText,
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
      let retryResponse: Response;
      try {
        retryResponse = await fetch(`${base}${endpoint}`, {
          ...fetchOptions,
          headers: requestHeaders,
        });
      } catch (reErr) {
        const raw = reErr instanceof Error ? reErr.message : String(reErr ?? "erro de rede");
        if (/failed to fetch|networkerror|load failed|network request failed/i.test(raw)) {
          throw new Error(networkFailureHint(base, raw));
        }
        throw reErr;
      }

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
    LOG("apiRequest", "ERRO", response.status, endpoint, "body:", error);
    const msg = error?.detail ?? error?.message ?? error?.msg ?? 'Erro na requisição';
    let errorMessage =
      typeof msg === 'string'
        ? msg
        : msg && typeof msg === 'object'
          ? String((msg as Record<string, unknown>).message ?? (msg as Record<string, unknown>).msg ?? JSON.stringify(msg))
          : 'Erro na requisição';

    // Railway devolve 404 JSON com "Application not found" quando o domínio não tem app a escutar (URL antiga, serviço parado, etc.)
    if (
      response.status === 404 &&
      typeof errorMessage === 'string' &&
      /application not found/i.test(errorMessage)
    ) {
      errorMessage = `${errorMessage} — A URL da API não está alcançando o backend (comum no Railway: serviço parado, domínio antigo ou URL errada). Verifique VITE_API_URL e o deploy no painel do Railway. Em desenvolvimento: npm run dev e API em 127.0.0.1:8000.`;
    }

    throw new Error(errorMessage);
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
    LOG("authApi.login", "iniciando", { email, rememberMe });
    setRememberMe(rememberMe);
    try {
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
      LOG("authApi.login", "sucesso", { hasToken: !!response.access_token });
      setStoredTokens(response.access_token, response.refresh_token);
      return response;
    } catch (err) {
      LOG("authApi.login", "erro", err instanceof Error ? err.message : err);
      throw err;
    }
  },

  signup: async (email: string, password: string, name: string, rememberMe: boolean = false) => {
    LOG("authApi.signup", "iniciando", { email, name, rememberMe });
    setRememberMe(rememberMe);
    try {
      const response = await apiRequest<{ 
      access_token: string;
      accessToken?: string; // fallback camelCase
      refresh_token?: string;
      refreshToken?: string;
      token_type?: string;
      user?: { id: string; email: string; name: string };
      id?: string;
    }>(
      '/auth/signup',
      {
        method: 'POST',
        body: JSON.stringify({ email, password, name }),
        skipAuth: true,
      }
    );
      const accessToken = response.access_token ?? response.accessToken;
      const refreshToken = response.refresh_token ?? response.refreshToken;
      if (!accessToken) throw new Error('Token não retornado pelo servidor');
      LOG("authApi.signup", "sucesso", { hasToken: !!accessToken });
      setStoredTokens(accessToken, refreshToken);
      return { ...response, access_token: accessToken, refresh_token: refreshToken, user: response.user };
    } catch (err) {
      LOG("authApi.signup", "erro", err instanceof Error ? err.message : err);
      throw err;
    }
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
    return apiRequest<{ id: string; email: string; name: string; picture?: string }>('/auth/me');
  },

  updateMe: async (payload: { name?: string; email?: string; new_password?: string; picture?: string }) => {
    return apiRequest<{ id: string; name: string; email: string; picture?: string }>('/auth/me', {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
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

export { invalidateCache } from './apiCache';
import { getCached, setCache, invalidateCache, CACHE_TTL } from './apiCache';

type ProfileItem = {
  id: string;
  user_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
};

// Profile-specific functions
export const profilesApi = {
  getAll: async () => {
    const cached = getCached<ProfileItem[]>('/auth/profiles');
    if (cached) return cached;
    const data = await apiRequest<ProfileItem[]>('/auth/profiles');
    setCache('/auth/profiles', data, CACHE_TTL.profiles);
    return data;
  },

  create: async (data: { name: string; description?: string }) => {
    const result = await apiRequest<ProfileItem>('/auth/profiles', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    invalidateCache('/auth/profiles');
    return result;
  },

  update: async (id: string, data: { name: string; description?: string }) => {
    const result = await apiRequest<ProfileItem>(`/auth/profiles/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    invalidateCache('/auth/profiles');
    return result;
  },

  delete: async (id: string) => {
    const result = await apiRequest<void>(`/auth/profiles/${id}`, {
      method: 'DELETE',
    });
    invalidateCache('/auth/profiles');
    return result;
  },

  setCurrentId: setStoredProfileId,
  getCurrentId: getStoredProfileId,
  clearCurrentId: removeStoredProfileId,
};

// Subscription-specific functions  
export const subscriptionApi = {
  get: async () => {
    const cached = getCached<{ subscription: unknown }>('/subscription');
    if (cached) return cached;
    const data = await apiRequest<{ subscription: unknown }>('/subscription');
    setCache('/subscription', data, CACHE_TTL.subscription);
    return data;
  },

  getInvoices: async () => {
    return apiRequest<{ invoices: unknown[] }>('/subscription/invoices');
  },

  cancel: async (immediately: boolean = false) => {
    const result = await apiRequest<{ subscription: unknown }>('/subscription/cancel', {
      method: 'POST',
      body: JSON.stringify({ immediately }),
    });
    invalidateCache('/subscription');
    return result;
  },

  resume: async () => {
    const result = await apiRequest<{ subscription: unknown }>('/subscription/resume', {
      method: 'POST',
    });
    invalidateCache('/subscription');
    return result;
  },

  changePlan: async (planId: string, billingCycle: string) => {
    const result = await apiRequest<{ subscription: unknown }>('/subscription/change-plan', {
      method: 'POST',
      body: JSON.stringify({ planId, billingCycle }),
    });
    invalidateCache('/subscription');
    return result;
  },

  getPortalUrl: async () => {
    return apiRequest<{ url: string }>('/subscription/portal');
  },

  checkout: async (payload: {
    planId: string;
    billingCycle?: string;
    successUrl?: string;
    cancelUrl?: string;
  }) => {
    return apiRequest<{ checkout_url: string }>('/subscription/checkout', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

// Inteligência de Dados API – db_config flexível (SQL: host/port/user/password; MongoDB: uri/database, user/password opcionais)
export type DbConfig = {
  db_type?: string;
  host?: string;
  port?: number;
  user?: string;
  password?: string;
  database: string;
  uri?: string;
  dataset_ref?: string;
};

export const inteligenciaApi = {
  query: async (payload: {
    prompt: string;
    db_config: DbConfig;
  }) => {
    return apiRequest<{ answer?: string; result?: unknown; data?: unknown }>('/inteligencia-dados/query', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  capturaDados: async (payload: {
    id_requisicao: string;
    usuario?: string;
    tipo_base: string;
    db_config: DbConfig;
    incluir_amostra?: boolean;
    max_rows_amostra?: number;
  }) => {
    return apiRequest<{
      message?: string;
      dataset_ref?: string;
      tabelas?: unknown[];
      estrutura?: unknown;
      captura_dados?: {
        tipo_base?: string;
        tabelas?: string[];
        quantidade_tabelas?: number;
        quantidade_registros?: Record<string, number>;
        teor_dados?: string;
        indices?: Record<string, unknown[]>;
        consultas_exploracao?: string[];
        amostra?: { colunas: string[]; linhas: Record<string, unknown>[] };
      };
    }>('/inteligencia-dados/captura-dados', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** POST /inteligencia-dados/chat - db_config opcional; sem conexão, backend retorna instruções */
  chat: async (payload: {
    mensagem: string;
    id_requisicao: string;
    db_config?: DbConfig;
    usuario?: string;
    dataset_ref?: string;
    model_ref?: string;
  }) => {
    return apiRequest<{
      id_requisicao?: string;
      resposta_texto: string;
      sugestao_proximo_passo?: string;
      etapas_executadas?: string[];
      dataset_ref?: string;
      model_ref?: string;
      captura_dados?: {
        tipo_base?: string;
        tabelas?: string[];
        quantidade_registros?: Record<string, number>;
        teor_dados?: string;
        amostra?: { colunas: string[]; linhas: Record<string, unknown>[] };
      };
      analise_estatistica?: {
        graficos_metadados?: Array<{ tipo?: string; titulo?: string; eixo_x?: string; eixo_y?: string; explicacao?: string; vantagens?: string[]; desvantagens?: string[] }>;
        graficos_dados?: Array<{ labels?: string[]; values?: number[]; x?: number[]; y?: number[] }>;
      };
      amostra?: { colunas: string[]; linhas: Record<string, unknown>[] };
      modelo_ml?: {
        modelo_escolhido?: string;
        resultados?: Record<string, number>;
        matriz_confusao?: number[][];
        importancia_variaveis?: Array<{ variavel?: string; variable?: string; importancia?: number; importance?: number }>;
        metricas_negocio?: { total_amostra?: number; distribuicao_classe?: Record<string, number> };
        modelos_comparados?: Array<Record<string, string | number>>;
        previsoes_amostra?: unknown[];
      };
    }>('/inteligencia-dados/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

export type InsightsServiceFilter = "pulso" | "cloud" | "finops" | "data" | "custom";
export type InsightsChartType = "area" | "bar" | "line" | "pie" | "progress";

export type InsightsWidgetResponse = {
  id: string;
  title: string;
  value: string;
  trend: string;
  period: string;
  chart_type: InsightsChartType;
  progress_percent?: number;
  insights: string[];
  service_filter?: InsightsServiceFilter;
  custom_prompt?: string;
  analysis_summary?: string;
  technical_conclusion?: string;
  data?: Array<{ label: string; value: number }>;
};

export const insightsApi = {
  listWidgets: async () => {
    return apiRequest<{ widgets: InsightsWidgetResponse[] }>("/inteligencia-dados/insights/widgets");
  },

  generateWidget: async (payload: {
    prompt: string;
    id_requisicao: string;
    dataset_ref?: string;
    service_filter?: InsightsServiceFilter;
  }) => {
    return apiRequest<{
      id_requisicao: string;
      dataset_ref?: string;
      widget: InsightsWidgetResponse;
    }>("/inteligencia-dados/insights/generate", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};

// FinOps API
export const finopsApi = {
  chat: async (payload: {
    mensagem: string;
    id_requisicao?: string;
    usuario?: string;
    aws_credentials?: { access_key_id: string; secret_access_key: string; region: string };
    azure_credentials?: { tenant_id: string; client_id: string; client_secret: string; subscription_id: string };
    gcp_credentials?: { service_account_json: Record<string, unknown>; project_id: string };
  }) => {
    return apiRequest<{
      resposta_texto: string;
      id_requisicao?: string;
      cloud?: string;
      etapas_executadas?: string[];
    }>('/finops/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  analyze: async (payload: {
    mensagem?: string;
    id_requisicao?: string;
    usuario?: string;
    aws_credentials?: { access_key_id: string; secret_access_key: string; region: string };
    azure_credentials?: { tenant_id: string; client_id: string; client_secret: string; subscription_id: string };
    gcp_credentials?: { service_account_json: Record<string, unknown>; project_id: string };
  }) => {
    return apiRequest<{ message: string }>('/finops/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

// Infra (Cloud) API
export const infraApi = {
  analyze: async (payload: {
    root_path?: string;
    tenant_id?: string;
    id_requisicao?: string;
    user_request?: string;
    providers?: string[];
    envs?: Record<string, string>;
  }) => {
    return apiRequest<{
      repo_context?: string;
      infra_spec_draft?: unknown;
      cost_estimate?: unknown;
    }>('/infra/analyze', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  generate: async (payload: {
    infra_spec?: unknown;
    user_request?: string;
    root_path?: string;
    tenant_id?: string;
    id_requisicao?: string;
  }) => {
    return apiRequest<{
      message?: string;
      terraform_code?: string;
      artifacts?: unknown;
    }>('/infra/generate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

/** Resposta final de POST /comprehension/run (síncrono ou após polling do job). */
export type ComprehensionRunResponse = {
  intent: string;
  project_state: string;
  should_execute: boolean;
  target_endpoint: string | null;
  explanation: string;
  next_action: string;
  message: string;
  file_tree: string | null;
  system_behavior: Record<string, unknown> | null;
  frontend_suggestion: string | null;
  curl_commands?: string[];
  preview_frontend_url?: string | null;
  language?: string;
  framework?: string;
};

/** Alinhado a PULSO_CSA_WORKFLOW_MAX_SEC (300 s) no backend + margem de rede. */
const CSA_CLIENT_BUDGET_MS = 5 * 60 * 1000 + 20_000;

const COMPREHENSION_POLL_INTERVAL_MS = 2000;
const COMPREHENSION_POLL_MAX_MS = 5 * 60 * 1000;

/**
 * fetch com Bearer + token local; em 401 tenta refresh uma vez (mesmo padrão de apiRequest).
 */
async function fetchWithAuthRetry(
  fullUrl: string,
  fetchOptions: RequestInit,
  baseOverride: ApiRequestBaseOverride | null,
): Promise<Response> {
  const method = (fetchOptions.method || 'GET').toUpperCase();
  const hasJsonBody =
    fetchOptions.body != null && method !== 'GET' && method !== 'HEAD';
  const requestHeaders: Record<string, string> = {
    ...(hasJsonBody ? { 'Content-Type': 'application/json' } : {}),
    ...(fetchOptions.headers as Record<string, string> | undefined),
  };

  const token = await getValidToken();
  if (token) requestHeaders['Authorization'] = `Bearer ${token}`;
  if (baseOverride?.localToken) {
    requestHeaders['X-Pulso-Local-Token'] = baseOverride.localToken;
  }

  let response = await fetch(fullUrl, {
    ...fetchOptions,
    headers: requestHeaders,
    signal: fetchOptions.signal,
  });

  if (response.status === 401) {
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = refreshAccessToken();
    }
    const newToken = await refreshPromise;
    isRefreshing = false;
    refreshPromise = null;

    if (newToken) {
      requestHeaders['Authorization'] = `Bearer ${newToken}`;
      response = await fetch(fullUrl, {
        ...fetchOptions,
        headers: requestHeaders,
        signal: fetchOptions.signal,
      });
    } else {
      removeStoredTokens();
      removeStoredProfileId();
      dispatchSessionExpired();
      throw new Error('Sessão expirada. Faça login novamente.');
    }
  }

  return response;
}

async function parseJsonErrorAndThrow(response: Response, endpoint: string): Promise<never> {
  const error = await response.json().catch(() => ({ message: 'Erro desconhecido' }));
  LOG('apiRequest', 'ERRO', response.status, endpoint, 'body:', error);
  const msg = (error as { detail?: unknown; message?: unknown; msg?: unknown }).detail ??
    (error as { message?: unknown }).message ??
    (error as { msg?: unknown }).msg ??
    'Erro na requisição';
  let errorMessage =
    typeof msg === 'string'
      ? msg
      : msg && typeof msg === 'object'
        ? String(
            (msg as Record<string, unknown>).message ??
              (msg as Record<string, unknown>).msg ??
              JSON.stringify(msg),
          )
        : 'Erro na requisição';
  if (
    response.status === 404 &&
    typeof errorMessage === 'string' &&
    /application not found/i.test(errorMessage)
  ) {
    errorMessage = `${errorMessage} — A URL da API não está alcançando o backend (comum no Railway: serviço parado, domínio antigo ou URL errada). Verifique VITE_API_URL e o deploy no painel do Railway. Em desenvolvimento: npm run dev e API em 127.0.0.1:8000.`;
  }
  throw new Error(errorMessage);
}

async function pollComprehensionJob(
  base: string,
  pollPath: string,
  baseOverride: ApiRequestBaseOverride | null,
  outerSignal: AbortSignal | undefined,
): Promise<ComprehensionRunResponse> {
  const deadline = Date.now() + COMPREHENSION_POLL_MAX_MS;
  LOG('comprehensionPoll', 'polling', pollPath);

  while (Date.now() < deadline) {
    await new Promise((r) => setTimeout(r, COMPREHENSION_POLL_INTERVAL_MS));
    const url = `${base}${pollPath}`;
    let res: Response;
    try {
      res = await fetchWithAuthRetry(
        url,
        {
          method: 'GET',
          ...(outerSignal ? { signal: outerSignal } : {}),
        },
        baseOverride,
      );
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') {
        throw new Error(
          'Tempo máximo de 5 minutos para a operação Pulso CSA (rede + geração). Tente um pedido mais específico.',
        );
      }
      throw e;
    }
    if (!res.ok) {
      await parseJsonErrorAndThrow(res, pollPath);
    }
    const data = (await res.json()) as {
      status?: string;
      response?: ComprehensionRunResponse | null;
      error?: { code?: string; message?: string } | null;
    };
    const st = data.status;
    if (
      st !== 'pending' &&
      st !== 'running' &&
      st !== 'completed' &&
      st !== 'failed'
    ) {
      LOG('comprehensionPoll', 'estado inválido ou ausente', data);
      throw new Error(
        st
          ? `Estado de job desconhecido: ${String(st)}`
          : 'Resposta inválida ao consultar o job (sem status).',
      );
    }
    if (data.status === 'completed') {
      if (!data.response || typeof data.response !== 'object') {
        throw new Error('Workflow concluído sem corpo de resposta.');
      }
      return data.response;
    }
    if (data.status === 'failed') {
      const m = data.error?.message ?? data.error?.code ?? 'Workflow falhou.';
      throw new Error(typeof m === 'string' ? m : JSON.stringify(m));
    }
  }
  throw new Error(
    'Tempo máximo de 5 minutos ao aguardar o workflow de compreensão. Tente um pedido mais curto ou em etapas.',
  );
}

async function postComprehensionRun(
  endpointPath: string,
  body: string,
  baseOverride: ApiRequestBaseOverride | null,
): Promise<ComprehensionRunResponse> {
  const base = (baseOverride?.baseUrl ?? getApiBaseUrl()).replace(/\/$/, '');
  /** Motor local (127.0.0.1): síncrono evita 202 + job em memória e garante escrita na pasta do PC. */
  const asyncOff =
    baseOverride != null
      ? (endpointPath.includes('?') ? '&' : '?') + 'async_mode=false'
      : '';
  const fullUrl = `${base}${endpointPath}${asyncOff}`;
  LOG('comprehensionRun', 'POST', fullUrl, baseOverride ? '(local, async_mode=false)' : '(cloud)');

  const budgetController = new AbortController();
  const budgetTimer = globalThis.setTimeout(() => budgetController.abort(), CSA_CLIENT_BUDGET_MS);

  let response: Response;
  try {
    response = await fetchWithAuthRetry(
      fullUrl,
      { method: 'POST', body, signal: budgetController.signal },
      baseOverride,
    );
  } catch (err) {
    clearTimeout(budgetTimer);
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new Error(
        'Tempo máximo de 5 minutos para a operação Pulso CSA (rede + geração). Tente um pedido mais específico.',
      );
    }
    throw err;
  }

  if (response.status === 401) {
    clearTimeout(budgetTimer);
    removeStoredTokens();
    removeStoredProfileId();
    dispatchSessionExpired();
    throw new Error('Sessão expirada. Faça login novamente.');
  }

  if (response.status === 202) {
    const accept = (await response.json()) as {
      job_id?: string;
      poll_path?: string;
    };
    const jobId = accept.job_id;
    const defaultPoll = endpointPath.includes('comprehension-js')
      ? `/comprehension-js/jobs/${jobId}`
      : `/comprehension/jobs/${jobId}`;
    const pollPath =
      typeof accept.poll_path === 'string' && accept.poll_path.startsWith('/')
        ? accept.poll_path
        : jobId
          ? defaultPoll
          : '';
    if (!pollPath || !jobId) {
      clearTimeout(budgetTimer);
      throw new Error('Resposta 202 inválida: falta job_id ou poll_path.');
    }
    try {
      return await pollComprehensionJob(
        base,
        pollPath,
        baseOverride,
        budgetController.signal,
      );
    } finally {
      clearTimeout(budgetTimer);
    }
  }

  if (!response.ok) {
    clearTimeout(budgetTimer);
    await parseJsonErrorAndThrow(response, endpointPath);
  }

  const text = await response.text();
  clearTimeout(budgetTimer);
  if (!text) {
    return {} as ComprehensionRunResponse;
  }
  return JSON.parse(text) as ComprehensionRunResponse;
}

// Workflow API (legado; preferir comprehensionApi para o fluxo do chat)
export const workflowApi = {
  runCorrect: async (payload: {
    usuario: string;
    prompt: string;
    root_path: string;
    env_content?: string;
  }) => {
    return apiRequest<{ request_id?: string; message?: string }>('/workflow/correct/run', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

// Comprehension API – entrada única do fluxo (análise/criação/correção)
export const comprehensionApi = {
  run: async (
    payload: {
      usuario: string;
      prompt: string;
      root_path: string | null;
      use_python?: boolean;
      use_javascript?: boolean;
      use_typescript?: boolean;
      use_react?: boolean;
      use_vue?: boolean;
      use_angular?: boolean;
    },
    endpoint: string = 'comprehension',
  ) => {
    const endpointPath =
      endpoint === 'comprehension-js' ? '/comprehension-js/run' : '/comprehension/run';
    const localCfg = await getLocalApiConfig();
    const baseOverride = localCfg
      ? { baseUrl: localCfg.baseUrl, localToken: localCfg.token }
      : null;
    return postComprehensionRun(endpointPath, JSON.stringify(payload), baseOverride);
  },
};

// Preview API – inicia servidor de desenvolvimento (npm run dev / streamlit run)
export const previewApi = {
  start: async (payload: { root_path: string; project_type?: "auto" | "javascript" | "python" }) => {
    const localCfg = await getLocalApiConfig();
    const baseOverride = localCfg
      ? { baseUrl: localCfg.baseUrl, localToken: localCfg.token }
      : null;
    return apiRequest<{
      success: boolean;
      preview_url?: string | null;
      /** URL do frontend (alternativa a preview_url). Backend pode retornar um ou outro. */
      preview_frontend_url?: string | null;
      /** Backend retorna sempre false. Quando false: NUNCA abrir nova aba/terminal/navegador automaticamente. */
      preview_auto_open?: boolean;
      message?: string;
      project_type?: string;
      details?: unknown;
    }>("/preview/start", {
      method: "POST",
      body: JSON.stringify({ ...payload, project_type: payload.project_type ?? "auto" }),
    }, baseOverride);
  },
};

// Deploy / Logs API - Docker e Venv
export const deployApi = {
  // Docker
  docker: {
    getLogs: () => apiRequest<{ logs?: string; lines?: string[] }>('/deploy/docker/logs'),
    clearLogs: () => apiRequest<void>('/deploy/docker/logs/clear', { method: 'DELETE' }),
    start: () => apiRequest<{ message?: string }>('/deploy/docker/start', { method: 'POST' }),
    rebuild: () => apiRequest<{ message?: string }>('/deploy/docker/rebuild', { method: 'POST' }),
    stop: () => apiRequest<{ message?: string }>('/deploy/docker/stop', { method: 'POST' }),
  },
  // Venv
  venv: {
    getLogs: () => apiRequest<{ logs?: string; lines?: string[] }>('/venv/logs'),
    clearLogs: () => apiRequest<void>('/venv/logs/clear', { method: 'DELETE' }),
    create: () => apiRequest<{ message?: string }>('/venv/create', { method: 'POST' }),
    recreate: () => apiRequest<{ message?: string }>('/venv/recreate', { method: 'POST' }),
    deactivate: () => apiRequest<{ message?: string }>('/venv/deactivate', { method: 'POST' }),
  },
};

// SFAP — Sistema Financeiro Administrativo Pulso (requer X-Profile-Id)
function sfapHeaders(): Record<string, string> {
  const profileId = profilesApi.getCurrentId();
  if (!profileId) return {};
  return { 'X-Profile-Id': profileId };
}

export const sfapApi = {
  visibility: async (): Promise<{ allowed: boolean }> => {
    const h = sfapHeaders();
    if (!h['X-Profile-Id']) return { allowed: false };
    return apiRequest<{ allowed: boolean }>('/sfap/visibility', { headers: h });
  },
  dashboard: async (): Promise<{ receita_total_usd: number; custo_total_usd: number; saldo_usd: number }> => {
    return apiRequest('/sfap/dashboard', { headers: sfapHeaders() });
  },
  planos: {
    list: async (tipo?: string): Promise<PlanoItem[]> => {
      const q = tipo ? `?tipo=${encodeURIComponent(tipo)}` : '';
      return apiRequest<PlanoItem[]>(`/sfap/planos${q}`, { headers: sfapHeaders() });
    },
    create: async (data: PlanoCreate): Promise<PlanoItem> => {
      return apiRequest<PlanoItem>('/sfap/planos', { method: 'POST', body: JSON.stringify(data), headers: sfapHeaders() });
    },
    update: async (id: string, data: Partial<PlanoCreate>): Promise<PlanoItem> => {
      return apiRequest<PlanoItem>(`/sfap/planos/${id}`, { method: 'PATCH', body: JSON.stringify(data), headers: sfapHeaders() });
    },
    delete: async (id: string): Promise<void> => {
      return apiRequest<void>(`/sfap/planos/${id}`, { method: 'DELETE', headers: sfapHeaders() });
    },
  },
  movimentos: {
    list: async (params?: { tipo?: string; categoria?: string; data_inicio?: string; data_fim?: string }): Promise<MovimentoItem[]> => {
      const sp = new URLSearchParams();
      if (params?.tipo) sp.set('tipo', params.tipo);
      if (params?.categoria) sp.set('categoria', params.categoria);
      if (params?.data_inicio) sp.set('data_inicio', params.data_inicio);
      if (params?.data_fim) sp.set('data_fim', params.data_fim);
      const q = sp.toString() ? `?${sp.toString()}` : '';
      return apiRequest<MovimentoItem[]>(`/sfap/movimentos${q}`, { headers: sfapHeaders() });
    },
    create: async (data: MovimentoCreate): Promise<MovimentoItem> => {
      return apiRequest<MovimentoItem>('/sfap/movimentos', { method: 'POST', body: JSON.stringify(data), headers: sfapHeaders() });
    },
    update: async (id: string, data: Partial<MovimentoCreate>): Promise<MovimentoItem> => {
      return apiRequest<MovimentoItem>(`/sfap/movimentos/${id}`, { method: 'PATCH', body: JSON.stringify(data), headers: sfapHeaders() });
    },
    delete: async (id: string): Promise<void> => {
      return apiRequest<void>(`/sfap/movimentos/${id}`, { method: 'DELETE', headers: sfapHeaders() });
    },
  },
};

export type PlanoItem = {
  id: string;
  tipo_plano: string;
  preco_unit_usd: number;
  taxa_stripe_unit_usd: number;
  taxa_stripe_total_10k_usd: number;
  lucro_100_usd: number;
  lucro_1000_usd: number;
  lucro_10000_usd: number;
  created_at?: string;
  updated_at?: string;
};

export type PlanoCreate = {
  tipo_plano: string;
  preco_unit_usd: number;
  taxa_stripe_unit_usd: number;
  taxa_stripe_total_10k_usd: number;
  lucro_100_usd: number;
  lucro_1000_usd: number;
  lucro_10000_usd: number;
};

export type MovimentoItem = {
  id: string;
  data: string;
  tipo: 'ganho' | 'gasto';
  categoria: string;
  descricao: string;
  valor_usd: number;
  moeda: string;
  notas?: string;
  recorrencia?: string;
  recorrencia_intervalo?: number;
  recorrencia_unidade?: string;
  plano_tipo?: string;
  plano_preco?: number;
  num_usuarios?: number;
  created_at?: string;
  updated_at?: string;
};

export type MovimentoCreate = {
  data: string;
  tipo: 'ganho' | 'gasto';
  categoria: string;
  descricao: string;
  valor_usd: number;
  moeda: string;
  notas?: string;
  recorrencia?: string;
  recorrencia_intervalo?: number;
  recorrencia_unidade?: string;
  plano_tipo?: string;
  plano_preco?: number;
  num_usuarios?: number;
};
