import { useState, useRef, useEffect } from "react";
import { Send, Copy, FolderOpen, FileCode, Plus, X, Upload, TestTube, Play, Workflow, ChevronDown } from "lucide-react";
import { Elemento10DeleteButton } from "@/components/ui/Elemento10DeleteButton";
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
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import FileTree, { type FileNode } from "./FileTree";
import { LoaderEstudandoArquivos, LoaderEscrevendoCodigo } from "@/components/loaders";
import { exportReport } from "@/lib/exportReport";
import { DownloadReportButton } from "@/components/ui/DownloadReportButton";
import { ChatSidebar } from "./ChatSidebar";
import { PromptSearchInput } from "@/components/ui/PromptSearchInput";
import { ProjectStructureDropdown } from "./ProjectStructureDropdown";
import { getPulsoCsaSessions, setPulsoCsaSessions, type ChatSession } from "@/lib/connectionStorage";

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

export interface ComprehensionResult {
  curl_commands?: string[];
  preview_frontend_url?: string | null;
}

/** Parseia cURL e executa via fetch (GET e POST com JSON) */
async function executeCurl(curlStr: string): Promise<{ ok: boolean; status: number; body: string }> {
  const urlMatch = curlStr.match(/https?:\/\/[^\s'"]+/);
  const url = urlMatch?.[0];
  if (!url) throw new Error("URL não encontrada no cURL");

  const methodMatch = curlStr.match(/-X\s+(GET|POST|PUT|DELETE|PATCH)/i);
  const method = (methodMatch?.[1]?.toUpperCase() ?? "GET") as RequestInit["method"];

  let body: string | undefined;
  const dMatch = curlStr.match(/-d\s+'([^']*(?:\\'[^']*)*)'/);
  if (dMatch) {
    body = dMatch[1].replace(/\\'/g, "'");
  } else {
    const dMatch2 = curlStr.match(/-d\s+"([^"]*(?:\\"[^"]*)*)"/);
    if (dMatch2) body = dMatch2[1].replace(/\\"/g, '"');
  }

  const headers: Record<string, string> = {};
  const hMatches = curlStr.matchAll(/-H\s+["']([^:]+):\s*([^"']+)["']/g);
  for (const m of hMatches) {
    headers[m[1].trim()] = m[2].trim();
  }
  if (!headers["Content-Type"] && body) headers["Content-Type"] = "application/json";

  const res = await fetch(url, { method, headers, body });
  const text = await res.text();
  return { ok: res.ok, status: res.status, body: text };
}

interface ChatMessage {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: Date;
}

/** Serializa mensagem para persistência */
function msgToStorage(m: ChatMessage) {
  return { ...m, timestamp: m.timestamp.toISOString() };
}

