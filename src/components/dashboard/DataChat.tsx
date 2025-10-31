import { useState } from "react";
import { Send, Database, ChevronDown, ChevronUp, BarChart3, Brain } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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
  data?: any;
}

const DataChat = () => {
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

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
    };

    setMessages([...messages, userMessage]);
    setInput("");
    setLoading(true);

    // Simular resposta baseada no input
    setTimeout(() => {
      let systemMessage: Message;

      if (input.toLowerCase().includes("estrutura")) {
        systemMessage = {
          id: (Date.now() + 1).toString(),
          role: "system",
          content: "Explorando estrutura da base de dados...",
          timestamp: new Date(),
          dataType: "structure",
          data: {
            tables: [
              { name: "usuarios", records: 15420, indexes: 3, columns: ["id", "nome", "email", "created_at"] },
              { name: "transacoes", records: 89234, indexes: 5, columns: ["id", "user_id", "valor", "data", "status"] },
              { name: "produtos", records: 2341, indexes: 2, columns: ["id", "nome", "preco", "categoria"] },
            ]
          }
        };
      } else if (input.toLowerCase().includes("correlação") || input.toLowerCase().includes("estatística")) {
        systemMessage = {
          id: (Date.now() + 1).toString(),
          role: "system",
          content: "Calculando estatísticas e correlações...",
          timestamp: new Date(),
          dataType: "stats",
          data: {
            metrics: [
              { label: "Valor médio", value: "R$ 245,80" },
              { label: "Desvio padrão", value: "R$ 127,50" },
              { label: "Total transações", value: "89.234" },
              { label: "Taxa aprovação", value: "94,2%" },
            ],
            correlations: [
              { vars: "valor × horário", strength: "Forte", value: 0.87 },
              { vars: "categoria × região", strength: "Moderada", value: 0.62 },
              { vars: "idade × ticket_médio", strength: "Fraca", value: 0.31 },
            ]
          }
        };
      } else if (input.toLowerCase().includes("modelo") || input.toLowerCase().includes("ml") || input.toLowerCase().includes("fraude")) {
        systemMessage = {
          id: (Date.now() + 1).toString(),
          role: "system",
          content: "Analisando dados e sugerindo modelo de Machine Learning...",
          timestamp: new Date(),
          dataType: "model",
          data: {
            model: "Random Forest Classifier",
            metrics: [
              { name: "AUC", value: "0.94" },
              { name: "Precisão", value: "91%" },
              { name: "Recall", value: "88%" },
              { name: "F1-Score", value: "0.89" },
            ],
            insights: [
              "90% das fraudes ocorrem à noite (22h-4h)",
              "Transações acima de R$ 500 têm 3x mais risco",
              "Região Sul apresenta 45% menos fraudes",
            ],
            nextSteps: [
              "Aplicar feature engineering em horários",
              "Balancear classes (fraude vs normal)",
              "Testar ensemble com XGBoost",
            ]
          }
        };
      } else {
        systemMessage = {
          id: (Date.now() + 1).toString(),
          role: "system",
          content: "Compreendi sua pergunta. Com base nos dados disponíveis, posso ajudar com análises de estrutura, estatísticas ou sugestões de modelos. Pode me fazer uma pergunta mais específica?",
          timestamp: new Date(),
        };
      }

      setMessages((prev) => [...prev, systemMessage]);
      setLoading(false);
    }, 1500);
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    setTimeout(() => handleSend(), 100);
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

          <Button size="sm" className="w-full">
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
