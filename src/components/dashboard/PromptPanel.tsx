import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Copy, Clock, FolderOpen, FileCode, Plus, X, Upload, TestTube } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { comprehensionApi } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import FileTree, { type FileNode } from "./FileTree";

interface EnvVariable {
  name: string;
  value: string;
}

/** Converte a string file_tree da API (com * nos itens novos) em árvore para o FileTree. */
function parseFileTreeString(fileTree: string): FileNode[] {
  const lines = fileTree.trim().split("\n").filter(Boolean);
  if (lines.length === 0) return [];

  const items: { level: number; name: string; type: "file" | "folder"; isNew: boolean }[] = [];
  for (const line of lines) {
    const indent = line.match(/^\s*/)?.[0].length ?? 0;
    const level = Math.floor(indent / 2);
    let rest = line.trim();
    const isNew = rest.endsWith("*");
    if (isNew) rest = rest.slice(0, -1).trim();
    const isFolder = rest.endsWith("/");
    const name = isFolder ? rest.slice(0, -1) : rest;
    if (!name) continue;
    items.push({
      level,
      name,
      type: isFolder ? "folder" : "file",
      isNew,
    });
  }

  const stack: { node: FileNode; level: number }[] = [];
  const root: FileNode[] = [];

  for (const item of items) {
    const node: FileNode = {
      name: item.name,
      type: item.type,
      isNew: item.isNew,
      ...(item.type === "folder" ? { children: [] } : {}),
    };
    while (stack.length > 0 && stack[stack.length - 1].level >= item.level) stack.pop();
    if (stack.length === 0) {
      root.push(node);
    } else {
      const parent = stack[stack.length - 1].node;
      if (parent.children) parent.children.push(node);
    }
    if (item.type === "folder") stack.push({ node, level: item.level });
  }

  return root;
}

interface PromptHistory {
  id: string;
  text: string;
  timestamp: Date;
}

interface ChatMessage {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: Date;
}

/** Monta o conteúdo .env a partir das variáveis (arquivo carregado ou pares nome-valor) */
function buildEnvContent(envVars: EnvVariable[]): string {
  return envVars
    .map(({ name, value }) => {
      const needsQuotes = /[\s#"']/.test(value);
      return `${name}=${needsQuotes ? `"${value.replace(/"/g, '\\"')}"` : value}`;
    })
    .join("\n");
}

