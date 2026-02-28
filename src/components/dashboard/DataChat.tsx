import { useState, useEffect, useCallback, useRef } from "react";
import { Send, Database, ChevronDown, ChevronUp, BarChart3, Brain, RefreshCw, Trash2, Plus, MessageSquare } from "lucide-react";
import { DataChatCharts } from "./DataChatCharts";
import { DataChatML, stripMarkdown } from "./DataChatML";
import { DataPreviewTable } from "./DataPreviewTable";
import { LoaderEscrevendoCodigo, LoaderEstudandoArquivos } from "@/components/loaders";
import { ChatSidebar } from "./ChatSidebar";
import { exportReport } from "@/lib/exportReport";
import { DownloadReportButton } from "@/components/ui/DownloadReportButton";

/** Tenta extrair tabela do texto (ex.: "Primeiras 5 linhas:" + dados) e retorna colunas/linhas ou null */
function parseTableFromText(content: string): { colunas: string[]; linhas: Record<string, unknown>[]; contentWithoutTable: string } | null {
  if (!content?.trim()) return null;
  const lines = content.split(/\r?\n/);
  const idx = lines.findIndex((l) =>
    /Primeiras\s*\d*\s*linhas?/i.test(l) ||
    /primeiras\s+linhas/i.test(l) ||
    /Amostra\s*(dos\s*dados)?\s*:?/i.test(l) ||
    /Primeiras\s*\d+\s*linhas?/i.test(l)
  );
  if (idx < 0) return null;

  const titleLine = lines[idx];
  const colonMatch = titleLine.match(/(?:Primeiras\s*\d*\s*linhas?|Amostra\s*(?:dos\s*dados)?)\s*:?\s*(.*)/i);
  const headersOnSameLine = colonMatch?.[1]?.trim();

  let cols: string[];
  let dataStartIdx: number;

  const parseRow = (line: string, sep: string): string[] => {
    if (sep === "\t") return line.split("\t").map((v) => v.trim());
    if (sep === "|") return line.split("|").map((v) => v.trim());
    if (sep === ",") return line.split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/).map((v) => v.replace(/^"|"$/g, "").trim());
    return line.split(/\s+/).filter(Boolean);
  };

  if (headersOnSameLine) {
    const headerLine = headersOnSameLine;
    let sep = "\t";
    if (headerLine.includes("\t")) sep = "\t";
    else if (headerLine.includes("|")) sep = "|";
    else if (headerLine.includes(",")) sep = ",";
    cols = sep === "," ? parseRow(headerLine, sep) : headerLine.split(/\s+/).filter(Boolean);
    dataStartIdx = idx + 1;
  } else {
    const nextLine = lines[idx + 1]?.trim();
    if (!nextLine) return null;
    let sep = "\t";
    if (nextLine.includes("\t")) sep = "\t";
    else if (nextLine.includes("|")) sep = "|";
    else if (nextLine.includes(",")) sep = ",";
    cols = sep === "," ? parseRow(nextLine, sep) : nextLine.split(/\s+/).filter(Boolean);
    dataStartIdx = idx + 2;
  }

  if (cols.length < 2) return null;

  const dataLines: string[] = [];
  for (let i = dataStartIdx; i < lines.length; i++) {
    const line = lines[i];
    if (!line.trim()) break;
    dataLines.push(line);
  }
  if (dataLines.length === 0) return null;

  let sep = "\t";
  const firstData = dataLines[0];
  if (firstData.includes("\t")) sep = "\t";
  else if (firstData.includes("|")) sep = "|";
  else if (firstData.includes(",")) sep = ",";

  const linhas: Record<string, unknown>[] = [];
  for (const line of dataLines) {
    const vals = parseRow(line, sep);
    const row: Record<string, unknown> = {};
    cols.forEach((c, i) => { row[c] = vals[i] ?? ""; });
    linhas.push(row);
  }

  const beforeTable = lines.slice(0, idx).join("\n").trim();
  const afterTable = lines.slice(dataStartIdx + dataLines.length).join("\n").trim();
  const contentWithoutTable = [beforeTable, afterTable].filter(Boolean).join("\n\n");

  return { colunas: cols, linhas, contentWithoutTable };
}
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatTextarea } from "@/components/ui/chat-textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { inteligenciaApi, type DbConfig } from "@/lib/api";
import { ErrorBoundary } from "@/components/ErrorBoundary";
import { cn } from "@/lib/utils";
import { getDbConnection, setDbConnection, getDataChatContext, setDataChatContext, clearDataChatContext, getDataChatSessions, setDataChatSessions, type ChatSession } from "@/lib/connectionStorage";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Message {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: Date;
  dataType?: "structure" | "stats" | "insights" | "model";
  data?: unknown;
  sugestaoProximoPasso?: string;
  retryPrompt?: string;
  errorType?: "connection" | "dataset_ref" | "generic";
}

