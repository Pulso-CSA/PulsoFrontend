import { useState, useEffect } from "react";
import { Send, TrendingDown, Server, DollarSign, Lightbulb, MessageSquare, Trash2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatTextarea } from "@/components/ui/chat-textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { finopsApi } from "@/lib/api";
import { getFinOpsChatSessions, setFinOpsChatSessions, type ChatSession } from "@/lib/connectionStorage";
import { exportReport } from "@/lib/exportReport";
import { DownloadReportButton } from "@/components/ui/DownloadReportButton";
import { LoaderEscrevendoCodigo } from "@/components/loaders";
import { ChatSidebar } from "./ChatSidebar";

interface Message {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: Date;
  recommendations?: string[];
  tags?: string[];
}

type FinOpsSession = ChatSession<Message & { timestamp: string }>;

function restoreMessages(messages: (Omit<Message, "timestamp"> & { timestamp: string })[]): Message[] {
  return messages.map((m) => ({ ...m, timestamp: new Date(m.timestamp) }));
}

const FinOpsChat = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [sessions, setSessions] = useState<FinOpsSession[]>(() => getFinOpsChatSessions());
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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

  const quickActions = [
    "Ver Quick Wins",
    "Comparar regiões",
    "Políticas de desligamento automático",
  ];

  const costSummary = {
    monthly: "R$ 12.450",
    topServices: ["EC2: R$ 5.200", "RDS: R$ 3.100", "S3: R$ 1.800"],
    trend: "↓ 8% vs mês anterior",
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
      <div className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 shrink-0">
        <div>
          <h2 className="text-lg font-semibold flex items-center gap-2 text-primary">
            <DollarSign className="h-5 w-5 text-primary" />
            FinOps Inteligente
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Insights de custo em linguagem natural · Atalho: Alt+F
          </p>
        </div>
        <DownloadReportButton
          onClick={async () => {
            const msgs = messages.map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp }));
            const result = await exportReport({ serviceId: "finops", messages: msgs, format: "md" });
            toast({ title: result === "saved" ? "Relatório salvo" : "Relatório baixado", description: result === "saved" ? "Salvo em C:\\Users\\pytho\\Desktop\\Study\\docs" : "Arquivo baixado" });
          }}
          disabled={messages.length === 0}
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 glass shrink-0">
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

      <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
        {/* Chat Area */}
        <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-5">
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
          messages.map((message, index) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} animate-slide-up`}
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <div
                className={`max-w-[80%] rounded-lg p-3 transition-all duration-300 hover:scale-[1.01] ${
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

                <p className="text-xs opacity-70 mt-2">
                  {message.timestamp.toLocaleTimeString('pt-BR', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </p>
              </div>
            </div>
          ))
        )}
        
        {loading && (
          <div className="flex justify-start animate-slide-up">
            <LoaderEscrevendoCodigo message="Analisando custos e gerando insights..." className="w-full max-w-sm" />
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
          <ChatTextarea
            id="finops-input"
            placeholder="Ex.: 'Como reduzir custos do RDS em horário ocioso?'"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onSend={handleSend}
            className="py-2"
          />
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

export default FinOpsChat;
