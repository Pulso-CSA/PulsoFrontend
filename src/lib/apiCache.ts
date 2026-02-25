/**
 * API Response Cache - TTL-based in-memory cache
 * Reduz requisições repetidas e melhora performance em multi-usuário
 */

const CACHE_PREFIX = "pulso_cache_";
const DEFAULT_TTL_MS = 5 * 60 * 1000; // 5 min

interface CacheEntry<T> {
  data: T;
  expiresAt: number;
}

const memoryCache = new Map<string, CacheEntry<unknown>>();

function cacheKey(endpoint: string, body?: string): string {
  return body ? `${CACHE_PREFIX}${endpoint}:${body}` : `${CACHE_PREFIX}${endpoint}`;
}

function isExpired(entry: CacheEntry<unknown>): boolean {
  return Date.now() > entry.expiresAt;
}

export function getCached<T>(endpoint: string, body?: string): T | null {
  const key = cacheKey(endpoint, body);
  const entry = memoryCache.get(key) as CacheEntry<T> | undefined;
  if (!entry || isExpired(entry)) {
    memoryCache.delete(key);
    return null;
  }
  return entry.data;
}

export function setCache<T>(
  endpoint: string,
  data: T,
  ttlMs: number = DEFAULT_TTL_MS,
  body?: string
): void {
  const key = cacheKey(endpoint, body);
  memoryCache.set(key, {
    data,
    expiresAt: Date.now() + ttlMs,
  });
}

export function invalidateCache(endpointPattern?: string | RegExp): void {
  if (!endpointPattern) {
    memoryCache.clear();
    return;
  }
  const pattern =
    typeof endpointPattern === "string"
      ? new RegExp(endpointPattern.replace(/\*/g, ".*"))
      : endpointPattern;
  for (const key of memoryCache.keys()) {
    if (pattern.test(key.replace(CACHE_PREFIX, ""))) {
      memoryCache.delete(key);
    }
  }
}

/** TTL por tipo de endpoint (ms) */
export const CACHE_TTL = {
  profiles: 2 * 60 * 1000, // 2 min
  subscription: 5 * 60 * 1000, // 5 min
  authMe: 1 * 60 * 1000, // 1 min
} as const;
