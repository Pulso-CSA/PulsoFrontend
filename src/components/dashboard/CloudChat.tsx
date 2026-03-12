import { useState, useEffect } from "react";
import { Copy, FolderOpen, FileCode, CloudCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PromptSearchTextarea } from "@/components/ui/PromptSearchTextarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { infraApi } from "@/lib/api";
import { getRootPath, setRootPath, getCloudChatSessions, setCloudChatSessions, getAllCloudCredentials, setCloudCredentials, type ChatSession } from "@/lib/connectionStorage";
import { exportReport } from "@/lib/exportReport";
import { DownloadReportButton } from "@/components/ui/DownloadReportButton";
import { FolderFileUpload } from "@/components/ui/FolderFileUpload";
import { LoaderGenerating } from "@/components/loaders";
import { ChatSidebar } from "./ChatSidebar";
import CloudCredentialsDialog, { type CloudCredentialsState } from "./CloudCredentialsDialog";

interface Message {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: Date;
  provider?: "aws" | "azure" | "gcp";
  resources?: string[];
  codeBlock?: string;
}

type CloudSession = ChatSession<Message & { timestamp: string }>;

function restoreMessages(messages: (Omit<Message, "timestamp"> & { timestamp: string })[]): Message[] {
  return messages.map((m) => ({ ...m, timestamp: new Date(m.timestamp) }));
}

