/**
 * Utilitário para exportar relatórios de chat.
 * - Electron: salva em C:\Users\pytho\Desktop\Study\docs (ou path configurável)
 * - Web: download via blob (Save As)
 */

const DEFAULT_SAVE_PATH = "C:\\Users\\pytho\\Desktop\\Study\\docs";

interface StoredReportItem {
  id: string;
  filename: string;
  createdAt: string;
  content?: string;
  format?: "txt" | "md";
}

export interface ExportOptions {
  serviceId: string;
  sessionId?: string;
  format?: "txt" | "md";
  messages: Array<{ role: string; content: string; timestamp?: string | Date }>;
}

function formatReport(options: ExportOptions): string {
  const { serviceId, messages, format = "txt" } = options;
  const lines: string[] = [];
  const sep = format === "md" ? "\n\n" : "\n";

  lines.push(`# Relatório - ${serviceId}`);
  lines.push(`Gerado em: ${new Date().toISOString()}`);
  lines.push("");

  for (const m of options.messages) {
    const role = m.role === "user" ? "Usuário" : "Sistema";
    const content = typeof m.content === "string" ? m.content : String(m.content);
    if (format === "md") {
      lines.push(`## ${role}`);
      lines.push(content);
      lines.push("");
    } else {
      lines.push(`[${role}]`);
      lines.push(content);
      lines.push("---");
    }
  }

  return lines.join(sep);
}

function getFilename(serviceId: string, format: string): string {
  const ts = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
  return `relatorio-${serviceId}-${ts}.${format}`;
}

function registerReport(serviceId: string, filename: string, content: string, format: "txt" | "md") {
  const key = `pulso_reports_${serviceId}`;
  const nextItem: StoredReportItem = {
    id: `report-${crypto.randomUUID()}`,
    filename,
    createdAt: new Date().toISOString(),
    content,
    format,
  };
  try {
    const raw = localStorage.getItem(key);
    const current = raw ? (JSON.parse(raw) as StoredReportItem[]) : [];
    const safeCurrent = Array.isArray(current) ? current : [];
    const next = [nextItem, ...safeCurrent].slice(0, 100);
    localStorage.setItem(key, JSON.stringify(next));
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("pulso-reports-updated", { detail: { serviceId } }));
    }
  } catch {
    // Se storage estiver indisponível, exportação continua normalmente.
  }
}

/** Download via blob (web) */
export function downloadReportAsBlob(options: ExportOptions): void {
  const { format = "txt" } = options;
  const content = formatReport(options);
  const filename = getFilename(options.serviceId, format);
  const blob = new Blob([content], { type: format === "md" ? "text/markdown" : "text/plain" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
  registerReport(options.serviceId, filename, content, format);
}

/** Salva em disco (Electron) - requer IPC save-report */
export async function saveReportToDisk(options: ExportOptions): Promise<boolean> {
  const win = typeof window !== "undefined" ? window : null;
  const electronAPI = (win as Window & { electronAPI?: { saveReport: (path: string, content: string) => Promise<boolean> } })?.electronAPI;
  if (!electronAPI?.saveReport) return false;

  const { format = "txt" } = options;
  const content = formatReport(options);
  const filename = getFilename(options.serviceId, format);
  const fullPath = `${DEFAULT_SAVE_PATH}\\${filename}`;
  const ok = await electronAPI.saveReport(fullPath, content);
  if (ok === true) registerReport(options.serviceId, filename, content, format);
  return ok === true;
}

/** Exporta relatório: tenta Electron, fallback para download blob */
export async function exportReport(options: ExportOptions): Promise<"saved" | "downloaded"> {
  const saved = await saveReportToDisk(options);
  if (saved) return "saved";
  downloadReportAsBlob(options);
  return "downloaded";
}
