import { useState } from "react";
import { Terminal, Filter, Trash2, Play, RotateCw, Power, FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { deployApi } from "@/lib/api";
import { cn } from "@/lib/utils";

interface LogEntry {
  id: string;
  timestamp: Date;
  level: "info" | "warning" | "error";
  message: string;
  source?: string;
}

const LogsPanel = () => {
  const { toast } = useToast();
  const [logs, setLogs] = useState<LogEntry[]>([
    {
      id: "1",
      timestamp: new Date(),
      level: "info",
      message: "Servidor iniciado na porta 3000",
      source: "server",
    },
    {
      id: "2",
      timestamp: new Date(Date.now() - 5000),
      level: "info",
      message: "Conexão com banco de dados estabelecida",
      source: "database",
    },
    {
      id: "3",
      timestamp: new Date(Date.now() - 10000),
      level: "warning",
      message: "Tempo de resposta da API acima do esperado (1.2s)",
      source: "api",
    },
    {
      id: "4",
      timestamp: new Date(Date.now() - 15000),
      level: "error",
      message: "Falha ao conectar com serviço externo: timeout",
      source: "external",
    },
  ]);
  const [filter, setFilter] = useState("");
  const [levelFilter, setLevelFilter] = useState<string>("all");
  const [environmentStatus, setEnvironmentStatus] = useState<"stopped" | "running">("stopped");
  const [environmentType, setEnvironmentType] = useState<"docker" | "venv" | null>(null);
  const [showAppLogs, setShowAppLogs] = useState(false);
  const [testEnvironment, setTestEnvironment] = useState<"docker" | "venv">("docker");
  const [isLoading, setIsLoading] = useState(false);

  /** Paleta legível sobre fundo cinza claro (#D1D5DB): tons mais escuros. */
  const levelTagClass = (level: LogEntry["level"]) => {
    switch (level) {
      case "info":
        return "text-cyan-800 font-semibold";
      case "warning":
        return "text-amber-800 font-semibold";
      case "error":
        return "text-red-700 font-semibold";
      default:
        return "text-cyan-800/90 font-semibold";
    }
  };

  const levelTagLabel = (level: LogEntry["level"]) => {
    switch (level) {
      case "info":
        return "[INF]";
      case "warning":
        return "[WRN]";
      case "error":
        return "[ERR]";
      default:
        return "[LOG]";
    }
  };

  const filteredLogs = logs.filter((log) => {
    const matchesText =
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.source?.toLowerCase().includes(filter.toLowerCase());
    const matchesLevel = levelFilter === "all" || log.level === levelFilter;
    return matchesText && matchesLevel;
  });

  /** Ordem cronológica (terminal: mais antigo no topo). */
  const terminalLogs = [...filteredLogs].sort(
    (a, b) => a.timestamp.getTime() - b.timestamp.getTime()
  );

  const addLog = (level: LogEntry["level"], message: string, source?: string) => {
    const newLog: LogEntry = {
      id: Date.now().toString(),
      timestamp: new Date(),
      level,
      message,
      source,
    };
    setLogs((prev) => [newLog, ...prev]);
  };

  const clearLogs = async () => {
    setIsLoading(true);
    try {
      if (testEnvironment === "docker") {
        await deployApi.docker.clearLogs();
      } else {
        await deployApi.venv.clearLogs();
      }
      setLogs([]);
      toast({
        title: "Logs limpos",
        description: `Logs do ${testEnvironment === "docker" ? "Docker" : "venv"} foram removidos no backend`,
      });
    } catch (err) {
      toast({
        title: "Erro ao limpar logs",
        description: err instanceof Error ? err.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchLogs = async () => {
    setIsLoading(true);
    try {
      const res = testEnvironment === "docker"
        ? await deployApi.docker.getLogs()
        : await deployApi.venv.getLogs();
      const lines: string[] = Array.isArray(res?.lines)
        ? res.lines
        : typeof res?.logs === "string"
          ? res.logs.split("\n").filter(Boolean)
          : [];
      const newEntries: LogEntry[] = lines.map((line, i) => ({
        id: `api-${Date.now()}-${i}`,
        timestamp: new Date(),
        level: "info" as const,
        message: line,
        source: testEnvironment === "docker" ? "docker" : "venv",
      }));
      setLogs((prev) => (lines.length > 0 ? [...newEntries, ...prev] : prev));
      toast({
        title: "Logs carregados",
        description: lines.length > 0
          ? `${lines.length} linhas do ${testEnvironment === "docker" ? "Docker" : "venv"}`
          : "Nenhum log retornado",
      });
    } catch (err) {
      toast({
        title: "Erro ao buscar logs",
        description: err instanceof Error ? err.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStartEnvironment = async () => {
    setIsLoading(true);
    addLog("info", `Iniciando ambiente ${testEnvironment === "docker" ? "Docker" : "venv"}...`, "environment");
    try {
      if (testEnvironment === "docker") {
        await deployApi.docker.start();
      } else {
        await deployApi.venv.create();
      }
      setEnvironmentType(testEnvironment);
      setEnvironmentStatus("running");
      addLog("info", `Ambiente ${testEnvironment === "docker" ? "Docker" : "venv"} iniciado com sucesso`, "environment");
      toast({
        title: "Ambiente iniciado",
        description: `${testEnvironment === "docker" ? "Docker" : "venv"} está rodando`,
      });
    } catch (err) {
      addLog("error", err instanceof Error ? err.message : "Falha ao iniciar ambiente", "environment");
      toast({
        title: "Erro ao iniciar",
        description: err instanceof Error ? err.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRestartEnvironment = async () => {
    if (environmentStatus === "stopped") {
      toast({
        title: "Ambiente parado",
        description: "Inicie o ambiente antes de reiniciar",
        variant: "destructive",
      });
      return;
    }
    setIsLoading(true);
    addLog("warning", `Reiniciando ambiente ${testEnvironment === "docker" ? "Docker" : "venv"}...`, "environment");
    try {
      if (testEnvironment === "docker") {
        await deployApi.docker.rebuild();
      } else {
        await deployApi.venv.recreate();
      }
      addLog("info", `Ambiente ${testEnvironment === "docker" ? "Docker" : "venv"} reiniciado com sucesso`, "environment");
      toast({
        title: "Ambiente reiniciado",
        description: "O ambiente foi reiniciado com sucesso",
      });
    } catch (err) {
      addLog("error", err instanceof Error ? err.message : "Falha ao reiniciar ambiente", "environment");
      toast({
        title: "Erro ao reiniciar",
        description: err instanceof Error ? err.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStopEnvironment = async () => {
    if (environmentStatus === "stopped") {
      toast({
        title: "Ambiente já parado",
        description: "O ambiente não está rodando",
        variant: "destructive",
      });
      return;
    }
    setIsLoading(true);
    addLog("warning", `Parando ambiente ${testEnvironment === "docker" ? "Docker" : "venv"}...`, "environment");
    try {
      if (testEnvironment === "docker") {
        await deployApi.docker.stop();
      } else {
        await deployApi.venv.deactivate();
      }
      setEnvironmentStatus("stopped");
      setEnvironmentType(null);
      addLog("info", "Ambiente desligado com sucesso", "environment");
      toast({
        title: "Ambiente desligado",
        description: "O ambiente foi desligado com sucesso",
      });
    } catch (err) {
      addLog("error", err instanceof Error ? err.message : "Falha ao desligar ambiente", "environment");
      toast({
        title: "Erro ao desligar",
        description: err instanceof Error ? err.message : "Erro desconhecido",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const toggleAppLogs = () => {
    setShowAppLogs(!showAppLogs);
    toast({
      title: showAppLogs ? "Logs da aplicação ocultos" : "Logs da aplicação visíveis",
      description: showAppLogs
        ? "Mostrando apenas logs do sistema"
        : "Mostrando logs da aplicação",
    });
  };

  const toolbarBtnClass = (enabled: boolean, extra?: string) =>
    cn(
      "h-[52px] w-[52px] sm:h-14 sm:w-14 shrink-0 rounded-xl border-0 shadow-md transition-all",
      "flex items-center justify-center text-white",
      enabled
        ? "bg-slate-900 hover:bg-slate-800 hover:scale-[1.02] active:scale-[0.98]"
        : "cursor-not-allowed bg-slate-400/50 text-white/70 opacity-70 dark:bg-muted dark:text-muted-foreground",
      extra
    );

  const LEVEL_FILTERS: { key: string; label: string }[] = [
    { key: "all", label: "Todos" },
    { key: "info", label: "Info" },
    { key: "warning", label: "Warning" },
    { key: "error", label: "Error" },
  ];

  return (
    <div className="space-y-5">
      <div className="glass-strong pulso-card rounded-2xl border-primary/20 p-5 shadow-sm sm:p-7">
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex min-w-0 flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 font-mono text-lg font-bold tracking-tight text-foreground">
              <span className="text-primary" aria-hidden>
                &gt;_
              </span>
              <Terminal className="h-6 w-6 shrink-0 text-primary" aria-hidden />
              <h2 className="text-xl font-bold text-foreground sm:text-[1.35rem]">Controle de Logs</h2>
            </div>
            {environmentStatus === "running" && environmentType && (
              <span className="rounded-full border border-primary/30 bg-primary/15 px-2.5 py-1 text-xs font-medium text-primary">
                {environmentType === "docker" ? "Docker" : "venv"} · rodando
              </span>
            )}
          </div>
          <Button
            variant="outline"
            size="default"
            onClick={clearLogs}
            disabled={isLoading}
            className="w-full shrink-0 gap-2 border-destructive/45 bg-background/80 text-destructive hover:bg-destructive/10 hover:text-destructive sm:w-auto"
          >
            <Trash2 className="h-4 w-4" />
            Limpar Logs
          </Button>
        </div>

        <div className="mb-6 rounded-xl border border-border/60 bg-muted/40 px-4 py-4 sm:px-5">
          <div className="flex flex-wrap items-center gap-4">
            <Label className="text-sm font-medium text-foreground sm:text-base">Ambiente de teste:</Label>
            <div className="flex flex-1 items-center justify-center gap-3 sm:justify-start">
              <span
                className={cn(
                  "text-sm font-semibold transition-colors",
                  testEnvironment === "docker" ? "text-blue-600 dark:text-blue-400" : "text-muted-foreground"
                )}
              >
                Docker
              </span>
              <Switch
                checked={testEnvironment === "venv"}
                onCheckedChange={(checked) => setTestEnvironment(checked ? "venv" : "docker")}
                className={
                  testEnvironment === "venv"
                    ? "data-[state=checked]:bg-emerald-500"
                    : "data-[state=unchecked]:bg-blue-500"
                }
              />
              <span
                className={cn(
                  "text-sm font-semibold transition-colors",
                  testEnvironment === "venv" ? "text-emerald-600 dark:text-emerald-400" : "text-muted-foreground"
                )}
              >
                venv
              </span>
            </div>
          </div>
        </div>

        <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-5 sm:gap-3">
          {[
            {
              key: "fetch",
              label: "Buscar Logs",
              icon: Download,
              onClick: fetchLogs,
              enabled: !isLoading,
            },
            {
              key: "app",
              label: "Logs da App",
              icon: FileText,
              onClick: toggleAppLogs,
              enabled: true,
              active: showAppLogs,
            },
            {
              key: "start",
              label: "Subir",
              icon: Play,
              onClick: handleStartEnvironment,
              enabled: environmentStatus !== "running" && !isLoading,
            },
            {
              key: "restart",
              label: "Reiniciar",
              icon: RotateCw,
              onClick: handleRestartEnvironment,
              enabled: environmentStatus !== "stopped" && !isLoading,
            },
            {
              key: "stop",
              label: "Desligar",
              icon: Power,
              onClick: handleStopEnvironment,
              enabled: environmentStatus !== "stopped" && !isLoading,
            },
          ].map(({ key, label, icon: Icon, onClick, enabled, active }) => (
            <div key={key} className="flex flex-col items-center gap-2">
              <button
                type="button"
                onClick={onClick}
                disabled={!enabled}
                className={toolbarBtnClass(
                  !!enabled,
                  active ? "ring-2 ring-primary ring-offset-2 ring-offset-background" : ""
                )}
              >
                <Icon className="h-5 w-5 sm:h-6 sm:w-6" />
                <span className="sr-only">{label}</span>
              </button>
              <span className="text-center text-[11px] font-medium leading-tight text-muted-foreground sm:text-xs">
                {label}
              </span>
            </div>
          ))}
        </div>

        <div className="mb-5 flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative min-w-0 flex-1">
            <Filter className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Filtrar logs..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="h-11 rounded-xl border-border/80 bg-background/80 pl-11 text-base shadow-sm focus-visible:ring-primary"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            {LEVEL_FILTERS.map(({ key, label }) => {
              const isActive = levelFilter === key;
              return (
                <Button
                  key={key}
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setLevelFilter(key)}
                  aria-pressed={isActive}
                  className={cn(
                    "h-9 min-w-[4.25rem] rounded-lg border-slate-800 bg-slate-900 px-3 text-xs font-medium text-white shadow-sm hover:bg-slate-800 hover:text-white",
                    "dark:border-zinc-600 dark:bg-zinc-800 dark:hover:bg-zinc-700",
                    isActive &&
                      "border-primary bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground dark:border-primary"
                  )}
                >
                  {label}
                </Button>
              );
            })}
          </div>
        </div>

        <div
          className="overflow-hidden rounded-2xl border border-slate-400/50 bg-[#D1D5DB] shadow-[inset_0_1px_0_rgba(255,255,255,0.65),0_6px_24px_rgba(15,23,42,0.08)]"
          aria-label="Saída de logs"
        >
          <div className="border-b border-slate-500/25 bg-slate-400/35 px-4 py-2">
            <span className="font-mono text-[10px] font-medium uppercase tracking-widest text-slate-700">
              Console
            </span>
          </div>
          {terminalLogs.length === 0 ? (
            <div className="px-4 py-16 text-center">
              <Terminal className="mx-auto mb-3 h-10 w-10 text-slate-500/70" />
              <p className="font-mono text-sm text-slate-600">Nenhum log encontrado</p>
            </div>
          ) : (
            <div className="max-h-[min(420px,50vh)] overflow-y-auto overscroll-y-contain px-4 py-4 sm:px-5 sm:py-5 [scrollbar-color:rgba(71,85,105,0.45)_transparent] [scrollbar-width:thin]">
              <div className="space-y-2.5 font-mono text-[13px] leading-relaxed tracking-normal sm:text-sm text-slate-900 [font-feature-settings:'tnum'] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-slate-500/35 [&::-webkit-scrollbar]:w-1.5">
                {terminalLogs.map((log) => {
                  const timeStr = log.timestamp.toLocaleTimeString("pt-BR", {
                    hour: "2-digit",
                    minute: "2-digit",
                    second: "2-digit",
                  });
                  return (
                    <div
                      key={log.id}
                      className="break-words rounded-md px-0.5 py-0.5 hover:bg-slate-500/15"
                    >
                      <span className="tabular-nums text-amber-900">{timeStr}</span>
                      <span className={levelTagClass(log.level)}>
                        {" "}
                        {levelTagLabel(log.level)}
                      </span>
                      {log.source ? (
                        <span className="text-teal-800"> [{log.source}]</span>
                      ) : null}
                      <span className="text-slate-900"> {log.message}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="mt-5 flex flex-col gap-3 border-t border-border/60 pt-5 text-sm text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <span className="font-medium text-foreground/80">
            Total: <span className="tabular-nums">{filteredLogs.length}</span>{" "}
            {filteredLogs.length === 1 ? "log" : "logs"}
          </span>
          <div className="flex flex-wrap gap-x-5 gap-y-1 text-xs sm:text-sm">
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 shrink-0 rounded-full bg-cyan-400" />
              {logs.filter((l) => l.level === "info").length} info
            </span>
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 shrink-0 rounded-full bg-amber-400" />
              {logs.filter((l) => l.level === "warning").length} warning
            </span>
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 shrink-0 rounded-full bg-red-500" />
              {logs.filter((l) => l.level === "error").length} error
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogsPanel;
