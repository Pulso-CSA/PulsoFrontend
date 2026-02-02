import { useState } from "react";
import { Send, Database, ChevronDown, ChevronUp, BarChart3, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import { inteligenciaApi } from "@/lib/api";
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

const DataChat = () => {
  const { toast } = useToast();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showConnection, setShowConnection] = useState(false);
  const [connectionData, setConnectionData] = useState({
    type: "sql",
    host: "",
    database: "",
    user: "",
    password: "",
  });
  const [showPassword, setShowPassword] = useState(false);

  const quickActions = [
    "Ver estrutura da base",
    "Calcular correlações principais",
    "Sugerir modelo para detecção de fraude",
  ];

  const handleSend = async (overridePrompt?: string) => {
    const promptText = (overridePrompt ?? input).trim();
    if (!promptText) return;

    if (
      !connectionData.host.trim() ||
      !connectionData.database.trim() ||
      !connectionData.user.trim()
    ) {
      toast({
        title: "Configure a conexão",
        description: "Preencha Host/URI, Base e Usuário na seção Conexão antes de enviar",
        variant: "destructive",
      });
      return;
    }

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
      const { host, port } = parseHostPort(connectionData.host);
      const res = await inteligenciaApi.query({
        prompt: promptText,
        db_config: {
          host,
          port,
          user: connectionData.user.trim(),
          password: connectionData.password,
          database: connectionData.database.trim(),
        },
      });

      const content =
        typeof res?.answer === "string"
          ? res.answer
          : typeof res?.result === "string"
            ? res.result
            : res?.data != null
              ? JSON.stringify(res.data, null, 2)
              : "Resposta recebida sem conteúdo textual.";

      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content,
        timestamp: new Date(),
        data: res?.data ?? res?.result,
      };

      setMessages((prev) => [...prev, systemMessage]);
    } catch (err) {
      toast({
        title: "Erro na consulta",
        description: err instanceof Error ? err.message : "Tente novamente",
        variant: "destructive",
      });
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content: `Erro: ${err instanceof Error ? err.message : "Falha ao conectar com a API de Inteligência de Dados."}`,
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
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold neon-text flex items-center gap-2" style={{ color: 'hsl(270 100% 80%)' }}>
              <Database className="h-5 w-5" style={{ color: 'hsl(270 100% 80%)' }} />
              Inteligência de Dados
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              Explore estrutura, estatísticas e modelos · Atalho: Alt+D
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowConnection(!showConnection)}
          >
            {showConnection ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            Conexão
          </Button>
        </div>
      </div>

      {/* Connection Drawer */}
      {showConnection && (
        <div className="p-4 glass border-b border-primary/30 space-y-3">
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
                placeholder="localhost:5432"
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
              <Label htmlFor="user" className="text-xs">Usuário</Label>
              <Input
                id="user"
                placeholder="admin"
                value={connectionData.user}
                onChange={(e) => setConnectionData({ ...connectionData, user: e.target.value })}
              />
            </div>

            <div className="md:col-span-2">
              <Label htmlFor="password" className="text-xs">Senha</Label>
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
            size="sm"
            className="w-full"
            onClick={() => {
              if (connectionData.host && connectionData.database && connectionData.user) {
                toast({ title: "Conexão configurada", description: "Os parâmetros serão usados nas próximas consultas." });
                setShowConnection(false);
              } else {
                toast({
                  title: "Campos obrigatórios",
                  description: "Preencha Host/URI, Base e Usuário",
                  variant: "destructive",
                });
              }
            }}
          >
            Aplicar conexão
          </Button>
        </div>
      )}

      {/* Chat Messages */}
      <div className="h-[400px] overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
            <Brain className="h-12 w-12 text-muted-foreground" />
            <div>
              <p className="text-sm text-foreground font-medium">
                Conecte-se à base ou faça uma pergunta
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                Ex.: "Quais são as tabelas e volumes?" ou "Mostre as principais correlações"
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[90%] rounded-lg p-3 ${
                  message.role === "user"
                    ? "bg-chat-user text-primary-foreground"
                    : "bg-chat-system text-foreground"
                }`}
              >
                <p className="text-sm">{message.content}</p>

                {/* Structure Data */}
                {message.dataType === "structure" && message.data && (
                  <div className="mt-3 overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-border">
                          <th className="text-left py-1 px-2">Tabela</th>
                          <th className="text-left py-1 px-2">Registros</th>
                          <th className="text-left py-1 px-2">Índices</th>
                          <th className="text-left py-1 px-2">Tipo</th>
                        </tr>
                      </thead>
                      <tbody>
                        {message.data.tables.map((table: any, idx: number) => (
                          <tr key={idx} className="border-b border-border/50">
                            <td className="py-1 px-2 font-mono">{table.name}</td>
                            <td className="py-1 px-2">{table.records.toLocaleString('pt-BR')}</td>
                            <td className="py-1 px-2">{table.indexes}</td>
                            <td className="py-1 px-2">
                              <Badge variant="outline" className="text-xs">texto</Badge>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {/* Statistics Data */}
                {message.dataType === "stats" && message.data && (
                  <div className="mt-3 space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      {message.data.metrics.map((metric: any, idx: number) => (
                        <div key={idx} className="p-2 bg-background/20 rounded">
                          <p className="text-xs text-muted-foreground">{metric.label}</p>
                          <p className="text-sm font-semibold">{metric.value}</p>
                        </div>
                      ))}
                    </div>
                    
                    <div>
                      <p className="text-xs font-semibold mb-2 flex items-center gap-1">
                        <BarChart3 className="h-3 w-3" />
                        Correlações:
                      </p>
                      <div className="space-y-1">
                        {message.data.correlations.map((corr: any, idx: number) => (
                          <div key={idx} className="flex items-center justify-between text-xs p-1.5 bg-background/20 rounded">
                            <span>{corr.vars}</span>
                            <Badge variant={corr.strength === "Forte" ? "default" : "secondary"} className="text-xs">
                              {corr.strength} ({corr.value})
                            </Badge>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                {/* Model Data */}
                {message.dataType === "model" && message.data && (
                  <div className="mt-3 space-y-3">
                    <div className="p-3 bg-background/20 rounded">
                      <p className="text-xs text-muted-foreground mb-1">Modelo sugerido:</p>
                      <p className="text-sm font-bold">{message.data.model}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      {message.data.metrics.map((metric: any, idx: number) => (
                        <div key={idx} className="p-2 bg-background/20 rounded text-center">
                          <p className="text-xs text-muted-foreground">{metric.name}</p>
                          <p className="text-lg font-bold text-success">{metric.value}</p>
                        </div>
                      ))}
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs font-semibold">💡 Insights:</p>
                      {message.data.insights.map((insight: string, idx: number) => (
                        <div key={idx} className="flex items-start gap-2 p-2 bg-warning/10 rounded">
                          <Badge className="text-xs bg-warning text-warning-foreground">!</Badge>
                          <span className="text-xs">{insight}</span>
                        </div>
                      ))}
                    </div>

                    <div className="space-y-1">
                      <p className="text-xs font-semibold">Próximos passos:</p>
                      <ul className="text-xs space-y-1">
                        {message.data.nextSteps.map((step: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2">
                            <span className="text-primary">→</span>
                            <span>{step}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
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
          <div className="flex justify-start">
            <div className="bg-chat-system text-foreground rounded-lg p-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-info rounded-full animate-pulse" />
                  <div className="w-2 h-2 bg-info rounded-full animate-pulse delay-75" />
                  <div className="w-2 h-2 bg-info rounded-full animate-pulse delay-150" />
                </div>
                <span className="text-sm text-muted-foreground">Executando análise...</span>
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
            id="data-input"
            placeholder="Ex.: 'Quais são as tabelas e volumes?'"
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

export default DataChat;
