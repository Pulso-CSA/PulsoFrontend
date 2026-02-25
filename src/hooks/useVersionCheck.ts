import { useState, useEffect, useCallback } from "react";
import { fetchVersion, type VersionInfo } from "@/lib/version";

const CURRENT_VERSION = (import.meta.env.VITE_APP_VERSION as string) || "0.0.0";

function compareVersions(a: string, b: string): number {
  const pa = a.split(".").map(Number);
  const pb = b.split(".").map(Number);
  for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
    const va = pa[i] ?? 0;
    const vb = pb[i] ?? 0;
    if (va !== vb) return va - vb;
  }
  return 0;
}

export interface VersionCheckResult {
  data: VersionInfo | null;
  loading: boolean;
  error: string | null;
  shouldBlock: boolean;
  forceUpgrade: boolean;
  latestVersion: string | null;
  currentVersion: string;
  refetch: () => Promise<void>;
}

export function useVersionCheck(platform = "win"): VersionCheckResult {
  const [data, setData] = useState<VersionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const doFetch = useCallback(async () => {
    if (import.meta.env.VITE_VERSION_CHECK_ENABLED !== "true") {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const info = await fetchVersion(platform);
      setData(info);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao verificar versão");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [platform]);

  useEffect(() => {
    doFetch();
  }, [doFetch]);

  const intervalMs = Number(import.meta.env.VITE_VERSION_CHECK_INTERVAL_MS) || 3600000;
  useEffect(() => {
    if (import.meta.env.VITE_VERSION_CHECK_ENABLED !== "true" || intervalMs <= 0) return;
    const id = setInterval(doFetch, intervalMs);
    return () => clearInterval(id);
  }, [doFetch, intervalMs]);

  const shouldBlock =
    !!data?.forceUpgrade &&
    compareVersions(CURRENT_VERSION, data.minClientVersion) < 0;

  return {
    data,
    loading,
    error,
    shouldBlock,
    forceUpgrade: !!data?.forceUpgrade,
    latestVersion: data?.latestVersion ?? null,
    currentVersion: CURRENT_VERSION,
    refetch: doFetch,
  };
}