const CloudChat = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [sessions, setSessions] = useState<CloudSession[]>(() => getCloudChatSessions());
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [rootPath, setRootPathState] = useState(() => getRootPath());
  const [loading, setLoading] = useState(false);
  const [activeProvider, setActiveProvider] = useState<"aws" | "azure" | "gcp">("aws");
  const [credentialsOpen, setCredentialsOpen] = useState(false);
  const [credentials, setCredentials] = useState<CloudCredentialsState>(getAllCloudCredentials);

  useEffect(() => {
    setRootPathState(getRootPath());
    setCredentials(getAllCloudCredentials());
  }, []);

  useEffect(() => {
    const openCredentials = (event: Event) => {
      const detail = (event as CustomEvent<{ target?: "cloud" | "finops" }>).detail;
      if (detail?.target !== "cloud") return;
      setCredentialsOpen(true);
    };
    const selectProvider = (event: Event) => {
      const detail = (event as CustomEvent<{ target?: "cloud" | "finops"; provider?: "aws" | "azure" | "gcp" }>).detail;
      if (detail?.target !== "cloud" || !detail.provider) return;
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
    const s = getCloudChatSessions();
    setSessions(s);
    if (s.length > 0 && !currentSessionId) {
      const last = s[s.length - 1];
      setCurrentSessionId(last.id);
      setMessages(restoreMessages(last.messages as (Omit<Message, "timestamp"> & { timestamp: string })[]));
    }
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
    if (sessions.length > 0) setCloudChatSessions(sessions);
  }, [sessions]);

  const quickActions = [
    "Criar VPC com subnets públicas e privadas",
    "Deploy de container ECS com load balancer",
    "Configurar banco RDS PostgreSQL",
    "Setup de bucket S3 com CloudFront",
  ];

  const providerColors = {
    aws: { bg: "bg-orange-500", border: "border-orange-500", text: "text-orange-400", hsl: "hsl(35 100% 55%)" },
    azure: { bg: "bg-blue-500", border: "border-blue-500", text: "text-blue-400", hsl: "hsl(210 100% 55%)" },
    gcp: { bg: "bg-red-500", border: "border-red-500", text: "text-red-400", hsl: "hsl(4 80% 55%)" },
  };

  const handleRootPathChange = (value: string) => {
    setRootPathState(value);
    setRootPath(value);
  };

  const handleSend = async () => {
    const promptText = input.trim();
    if (!promptText) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: promptText,
      timestamp: new Date(),
      provider: activeProvider,
    };

    if (!currentSessionId) {
      const newId = `chat-${crypto.randomUUID()}`;
      setCurrentSessionId(newId);
      setSessions((prev) => [...prev, { id: newId, title: promptText.slice(0, 50), messages: [], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }]);
    }
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setLoading(true);

    const idRequisicao = `INFRA-${Date.now()}`;

    try {
      const tenantId = user?.id ?? "default";

      const effectiveRootPath = rootPath.trim() || ".";
      let infraSpec: unknown = null;
      const analyzeRes = await infraApi.analyze({
        root_path: effectiveRootPath,
        tenant_id: tenantId,
        id_requisicao: idRequisicao,
        user_request: promptText,
        providers: [activeProvider],
      });

      const reports = (analyzeRes as { reports?: { infra_spec_draft?: unknown } })?.reports;
      if (reports?.infra_spec_draft) {
        infraSpec = reports.infra_spec_draft;
      }

      const generateRes = await infraApi.generate({
        infra_spec: infraSpec,
        user_request: promptText,
        root_path: effectiveRootPath,
        tenant_id: tenantId,
        id_requisicao: idRequisicao,
      });

      const terraformCode =
        (generateRes as { terraform_code?: string })?.terraform_code ??
        (generateRes as { reports?: { terraform_code?: string } })?.reports?.terraform_code ??
        "";
      const artifacts =
        (generateRes as { artifacts?: string[] })?.artifacts ??
        (generateRes as { reports?: { artifacts?: string[] } })?.reports?.artifacts ??
        [];
      const content = terraformCode
        ? `Infraestrutura Terraform gerada para ${activeProvider.toUpperCase()}.`
        : artifacts.length > 0
          ? `Arquivos Terraform criados: ${artifacts.join(", ")}`
          : `Infraestrutura gerada para ${activeProvider.toUpperCase()}.`;

      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content,
        timestamp: new Date(),
        provider: activeProvider,
        resources: terraformCode ? ["Código Terraform gerado"] : undefined,
        codeBlock: terraformCode || undefined,
      };

      setMessages((prev) => [...prev, systemMessage]);
    } catch (err) {
      toast({
        title: "Erro na geração de infraestrutura",
        description: err instanceof Error ? err.message : "Tente novamente",
        variant: "destructive",
      });
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content: `Erro: ${err instanceof Error ? err.message : "Falha ao conectar com a API de Infraestrutura."}`,
        timestamp: new Date(),
        provider: activeProvider,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = (action: string) => setInput(action);

  const handleNewChat = () => {
    const newId = `chat-${crypto.randomUUID()}`;
    setCurrentSessionId(newId);
    setMessages([]);
    setInput("");
    setSessions((prev) => [...prev, { id: newId, title: "Novo chat", messages: [], createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() }]);
  };

  const handleOpenChat = (session: CloudSession) => {
    setCurrentSessionId(session.id);
    setMessages(restoreMessages(session.messages as (Omit<Message, "timestamp"> & { timestamp: string })[]));
  };

  const handleDeleteChat = (id: string) => {
    const next = sessions.filter((s) => s.id !== id);
    setSessions(next);
    setCloudChatSessions(next);
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
    toast({ title: "Chat removido", description: "O chat foi excluído" });
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast({ title: "Código copiado", description: "Terraform copiado para a área de transferência" });
  };

  const handleSaveCredentials = (provider: "aws" | "azure" | "gcp") => {
    setCloudCredentials(provider, credentials[provider]);
    setCredentialsOpen(false);
    toast({
      title: "Credenciais salvas",
      description: `Credenciais ${provider.toUpperCase()} atualizadas com sucesso`,
    });
  };

  const sessionItems = sessions.map((s) => ({ id: s.id, title: s.title, updatedAt: s.updatedAt }));

  return (
    <div className="pulso-chat-layout h-full min-h-0 overflow-hidden">
      {/* Sidebar — Histórico (mesma posição que PulsoCSA) */}
      <div className="pulso-chat-sidebar glass-strong">
        <ChatSidebar
          serviceId="cloud"
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
      <div className="pulso-chat-main-header p-3 flex flex-row items-center justify-between gap-3 shrink-0 min-w-0">
        {/* Caminho do projeto + Escolher arquivo à esquerda */}
        <div className="flex items-center min-w-0 flex-1">
          <div className="relative w-full max-w-[320px] min-w-[200px] overflow-visible showcase-search-poda--prompt showcase-search-poda--toolbar">
            <div className="showcase-search-poda w-full">
              <div className="showcase-search-glow" aria-hidden />
              <div className="showcase-search-darkBorderBg" aria-hidden />
              <div className="showcase-search-darkBorderBg" aria-hidden />
              <div className="showcase-search-darkBorderBg" aria-hidden />
              <div className="showcase-search-white" aria-hidden />
              <div className="showcase-search-border" aria-hidden />
              <div className="showcase-search-main flex-1 min-w-0 flex items-center relative">
                <input
                  type="text"
                  placeholder="Caminho do projeto (opcional)"
                  value={rootPath}
                  onChange={(e) => handleRootPathChange(e.target.value)}
                  className="showcase-search-input showcase-search-input--prompt showcase-search-input--no-lupa w-full min-w-0 flex-1 !pl-3 !pr-12 border-0 focus:outline-none focus:ring-0"
                  aria-label="Caminho do projeto"
                />
                <FolderFileUpload
                  compact
                  className="pulso-folder-file-upload--inline-path"
                  onFileChange={(files) => {
                    const f = files?.item(0);
                    if (f) handleRootPathChange((f as File & { path?: string }).path ?? f.name ?? "");
                  }}
                >
                  {""}
                </FolderFileUpload>
              </div>
            </div>
          </div>
        </div>
        <DownloadReportButton
          onClick={async () => {
            const msgs = messages.map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp }));
            const result = await exportReport({ serviceId: "cloud", messages: msgs, format: "md" });
            toast({ title: result === "saved" ? "Relatório salvo" : "Relatório baixado", description: result === "saved" ? "Salvo em C:\\Users\\pytho\\Desktop\\Study\\docs" : "Arquivo baixado" });
          }}
          disabled={messages.length === 0}
          className="showcase-download-report-btn--compact text-white shrink-0 ml-2"
        />
      </div>

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Chat Area */}
        <div className="pulso-chat-scroll-area p-5 space-y-5">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <CloudCog className="h-12 w-12 text-primary/50" />
                <div>
                  <p className="text-sm text-foreground font-medium">Descreva a infraestrutura que deseja criar</p>
                  <p className="text-xs text-muted-foreground mt-1">Use linguagem natural ou informe o caminho de um arquivo</p>
                </div>
                <div className="pt-4 w-full max-w-md">
                  <p className="text-xs text-muted-foreground mb-2">Sugestões:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {quickActions.map((action, idx) => (
                      <Button key={idx} variant="outline" size="sm" onClick={() => handleQuickAction(action)} className="text-xs pulso-suggestion-btn">
                        {action}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-lg p-3 ${message.role === "user" ? "bg-chat-user pulso-chat-user-bubble text-chat-user-foreground border" : "bg-chat-system text-chat-system-foreground border border-border/50"}`}>
                    {message.provider && (
                      <Badge variant="outline" className="mb-2 text-xs" style={{ borderColor: providerColors[message.provider].hsl, color: providerColors[message.provider].hsl }}>
                        {message.provider.toUpperCase()}
                      </Badge>
                    )}
                    <p className="text-sm text-foreground whitespace-pre-wrap">{message.content}</p>
                    {message.resources && (
                      <div className="mt-3 space-y-2 p-3 bg-background/30 rounded border border-primary/20">
                        <p className="text-xs font-semibold flex items-center gap-1 text-primary"><FolderOpen className="h-3 w-3" />Recursos criados:</p>
                        <ul className="space-y-1 text-xs">
                          {message.resources.map((resource, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-muted-foreground"><span className="text-primary mt-0.5">•</span><span>{resource}</span></li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {message.codeBlock && (
                      <div className="mt-3 relative">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs text-muted-foreground flex items-center gap-1"><FileCode className="h-3 w-3" />Terraform</span>
                          <Button variant="ghost" size="sm" onClick={() => handleCopyCode(message.codeBlock!)} className="h-6 px-2 text-xs"><Copy className="h-3 w-3 mr-1" />Copiar</Button>
                        </div>
                        <pre className="bg-background/50 rounded p-3 text-xs font-mono overflow-x-auto border border-primary/20">{message.codeBlock}</pre>
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">{message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</p>
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

        <div className="p-4 shrink-0">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex gap-2 items-end"
            >
              <div className="flex-1 min-w-0">
                <PromptSearchTextarea
                  placeholder="Ex.: 'Criar VPC com 2 subnets públicas e 2 privadas'"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onSend={handleSend}
                  disabled={loading}
                />
              </div>
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
        title="Credenciais Cloud IaC"
        description="Preencha as credenciais do provedor selecionado para usar no Cloud IaC."
      />
    </div>
  );
};

export default CloudChat;
