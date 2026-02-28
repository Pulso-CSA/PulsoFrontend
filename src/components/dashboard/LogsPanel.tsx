import { useState } from "react";
import { Terminal, Info, AlertTriangle, XCircle, Filter, Trash2, Play, RotateCw, Power, FileText, Download } from "lucide-react";
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

  const getLevelIcon = (level: string) => {
    switch (level) {
      case "info":
        return <Info className="h-5 w-5 text-primary" />;
      case "warning":
        return <AlertTriangle className="h-5 w-5 text-warning" />;
      case "error":
        return <XCircle className="h-5 w-5 text-destructive" />;
      default:
        return <Terminal className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getLevelColor = (level: string) => {
    switch (level) {
      case "info":
        return "border-l-primary bg-primary/5";
      case "warning":
        return "border-l-warning bg-warning/5";
      case "error":
        return "border-l-destructive bg-destructive/5";
      default:
        return "border-l-muted bg-muted/5";
    }
  };

  const filteredLogs = logs.filter((log) => {
    const matchesText =
      log.message.toLowerCase().includes(filter.toLowerCase()) ||
      log.source?.toLowerCase().includes(filter.toLowerCase());
    const matchesLevel = levelFilter === "all" || log.level === levelFilter;
    return matchesText && matchesLevel;
  });

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
          <Button
            variant="pulso"
            size="default"
            onClick={fetchLogs}
            disabled={isLoading}
            className="min-h-[42px] gap-2"
          >
            <Download className="h-4 w-4" />
            Buscar Logs
          </Button>
          <Button
            variant="pulso"
            size="default"
            onClick={toggleAppLogs}
            className={`min-h-[42px] gap-2 ${showAppLogs ? "bg-primary/20 border-primary" : ""}`}
          >
            <FileText className="h-4 w-4" />
            Logs da App
          </Button>
          <Button
            variant="pulso"
            size="default"
            onClick={handleStartEnvironment}
            disabled={environmentStatus === "running" || isLoading}
            className="min-h-[42px] gap-2"
          >
            <Play className="h-4 w-4" />
            Subir
          </Button>

          <Button
            variant="pulso"
            size="default"
            onClick={handleRestartEnvironment}
            disabled={environmentStatus === "stopped" || isLoading}
            className="min-h-[42px] gap-2"
          >
            <RotateCw className="h-4 w-4" />
            Reiniciar
          </Button>

          <Button
            variant="pulso"
            size="default"
            onClick={handleStopEnvironment}
            disabled={environmentStatus === "stopped" || isLoading}
            className="min-h-[42px] gap-2"
          >
            <Power className="h-4 w-4" />
            Desligar
          </Button>
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
          <div className="flex gap-2 flex-wrap">
            {["all", "info", "warning", "error"].map((level) => (
              <Button
                key={level}
                variant="pulso"
                size="default"
                onClick={() => setLevelFilter(level)}
                className={`capitalize shrink-0 min-h-[40px] ${levelFilter === level ? "bg-primary/20 border-primary" : ""}`}
              >
                {level === "all" ? "Todos" : level}
              </Button>
            ))}
          </div>
        </div>

        {/* Lista de Logs */}
        <div className="space-y-2 max-h-[600px] overflow-y-auto">
          {filteredLogs.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Terminal className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p>Nenhum log encontrado</p>
            </div>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className={`border-l-4 rounded-lg p-4 ${getLevelColor(
                  log.level
                )}`}
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{getLevelIcon(log.level)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline justify-between gap-2 mb-1.5">
                      <span className="text-sm font-mono text-muted-foreground">
                        {log.timestamp.toLocaleTimeString("pt-BR")}
                      </span>
                      {log.source && (
                        <span className="text-sm px-2.5 py-1 rounded-full bg-primary/10 text-primary font-mono">
                          {log.source}
                        </span>
                      )}
                    </div>
                    <p className="text-base text-foreground font-mono break-words">
                      {log.message}
                    </p>
                  </div>
                </div>
              </div>
            ))
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
