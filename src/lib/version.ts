const API_URL = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").toString().trim();

export interface VersionInfo {
  minClientVersion: string;
  latestVersion: string;
  releaseNotes: string | null;
  forceUpgrade: boolean;
  downloadUrl: string | null;
  platform: string;
}

export async function fetchVersion(platform = "win"): Promise<VersionInfo> {
  const res = await fetch(`${API_URL}/api/version?platform=${platform}`);
  if (!res.ok) throw new Error("Falha ao buscar versão");
  return res.json();
}

export interface VersionUpdatePayload {
  platform: string;
  minClientVersion?: string;
  latestVersion?: string;
  releaseNotes?: string | null;
  forceUpgrade?: boolean;
  downloadUrl?: string | null;
}

export async function updateVersion(
  token: string,
  payload: VersionUpdatePayload
): Promise<VersionInfo> {
  const res = await fetch(`${API_URL}/api/version`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Falha ao atualizar versão");
  }
  return res.json();
}
