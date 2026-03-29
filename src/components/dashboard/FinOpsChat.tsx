import { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { TrendingDown, Server, DollarSign, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PromptSearchTextarea } from "@/components/ui/PromptSearchTextarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { finopsApi } from "@/lib/api";
import { getFinOpsChatSessions, setFinOpsChatSessions, getAllCloudCredentials, setCloudCredentials, type ChatSession } from "@/lib/connectionStorage";
import { exportReport } from "@/lib/exportReport";
import { DownloadReportButton } from "@/components/ui/DownloadReportButton";
import { LoaderGenerating } from "@/components/loaders";
import { ChatSidebar } from "./ChatSidebar";
import CloudCredentialsDialog, { type CloudCredentialsState } from "./CloudCredentialsDialog";

interface Message {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: Date;
  recommendations?: string[];
  tags?: string[];
}

interface FinOpsCostSummary {
  monthly: string;
  topServices: string[];
  trend: string;
}

type FinOpsSession = ChatSession<Message & { timestamp: string }>;
const FINOPS_COST_SUMMARY_KEY = "pulso_finops_cost_summary";

function getFinOpsCostSummaryFromStorage(): FinOpsCostSummary | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(FINOPS_COST_SUMMARY_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as Partial<FinOpsCostSummary>;
    if (
      typeof parsed.monthly !== "string" ||
      !Array.isArray(parsed.topServices) ||
      parsed.topServices.some((item) => typeof item !== "string") ||
      typeof parsed.trend !== "string"
    ) {
      return null;
    }
    return {
      monthly: parsed.monthly,
      topServices: parsed.topServices,
      trend: parsed.trend,
    };
  } catch {
    return null;
  }
}

function restoreMessages(messages: (Omit<Message, "timestamp"> & { timestamp: string })[]): Message[] {
  return messages.map((m) => ({ ...m, timestamp: new Date(m.timestamp) }));
}