const PromptPanel = () => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [envVars, setEnvVars] = useState<EnvVariable[]>([]);
  const [newVarName, setNewVarName] = useState("");
  const [newVarValue, setNewVarValue] = useState("");
  const [folderPath, setFolderPath] = useState("");
  const [requestId, setRequestId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<PromptHistory[]>([]);
  const [fileStructure, setFileStructure] = useState<FileNode[] | null>(null);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  const addEnvVariable = () => {
    if (!newVarName.trim() || !newVarValue.trim()) {
      toast({
        title: "Campos vazios",
        description: "Preencha o nome e o valor da variável",
        variant: "destructive",
      });
      return;
    }

    if (envVars.some(v => v.name === newVarName)) {
      toast({
        title: "Variável duplicada",
        description: "Uma variável com este nome já existe",
        variant: "destructive",
      });
      return;
    }

    setEnvVars([...envVars, { name: newVarName, value: newVarValue }]);
    setNewVarName("");
    setNewVarValue("");
  };

  const removeEnvVariable = (index: number) => {
    setEnvVars(envVars.filter((_, i) => i !== index));
  };

  const handleSubmit = async () => {
    const promptText = input.trim();
    if (!promptText) return;
    if (!user?.id) {
      toast({
        title: "Usuário não autenticado",
        description: "Faça login para enviar o prompt",
        variant: "destructive",
      });
      return;
    }

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: promptText,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const payload = {
        usuario: user.id,
        prompt: promptText,
        root_path: folderPath.trim() || null,
      };

      const res = await comprehensionApi.run(payload);

      const systemMsg: ChatMessage = {
        id: `s-${Date.now()}`,
        role: "system",
        content: res.message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, systemMsg]);

      if (res.file_tree?.trim()) {
        setFileStructure(parseFileTreeString(res.file_tree));
      } else {
        setFileStructure(null);
      }
      setRequestId(null);

      const newEntry: PromptHistory = {
        id: `req-${Date.now()}`,
        text: promptText,
        timestamp: new Date(),
      };
      setHistory((prev) => [newEntry, ...prev.slice(0, 4)]);

      toast({
        title: res.intent === "EXECUTAR" && res.should_execute ? "Executado" : "Resposta recebida",
        description: res.next_action || undefined,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Tente novamente";
      const is400 = msg.includes("400") || msg.toLowerCase().includes("vazio") || msg.toLowerCase().includes("obrigatório");
      const errMsg: ChatMessage = {
        id: `s-${Date.now()}`,
        role: "system",
        content: is400 ? `Validação: ${msg}` : `Erro: ${msg}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errMsg]);
      toast({
        title: is400 ? "Dados inválidos" : "Erro ao enviar prompt",
        description: msg,
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
    setInput("");
    setEnvVars([]);
    setNewVarName("");
    setNewVarValue("");
    setFolderPath("");
    setRequestId(null);
    setFileStructure(null);
  };

  const handleCopyId = () => {
    if (requestId) {
      navigator.clipboard.writeText(requestId);
      toast({
        title: "ID copiado",
        description: "ID da requisição copiado para a área de transferência",
      });
    }
  };

  const handleReusePrompt = (text: string) => {
    setInput(text);
    document.getElementById('chat-input')?.focus();
  };

  const handleEnvFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      const lines = content.split('\n');
      const newVars: EnvVariable[] = [];

      lines.forEach((line) => {
        const trimmed = line.trim();
        if (trimmed && !trimmed.startsWith('#')) {
          const [name, ...valueParts] = trimmed.split('=');
          if (name && valueParts.length > 0) {
            const value = valueParts.join('=').replace(/^["']|["']$/g, '');
            newVars.push({ name: name.trim(), value: value.trim() });
          }
        }
      });

      if (newVars.length > 0) {
        setEnvVars((prev) => {
          const existing = new Map(prev.map(v => [v.name, v]));
          newVars.forEach(v => existing.set(v.name, v));
          return Array.from(existing.values());
        });
        toast({
          title: "Arquivo carregado",
          description: `${newVars.length} variável(eis) importada(s)`,
        });
      }
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    const file = e.dataTransfer.files?.[0];
    if (file && (file.name.endsWith('.env') || file.type === 'text/plain')) {
      const fakeEvent = {
        target: { files: [file] }
      } as any;
      handleEnvFileUpload(fakeEvent);
    } else {
      toast({
        title: "Arquivo inválido",
        description: "Por favor, envie um arquivo .env",
        variant: "destructive",
      });
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleCopyCurl = (curl: string) => {
    navigator.clipboard.writeText(curl);
    toast({
      title: "cURL copiado",
      description: "Comando copiado para a área de transferência",
    });
  };

  const apiBase = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const comprehensionPayload = input.trim()
    ? JSON.stringify({
        usuario: user?.id ?? "USER_ID",
        prompt: input.trim(),
        root_path: folderPath.trim() || null,
      })
    : null;
  const comprehensionCurl = comprehensionPayload
    ? `curl -X POST "${apiBase}/comprehension/run" -H "Content-Type: application/json" -d '${comprehensionPayload.replace(/'/g, "'\\''")}'`
    : null;

  const testCurls = [
    ...(comprehensionCurl
      ? [
          {
            name: "Comprehension Run (atual)",
            curl: comprehensionCurl,
          },
        ]
      : []),
    {
      name: "Health Check",
      curl: `curl -X GET ${apiBase}/health`,
    },
    {
      name: "API Status",
      curl: `curl -X GET ${apiBase}/api/status`,
    },
    {
      name: "List Users",
      curl: `curl -X GET ${apiBase}/api/users`,
    },
    {
      name: "Create User",
      curl: `curl -X POST ${apiBase}/api/users -H "Content-Type: application/json" -d '{"name": "John Doe", "email": "john@example.com"}'`,
    },
    {
      name: "Upload File",
      curl: `curl -X POST ${apiBase}/api/upload -F "file=@/path/to/file.pdf"`,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Área de input */}
      <div className="glass-strong neon-glow rounded-2xl p-6 space-y-4">
        {/* Caminho da Pasta */}
        <div className="space-y-2">
          <Label htmlFor="folder-path" className="text-sm font-medium text-foreground flex items-center gap-2">
            <FolderOpen className="h-4 w-4 text-primary" />
            Caminho da Pasta Raiz do Projeto
          </Label>
          <Input
            id="folder-path"
            placeholder="Ex.: C:\Users\pytho\Desktop\Study\Github Repos\PulsoAPI"
            value={folderPath}
            onChange={(e) => setFolderPath(e.target.value)}
            className="border-primary/30 bg-background/50 focus-visible:ring-primary"
          />
          <p className="text-xs text-muted-foreground">
            Informe o caminho completo da pasta raiz do seu projeto
          </p>
        </div>

        {/* Variáveis de Ambiente */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label className="text-sm font-medium text-foreground flex items-center gap-2">
              <FileCode className="h-4 w-4 text-primary" />
              Variáveis de Ambiente
            </Label>
            <div className="flex gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".env,text/plain"
                onChange={handleEnvFileUpload}
                className="hidden"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="h-8 text-xs"
              >
                <Upload className="h-3 w-3 mr-1" />
                Carregar .env
              </Button>
            </div>
          </div>
          
          <div
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="border-2 border-dashed border-primary/30 rounded-lg p-3 text-center bg-background/30 hover:border-primary/50 transition-colors"
          >
            <p className="text-xs text-muted-foreground">
              Arraste um arquivo .env aqui ou use o botão acima
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              O .env será criado na pasta raiz do projeto ao enviar o prompt
            </p>
          </div>
          
          {/* Tabela de variáveis */}
          {envVars.length > 0 && (
            <div className="border border-primary/30 rounded-lg overflow-hidden bg-background/50">
              <div className="max-h-[200px] overflow-y-auto">
                <table className="w-full">
                  <thead className="bg-primary/10 sticky top-0">
                    <tr>
                      <th className="text-left text-xs font-semibold text-foreground px-3 py-2 border-b border-primary/20">
                        Nome da Variável
                      </th>
                      <th className="text-left text-xs font-semibold text-foreground px-3 py-2 border-b border-primary/20">
                        Valor
                      </th>
                      <th className="w-12 border-b border-primary/20"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {envVars.map((envVar, index) => (
                      <tr key={index} className="border-b border-primary/10 hover:bg-primary/5 transition-colors">
                        <td className="px-3 py-2 text-sm font-mono text-foreground">
                          {envVar.name}
                        </td>
                        <td className="px-3 py-2 text-sm font-mono text-muted-foreground truncate max-w-[200px]">
                          {envVar.value}
                        </td>
                        <td className="px-3 py-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => removeEnvVariable(index)}
                            className="h-7 w-7 text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Formulário para adicionar nova variável */}
          <div className="grid grid-cols-[1fr,1fr,auto] gap-2">
            <Input
              placeholder="Nome (ex: API_KEY)"
              value={newVarName}
              onChange={(e) => setNewVarName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addEnvVariable()}
              className="border-primary/30 bg-background/50 focus-visible:ring-primary"
            />
            <Input
              placeholder="Valor"
              value={newVarValue}
              onChange={(e) => setNewVarValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && addEnvVariable()}
              className="border-primary/30 bg-background/50 focus-visible:ring-primary"
            />
            <Button
              onClick={addEnvVariable}
              size="icon"
              className="h-10 w-10"
              variant="outline"
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Chat - Descrição do Projeto */}
        <div className="space-y-2">
          <Label htmlFor="chat-input" className="text-sm font-medium text-foreground flex items-center gap-2">
            <Send className="h-4 w-4 text-primary" />
            Descrição do Projeto
          </Label>
          <div className="min-h-[200px] max-h-[320px] overflow-y-auto rounded-lg border border-primary/30 bg-background/30 p-3 space-y-3">
            {messages.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Ex.: &quot;Gerar blueprint de pastas e endpoints para um sistema de gestão de pedidos...&quot;
              </p>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[90%] rounded-lg p-3 text-sm ${
                      msg.role === "user"
                        ? "bg-primary/20 text-foreground"
                        : "bg-muted/50 text-foreground"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    <p className="text-xs opacity-70 mt-1">
                      {msg.timestamp.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="flex gap-2">
            <Input
              id="chat-input"
              placeholder="Ex.: 'Gerar blueprint de pastas e endpoints para um sistema de gestão de pedidos...'"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSubmit(); } }}
              className="border-primary/30 bg-background/50 focus-visible:ring-primary"
            />
            <Button
              onClick={handleSubmit}
              disabled={!input.trim() || loading}
              className="shrink-0 h-10"
            >
              {loading ? "..." : <Send className="h-4 w-4" />}
            </Button>
          </div>
        </div>

        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => setShowTestDialog(true)}
            className="h-12 px-6 border-finops/40 hover:border-finops hover:bg-finops/10 text-finops"
            title="Testar aplicação"
          >
            <TestTube className="h-5 w-5 mr-2" />
            Testar
          </Button>
          <Button 
            variant="outline" 
            onClick={handleClear}
            disabled={messages.length === 0 && !requestId}
            className="h-12 px-6"
          >
            <Trash2 className="h-5 w-5" />
          </Button>
        </div>

        {requestId && (
          <div className="flex items-center gap-2 p-4 glass border border-primary/30 rounded-xl neon-glow">
            <span className="text-sm font-mono text-primary flex-1">
              ID: {requestId}
            </span>
            <Button variant="ghost" size="icon" onClick={handleCopyId} className="h-8 w-8">
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Estrutura de arquivos */}
      {fileStructure && (
        <div className="glass-strong neon-glow rounded-2xl p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-semibold text-primary neon-glow">
              Árvore do projeto
            </h3>
            <span className="text-xs text-muted-foreground font-mono">
              {requestId}
            </span>
          </div>
          <p className="text-xs text-muted-foreground mb-2">
            <span className="text-emerald-600 dark:text-emerald-400 font-medium">*</span> = criado neste run
          </p>
          <div className="bg-background/30 rounded-xl p-4 max-h-96 overflow-y-auto border border-primary/20">
            <FileTree structure={fileStructure} />
          </div>
        </div>
      )}

      {/* Histórico */}
      {history.length > 0 && (
        <div className="glass-strong neon-glow rounded-2xl p-6">
          <h3 className="text-base font-semibold text-primary neon-glow mb-4">
            Histórico recente
          </h3>
          <div className="space-y-3">
            {history.map((item) => (
              <button
                key={item.id}
                onClick={() => handleReusePrompt(item.text)}
                className="w-full text-left p-4 rounded-xl bg-primary/5 hover:bg-primary/10 border border-primary/20 hover:border-primary/30 transition-all duration-200 hover:shadow-md group"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm text-foreground line-clamp-2 flex-1">
                    {item.text}
                  </p>
                  <Clock className="h-4 w-4 text-muted-foreground flex-shrink-0 mt-0.5" />
                </div>
                <div className="flex items-center justify-between mt-3">
                  <span className="text-xs text-muted-foreground">
                    {item.timestamp.toLocaleString('pt-BR', {
                      day: '2-digit',
                      month: '2-digit',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                  <span className="text-xs text-primary opacity-0 group-hover:opacity-100 transition-opacity">
                    Reusar
                  </span>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {messages.length === 0 && !requestId && history.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            Descreva sua solicitação para começarmos
          </p>
        </div>
      )}

      {/* Dialog de Testes com cURL */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle className="text-2xl font-bold text-primary flex items-center gap-2">
              <TestTube className="h-6 w-6" />
              Exemplos de Testes cURL
            </DialogTitle>
            <DialogDescription>
              Comandos de teste para seu backend
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            {testCurls.map((test, index) => (
              <div key={index} className="glass p-4 rounded-lg border border-primary/20">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-foreground">{test.name}</h4>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleCopyCurl(test.curl)}
                    className="h-7 border-primary/40 hover:border-primary hover:bg-primary/10"
                  >
                    <Copy className="h-3 w-3 mr-1" />
                    Copiar
                  </Button>
                </div>
                <pre className="text-xs bg-background/50 p-3 rounded border border-primary/10 overflow-x-auto">
                  <code className="text-muted-foreground font-mono">{test.curl}</code>
                </pre>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PromptPanel;