type DataChatSession = ChatSession<Message & { timestamp: string }>;

function restoreMessages(messages: (Omit<Message, "timestamp"> & { timestamp: string })[]): Message[] {
  if (!Array.isArray(messages)) return [];
  return messages
    .filter((m): m is Omit<Message, "timestamp"> & { timestamp: string } => m && typeof m === "object" && "content" in m)
    .map((m) => ({ ...m, timestamp: new Date(m.timestamp || Date.now()) }));
}

/** Carrega sessões do storage com validação para evitar erros de estrutura */
function loadDataChatSessions(): DataChatSession[] {
  try {
    const raw = getDataChatSessions();
    if (!Array.isArray(raw)) return [];
    return raw.filter((s): s is DataChatSession => {
      if (!s || typeof s !== "object" || !s.id || !s.title) return false;
      if (!Array.isArray(s.messages)) return false;
      return true;
    });
  } catch {
    return [];
  }
}

interface StatsMetric {
  label: string;
  value: string | number;
}

interface Correlation {
  vars: string;
  strength: string;
  value: string | number;
}

interface ModelMetric {
  name: string;
  value: string | number;
}

interface ModelData {
  model: string;
  metrics: ModelMetric[];
  insights: string[];
  nextSteps: string[];
}

/** Valida conexão conforme tipo (SQL exige user/senha; NoSQL não) */
function validarConexao(
  tipo: "SQL" | "NoSQL",
  host: string,
  base: string,
  user: string,
  password: string
): string | null {
  if (!host?.trim()) return "Preencha Host/URI";
  if (!base?.trim()) return "Preencha Base";
  if (tipo === "SQL") {
    if (!user?.trim()) return "Preencha Usuário";
    if (!password?.trim()) return "Preencha Senha";
  }
  return null;
}

/** Parseia "host:port" em { host, port } */
function parseHostPort(hostUri: string): { host: string; port: number } {
  const trimmed = hostUri.trim();
  const colonIdx = trimmed.lastIndexOf(":");
  if (colonIdx > 0) {
    const host = trimmed.slice(0, colonIdx);
    const port = parseInt(trimmed.slice(colonIdx + 1), 10);
    return { host, port: isNaN(port) ? 3306 : port };
  }
  return { host: trimmed || "127.0.0.1", port: 3306 };
}

/** Mapeia tipo e porta para db_type do backend */
function getDbType(type: string, port: number): string {
  if (type === "nosql") return "mongodb";
  if (port === 5432) return "postgresql";
  if (port === 3306) return "mysql";
  if (port === 1433) return "sqlserver";
  return "postgresql";
}

/** Monta DbConfig a partir dos dados de conexão (usado ao carregar do storage) */
function buildDbConfigFromStored(data: { type?: string; host?: string; database?: string; user?: string; password?: string }): DbConfig {
  const type = data.type ?? "sql";
  const hostOrUri = (data.host ?? "").trim();
  const base = (data.database ?? "").trim();
  const user = (data.user ?? "").trim();
  const password = data.password ?? "";
  if (type === "nosql") {
    const auth = user && password ? { user, password } : {};
    return hostOrUri.startsWith("mongodb://")
      ? { uri: hostOrUri, database: base, ...auth }
      : {
          host: hostOrUri.split(":")[0] || "localhost",
          port: parseInt(hostOrUri.split(":")[1] || "27017", 10),
          database: base,
          ...auth,
        };
  }
  const { host: h, port } = parseHostPort(hostOrUri);
  const db_type = getDbType(type, port);
  return { db_type, host: h, port, database: base, user, password };
}