const FinOpsChat = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const { t } = useTranslation();
  const [sessions, setSessions] = useState<FinOpsSession[]>(() => getFinOpsChatSessions());
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeProvider, setActiveProvider] = useState<"aws" | "azure" | "gcp">("aws");
  const [credentialsOpen, setCredentialsOpen] = useState(false);
  const [credentials, setCredentials] = useState<CloudCredentialsState>(getAllCloudCredentials);
  const [costSummary, setCostSummary] = useState<FinOpsCostSummary | null>(() => getFinOpsCostSummaryFromStorage());
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const s = getFinOpsChatSessions();
    setSessions(s);
    if (s.length > 0 && !currentSessionId) {
      const last = s[s.length - 1];
      setCurrentSessionId(last.id);
      setMessages(restoreMessages(last.messages as (Omit<Message, "timestamp"> & { timestamp: string })[]));
    }
  }, []);

  useEffect(() => {
    setCredentials(getAllCloudCredentials());
  }, []);

  useEffect(() => {
    const refreshCostSummary = () => setCostSummary(getFinOpsCostSummaryFromStorage());
    window.addEventListener("storage", refreshCostSummary);
    return () => {
      window.removeEventListener("storage", refreshCostSummary);
    };
  }, []);

  useEffect(() => {
    const openCredentials = (event: Event) => {
      const detail = (event as CustomEvent<{ target?: "cloud" | "finops" }>).detail;
      if (detail?.target !== "finops") return;
      setCredentialsOpen(true);
    };
    const selectProvider = (event: Event) => {
      const detail = (event as CustomEvent<{ target?: "cloud" | "finops"; provider?: "aws" | "azure" | "gcp" }>).detail;
      if (detail?.target !== "finops" || !detail.provider) return;
      setActiveProvider(detail.provider);
    };
    window.addEventListener("pulso-open-cloud-credentials", openCredentials as EventListener);
    window.addEventListener("pulso-select-cloud-provider", selectProvider as EventListener);
    return () => {
      window.removeEventListener("pulso-open-cloud-credentials", openCredentials as EventListener);
      window.removeEventListener("pulso-select-cloud-provider", selectProvider as EventListener);
    };
  }, []);

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
    if (sessions.length > 0) setFinOpsChatSessions(sessions);
  }, [sessions]);

  // Mantém rolagem unitária no container da conversa.
  useEffect(() => {
    const el = messagesContainerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, loading, currentSessionId]);

  const quickActions = [
    "Ver Quick Wins",
    "Comparar regiões",
    "Políticas de desligamento automático",
  ];

  const buildProviderCredentialsPayload = () => {
    if (activeProvider === "aws") {
      const c = credentials.aws;
      if (!c.accessKeyId || !c.secretAccessKey || !c.region) return {};
      return {
        aws_credentials: {
          access_key_id: c.accessKeyId,
          secret_access_key: c.secretAccessKey,
          region: c.region,
        },
      };
    }
    if (activeProvider === "azure") {
      const c = credentials.azure;
      if (!c.tenantId || !c.clientId || !c.clientSecret || !c.subscriptionId) return {};
      return {
        azure_credentials: {
          tenant_id: c.tenantId,
          client_id: c.clientId,
          client_secret: c.clientSecret,
          subscription_id: c.subscriptionId,
        },
      };
    }
    const c = credentials.gcp;
    if (!c.projectId || !c.clientEmail || !c.privateKey) return {};
    return {
      gcp_credentials: {
        project_id: c.projectId,
        service_account_json: {
          type: "service_account",
          project_id: c.projectId,
          client_email: c.clientEmail,
          private_key: c.privateKey,
        },
      },
    };
  };

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
    setLoading(true);

    try {
      const idRequisicao = `FINOP-${Date.now()}`;
      const res = await finopsApi.chat({
        mensagem: promptText,
        id_requisicao: idRequisicao,
        usuario: user?.id,
        ...buildProviderCredentialsPayload(),
      });

      const content = res?.resposta_texto ?? "Resposta recebida sem conteúdo.";
      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content,
        timestamp: new Date(),
        tags: res?.etapas_executadas,
      };

      setMessages((prev) => [...prev, systemMessage]);
    } catch (err) {
      toast({
        title: "Erro na análise FinOps",
        description: err instanceof Error ? err.message : "Tente novamente",
        variant: "destructive",
      });
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content: `Erro: ${err instanceof Error ? err.message : "Falha ao conectar com a API FinOps."}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

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

  const handleOpenChat = (session: FinOpsSession) => {
    setCurrentSessionId(session.id);
    setMessages(restoreMessages(session.messages as (Omit<Message, "timestamp"> & { timestamp: string })[]));
  };

  const handleDeleteChat = (id: string) => {
    const next = sessions.filter((s) => s.id !== id);
    setSessions(next);
    setFinOpsChatSessions(next);
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

  const sessionItems = sessions.map((s) => ({ id: s.id, title: s.title, updatedAt: s.updatedAt }));

  const handleSaveCredentials = (provider: "aws" | "azure" | "gcp") => {
    setCloudCredentials(provider, credentials[provider]);
    setCredentialsOpen(false);
    toast({
      title: "Credenciais salvas",
      description: `Credenciais ${provider.toUpperCase()} atualizadas com sucesso`,
    });
  };

  return (
    <div className="pulso-chat-layout flex-1 h-full min-h-0 overflow-hidden">
      {/* Sidebar — Histórico (mesma posição que PulsoCSA) */}
      <div className="pulso-chat-sidebar glass-strong">
        <ChatSidebar
          serviceId="finops"
          sessions={sessionItems}
          currentSessionId={currentSessionId}
          onSelect={handleOpenChat}
          onDelete={handleDeleteChat}
          onNewChat={handleNewChat}
          emptyMessage="Nenhum chat ainda"
        />
      </div>

      {/* Área principal */}
      <div className="pulso-chat-main pulso-chat-main-shell flex flex-col min-h-0 rounded-xl border border-primary/20 glass-strong overflow-hidden">
      <div className="pulso-chat-main-header p-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 shrink-0 border-b border-primary/10">
        <div className="min-w-0 flex-1">
          <h2 className="text-base font-semibold flex items-center gap-1.5 text-primary truncate">
            <DollarSign className="h-4 w-4 shrink-0 text-primary" />
            FinOps Inteligente
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5 truncate">
            Insights de custo em linguagem natural · Alt+F
          </p>
        </div>
        <DownloadReportButton
          onClick={async () => {
            const msgs = messages.map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp }));
            const result = await exportReport({ serviceId: "finops", messages: msgs, format: "md" });
            toast({
              title: result === "saved" ? t("pulsoCsa.reportSaved") : t("pulsoCsa.reportDownloaded"),
              description: result === "saved" ? t("pulsoCsa.reportSavedDesc") : t("pulsoCsa.reportDownloadStarted"),
            });
          }}
          disabled={messages.length === 0}
          className="showcase-download-report-btn--compact shrink-0"
          aria-label={t("dashboard.exportReportAria")}
          title={t("dashboard.exportReportTitle")}
        >
          {t("dashboard.exportReportTitle")}
        </DownloadReportButton>
      </div>

      {costSummary && (
        <div className="pulso-chat-main-fixed-section grid grid-cols-1 md:grid-cols-3 gap-4 p-4 glass shrink-0">
          <div className="space-y-1 opacity-0 animate-fade-in stagger-1">
            <p className="text-xs text-muted-foreground">Custo mensal</p>
            <p className="text-xl font-bold text-foreground">{costSummary.monthly}</p>
          </div>
          <div className="space-y-1 opacity-0 animate-fade-in stagger-2">
            <p className="text-xs text-muted-foreground">Principais serviços</p>
            <div className="text-sm text-foreground space-y-0.5">
              {costSummary.topServices.map((service, idx) => (
                <div key={idx}>{service}</div>
              ))}
            </div>
          </div>
          <div className="space-y-1 opacity-0 animate-fade-in stagger-3">
            <p className="text-xs text-muted-foreground">Tendência</p>
            <p className="text-lg font-semibold text-primary flex items-center gap-1">
              <TrendingDown className="h-4 w-4 animate-bounce-subtle" />
              {costSummary.trend}
            </p>
          </div>
        </div>
      )}

      <div className="pulso-chat-main-body">
        {/* Chat Area */}
        <div ref={messagesContainerRef} className="pulso-chat-scroll-area p-5 space-y-5">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <Server className="h-12 w-12 text-primary/50" />
                <div>
                  <p className="text-sm text-foreground font-medium">
                    Faça uma pergunta sobre custos e otimizações
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">
                    Ex.: "Como reduzir custos do RDS em horário ocioso?"
                  </p>
                </div>
                <div className="pt-4 w-full max-w-md">
                  <p className="text-xs text-muted-foreground mb-2">Sugestões:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {quickActions.map((action, idx) => (
                      <Button
                        key={idx}
                        variant="outline"
                        size="sm"
                        onClick={() => handleQuickAction(action)}
                        className="text-xs pulso-suggestion-btn"
                      >
                        {action}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
          messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-slide-up`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div
                className={`max-w-[85%] rounded-lg p-3 transition-all duration-300 hover:scale-[1.01] ${
                  message.role === "user"
                    ? "bg-chat-user pulso-chat-user-bubble text-chat-user-foreground border border-primary/20"
                    : "bg-chat-system text-chat-system-foreground"
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                
                {message.recommendations && (
                  <div className="mt-3 space-y-2 p-3 bg-background/10 rounded border border-border/50">
                    <p className="text-xs font-semibold flex items-center gap-1">
                      <Lightbulb className="h-3 w-3" />
                      Recomendações:
                    </p>
                    <ul className="space-y-1.5 text-xs">
                      {message.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start gap-2">
                          <span className="text-success mt-0.5">•</span>
                          <span>{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {message.tags && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {message.tags.map((tag, idx) => (
                      <Badge key={idx} variant="secondary" className="text-xs">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                )}

                <span className="pulso-chat-msg-timestamp mt-2">
                  {message.timestamp.toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            </div>
          ))
        )}
        
        {loading && (
          <div className="relative min-h-[120px]">
            <LoaderGenerating />
          </div>
        )}
        </div>

        <div className="pulso-chat-main-footer">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2 items-end"
        >
          <PromptSearchTextarea
            id="finops-input"
            placeholder="Ex.: 'Como reduzir custos do RDS em horário ocioso?'"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onSend={handleSend}
            disabled={loading}
          />
        </form>
        </div>
      </div>
      </div>
      <CloudCredentialsDialog
        open={credentialsOpen}
        onOpenChange={setCredentialsOpen}
        provider={activeProvider}
        credentials={credentials}
        onCredentialsChange={setCredentials}
        onSave={handleSaveCredentials}
        title="Credenciais FinOps"
        description="Preencha as credenciais do provedor selecionado para usar no FinOps."
      />
    </div>
  );
};

export default FinOpsChat;