/** Restaura mensagem do storage */
function msgFromStorage(m: { id: string; role: "user" | "system"; content: string; timestamp: string }): ChatMessage {
  return { ...m, timestamp: new Date(m.timestamp) };
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

interface PromptPanelProps {
  onComprehensionResult?: (result: ComprehensionResult) => void;
  onClear?: () => void;
}

type PulsoCsaSession = ChatSession<{ id: string; role: string; content: string; timestamp: string }>;

const PromptPanel = ({ onComprehensionResult, onClear }: PromptPanelProps) => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<PulsoCsaSession[]>(() => getPulsoCsaSessions());
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [envVars, setEnvVars] = useState<EnvVariable[]>([]);
  const [newVarName, setNewVarName] = useState("");
  const [newVarValue, setNewVarValue] = useState("");
  const [folderPath, setFolderPath] = useState("");
  const [requestId, setRequestId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPhase, setLoadingPhase] = useState<"analisando" | "escrevendo">("analisando");
  const [history, setHistory] = useState<PromptHistory[]>([]);
  const [fileStructure, setFileStructure] = useState<FileNode[] | null>(null);
  const [showTestDialog, setShowTestDialog] = useState(false);
  const [curlCommands, setCurlCommands] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem("pulso_curl_commands");
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });
  const [showRenameDialog, setShowRenameDialog] = useState(false);
  const [renameSessionId, setRenameSessionId] = useState<string | null>(null);
  const [renameValue, setRenameValue] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();

  // Alternar loading entre "analisando seu projeto" (04) e "escrevendo seu código" (05)
  useEffect(() => {
    if (!loading) return;
    const t = setInterval(() => {
      setLoadingPhase((p) => (p === "analisando" ? "escrevendo" : "analisando"));
    }, 2500);
    return () => clearInterval(t);
  }, [loading]);

  // Carregar sessão ao selecionar
  useEffect(() => {
    if (!currentSessionId) {
      setMessages([]);
      setFileStructure(null);
      setFolderPath("");
      setEnvVars([]);
      return;
    }
    const s = sessions.find((x) => x.id === currentSessionId);
    if (!s) return;
    const rawMsgs = s.messages as { id?: string; role?: string; content?: string; timestamp?: string }[] | undefined;
    const msgs = Array.isArray(rawMsgs)
      ? rawMsgs
          .filter((m) => m && typeof m.timestamp === "string")
          .map((m) => msgFromStorage(m as { id: string; role: "user" | "system"; content: string; timestamp: string }))
      : [];
    setMessages(msgs);
    const ctx = s.context as { folderPath?: string; envVars?: EnvVariable[]; fileStructure?: FileNode[] } | undefined;
    setFolderPath(ctx?.folderPath ?? "");
    setEnvVars(ctx?.envVars ?? []);
    setFileStructure(ctx?.fileStructure ?? null);
  }, [currentSessionId, sessions]);

  // Persistir sessões
  useEffect(() => {
    setPulsoCsaSessions(sessions);
  }, [sessions]);

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

  const syncToSession = (msgs: ChatMessage[], fStruct: FileNode[] | null) => {
    if (!currentSessionId) return;
    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSessionId
          ? {
              ...s,
              messages: msgs.map(msgToStorage),
              context: { folderPath, envVars, fileStructure: fStruct },
              updatedAt: new Date().toISOString(),
              title: s.title || msgs.find((m) => m.role === "user")?.content?.slice(0, 50) || "Novo chat",
            }
          : s
      )
    );
  };

  const handleNewChat = () => {
    if (messages.length > 0 && !currentSessionId) {
      const id = `csa-${Date.now()}`;
      const title = messages[0]?.content?.slice(0, 50) || "Novo chat";
      setSessions((prev) => [
        ...prev,
        {
          id,
          title,
          messages: messages.map(msgToStorage),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          context: { folderPath, envVars, fileStructure },
        },
      ]);
      setCurrentSessionId(id);
    }
    setCurrentSessionId(null);
    setMessages([]);
    setInput("");
    setFileStructure(null);
    setFolderPath("");
    setEnvVars([]);
    setHistory([]);
    onClear?.();
  };

  const handleSelectSession = (session: { id: string }) => {
    setCurrentSessionId(session.id);
  };

  const handleDeleteSession = (id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (currentSessionId === id) {
      setCurrentSessionId(null);
      setMessages([]);
      setFileStructure(null);
      setFolderPath("");
      setEnvVars([]);
    }
  };

  const handleRenameSession = (session: { id: string; title?: string }) => {
    setRenameSessionId(session.id);
    setRenameValue(session.title || "");
    setShowRenameDialog(true);
  };

  const confirmRename = () => {
    if (renameSessionId && renameValue.trim()) {
      setSessions((prev) =>
        prev.map((s) => (s.id === renameSessionId ? { ...s, title: renameValue.trim(), updatedAt: new Date().toISOString() } : s))
      );
      setShowRenameDialog(false);
      setRenameSessionId(null);
      setRenameValue("");
    }
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

    if (!currentSessionId) {
      const id = `csa-${Date.now()}`;
      setCurrentSessionId(id);
      setSessions((prev) => [
        ...prev,
        {
          id,
          title: promptText.slice(0, 50),
          messages: [],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          context: { folderPath, envVars, fileStructure },
        },
      ]);
    }

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      role: "user",
      content: promptText,
      timestamp: new Date(),
    };
    const nextMessages = [...messages, userMsg];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setLoadingPhase("analisando");

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
      const allMessages = [...nextMessages, systemMsg];
      setMessages(allMessages);

      const fStruct = res.file_tree?.trim() ? parseFileTreeString(res.file_tree) : null;
      setFileStructure(fStruct);
      setRequestId(null);

      syncToSession(allMessages, fStruct);

      if (res.curl_commands?.length) {
        setCurlCommands(res.curl_commands);
        localStorage.setItem("pulso_curl_commands", JSON.stringify(res.curl_commands));
        setShowTestDialog(true);
      } else {
        setCurlCommands([]);
        localStorage.removeItem("pulso_curl_commands");
        setShowTestDialog(false);
      }
      onComprehensionResult?.({
        curl_commands: res.curl_commands ?? [],
        preview_frontend_url: res.preview_frontend_url ?? null,
      });

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
      const allMessages = [...nextMessages, errMsg];
      setMessages(allMessages);
      syncToSession(allMessages, fileStructure);
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
    handleNewChat();
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
    document.getElementById('prompt-input')?.focus();
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

  const handleCopyCurl = (curl: string) => {
    navigator.clipboard.writeText(curl);
    toast({
      title: "cURL copiado",
      description: "Comando copiado para a área de transferência",
    });
  };

  const [executingCurl, setExecutingCurl] = useState<number | null>(null);
  const handleExecuteCurl = async (curl: string, index: number) => {
    setExecutingCurl(index);
    try {
      const result = await executeCurl(curl);
      if (result.ok) {
        toast({
          title: "cURL executado",
          description: `Status ${result.status}. Resposta: ${result.body.slice(0, 100)}${result.body.length > 100 ? "..." : ""}`,
        });
      } else {
        toast({
          title: "cURL retornou erro",
          description: `Status ${result.status}: ${result.body.slice(0, 150)}`,
          variant: "destructive",
        });
      }
    } catch (err) {
      toast({
        title: "Erro ao executar cURL",
        description: err instanceof Error ? err.message : "Falha na execução",
        variant: "destructive",
      });
    } finally {
      setExecutingCurl(null);
    }
  };

  const apiBase = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000").toString().trim();
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

  const fallbackCurls = [
    ...(comprehensionCurl
      ? [{ name: "Comprehension Run (atual)", curl: comprehensionCurl }]
      : []),
    { name: "Health Check", curl: `curl -X GET ${apiBase}/health` },
    { name: "API Status", curl: `curl -X GET ${apiBase}/api/status` },
    { name: "List Users", curl: `curl -X GET ${apiBase}/api/users` },
    { name: "Create User", curl: `curl -X POST ${apiBase}/api/users -H "Content-Type: application/json" -d '{"name": "John Doe", "email": "john@example.com"}'` },
    { name: "Upload File", curl: `curl -X POST ${apiBase}/api/upload -F "file=@/path/to/file.pdf"` },
  ];

  const displayCurls = curlCommands.length > 0
    ? curlCommands.map((curl, i) => ({ name: `Comando ${i + 1}`, curl }))
    : fallbackCurls;

  const sessionItems = sessions.map((s) => ({
    id: s.id,
    title: s.title,
    updatedAt: s.updatedAt,
  }));

  return (
    <div className="pulso-chat-layout h-full min-h-0">
      {/* Sidebar - Histórico de conversas (elementos 08 Save, 10 Delete) */}
      <div className="pulso-chat-sidebar glass-strong">
        <ChatSidebar
          sessions={sessionItems}
          currentSessionId={currentSessionId}
          onSelect={handleSelectSession}
          onDelete={handleDeleteSession}
          onNewChat={handleNewChat}
          onRename={handleRenameSession}
          emptyMessage="Nenhum chat ainda"
        />
      </div>

      {/* Área principal — formato de chat (igual CloudChat, DataChat, FinOpsChat) */}
      <div className="pulso-chat-main flex flex-col min-h-0 rounded-xl border border-primary/20 glass-strong overflow-hidden">
        <div className="p-5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 shrink-0">
          <div className="flex items-center gap-4 min-w-0">
            <div>
              <h2 className="text-xl font-semibold flex items-center gap-2.5 text-primary">
                <Workflow className="h-6 w-6 text-primary" />
                Pulso CSA
              </h2>
              <p className="text-base text-muted-foreground mt-1.5">
                Blueprint e estrutura de projetos · Atalho: Alt+P
              </p>
            </div>
            {fileStructure && fileStructure.length > 0 && (
              <div className="shrink-0">
                <ProjectStructureDropdown structure={fileStructure} />
              </div>
            )}
          </div>
          <div className="flex gap-3 flex-wrap shrink-0 items-center">
            <DownloadReportButton
              onClick={async () => {
                if (messages.length === 0) return;
                const msgs = messages.map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp }));
                const result = await exportReport({ serviceId: "pulso-csa", messages: msgs, format: "md" });
                toast({ title: result === "saved" ? "Relatório salvo" : "Relatório baixado", description: result === "saved" ? "Salvo em C:\\Users\\pytho\\Desktop\\Study\\docs" : "Download iniciado" });
              }}
              disabled={messages.length === 0}
              className="text-base min-h-[42px]"
            />
            <Button variant="ghost" size="default" onClick={() => setShowTestDialog(true)} disabled={curlCommands.length === 0} title={curlCommands.length === 0 ? "Aguarde a resposta do backend" : "Testar aplicação"} className="min-h-[42px] px-4 gap-2">
              <TestTube className="h-5 w-5" />
              Testar
            </Button>
            <Elemento10DeleteButton onClick={handleClear} disabled={messages.length === 0 && !requestId} compact />
          </div>
        </div>

        {/* Config — colapsável */}
        <Collapsible defaultOpen={false}>
          <CollapsibleTrigger className="w-full p-3 flex items-center justify-between shrink-0 hover:bg-primary/5 transition-colors">
            <span className="text-sm font-medium text-muted-foreground flex items-center gap-2">
              <FolderOpen className="h-4 w-4" />
              Configuração (pasta, .env)
            </span>
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="p-4 space-y-4 border-t border-primary/10">
              <div className="space-y-2">
                <Label htmlFor="folder-path" className="text-sm font-medium">Caminho da pasta raiz</Label>
                <Input
                  id="folder-path"
                  placeholder="Ex.: C:\Users\pytho\Desktop\Study\Github Repos\PulsoAPI"
                  value={folderPath}
                  onChange={(e) => setFolderPath(e.target.value)}
                  className="border-primary/30 bg-background/50 focus-visible:ring-primary"
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">Variáveis de Ambiente</Label>
                  <input ref={fileInputRef} type="file" accept=".env,text/plain" onChange={handleEnvFileUpload} className="hidden" />
                  <Button variant="pulso" size="sm" onClick={() => fileInputRef.current?.click()} className="h-8 text-xs">
                    <Upload className="h-3 w-3 mr-1" />
                    Carregar .env
                  </Button>
                </div>
                <div onDragOver={handleDragOver} onDrop={handleDrop} className="border-2 border-dashed border-primary/30 rounded-lg p-3 text-center bg-background/30 hover:border-primary/50 transition-colors">
                  <p className="text-xs text-muted-foreground">Arraste um .env aqui ou use o botão acima</p>
                </div>
                {envVars.length > 0 && (
                  <div className="border border-primary/30 rounded-lg overflow-hidden bg-background/50">
                    <div className="max-h-[160px] overflow-y-auto">
                      <table className="w-full">
                        <thead className="bg-primary/10 sticky top-0">
                          <tr>
                            <th className="text-left text-xs font-semibold px-3 py-2 border-b border-primary/20">Nome</th>
                            <th className="text-left text-xs font-semibold px-3 py-2 border-b border-primary/20">Valor</th>
                            <th className="w-12 border-b border-primary/20"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {envVars.map((envVar, index) => (
                            <tr key={index} className="border-b border-primary/10 hover:bg-primary/5">
                              <td className="px-3 py-2 text-sm font-mono truncate max-w-[120px]">{envVar.name}</td>
                              <td className="px-3 py-2 text-sm font-mono text-muted-foreground truncate max-w-[140px]">{envVar.value}</td>
                              <td className="px-3 py-2">
                                <Button variant="ghost" size="icon" onClick={() => removeEnvVariable(index)} className="h-7 w-7 text-destructive hover:bg-destructive/10">
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
                <div className="grid grid-cols-[1fr,1fr,auto] gap-2">
                  <Input placeholder="Nome (ex: API_KEY)" value={newVarName} onChange={(e) => setNewVarName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addEnvVariable()} className="border-primary/30 bg-background/50" />
                  <Input placeholder="Valor" value={newVarValue} onChange={(e) => setNewVarValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addEnvVariable()} className="border-primary/30 bg-background/50" />
                  <Button onClick={addEnvVariable} size="icon" className="h-10 w-10" variant="pulso">
                    <Plus className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Chat area */}
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
          <div className="flex-1 min-h-0 overflow-y-auto p-5 space-y-5">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <Workflow className="h-12 w-12 text-primary/50" />
                <div>
                  <p className="text-sm text-foreground font-medium">Descreva o projeto que deseja gerar</p>
                  <p className="text-xs text-muted-foreground mt-1">Ex.: Gerar blueprint de pastas e endpoints para um sistema de gestão de pedidos</p>
                </div>
                <div className="pt-4 w-full max-w-md space-y-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">Sugestões:</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {["Gerar blueprint de pastas e endpoints", "Criar estrutura de API REST", "Sistema de gestão de pedidos"].map((s, i) => (
                        <Button key={i} variant="pulso" size="sm" onClick={() => setInput(s)} className="text-xs">
                          {s}
                        </Button>
                      ))}
                    </div>
                  </div>
                  {history.length > 0 && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">Conversas recentes:</p>
                      <div className="flex flex-wrap gap-2 justify-center">
                        {history.slice(0, 3).map((item) => (
                          <Button key={item.id} variant="outline" size="sm" onClick={() => handleReusePrompt(item.text)} className="text-xs max-w-[200px] truncate">
                            {item.text.slice(0, 40)}{item.text.length > 40 ? "…" : ""}
                          </Button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <>
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex items-end gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
                    {msg.role === "system" && (
                      <div className="shrink-0 w-9 h-9 rounded-full overflow-hidden ring-2 ring-primary/40 ring-offset-2 ring-offset-background/80 flex items-center justify-center">
                        <img src={import.meta.env.BASE_URL + "App.png"} alt="Pulso CSA" className="w-7 h-7 object-contain" />
                      </div>
                    )}
                    <div className={`max-w-[85%] rounded-lg p-3 text-sm ${msg.role === "user" ? "bg-chat-user pulso-chat-user-bubble text-chat-user-foreground border" : "bg-chat-system text-chat-system-foreground border border-border/50"}`}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      <p className="text-xs opacity-70 mt-1">{msg.timestamp.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</p>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="flex items-end gap-2 justify-start animate-slide-up">
                    <div className="shrink-0 w-9 h-9 rounded-full overflow-hidden ring-2 ring-primary/40 ring-offset-2 ring-offset-background/80 flex items-center justify-center">
                      <img src={import.meta.env.BASE_URL + "App.png"} alt="Pulso CSA" className="w-7 h-7 object-contain" />
                    </div>
                    <div className="bg-muted/50 text-foreground rounded-lg p-4">
                      {loadingPhase === "analisando" ? <LoaderEstudandoArquivos message="Analisando seu projeto..." /> : <LoaderEscrevendoCodigo message="Escrevendo seu código..." />}
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input bar — igual aos outros chats */}
          <div className="p-4 shrink-0">
            <form
              onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
              className="flex gap-2 items-end"
            >
              <div className="flex-1 min-w-0">
                <PromptSearchInput
                  id="prompt-input"
                  placeholder="Ex.: Gerar blueprint de pastas e endpoints para um sistema de gestão de pedidos..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onSend={handleSubmit}
                  variant="prompt"
                />
              </div>
            </form>
          </div>
        </div>

        {requestId && (
          <div className="flex items-center gap-2 p-4 glass border-t border-primary/20 shrink-0">
            <span className="text-sm font-mono text-primary flex-1">ID: {requestId}</span>
            <Button variant="ghost" size="icon" onClick={handleCopyId} className="h-8 w-8">
              <Copy className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Dialog Renomear chat */}
      <Dialog open={showRenameDialog} onOpenChange={(open) => !open && (setShowRenameDialog(false), setRenameSessionId(null), setRenameValue(""))}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Renomear chat</DialogTitle>
            <DialogDescription>Digite o novo nome para esta conversa.</DialogDescription>
          </DialogHeader>
          <div className="flex gap-2 py-4">
            <Input
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              placeholder="Nome do chat"
              onKeyDown={(e) => e.key === "Enter" && confirmRename()}
            />
            <Button variant="pulso" onClick={confirmRename}>Salvar</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog de Testes com cURL */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="w-[min(90vw,920px)] max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-foreground flex items-center gap-2">
              <TestTube className="h-5 w-5 text-primary" />
              Exemplos de Testes cURL
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Comandos de teste para seu backend
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 mt-2 overflow-y-auto flex-1 min-h-0 pr-1">
            {displayCurls.map((test, index) => (
              <div
                key={index}
                className="rounded-xl border border-border bg-muted/30 p-4 transition-colors hover:bg-muted/50"
              >
                <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
                  <h4 className="font-medium text-foreground text-sm">{test.name}</h4>
                  <div className="flex gap-2">
                    <Button
                      variant="pulso"
                      size="sm"
                      onClick={() => handleExecuteCurl(test.curl, index)}
                      disabled={executingCurl !== null}
                      className="h-8 text-xs"
                    >
                      {executingCurl === index ? (
                        <span className="animate-pulse">Executando...</span>
                      ) : (
                        <>
                          <Play className="h-3.5 w-3.5 mr-1.5" />
                          Executar
                        </>
                      )}
                    </Button>
                    <Button
                      variant="pulso"
                      size="sm"
                      onClick={() => handleCopyCurl(test.curl)}
                      className="h-8 text-xs"
                    >
                      <Copy className="h-3.5 w-3.5 mr-1.5" />
                      Copiar
                    </Button>
                  </div>
                </div>
                <div className="overflow-x-auto rounded-lg bg-background/80 border border-border/60 p-3">
                  <pre className="text-xs font-mono text-foreground whitespace-pre min-w-max">
                    <code>{test.curl}</code>
                  </pre>
                </div>
              </div>
            ))}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PromptPanel;