/** Formata a estrutura retornada por captura-dados ou chat para exibição */
function formatarEstrutura(
  captura?: {
    tipo_base?: string;
    tabelas?: string[];
    quantidade_tabelas?: number;
    quantidade_registros?: Record<string, number>;
    teor_dados?: string;
    indices?: Record<string, unknown[]>;
    consultas_exploracao?: string[];
  },
  res?: { estrutura?: unknown; message?: string }
): string {
  if (!captura && res?.estrutura) {
    return JSON.stringify(res.estrutura, null, 2);
  }
  if (!captura) {
    return res?.message ?? "Estrutura capturada com sucesso.";
  }

  const linhas: string[] = ["Estrutura capturada com sucesso.", ""];
  const tipo = captura.tipo_base === "NoSQL" ? "NoSQL (MongoDB)" : captura.tipo_base ?? "SQL";
  linhas.push(`Tipo: ${tipo}`);

  const tabelas = captura.tabelas ?? [];
  const labelTabelas = captura.tipo_base === "NoSQL" ? "Coleções" : "Tabelas";
  linhas.push(`${labelTabelas}: ${tabelas.length > 0 ? tabelas.join(", ") : "—"}`);

  const registros = captura.quantidade_registros ?? {};
  if (Object.keys(registros).length > 0) {
    const regStr = Object.entries(registros)
      .map(([nome, qtd]) => `${nome}: ${Number(qtd).toLocaleString("pt-BR")}`)
      .join(" · ");
    linhas.push(`Registros: ${regStr}`);
  }

  if (captura.teor_dados?.trim()) {
    linhas.push(`Teor: ${captura.teor_dados.trim()}`);
  }

  if (captura.consultas_exploracao && captura.consultas_exploracao.length > 0) {
    linhas.push("", "Consultas de exploração:");
    captura.consultas_exploracao.forEach((q) => linhas.push(`- \`${q}\``));
  }

  return linhas.join("\n");
}

