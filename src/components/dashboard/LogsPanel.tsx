import { useState } from "react";
import { Terminal, Filter, Trash2, Play, RotateCw, Power, FileText, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { deployApi } from "@/lib/api";

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

  const levelTagClass = (level: LogEntry["level"]) => {
    switch (level) {
      case "info":
        return "text-emerald-400";
      case "warning":
        return "text-amber-400";
      case "error":
        return "text-red-400";
      default:
        return "text-emerald-400/80";
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

  return (
    <div className="space-y-5">
      <div className="glass-strong pulso-card rounded-2xl p-6 border-primary/20">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <Terminal className="h-6 w-6 text-primary" />
            <h2 className="text-xl font-bold text-foreground">
              Controle de Logs
            </h2>
            {environmentStatus === "running" && environmentType && (
              <span className="text-xs px-2 py-1 rounded-full bg-primary/20 text-primary border border-primary/30">
                {environmentType === "docker" ? "Docker" : "venv"} • rodando
              </span>
            )}
          </div>
          <Button
            variant="outline"
            size="default"
            onClick={clearLogs}
            disabled={isLoading}
            className="border-destructive/40 hover:border-destructive hover:bg-destructive/10 text-destructive disabled:opacity-50 min-h-[40px] gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Limpar Logs
          </Button>
        </div>

        {/* Switch Docker/venv */}
        <div className="mb-6 flex items-center gap-4 p-5 glass border border-primary/20 rounded-xl">
          <Label className="text-base font-medium text-foreground">
            Ambiente de teste:
          </Label>
          <div className="flex items-center gap-3">
            <span className={`text-sm font-medium transition-colors ${
              testEnvironment === "docker" ? "text-blue-500" : "text-muted-foreground"
            }`}>
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
            <span className={`text-sm font-medium transition-colors ${
              testEnvironment === "venv" ? "text-emerald-500" : "text-muted-foreground"
            }`}>
              venv
            </span>
          </div>
        </div>

        {/* Controles de Ambiente */}
        <div className="mb-6 grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="flex flex-col items-center gap-1">
            <Button
              variant="pulso"
              size="default"
              onClick={fetchLogs}
              disabled={isLoading}
              className="min-h-[42px] gap-2"
            >
              <Download className="h-4 w-4 shrink-0" />
              <span className="sr-only">Buscar Logs</span>
            </Button>
            <span className="text-[11px] leading-tight text-muted-foreground">
              Buscar Logs
            </span>
          </div>

          <div className="flex flex-col items-center gap-1">
            <Button
              variant="pulso"
              size="default"
              onClick={toggleAppLogs}
              className={`min-h-[42px] gap-2 ${showAppLogs ? "bg-primary/20 border-primary" : ""}`}
            >
              <FileText className="h-4 w-4 shrink-0" />
              <span className="sr-only">Logs da App</span>
            </Button>
            <span className="text-[11px] leading-tight text-muted-foreground">
              Logs da App
            </span>
          </div>

          <div className="flex flex-col items-center gap-1">
            <Button
              variant="pulso"
              size="default"
              onClick={handleStartEnvironment}
              disabled={environmentStatus === "running" || isLoading}
              className="min-h-[42px] gap-2"
            >
              <Play className="h-4 w-4 shrink-0" />
              <span className="sr-only">Subir ambiente</span>
            </Button>
            <span className="text-[11px] leading-tight text-muted-foreground">
              Subir
            </span>
          </div>

          <div className="flex flex-col items-center gap-1">
            <Button
              variant="pulso"
              size="default"
              onClick={handleRestartEnvironment}
              disabled={environmentStatus === "stopped" || isLoading}
              className="min-h-[42px] gap-2"
            >
              <RotateCw className="h-4 w-4 shrink-0" />
              <span className="sr-only">Reiniciar ambiente</span>
            </Button>
            <span className="text-[11px] leading-tight text-muted-foreground">
              Reiniciar
            </span>
          </div>

          <div className="flex flex-col items-center gap-1">
            <Button
              variant="pulso"
              size="default"
              onClick={handleStopEnvironment}
              disabled={environmentStatus === "stopped" || isLoading}
              className="min-h-[42px] gap-2"
            >
              <Power className="h-4 w-4 shrink-0" />
              <span className="sr-only">Desligar ambiente</span>
            </Button>
            <span className="text-[11px] leading-tight text-muted-foreground">
              Desligar
            </span>
          </div>
        </div>

        {/* Filtros */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="relative">
            <Filter className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Filtrar logs..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="pl-12 h-11 text-base border-primary/30 bg-background/50 focus-visible:ring-primary"
            />
          </div>
          <div className="flex gap-3 flex-wrap">
            {["all", "info", "warning", "error"].map((level) => {
              const label = level === "all" ? "Todos" : level;
              const isActive = levelFilter === level;
              return (
                <div key={level} className="flex flex-col items-center gap-1">
                  <Button
                    variant="pulso"
                    size="default"
                    onClick={() => setLevelFilter(level)}
                    className={`shrink-0 min-h-[36px] px-3 ${isActive ? "bg-primary/20 border-primary" : ""}`}
                    aria-pressed={isActive}
                  >
                    <span className="sr-only">{label}</span>
                  </Button>
                  <span className="text-[11px] leading-tight text-muted-foreground capitalize">
                    {label}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Terminal (estilo sessão ativa — fundo escuro, mono, timestamps em verde) */}
        <div
          className="rounded-xl border border-white/10 bg-[#080c12] shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] overflow-hidden"
          aria-label="Saída de logs"
        >
          {terminalLogs.length === 0 ? (
            <div className="text-center py-14 px-4">
              <Terminal className="h-10 w-10 mx-auto mb-3 text-emerald-500/40" />
              <p className="text-sm font-mono text-slate-500">Nenhum log encontrado</p>
            </div>
          ) : (
            <div className="p-4 sm:p-5 font-mono text-[13px] sm:text-sm leading-relaxed space-y-2 text-left [font-feature-settings:'tnum']">
              {terminalLogs.map((log) => {
                const timeStr = log.timestamp.toLocaleTimeString("pt-BR", {
                  hour: "2-digit",
                  minute: "2-digit",
                  second: "2-digit",
                });
                return (
                  <div key={log.id} className="break-words">
                    <span className="text-emerald-400 tabular-nums">{timeStr}</span>
                    <span className={`${levelTagClass(log.level)}`}>
                      {" "}
                      {levelTagLabel(log.level)}
                    </span>
                    {log.source ? (
                      <span className="text-emerald-500/70"> [{log.source}]</span>
                    ) : null}
                    <span className="text-slate-100"> {log.message}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer com stats */}
        <div className="mt-4 pt-4 border-t border-primary/20 flex justify-between text-sm text-muted-foreground">
          <span>Total: {filteredLogs.length} logs</span>
          <div className="flex gap-4">
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-primary"></div>
              {logs.filter((l) => l.level === "info").length} info
            </span>
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-warning"></div>
              {logs.filter((l) => l.level === "warning").length} warning
            </span>
            <span className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-destructive"></div>
              {logs.filter((l) => l.level === "error").length} error
            </span>
          </div>
        </div>
      </div>

    </div>
  );
};

export default LogsPanel;
