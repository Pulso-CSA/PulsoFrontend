import { useState } from "react";
import { Send, TrendingDown, Server, DollarSign, Lightbulb } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { finopsApi } from "@/lib/api";

interface Message {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: Date;
  recommendations?: string[];
  tags?: string[];
}

const FinOpsChat = () => {
  const { user } = useAuth();
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

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

  return (
    <div className="glass-strong neon-glow rounded-lg overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-primary/30">
        <h2 className="text-lg font-semibold neon-text flex items-center gap-2" style={{ color: 'hsl(150 100% 65%)' }}>
          <DollarSign className="h-5 w-5" style={{ color: 'hsl(150 100% 65%)' }} />
          FinOps Inteligente
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Insights de custo em linguagem natural · Atalho: Alt+F
        </p>
      </div>

      {/* Cost Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 glass border-y border-primary/20">
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
          <p className="text-lg font-semibold text-finops flex items-center gap-1">
            <TrendingDown className="h-4 w-4 animate-bounce-subtle" />
            {costSummary.trend}
          </p>
        </div>
      </div>

      {/* Chat Messages */}
      <div className="h-[400px] overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <Server className="h-12 w-12 text-muted-foreground" />
            <div>
              <p className="text-sm text-foreground font-medium">
                Faça uma pergunta sobre custos e otimizações
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Ex.: "Como reduzir custos do RDS em horário ocioso?"
              </p>
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
                    ? "bg-chat-user text-primary-foreground"
                    : "bg-chat-system text-foreground"
                }`}
              >
                <p className="text-sm">{message.content}</p>
                
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
            <div className="bg-chat-system text-foreground rounded-lg p-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1.5 items-end h-4">
                  <div
                    className="w-2 h-2 rounded-full animate-typing-bounce"
                    style={{ backgroundColor: "hsl(150 100% 65%)", animationDelay: "0ms" }}
                  />
                  <div
                    className="w-2 h-2 rounded-full animate-typing-bounce"
                    style={{ backgroundColor: "hsl(150 100% 65%)", animationDelay: "200ms" }}
                  />
                  <div
                    className="w-2 h-2 rounded-full animate-typing-bounce"
                    style={{ backgroundColor: "hsl(150 100% 65%)", animationDelay: "400ms" }}
                  />
                </div>
                <span className="text-sm text-muted-foreground">Digitando...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {messages.length === 0 && (
        <div className="px-4 pb-4">
          <p className="text-xs text-muted-foreground mb-2">Ações rápidas:</p>
          <div className="flex flex-wrap gap-2">
            {quickActions.map((action, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                onClick={() => handleQuickAction(action)}
                className="text-xs"
              >
                {action}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-border">
        <div className="flex gap-2">
          <Input
            id="finops-input"
            placeholder="Ex.: 'Como reduzir custos do RDS em horário ocioso?'"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
          />
          <Button onClick={handleSend} disabled={!input.trim() || loading}>
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default FinOpsChat;