const DataChat = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [sessions, setSessions] = useState<DataChatSession[]>(() => loadDataChatSessions());
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const s = loadDataChatSessions();
    setSessions(s);
    if (s.length > 0 && !currentSessionId) {
      const last = s[s.length - 1];
      setCurrentSessionId(last.id);
      try {
        const restored = restoreMessages(last.messages as (Omit<Message, "timestamp"> & { timestamp: string })[]);
        setMessages(restored);
      } catch {
        setMessages([]);
      }
    }
  }, []);

  /** Atualiza sessão quando messages mudam */
  useEffect(() => {
    if (!currentSessionId || messages.length === 0) return;
    const title = messages.find((m) => m.role === "user")?.content?.slice(0, 50) ?? "Novo chat";
    const toStore = messages.map((m) => ({ ...m, timestamp: m.timestamp.toISOString() }));
    const now = new Date().toISOString();
    setSessions((prev) => {
      const idx = prev.findIndex((s) => s.id === currentSessionId);
      return idx >= 0
        ? prev.map((s, i) => (i === idx ? { ...s, title, messages: toStore, updatedAt: now } : s))
        : [...prev, { id: currentSessionId, title, messages: toStore, createdAt: now, updatedAt: now }];
    });
  }, [currentSessionId, messages]);

  useEffect(() => {
    if (sessions.length > 0) setDataChatSessions(sessions);
  }, [sessions]);
  const [showConnection, setShowConnection] = useState(false);
  const [connectionData, setConnectionData] = useState(() => {
    const stored = getDbConnection();
    return stored ?? { type: "sql", host: "", database: "", user: "", password: "" };
  });

  useEffect(() => {
    const stored = getDbConnection();
    if (stored) {
      setConnectionData(stored);
      const tipo = stored.type === "nosql" ? "NoSQL" : "SQL";
      const erro = validarConexao(tipo, stored.host, stored.database, stored.user, stored.password);
      if (!erro) {
        setDbConfig(buildDbConfigFromStored(stored));
        setTipoBase(tipo);
      }
    }
    const ctx = getDataChatContext();
    if (ctx) {
      setIdRequisicao(ctx.idRequisicao);
      if (ctx.datasetRef != null) setDatasetRef(ctx.datasetRef);
      if (ctx.modelRef != null) setModelRef(ctx.modelRef);
    }
  }, []);
  const [showPassword, setShowPassword] = useState(false);
  const [idRequisicao, setIdRequisicao] = useState(() => {
    const stored = getDataChatContext();
    return stored?.idRequisicao ?? `id-${crypto.randomUUID()}`;
  });
  const [dbConfig, setDbConfig] = useState<DbConfig | null>(null);
  const [tipoBase, setTipoBase] = useState<"SQL" | "NoSQL">("SQL");
  const [datasetRef, setDatasetRef] = useState<string | null>(() => getDataChatContext()?.datasetRef ?? null);
  const [modelRef, setModelRef] = useState<string | null>(() => getDataChatContext()?.modelRef ?? null);

  /** Persiste contexto no sessionStorage para manter entre trocas de layer e recarregamentos */
  useEffect(() => {
    setDataChatContext({
      idRequisicao,
      datasetRef: datasetRef ?? null,
      modelRef: modelRef ?? null,
    });
  }, [idRequisicao, datasetRef, modelRef]);

  const quickActions = [
    "Ver estrutura da base",
    "Calcular correlações principais",
    "Sugerir modelo para detecção de fraude",
  ];

  const buildDbConfig = useCallback((): DbConfig => {
    const { host, database, user, password } = connectionData;
    const hostOrUri = (host ?? "").trim();
    const base = (database ?? "").trim();
    const auth = user?.trim() && password?.trim() ? { user: user.trim(), password: password.trim() } : {};

    if (connectionData.type === "nosql") {
      return hostOrUri.startsWith("mongodb://")
        ? { uri: hostOrUri, database: base, ...auth }
        : {
            host: hostOrUri.split(":")[0] || "localhost",
            port: parseInt(hostOrUri.split(":")[1] || "27017", 10),
            database: base,
            ...auth,
          };
    }

    const { host: h, port } = parseHostPort(hostOrUri);
    const db_type = getDbType(connectionData.type, port);
    return {
      db_type,
      host: h,
      port,
      database: base,
      user: (user ?? "").trim(),
      password: password ?? "",
    };
  }, [connectionData]);

  const handleSend = async (overridePrompt?: string) => {
    const promptText = (overridePrompt ?? input).trim();
    if (!promptText) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: promptText,
      timestamp: new Date(),
    };

    if (!currentSessionId) {
      const newId = `chat-${crypto.randomUUID()}`;
      setCurrentSessionId(newId);
      setSessions((prev) => [...prev, { id: newId, title: promptText.slice(0, 50), messages: [], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }]);
    }
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    loadingPhaseRef.current = (messages.length === 0 || /estrutura|carregar|conectar|dados|base/i.test(promptText)) ? "connecting" : "writing";
    setLoading(true);

    try {
      // Botões de sugestão e todas as mensagens: sempre POST /chat (db_config opcional)
      const res = await inteligenciaApi.chat({
        mensagem: promptText,
        id_requisicao: idRequisicao,
        ...(dbConfig && { db_config: dbConfig }),
        usuario: user?.id,
        ...(datasetRef && { dataset_ref: datasetRef }),
        ...(modelRef && { model_ref: modelRef }),
      });

      if (res?.dataset_ref) setDatasetRef(res.dataset_ref);
      if (res?.model_ref) setModelRef(res.model_ref);

      // resposta_texto é sempre o conteúdo principal (backend retorna 200 mesmo em erros internos)
      const content = res?.resposta_texto ?? "Resposta recebida sem conteúdo textual.";
      const captura = res?.captura_dados;
      const dataType: "structure" | undefined = captura ? "structure" : undefined;
      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content,
        timestamp: new Date(),
        dataType,
        data: res,
        sugestaoProximoPasso: res?.sugestao_proximo_passo,
      };
      setMessages((prev) => [...prev, systemMessage]);
    } catch (err: unknown) {
      const errObj = err as { response?: { data?: { detail?: unknown } }; message?: string };
      const msg = errObj?.response?.data?.detail ?? errObj?.message;
      const rawMsg: string =
        typeof msg === "string"
          ? msg
          : (msg && typeof msg === "object" ? (msg as Record<string, unknown>).message : undefined) ?? (msg != null ? JSON.stringify(msg) : "Erro na consulta. Tente novamente.");
      const isConnectionError = /conexão|conectar ao banco|connection refused|timeout/i.test(rawMsg);
      const isDatasetRefError = /dataset_ref|model_ref|contexto/i.test(rawMsg);
      const displayMsg = isConnectionError
        ? "Não foi possível conectar ao banco de dados. Verifique sua conexão e tente novamente."
        : isDatasetRefError
          ? "Não foi possível concluir. Verifique se enviou o contexto (dataset_ref) e tente novamente."
          : `Erro: ${rawMsg}`;
      toast({
        title: isConnectionError ? "Erro de conexão" : "Erro na consulta",
        description: displayMsg,
        variant: "destructive",
      });
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content: displayMsg,
        timestamp: new Date(),
        retryPrompt: promptText,
        errorType: isConnectionError ? "connection" : isDatasetRefError ? "dataset_ref" : "generic",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const loadingPhaseRef = useRef<"connecting" | "writing">("writing");

  const handleQuickAction = (action: string) => {
    setInput(action);
    handleSend(action);
  };

  const handleNewChat = () => {
    const newId = `chat-${crypto.randomUUID()}`;
    setCurrentSessionId(newId);
    setMessages([]);
    setInput("");
    setSessions((prev) => [...prev, { id: newId, title: "Novo chat", messages: [], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }]);
  };

  const handleOpenChat = (session: DataChatSession) => {
    setCurrentSessionId(session.id);
    setMessages(restoreMessages(session.messages as (Omit<Message, "timestamp"> & { timestamp: string })[]));
  };

  const handleDeleteChat = (id: string) => {
    const next = sessions.filter((s) => s.id !== id);
    setSessions(next);
    setDataChatSessions(next);
    if (currentSessionId === id) {
      const last = next[next.length - 1];
      if (last) {
        setCurrentSessionId(last.id);
        setMessages(restoreMessages(last.messages as (Omit<Message, "timestamp"> & { timestamp: string })[]));
      } else {
        setCurrentSessionId(null);
        setMessages([]);
      }
    }
  };

  const handleApplyConnection = () => {
    const tipo = connectionData.type === "nosql" ? "NoSQL" : "SQL";
    const erro = validarConexao(
      tipo,
      connectionData.host,
      connectionData.database,
      connectionData.user,
      connectionData.password
    );
    if (!erro) {
      setDbConfig(buildDbConfig());
      setTipoBase(tipo);
      setDatasetRef(null);
      setModelRef(null);
      clearDataChatContext();
      setDbConnection(connectionData);
      toast({ title: "Conexão configurada", description: "Os parâmetros foram salvos e serão usados nas próximas consultas." });
      setShowConnection(false);
    } else {
      toast({
        title: "Campos obrigatórios",
        description: erro,
        variant: "destructive",
      });
    }
  };

  const sessionItems = sessions.map((s) => ({ id: s.id, title: s.title, updatedAt: s.updatedAt }));

  return (
    <div className="pulso-chat-layout h-full min-h-0">
      {/* Sidebar — Histórico (mesma posição que PulsoCSA) */}
      <div className="pulso-chat-sidebar glass-strong">
        <ChatSidebar
          sessions={sessionItems}
          currentSessionId={currentSessionId}
          onSelect={handleOpenChat}
          onDelete={handleDeleteChat}
          onNewChat={handleNewChat}
          emptyMessage="Nenhum chat ainda"
        />
      </div>

      {/* Área principal */}
      <div className="pulso-chat-main flex flex-col min-h-0 rounded-xl border border-primary/20 glass-strong overflow-hidden">
      <div className="p-4 shrink-0">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold flex items-center gap-2 text-primary">
              <Database className="h-5 w-5 text-primary" />
              Inteligência de Dados
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Explore estrutura, estatísticas e modelos · Atalho: Alt+D
            </p>
          </div>
          <div className="flex gap-2">
            <DownloadReportButton
              onClick={async () => {
                const msgs = messages.map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp }));
                const result = await exportReport({ serviceId: "dados-ia", messages: msgs, format: "md" });
                toast({ title: result === "saved" ? "Relatório salvo" : "Relatório baixado", description: result === "saved" ? "Salvo em C:\\Users\\pytho\\Desktop\\Study\\docs" : "Arquivo baixado" });
              }}
              disabled={messages.length === 0}
            />
            <Button
              variant="pulso"
              size="sm"
              onClick={() => setShowConnection(!showConnection)}
            >
              {showConnection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              Conexão
            </Button>
          </div>
        </div>
      </div>

      {/* Connection Drawer */}
      {showConnection && (
        <div className="p-4 glass space-y-3">
          <h3 className="text-sm font-medium text-foreground">Conexão de Dados (Opcional)</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <Label htmlFor="db-type" className="text-xs">Tipo de Base</Label>
              <Select value={connectionData.type} onValueChange={(value) => setConnectionData({ ...connectionData, type: value })}>
                <SelectTrigger id="db-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sql">SQL</SelectItem>
                  <SelectItem value="nosql">NoSQL</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="host" className="text-xs">Host/URI</Label>
              <Input
                id="host"
                placeholder={connectionData.type === "nosql" ? "mongodb://localhost:27017" : "localhost:5432"}
                value={connectionData.host}
                onChange={(e) => setConnectionData({ ...connectionData, host: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="database" className="text-xs">Base</Label>
              <Input
                id="database"
                placeholder="meu_banco"
                value={connectionData.database}
                onChange={(e) => setConnectionData({ ...connectionData, database: e.target.value })}
              />
            </div>

            <div>
              <Label htmlFor="user" className="text-xs">
                Usuário{connectionData.type === "nosql" && " (opcional)"}
              </Label>
              <Input
                id="user"
                placeholder={connectionData.type === "nosql" ? "Ex.: admin (se houver autenticação)" : "admin"}
                value={connectionData.user}
                onChange={(e) => setConnectionData({ ...connectionData, user: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <Label htmlFor="password" className="text-xs">
                Senha{connectionData.type === "nosql" && " (opcional)"}
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={connectionData.password}
                  onChange={(e) => setConnectionData({ ...connectionData, password: e.target.value })}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground text-xs"
                >
                  {showPassword ? "Ocultar" : "Mostrar"}
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                ⚠️ Nunca compartilhe segredos nesta conversa
              </p>
            </div>
          </div>

          <Button
            variant="pulso"
            size="sm"
            className="w-full"
            onClick={handleApplyConnection}
          >
            Aplicar conexão
          </Button>
        </div>
      )}

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-5">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center min-h-[280px] text-center space-y-4">
                <Brain className="h-12 w-12 text-primary/60" />
                <div>
                  <p className="text-sm text-foreground font-medium">
                    Dados & IA — Pronto para usar
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Configure a conexão (opcional) ou faça uma pergunta. Ex.: &quot;Quais são as tabelas?&quot; ou &quot;Mostre correlações&quot;
                  </p>
                </div>
                <div className="pt-4 w-full max-w-md">
                  <p className="text-xs text-muted-foreground mb-2">Sugestões:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {quickActions.map((action, idx) => (
                      <Button
                        key={idx}
                        variant="pulso"
                        size="sm"
                        onClick={() => handleQuickAction(action)}
                        className="text-xs"
                      >
                        {action}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} mb-4 animate-slide-up`}
            >
              <div
                className={`max-w-[90%] rounded-2xl px-5 py-4 shadow-sm transition-all duration-fluid ease-fluid hover:shadow-md ${
                  message.role === "user"
                    ? "bg-chat-user pulso-chat-user-bubble text-chat-user-foreground shadow-md ml-auto border"
                    : message.retryPrompt
                      ? "rounded-xl border border-amber-500/30 bg-amber-500/5"
                      : "bg-chat-system text-chat-system-foreground border border-white/5 shadow-md hover:border-white/10"
                }`}
              >
                {message.retryPrompt ? (
                  <>
                    <div className="flex items-start gap-3">
                      <span className="text-amber-400 text-xl flex-shrink-0">⚠</span>
                      <div>
                        <p className="font-semibold text-amber-200">Não foi possível concluir</p>
                        <p className="text-[15px] text-muted-foreground mt-1 leading-relaxed">
                          {message.errorType === "connection"
                            ? "Verifique sua conexão com o banco de dados."
                            : message.errorType === "dataset_ref"
                              ? "O contexto da análise anterior não foi encontrado."
                              : "Possíveis causas: ausência de contexto (dataset_ref), timeout ou conexão."}
                        </p>
                        {message.errorType === "dataset_ref" && (
                          <p className="text-[13px] text-muted-foreground/90 mt-2 italic">
                            Dica: faça uma análise dos dados primeiro e, em seguida, peça para treinar o modelo.
                          </p>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="mt-3 text-sm font-medium text-amber-400 hover:text-amber-300 hover:bg-amber-500/10"
                          onClick={() => handleSend(message.retryPrompt)}
                          disabled={loading}
                        >
                          <RefreshCw className="h-3.5 w-3.5 mr-1.5" />
                          Tentar novamente
                        </Button>
                      </div>
                    </div>
                    <span className="text-xs text-amber-200/80 mt-2 block">
                      {message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </>
                ) : (
                  <ErrorBoundary
                    fallback={
                      <div className="space-y-2">
                        <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{stripMarkdown(message.content)}</p>
                        <p className="text-xs text-muted-foreground">Erro ao renderizar dados estruturados.</p>
                      </div>
                    }
                  >
                  <>
                    {(() => {
                      const res = message.data as { amostra?: { colunas?: unknown; linhas?: unknown } } | undefined;
                      const am = res?.amostra;
                      const colunasArr = Array.isArray(am?.colunas) ? am!.colunas : [];
                      const linhasArr = Array.isArray(am?.linhas) ? am!.linhas : [];
                      const hasStructuredAmostra = colunasArr.length > 0 && linhasArr.length > 0;
                      const parsedTable = !hasStructuredAmostra ? parseTableFromText(message.content) : null;
                      const displayContent = parsedTable ? parsedTable.contentWithoutTable : message.content;
                      const cols = hasStructuredAmostra ? (colunasArr as string[]).filter((c): c is string => typeof c === "string") : (parsedTable?.colunas ?? []);
                      const rows = hasStructuredAmostra ? (linhasArr as Record<string, unknown>[]) : (parsedTable?.linhas ?? []);
                      return (
                        <>
                          {displayContent.trim() && (
                            <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{stripMarkdown(displayContent)}</p>
                          )}
                          {cols.length > 0 && rows.length > 0 && (
                            <DataPreviewTable
                              colunas={cols}
                              linhas={rows}
                              titulo="Primeiras linhas"
                            />
                          )}
                        </>
                      );
                    })()}

                {/* Dados de ML (modelo_ml) */}
                {(() => {
                  try {
                    const res = message.data as { modelo_ml?: Record<string, unknown> } | undefined;
                    const ml = res?.modelo_ml;
                    if (!ml || typeof ml !== "object") return null;
                    return <DataChatML modeloMl={ml as Parameters<typeof DataChatML>[0]["modeloMl"]} />;
                  } catch {
                    return null;
                  }
                })()}

                {/* Gráficos automáticos (analise_estatistica) */}
                {(() => {
                  try {
                    const res = message.data as { analise_estatistica?: { graficos_metadados?: unknown[]; graficos_dados?: unknown[] } } | undefined;
                    const analise = res?.analise_estatistica;
                    const meta = Array.isArray(analise?.graficos_metadados) ? analise!.graficos_metadados : [];
                    const dados = Array.isArray(analise?.graficos_dados) ? analise!.graficos_dados : [];
                    if (!meta.length || !dados.length) return null;
                    return (
                      <DataChatCharts
                        graficosMetadados={meta as { tipo?: string; titulo?: string; eixo_x?: string; eixo_y?: string; explicacao?: string; vantagens?: string[]; desvantagens?: string[] }[]}
                        graficosDados={dados as { labels?: string[]; values?: number[]; x?: number[]; y?: number[] }[]}
                      />
                    );
                  } catch {
                    return null;
                  }
                })()}

                {/* Structure Data - suporta captura_dados (tabelas/quantidade_registros) ou legado (tables) */}
                {message.dataType === "structure" && message.data && (() => {
                  try {
                    const raw = message.data && typeof message.data === "object" ? (message.data as Record<string, unknown>) : {};
                    const d = (raw.captura_dados && typeof raw.captura_dados === "object" ? raw.captura_dados : raw) as Record<string, unknown>;
                    const rawTabelas = d?.tabelas ?? d?.tables;
                    let rows: { name: string; records: number }[] = [];
                    if (Array.isArray(rawTabelas)) {
                      const qtdRegistros = (d?.quantidade_registros && typeof d.quantidade_registros === "object") ? (d.quantidade_registros as Record<string, number>) : undefined;
                      rows = rawTabelas.map((t: unknown) => {
                        if (typeof t === "string") return { name: t, records: qtdRegistros?.[t] ?? 0 };
                        const obj = t && typeof t === "object" ? (t as { name?: string; records?: number }) : {};
                        return { name: String(obj.name ?? ""), records: Number(obj.records ?? 0) };
                      }).filter((r) => r.name);
                    }
                    const amostra = d?.amostra && typeof d.amostra === "object" ? (d.amostra as { colunas?: unknown; linhas?: unknown }) : undefined;
                    const colunas = Array.isArray(amostra?.colunas) ? (amostra!.colunas as string[]).filter((c): c is string => typeof c === "string") : [];
                    const linhas = Array.isArray(amostra?.linhas) ? (amostra!.linhas as Record<string, unknown>[]) : [];
                    const labelCol = d?.tipo_base === "NoSQL" ? "Coleção" : "Tabela";
                    return (
                      <div className="mt-3 space-y-4">
                        {rows.length > 0 && (
                          <div className="overflow-x-auto rounded-lg border border-border/50">
                            <table className="w-full text-sm">
                              <thead className="bg-muted/50">
                                <tr>
                                  <th className="text-left px-4 py-2 font-semibold">{labelCol}</th>
                                  <th className="text-left px-4 py-2 font-semibold">Registros</th>
                                </tr>
                              </thead>
                              <tbody>
                                {rows.map((row, idx) => (
                                  <tr key={idx} className={idx % 2 === 0 ? "bg-background" : "bg-muted/20"}>
                                    <td className="px-4 py-2 font-mono">{row.name}</td>
                                    <td className="px-4 py-2 tabular-nums">{Number(row.records).toLocaleString("pt-BR")}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                        {colunas.length > 0 && linhas.length > 0 ? (
                          <DataPreviewTable
                            colunas={colunas}
                            linhas={linhas}
                            titulo="Primeiras linhas"
                          />
                        ) : null}
                      </div>
                    );
                  } catch {
                    return null;
                  }
                })()}

                {/* Statistics Data */}
                {message.dataType === "stats" && message.data && (() => {
                  const stats = message.data as { metrics?: StatsMetric[]; correlations?: Correlation[] };
                  if (!Array.isArray(stats?.metrics) || !Array.isArray(stats?.correlations)) return null;
                  return (
                  <div className="mt-4 space-y-4">
                    <div className="grid grid-cols-2 gap-2">
                      {stats.metrics.map((metric, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-muted/30">
                          <p className="text-[13px] text-muted-foreground">{metric.label}</p>
                          <p className="text-[15px] font-semibold font-mono tabular-nums">{metric.value}</p>
                        </div>
                      ))}
                    </div>
                    <div>
                      <h4 className="font-semibold text-base mb-2 flex items-center gap-1">
                        <BarChart3 className="h-3.5 w-3.5" />
                        Correlações
                      </h4>
                      <ul className="space-y-1">
                        {stats.correlations.map((corr, idx) => (
                          <li key={idx} className="flex items-center justify-between text-[15px] p-2 rounded-lg bg-muted/30">
                            <span>{corr.vars}</span>
                            <Badge variant={corr.strength === "Forte" ? "default" : "secondary"} className="text-xs font-mono tabular-nums">
                              {corr.strength} ({corr.value})
                            </Badge>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  );
                })()}

                {/* Model Data */}
                {message.dataType === "model" && message.data && (() => {
                  const model = message.data as ModelData;
                  if (!model?.model || !Array.isArray(model?.metrics) || !Array.isArray(model?.insights) || !Array.isArray(model?.nextSteps)) return null;
                  return (
                  <div className="mt-4 space-y-4">
                    <div className="rounded-lg bg-muted/30 p-3">
                      <p className="text-[13px] text-muted-foreground mb-1">Modelo sugerido</p>
                      <p className="text-base font-semibold font-mono">{model.model}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      {model.metrics.map((metric, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-muted/30 text-center">
                          <p className="text-[13px] text-muted-foreground">{metric.name}</p>
                          <p className="text-lg font-semibold font-mono tabular-nums text-green-400">{metric.value}</p>
                        </div>
                      ))}
                    </div>

                    <div>
                      <h4 className="font-semibold text-base mb-2">💡 Insights</h4>
                      <div className="space-y-1">
                        {model.insights.map((insight, idx) => (
                          <div key={idx} className="flex items-start gap-2 p-3 rounded-lg bg-amber-500/10 border border-amber-500/20">
                            <Badge className="text-xs bg-amber-500/20 text-amber-200 shrink-0">!</Badge>
                            <span className="text-[15px] leading-relaxed">{insight}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-base mb-2">Próximos passos</h4>
                      <ul className="space-y-1 text-[15px]">
                        {model.nextSteps.map((step, idx) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-primary">→</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                  );
                })()}

                {/* Sugestão de próximo passo (quando sem conexão ou resposta mínima) */}
                {message.sugestaoProximoPasso?.trim() && (
                  <p className="text-sm text-muted-foreground mt-3 pt-3 border-t border-white/5 italic">
                    💡 {message.sugestaoProximoPasso}
                  </p>
                )}

                    <span className="text-xs text-white/80 mt-2 block">
                      {message.timestamp.toLocaleTimeString('pt-BR', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </>
                  </ErrorBoundary>
                )}
              </div>
            </div>
          ))
        )}

        </div>

        <div className="p-4 shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2 items-end"
        >
          {loading ? (
            <div
              className="flex-1 min-h-[44px] w-full rounded-lg border border-white/10 bg-background px-4 py-2 flex items-center"
              role="status"
              aria-live="polite"
              aria-label="Aguardando resposta"
            >
              {loadingPhaseRef.current === "connecting" ? (
                <LoaderEstudandoArquivos message="Conectando e carregando dataset..." compact className="!p-0 !min-h-0 !rounded-none !border-0 !bg-transparent w-full" />
              ) : (
                <LoaderEscrevendoCodigo message="Escrevendo seu código..." compact className="!p-0 !min-h-0 !rounded-none !border-0 !bg-transparent w-full" />
              )}
            </div>
          ) : (
          <ChatTextarea
            id="data-input"
            placeholder="Pergunte sobre dados, modelos ou previsões"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onSend={handleSend}
            className="py-2"
          />
          )}
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="showcase-sparkle-btn showcase-sparkle-btn--compact shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span className="showcase-spark" aria-hidden />
            <span className="absolute inset-[0.1em] rounded-[100px] bg-background/80 pointer-events-none" />
            <Send className="w-4 h-4 relative z-10 shrink-0" />
            <span className="relative z-10">Enviar</span>
          </button>
        </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataChat;
