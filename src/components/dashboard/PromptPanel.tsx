import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { useTranslation } from "react-i18next";
import { Send, Copy, FolderOpen, FileCode, Plus, X, Upload, TestTube, Play, Workflow, ChevronDown, Loader2 } from "lucide-react";
import { Elemento10DeleteButton } from "@/components/ui/Elemento10DeleteButton";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import {
  comprehensionApi,
  getLocalApiConfig,
  getLocalEngineDiagnostics,
  type LocalEngineDiagnostics,
} from "@/lib/api";
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
import { LoaderGenerating } from "@/components/loaders";
import { exportReport } from "@/lib/exportReport";
import { DownloadReportButton } from "@/components/ui/DownloadReportButton";
import { FolderFileUpload } from "@/components/ui/FolderFileUpload";
import { ChatSidebar } from "./ChatSidebar";
import { PromptSearchTextarea } from "@/components/ui/PromptSearchTextarea";
import { ProjectStructureDropdown } from "./ProjectStructureDropdown";
import { getPulsoCsaSessions, setPulsoCsaSessions, type ChatSession } from "@/lib/connectionStorage";
import { isElectronClient } from "@/lib/electronClient";

interface EnvVariable {
  name: string;
  value: string;
}

/** Converte a string file_tree da API (com * nos itens novos) em árvore para o FileTree. */
/** Suporta: (1) formato de árvore (├──, │, └──) e (2) indentação por espaços (backend Python). */
function parseFileTreeString(fileTree: string): FileNode[] {
  const lines = fileTree.trim().split("\n").filter(Boolean);
  if (lines.length === 0) return [];

  const hasTreeChars = lines.some((l) => /[├└│]/.test(l));
  const items: { level: number; name: string; type: "file" | "folder"; isNew: boolean }[] = [];

  for (const line of lines) {
    let level: number;
    let rawName: string;

    if (hasTreeChars) {
      // Formato de árvore: "├── nome *" ou "│   ├── nome" ou "projeto/"
      const treeMatch = line.match(/^((?:[\s│]*)(?:├|└)\s*──\s*)?(.+)$/);
      if (treeMatch) {
        const prefix = treeMatch[1] ?? "";
        rawName = (treeMatch[2] ?? "").trim();
        const pipeCount = (prefix.match(/│/g) || []).length;
        level = prefix.includes("├") || prefix.includes("└") ? pipeCount + 1 : 0;
      } else {
        rawName = line.trim();
        level = 0;
      }
      if (items.length === 0 && !/[├└]/.test(line)) {
        level = 0;
        rawName = line.trim();
      }
    } else {
      // Formato indentação (backend Python): "  pasta/" ou "    arquivo *"
      const indent = line.match(/^\s*/)?.[0].length ?? 0;
      level = Math.floor(indent / 2);
      rawName = line.trim();
    }

    const isNew = rawName.endsWith("*");
    if (isNew) rawName = rawName.slice(0, -1).trim();
    const isFolder = rawName.endsWith("/");
    const name = isFolder ? rawName.slice(0, -1).trim() : rawName.trim();
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
  /** Caminho da pasta do projeto (para botão "Testar Preview") */
  root_path?: string | null;
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
  /** Árvore de arquivos (API comprehension) — exibir em bloco colapsável */
  file_tree?: string | null;
  /** URL do preview — exibir como link clicável (nunca abrir automaticamente) */
  preview_frontend_url?: string | null;
  /** Sugestão de layout para a área do chat */
  frontend_suggestion?: string | null;
}

/** Serializa mensagem para persistência */
function msgToStorage(m: ChatMessage) {
  return {
    ...m,
    timestamp: m.timestamp.toISOString(),
    file_tree: m.file_tree ?? undefined,
    preview_frontend_url: m.preview_frontend_url ?? undefined,
    frontend_suggestion: m.frontend_suggestion ?? undefined,
  };
}

/** Restaura mensagem do storage */
function msgFromStorage(m: {
  id: string;
  role: "user" | "system";
  content: string;
  timestamp: string;
  file_tree?: string | null;
  preview_frontend_url?: string | null;
  frontend_suggestion?: string | null;
}): ChatMessage {
  return {
    ...m,
    timestamp: new Date(m.timestamp),
    file_tree: m.file_tree ?? undefined,
    preview_frontend_url: m.preview_frontend_url ?? undefined,
    frontend_suggestion: m.frontend_suggestion ?? undefined,
  };
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
  /** Conteúdo extra na toolbar (ex.: botões Logs e Preview) à esquerda de Baixar Relatório */
  toolbarExtra?: React.ReactNode;
}

type PulsoCsaSession = ChatSession<{ id: string; role: string; content: string; timestamp: string }>;

const PromptPanel = ({ onComprehensionResult, onClear, toolbarExtra }: PromptPanelProps) => {
  const { user } = useAuth();
  const [sessions, setSessions] = useState<PulsoCsaSession[]>(() => getPulsoCsaSessions());
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [envVars, setEnvVars] = useState<EnvVariable[]>([]);
  const [newVarName, setNewVarName] = useState("");
  const [newVarValue, setNewVarValue] = useState("");
  const [folderPath, setFolderPath] = useState("");
  const [usePython, setUsePython] = useState(false);
  const [useJavaScript, setUseJavaScript] = useState(false);
  const [useTypeScript, setUseTypeScript] = useState(false);
  const [useReact, setUseReact] = useState(false);
  const [useVue, setUseVue] = useState(false);
  const [useAngular, setUseAngular] = useState(false);
  const [requestId, setRequestId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<PromptHistory[]>([]);
  const [fileStructure, setFileStructure] = useState<FileNode[] | null>(null);
  const [rawFileTree, setRawFileTree] = useState<string | null>(null);
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
  const [localDiag, setLocalDiag] = useState<LocalEngineDiagnostics | null>(null);
  const [localDiagLoading, setLocalDiagLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const { toast } = useToast();
  const { t, i18n } = useTranslation();
  const timeLocale = i18n.language?.replace(/_/g, "-") || "pt-BR";

  const refreshLocalDiagnostics = useCallback(async () => {
    if (!isElectronClient()) {
      setLocalDiag(null);
      return;
    }
    setLocalDiagLoading(true);
    try {
      const d = await getLocalEngineDiagnostics(folderPath.trim());
      setLocalDiag(d ?? null);
    } finally {
      setLocalDiagLoading(false);
    }
  }, [folderPath]);

  useEffect(() => {
    void refreshLocalDiagnostics();
  }, [refreshLocalDiagnostics]);

  // Scroll apenas na lista de mensagens (sem afetar header/sidebar/layout)
  useEffect(() => {
    const el = messagesContainerRef.current;
    if (!el) return;
    el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  // Carregar sessão ao selecionar
  useEffect(() => {
    if (!currentSessionId) {
      setMessages([]);
    setFileStructure(null);
    setRawFileTree(null);
    setFolderPath("");
    setEnvVars([]);
    setUsePython(false);
    setUseJavaScript(false);
    setUseTypeScript(false);
    setUseReact(false);
    setUseVue(false);
    setUseAngular(false);
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
    const ctx = s.context as { 
      folderPath?: string; 
      envVars?: EnvVariable[]; 
      fileStructure?: FileNode[];
      rawFileTree?: string | null;
      usePython?: boolean;
      useJavaScript?: boolean;
      useTypeScript?: boolean;
      useReact?: boolean;
    } | undefined;
    setFolderPath(ctx?.folderPath ?? "");
    setEnvVars(ctx?.envVars ?? []);
    setFileStructure(ctx?.fileStructure ?? null);
    setRawFileTree(ctx?.rawFileTree ?? null);
    setUsePython(ctx?.usePython ?? false);
    setUseJavaScript(ctx?.useJavaScript ?? false);
    setUseTypeScript(ctx?.useTypeScript ?? false);
    setUseReact(ctx?.useReact ?? false);
    setUseVue(ctx?.useVue ?? false);
    setUseAngular(ctx?.useAngular ?? false);
  }, [currentSessionId, sessions]);

  // Persistir sessões
  useEffect(() => {
    setPulsoCsaSessions(sessions);
  }, [sessions]);

  const addEnvVariable = () => {
    if (!newVarName.trim() || !newVarValue.trim()) {
      toast({
        title: t("pulsoCsa.emptyEnvTitle"),
        description: t("pulsoCsa.emptyEnvDesc"),
        variant: "destructive",
      });
      return;
    }

    if (envVars.some(v => v.name === newVarName)) {
      toast({
        title: t("pulsoCsa.dupEnvTitle"),
        description: t("pulsoCsa.dupEnvDesc"),
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

  const syncToSession = (msgs: ChatMessage[], fStruct: FileNode[] | null, rawTree: string | null = null) => {
    if (!currentSessionId) return;
    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSessionId
          ? {
              ...s,
              messages: msgs.map(msgToStorage),
              context: { 
                folderPath, 
                envVars, 
                fileStructure: fStruct,
                rawFileTree: rawTree ?? rawFileTree,
                usePython,
                useJavaScript,
                useTypeScript,
                useReact,
                useVue,
                useAngular,
              },
              updatedAt: new Date().toISOString(),
              title: s.title || msgs.find((m) => m.role === "user")?.content?.slice(0, 50) || t("pulsoCsa.newChat"),
            }
          : s
      )
    );
  };

  const handleNewChat = () => {
    if (messages.length > 0 && !currentSessionId) {
      const id = `csa-${Date.now()}`;
      const title = messages[0]?.content?.slice(0, 50) || t("pulsoCsa.newChat");
      setSessions((prev) => [
        ...prev,
        {
          id,
          title,
          messages: messages.map(msgToStorage),
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          context: { folderPath, envVars, fileStructure, rawFileTree },
        },
      ]);
      setCurrentSessionId(id);
    }
    setCurrentSessionId(null);
      setMessages([]);
      setInput("");
    setFileStructure(null);
    setRawFileTree(null);
    setFolderPath("");
      setEnvVars([]);
      setUsePython(false);
      setUseJavaScript(false);
      setUseTypeScript(false);
      setUseReact(false);
      setUseVue(false);
      setUseAngular(false);
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
    setRawFileTree(null);
    setFolderPath("");
      setEnvVars([]);
      setUsePython(false);
      setUseJavaScript(false);
      setUseTypeScript(false);
      setUseReact(false);
      setUseVue(false);
      setUseAngular(false);
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
        title: t("pulsoCsa.notAuthTitle"),
        description: t("pulsoCsa.notAuthDesc"),
        variant: "destructive",
      });
      return;
    }

    if (folderPath.trim()) {
      const localCfg = await getLocalApiConfig();
      if (!localCfg) {
        toast({
          title: t("pulsoCsa.noLocalEngineTitle"),
          description: t("pulsoCsa.noLocalEngineDesc"),
          variant: "destructive",
        });
        return;
      }
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

    if (!currentSessionId) {
      const id = `csa-${Date.now()}`;
      setCurrentSessionId(id);
      setSessions((prev) => [
        ...prev,
        {
          id,
          title: promptText.slice(0, 50),
          messages: [msgToStorage(userMsg)],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
          context: { 
            folderPath, 
            envVars, 
            fileStructure,
            usePython,
            useJavaScript,
            useTypeScript,
            useReact,
          },
        },
      ]);
    }

    try {
      // Determina qual endpoint usar baseado nas seleções de linguagem
      const useJS = useJavaScript;
      const usePy = usePython;
      
      // Se JavaScript está selecionado, usa o endpoint JavaScript
      const endpoint = useJS ? 'comprehension-js' : 'comprehension';
      
      const payload = {
        usuario: user.id,
        prompt: promptText,
        root_path: folderPath.trim() || null,
        ...(useJS ? {
          use_python: usePy,
          use_javascript: useJS,
          use_typescript: useTypeScript,
          use_react: useReact,
          use_vue: useVue,
          use_angular: useAngular,
        } : {}),
      };

      const res = await comprehensionApi.run(payload, endpoint);

      const systemMsg: ChatMessage = {
        id: `s-${Date.now()}`,
        role: "system",
        content: res.message,
        timestamp: new Date(),
        file_tree: res.file_tree ?? null,
        preview_frontend_url: res.preview_frontend_url ?? null,
        frontend_suggestion: res.frontend_suggestion ?? null,
      };
      const allMessages = [...nextMessages, systemMsg];
      setMessages(allMessages);

      const rawTree = res.file_tree?.trim() ?? null;
      setRawFileTree(rawTree);
      const fStruct = rawTree ? parseFileTreeString(res.file_tree!) : null;
      setFileStructure(fStruct);
      setRequestId(null);

      syncToSession(allMessages, fStruct, rawTree);

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
        root_path: folderPath.trim() || null,
      });

      const newEntry: PromptHistory = {
        id: `req-${Date.now()}`,
        text: promptText,
        timestamp: new Date(),
      };
      setHistory((prev) => [newEntry, ...prev.slice(0, 4)]);

      toast({
        title: res.intent === "EXECUTAR" && res.should_execute ? t("pulsoCsa.executedTitle") : t("pulsoCsa.responseReceivedTitle"),
        description: res.next_action || undefined,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : t("pulsoCsa.tryAgain");
      const is400 =
        msg.includes("400") ||
        msg.toLowerCase().includes("vazio") ||
        msg.toLowerCase().includes("obrigatório") ||
        msg.toLowerCase().includes("required");
      const errMsg: ChatMessage = {
        id: `s-${Date.now()}`,
        role: "system",
        content: is400 ? `${t("pulsoCsa.validationPrefix")} ${msg}` : `${t("pulsoCsa.errorPrefix")} ${msg}`,
        timestamp: new Date(),
      };
      const allMessages = [...nextMessages, errMsg];
      setMessages(allMessages);
      syncToSession(allMessages, fileStructure, rawFileTree);
      toast({
        title: is400 ? t("pulsoCsa.invalidDataTitle") : t("pulsoCsa.sendErrorTitle"),
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
        title: t("pulsoCsa.idCopiedTitle"),
        description: t("pulsoCsa.idCopiedDesc"),
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
          title: t("pulsoCsa.envLoadedTitle"),
          description: t("pulsoCsa.envLoadedDesc", { count: newVars.length }),
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
        title: t("pulsoCsa.badFileTitle"),
        description: t("pulsoCsa.badFileDesc"),
        variant: "destructive",
      });
    }
  };

  const handleCopyCurl = (curl: string) => {
    navigator.clipboard.writeText(curl);
    toast({
      title: t("pulsoCsa.curlCopiedTitle"),
      description: t("pulsoCsa.curlCopiedDesc"),
    });
  };

  const [executingCurl, setExecutingCurl] = useState<number | null>(null);
  const handleExecuteCurl = async (curl: string, index: number) => {
    setExecutingCurl(index);
    try {
      const result = await executeCurl(curl);
      if (result.ok) {
        const snippet = `${result.body.slice(0, 100)}${result.body.length > 100 ? "..." : ""}`;
        toast({
          title: t("pulsoCsa.curlOkTitle"),
          description: t("pulsoCsa.curlOkDesc", { status: result.status, snippet }),
        });
      } else {
        const snippet = result.body.slice(0, 150);
        toast({
          title: t("pulsoCsa.curlErrTitle"),
          description: t("pulsoCsa.curlErrDesc", { status: result.status, snippet }),
          variant: "destructive",
        });
      }
    } catch (err) {
      toast({
        title: t("pulsoCsa.curlExecFailTitle"),
        description: err instanceof Error ? err.message : t("pulsoCsa.curlExecFailDesc"),
        variant: "destructive",
      });
    } finally {
      setExecutingCurl(null);
    }
  };

  const apiBase = (import.meta.env.VITE_API_URL || "https://pulsoapi-production-f227.up.railway.app").toString().trim();
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

  const fallbackCurls = useMemo(
    () => [
      ...(comprehensionCurl ? [{ name: t("pulsoCsa.curlComprehensionCurrent"), curl: comprehensionCurl }] : []),
      { name: t("pulsoCsa.curlHealth"), curl: `curl -X GET ${apiBase}/health` },
      { name: t("pulsoCsa.curlApiStatus"), curl: `curl -X GET ${apiBase}/api/status` },
      { name: t("pulsoCsa.curlListUsers"), curl: `curl -X GET ${apiBase}/api/users` },
      {
        name: t("pulsoCsa.curlCreateUser"),
        curl: `curl -X POST ${apiBase}/api/users -H "Content-Type: application/json" -d '{"name": "John Doe", "email": "john@example.com"}'`,
      },
      { name: t("pulsoCsa.curlUploadFile"), curl: `curl -X POST ${apiBase}/api/upload -F "file=@/path/to/file.pdf"` },
    ],
    [apiBase, comprehensionCurl, t]
  );

  const displayCurls =
    curlCommands.length > 0
      ? curlCommands.map((curl, i) => ({ name: t("pulsoCsa.commandN", { n: i + 1 }), curl }))
      : fallbackCurls;

  const sessionItems = sessions.map((s) => ({
    id: s.id,
    title: s.title,
    updatedAt: s.updatedAt,
  }));

  return (
    <div className="pulso-chat-layout flex-1 h-full min-h-0 overflow-hidden">
      {/* Sidebar - Histórico de conversas (elementos 08 Save, 10 Delete) */}
      <div className="pulso-chat-sidebar glass-strong">
        <ChatSidebar
          serviceId="pulso-csa"
          sessions={sessionItems}
          currentSessionId={currentSessionId}
          onSelect={handleSelectSession}
          onDelete={handleDeleteSession}
          onNewChat={handleNewChat}
          onRename={handleRenameSession}
          emptyMessage={t("pulsoCsa.emptyChats")}
        />
      </div>

      {/* Área principal — formato de chat (igual CloudChat, DataChat, FinOpsChat) */}
      <div className="pulso-chat-main pulso-chat-main-shell flex flex-col min-h-0 rounded-xl border border-primary/20 glass-strong overflow-hidden">
        <div className="pulso-chat-main-header p-3 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-3 shrink-0 border-b border-primary/10">
          <div className="flex items-center gap-2 min-w-0 flex-1 overflow-hidden">
            <div className="min-w-0 flex-1">
              <h2 className="text-base font-semibold flex items-center gap-1.5 text-primary truncate">
                <Workflow className="h-4 w-4 shrink-0 text-primary" />
                {t("dashboard.services.pulso")}
              </h2>
              <p className="text-xs text-foreground/70 mt-0.5 truncate">
                {t("pulsoCsa.subtitle")}
              </p>
            </div>
            {(fileStructure?.length || rawFileTree?.trim()) ? (
              <div className="shrink-0 min-w-0">
                <ProjectStructureDropdown structure={fileStructure} rawFileTree={rawFileTree} />
              </div>
            ) : null}
          </div>
          <div className="flex gap-1.5 flex-wrap items-center justify-end shrink-0 min-w-0">
            {toolbarExtra}
            <DownloadReportButton
              onClick={async () => {
                if (messages.length === 0) return;
                const msgs = messages.map((m) => ({ role: m.role, content: m.content, timestamp: m.timestamp }));
                const result = await exportReport({ serviceId: "pulso-csa", messages: msgs, format: "md" });
                toast({
                  title: result === "saved" ? t("pulsoCsa.reportSaved") : t("pulsoCsa.reportDownloaded"),
                  description: result === "saved" ? t("pulsoCsa.reportSavedDesc") : t("pulsoCsa.reportDownloadStarted"),
                });
              }}
              disabled={messages.length === 0}
              className="showcase-download-report-btn--compact"
              aria-label={t("dashboard.exportReportAria")}
              title={t("dashboard.exportReportTitle")}
            >
              {t("dashboard.exportReportTitle")}
            </DownloadReportButton>
            <Elemento10DeleteButton
              onClick={handleClear}
              disabled={messages.length === 0 && !requestId}
              compact
              aria-label={t("pulsoCsa.clearChatAria")}
            />
          </div>
        </div>

        {/* Config — colapsável */}
        <Collapsible
          defaultOpen={false}
          onOpenChange={(open) => {
            if (open) void refreshLocalDiagnostics();
          }}
        >
          <CollapsibleTrigger className="pulso-chat-main-fixed-section w-full p-3 flex items-center justify-between shrink-0 hover:bg-primary/5 transition-colors">
            <span className="text-sm font-medium text-foreground/85 flex items-center gap-2">
              <FolderOpen className="h-4 w-4 text-primary" />
              {t("pulsoCsa.configCollapsible")}
            </span>
            <ChevronDown className="h-4 w-4 text-foreground/65" />
          </CollapsibleTrigger>
          <CollapsibleContent>
            <div className="pulso-csa-config-scroll shrink-0 border-t border-primary/10">
            <div className="p-4 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="folder-path" className="text-sm font-medium">{t("pulsoCsa.rootFolderLabel")}</Label>
                <div className="relative w-full overflow-visible showcase-search-poda--prompt showcase-search-poda--toolbar">
                  <div className="showcase-search-poda w-full">
                    <div className="showcase-search-glow" aria-hidden />
                    <div className="showcase-search-darkBorderBg" aria-hidden />
                    <div className="showcase-search-darkBorderBg" aria-hidden />
                    <div className="showcase-search-darkBorderBg" aria-hidden />
                    <div className="showcase-search-white" aria-hidden />
                    <div className="showcase-search-border" aria-hidden />
                    <div className="showcase-search-main flex-1 min-w-0 flex items-center relative">
                      <input
                        id="folder-path"
                        type="text"
                        placeholder={t("pulsoCsa.rootFolderPlaceholder")}
                        value={folderPath}
                        onChange={(e) => setFolderPath(e.target.value)}
                        onBlur={() => {
                          if (!isElectronClient() || !folderPath.trim()) return;
                          const api = (
                            window as unknown as {
                              electronAPI?: { registerAllowedRoot?: (p: string) => Promise<unknown> };
                            }
                          ).electronAPI;
                          void (async () => {
                            await api?.registerAllowedRoot?.(folderPath.trim());
                            void refreshLocalDiagnostics();
                          })();
                        }}
                        className="showcase-search-input showcase-search-input--prompt showcase-search-input--no-lupa w-full min-w-0 flex-1 !pl-3 !pr-12 border-0 focus:outline-none focus:ring-0"
                        aria-label={t("pulsoCsa.rootFolderAria")}
                      />
                      <FolderFileUpload
                        compact
                        className="pulso-folder-file-upload--inline-path"
                        useElectronDirectoryPicker={isElectronClient()}
                        onElectronDirectoryPicked={(p) => setFolderPath(p)}
                        onFileChange={(files) => {
                          const f = files?.item(0);
                          if (f) setFolderPath((f as File & { path?: string }).path ?? f.name ?? "");
                        }}
                      >
                        {""}
                      </FolderFileUpload>
                    </div>
                  </div>
                </div>
              </div>

              <div className="rounded-lg border border-primary/20 bg-background/40 p-3 space-y-2">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-xs font-semibold text-foreground/90">{t("pulsoCsa.diagnosticsTitle")}</span>
                  {isElectronClient() ? (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs gap-1.5"
                      disabled={localDiagLoading}
                      onClick={() => void refreshLocalDiagnostics()}
                    >
                      {localDiagLoading ? <Loader2 className="h-3 w-3 animate-spin shrink-0" aria-hidden /> : null}
                      {t("pulsoCsa.diagnosticsRefresh")}
                    </Button>
                  ) : null}
                </div>
                {!isElectronClient() ? (
                  <p className="text-xs text-foreground/75 leading-relaxed">{t("pulsoCsa.diagnosticsOnlyElectron")}</p>
                ) : localDiagLoading && !localDiag ? (
                  <div className="flex items-center gap-2 text-xs text-foreground/65">
                    <Loader2 className="h-3.5 w-3.5 animate-spin shrink-0" />
                    {t("pulsoCsa.diagnosticsLoading")}
                  </div>
                ) : !localDiag ? (
                  <p className="text-xs text-foreground/70">{t("pulsoCsa.diagnosticsUnavailable")}</p>
                ) : (
                  <ul className="text-xs text-foreground/80 space-y-1.5 list-none pl-0">
                    <li className="flex items-start gap-2">
                      <span className="text-foreground/55 shrink-0">{t("pulsoCsa.diagnosticsEngine")}</span>
                      <span className={localDiag.engineRunning ? "text-emerald-600 dark:text-emerald-400" : "text-amber-700 dark:text-amber-300"}>
                        {localDiag.engineRunning ? t("pulsoCsa.diagnosticsEngineOn") : t("pulsoCsa.diagnosticsEngineOff")}
                      </span>
                    </li>
                    {localDiag.config?.baseUrl ? (
                      <li>
                        <span className="text-foreground/55">{t("pulsoCsa.diagnosticsLocalUrl")} </span>
                        <code className="text-[11px] break-all">{localDiag.config.baseUrl}</code>
                      </li>
                    ) : null}
                    {localDiag.lastStartError ? (
                      <li className="text-amber-800 dark:text-amber-200/90">
                        <span className="font-medium">{t("pulsoCsa.diagnosticsLastError")}: </span>
                        {t(`pulsoCsa.diagnosticsError.${localDiag.lastStartError}`, {
                          defaultValue: localDiag.lastStartError,
                        })}
                      </li>
                    ) : null}
                    {localDiag.apiRoot ? (
                      <li>
                        <span className="text-foreground/55">{t("pulsoCsa.diagnosticsApiRoot")} </span>
                        <code className="text-[11px] break-all">{localDiag.apiRoot}</code>
                      </li>
                    ) : null}
                    {!localDiag.apiRoot &&
                    localDiag.pulsoApiCandidates &&
                    localDiag.pulsoApiCandidates.length > 0 ? (
                      <li className="space-y-1">
                        <span className="text-foreground/55">{t("pulsoCsa.diagnosticsCandidatesTitle")}</span>
                        <ul className="pl-2 mt-1 space-y-1 border-l border-primary/20 list-none">
                          {localDiag.pulsoApiCandidates.map((c) => (
                            <li key={c.path} className="text-[11px]">
                              <code className="break-all opacity-90">{c.path}</code>{" "}
                              <span className={c.exists ? "text-emerald-600 dark:text-emerald-400" : "text-foreground/50"}>
                                {c.exists ? t("pulsoCsa.diagnosticsPathExists") : t("pulsoCsa.diagnosticsPathMissing")}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </li>
                    ) : null}
                    {localDiag.frontendRoot ? (
                      <li>
                        <span className="text-foreground/55">{t("pulsoCsa.diagnosticsFrontendRoot")} </span>
                        <code className="text-[10px] break-all opacity-80">{localDiag.frontendRoot}</code>
                      </li>
                    ) : null}
                    {!localDiag.apiRoot && localDiag.manualPulsoapiFile ? (
                      <li className="text-[11px] text-foreground/75 leading-snug">
                        {t("pulsoCsa.diagnosticsManualFileHint", { path: localDiag.manualPulsoapiFile })}
                      </li>
                    ) : null}
                    {!localDiag.apiRoot && !localDiag.envPulsoApiRoot ? (
                      <li className="text-[11px] text-foreground/60">{t("pulsoCsa.diagnosticsEnvUnset")}</li>
                    ) : null}
                    {!localDiag.apiRoot && localDiag.envPulsoApiRoot ? (
                      <li className="text-[11px] text-foreground/60">
                        {t("pulsoCsa.diagnosticsEnvSet", { path: localDiag.envPulsoApiRoot })}
                      </li>
                    ) : null}
                    <li>
                      <span className="text-foreground/55">{t("pulsoCsa.diagnosticsAllowlist")} </span>
                      {t("pulsoCsa.diagnosticsRootsCount", { count: localDiag.allowedRootCount })}
                      {localDiag.allowRootsPath ? (
                        <>
                          {" "}
                          <code className="text-[10px] break-all opacity-80">({localDiag.allowRootsPath})</code>
                        </>
                      ) : null}
                    </li>
                    {localDiag.allowedRootsPreview.length > 0 ? (
                      <li className="pl-2 border-l border-primary/15 text-[11px] text-foreground/65 max-h-20 overflow-y-auto space-y-0.5">
                        {localDiag.allowedRootsPreview.map((r) => (
                          <div key={r} className="truncate" title={r}>
                            {r}
                          </div>
                        ))}
                      </li>
                    ) : null}
                    <li>
                      {localDiag.folderInAllowlist === null ? (
                        <span className="text-foreground/65">{t("pulsoCsa.diagnosticsFolderUnset")}</span>
                      ) : localDiag.folderInAllowlist ? (
                        <span className="text-emerald-700 dark:text-emerald-400/90">{t("pulsoCsa.diagnosticsFolderOk")}</span>
                      ) : (
                        <span className="text-amber-800 dark:text-amber-200/90">{t("pulsoCsa.diagnosticsFolderBad")}</span>
                      )}
                    </li>
                    {localDiag.relaxAllowlistInDev ? (
                      <li className="text-foreground/60">{t("pulsoCsa.diagnosticsDevRelax")}</li>
                    ) : null}
                    {localDiag.logFilePath ? (
                      <li>
                        <span className="text-foreground/55">{t("pulsoCsa.diagnosticsLogFile")} </span>
                        <code className="text-[10px] break-all opacity-80">{localDiag.logFilePath}</code>
                      </li>
                    ) : null}
                  </ul>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium">{t("pulsoCsa.envVarsLabel")}</Label>
                  <input ref={fileInputRef} type="file" accept=".env,text/plain" onChange={handleEnvFileUpload} className="hidden" />
                  <Button variant="pulso" size="sm" onClick={() => fileInputRef.current?.click()} className="h-8 text-xs">
                    <Upload className="h-3 w-3 mr-1" />
                    {t("pulsoCsa.loadEnv")}
                  </Button>
                </div>
                <div onDragOver={handleDragOver} onDrop={handleDrop} className="border-2 border-dashed border-primary/30 rounded-lg p-3 text-center bg-background/30 hover:border-primary/50 transition-colors">
                  <p className="text-xs text-foreground/72">{t("pulsoCsa.dragEnvHint")}</p>
                </div>
                {envVars.length > 0 && (
                  <div className="border border-primary/30 rounded-lg overflow-hidden bg-background/50">
                    <div className="max-h-[160px] overflow-y-auto">
                      <table className="w-full">
                        <thead className="bg-primary/10 sticky top-0">
                          <tr>
                            <th className="text-left text-xs font-semibold px-3 py-2 border-b border-primary/20">{t("pulsoCsa.tableName")}</th>
                            <th className="text-left text-xs font-semibold px-3 py-2 border-b border-primary/20">{t("pulsoCsa.tableValue")}</th>
                            <th className="w-12 border-b border-primary/20"></th>
                          </tr>
                        </thead>
                        <tbody>
                          {envVars.map((envVar, index) => (
                            <tr key={index} className="border-b border-primary/10 hover:bg-primary/5">
                              <td className="px-3 py-2 text-sm font-mono truncate max-w-[120px]">{envVar.name}</td>
                              <td className="px-3 py-2 text-sm font-mono text-foreground/78 truncate max-w-[140px]">{envVar.value}</td>
                              <td className="px-3 py-2">
                                <Button variant="ghost" size="sm" onClick={() => removeEnvVariable(index)} className="h-7 gap-1 text-xs text-destructive hover:bg-destructive/10">
                                  <X className="h-4 w-4 shrink-0" />
                                  <span>{t("pulsoCsa.remove")}</span>
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
                  <Input placeholder={t("pulsoCsa.placeholderEnvName")} value={newVarName} onChange={(e) => setNewVarName(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addEnvVariable()} className="border-primary/30 bg-background/50 placeholder:text-foreground/55" />
                  <Input placeholder={t("pulsoCsa.placeholderValue")} value={newVarValue} onChange={(e) => setNewVarValue(e.target.value)} onKeyDown={(e) => e.key === "Enter" && addEnvVariable()} className="border-primary/30 bg-background/50 placeholder:text-foreground/55" />
                  <Button onClick={addEnvVariable} size="sm" className="h-10 gap-1.5 px-3" variant="pulso">
                    <Plus className="h-4 w-4 shrink-0" />
                    <span>{t("pulsoCsa.add")}</span>
                  </Button>
                </div>
              </div>
              
              {/* Seção de Linguagens */}
              <div className="space-y-3 pt-3 border-t border-primary/10">
                <div className="flex items-center justify-between">
                  <Label className="text-sm font-medium text-foreground">{t("pulsoCsa.languagesFrameworks")}</Label>
                  {(usePython || useJavaScript) && (
                    <span className="text-xs text-muted-foreground px-2 py-1 rounded-md bg-primary/10 border border-primary/20">
                      {usePython && useJavaScript ? t("pulsoCsa.stackPythonJs") : usePython ? "Python" : "JavaScript"}
                      {useJavaScript && (useTypeScript || useReact || useVue || useAngular) && (
                        <span className="ml-1">
                          ({[
                            useTypeScript && "TS",
                            useReact && "React",
                            useVue && "Vue",
                            useAngular && "Angular"
                          ].filter(Boolean).join(" + ") || ""})
                        </span>
                      )}
                    </span>
                  )}
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Python */}
                  <div className="flex items-center space-x-2 p-2 rounded-lg border border-primary/20 bg-background/30 hover:bg-primary/5 transition-colors">
                      <Checkbox
                        id="use-python"
                        checked={usePython}
                        onCheckedChange={(checked) => {
                          setUsePython(checked === true);
                          if (checked && useJavaScript) {
                            setUseJavaScript(false);
                            setUseTypeScript(false);
                            setUseReact(false);
                            setUseVue(false);
                            setUseAngular(false);
                          }
                        }}
                        className="border-primary/30 data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                      />
                    <Label
                      htmlFor="use-python"
                      className="text-sm font-medium cursor-pointer text-foreground flex-1"
                    >
                      Python
                    </Label>
                  </div>

                  {/* JavaScript */}
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2 p-2 rounded-lg border border-primary/20 bg-background/30 hover:bg-primary/5 transition-colors">
                      <Checkbox
                        id="use-javascript"
                        checked={useJavaScript}
                        onCheckedChange={(checked) => {
                          setUseJavaScript(checked === true);
                          if (checked && usePython) {
                            setUsePython(false);
                          }
                          if (!checked) {
                            setUseTypeScript(false);
                            setUseReact(false);
                            setUseVue(false);
                            setUseAngular(false);
                          }
                        }}
                        className="border-primary/30 data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                      />
                      <Label
                        htmlFor="use-javascript"
                        className="text-sm font-medium cursor-pointer text-foreground flex-1"
                      >
                        JavaScript
                      </Label>
                    </div>
                    
                    {/* Sub-opções de JavaScript */}
                    {useJavaScript && (
                      <div className="pl-4 space-y-2 border-l-2 border-primary/30 ml-2">
                        <div className="flex items-center space-x-2 p-1.5 rounded-md bg-background/20 hover:bg-primary/5 transition-colors">
                          <Checkbox
                            id="use-typescript"
                            checked={useTypeScript}
                            onCheckedChange={(checked) => setUseTypeScript(checked === true)}
                            className="border-primary/30 data-[state=checked]:bg-primary data-[state=checked]:border-primary h-3.5 w-3.5"
                          />
                          <Label
                            htmlFor="use-typescript"
                            className="text-xs font-normal cursor-pointer text-muted-foreground"
                          >
                            TypeScript
                          </Label>
                        </div>
                        <div className="flex items-center space-x-2 p-1.5 rounded-md bg-background/20 hover:bg-primary/5 transition-colors">
                          <Checkbox
                            id="use-react"
                            checked={useReact}
                            onCheckedChange={(checked) => {
                              setUseReact(checked === true);
                              if (checked) {
                                setUseVue(false);
                                setUseAngular(false);
                              }
                            }}
                            className="border-primary/30 data-[state=checked]:bg-primary data-[state=checked]:border-primary h-3.5 w-3.5"
                          />
                          <Label
                            htmlFor="use-react"
                            className="text-xs font-normal cursor-pointer text-muted-foreground"
                          >
                            React
                          </Label>
                        </div>
                        <div className="flex items-center space-x-2 p-1.5 rounded-md bg-background/20 hover:bg-primary/5 transition-colors">
                          <Checkbox
                            id="use-vue"
                            checked={useVue}
                            onCheckedChange={(checked) => {
                              setUseVue(checked === true);
                              if (checked) {
                                setUseReact(false);
                                setUseAngular(false);
                              }
                            }}
                            className="border-primary/30 data-[state=checked]:bg-primary data-[state=checked]:border-primary h-3.5 w-3.5"
                          />
                          <Label
                            htmlFor="use-vue"
                            className="text-xs font-normal cursor-pointer text-muted-foreground"
                          >
                            Vue.js
                          </Label>
                        </div>
                        <div className="flex items-center space-x-2 p-1.5 rounded-md bg-background/20 hover:bg-primary/5 transition-colors">
                          <Checkbox
                            id="use-angular"
                            checked={useAngular}
                            onCheckedChange={(checked) => {
                              setUseAngular(checked === true);
                              if (checked) {
                                setUseReact(false);
                                setUseVue(false);
                              }
                            }}
                            className="border-primary/30 data-[state=checked]:bg-primary data-[state=checked]:border-primary h-3.5 w-3.5"
                          />
                          <Label
                            htmlFor="use-angular"
                            className="text-xs font-normal cursor-pointer text-muted-foreground"
                          >
                            Angular
                          </Label>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
            </div>
          </CollapsibleContent>
        </Collapsible>

        {/* Chat area */}
        <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
          <div ref={messagesContainerRef} className="pulso-chat-scroll-area p-5 space-y-5">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <Workflow className="h-12 w-12 text-primary/50" />
                <div>
                  <p className="text-sm text-foreground font-medium">{t("pulsoCsa.emptyStateTitle")}</p>
                  <p className="text-xs text-muted-foreground mt-1">{t("pulsoCsa.emptyStateHint")}</p>
                </div>
                <div className="pt-4 w-full max-w-md space-y-4">
                  <div>
                    <p className="text-xs text-muted-foreground mb-2">{t("pulsoCsa.suggestions")}</p>
                    <div className="flex flex-wrap gap-2 justify-center">
                      {[t("pulsoCsa.suggestionBlueprint"), t("pulsoCsa.suggestionRest"), t("pulsoCsa.suggestionOrders")].map((s, i) => (
                        <Button key={i} variant="outline" size="sm" onClick={() => setInput(s)} className="text-xs pulso-suggestion-btn">
                          {s}
                        </Button>
                      ))}
                    </div>
                  </div>
                  {history.length > 0 && (
                    <div>
                      <p className="text-xs text-muted-foreground mb-2">{t("pulsoCsa.recentChats")}</p>
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
                        <img src={import.meta.env.BASE_URL + "App.png"} alt={t("pulsoCsa.assistantAlt")} className="w-7 h-7 object-contain" />
                      </div>
                    )}
                    <div className={`max-w-[85%] rounded-lg p-3 text-sm ${msg.role === "user" ? "bg-chat-user pulso-chat-user-bubble text-chat-user-foreground border" : "bg-chat-system text-chat-system-foreground border border-border/50"}`}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                      {msg.role === "system" && msg.preview_frontend_url?.trim() && (
                        <p className="mt-2 text-xs">
                          <a
                            href={msg.preview_frontend_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-primary underline font-medium hover:underline"
                          >
                            {t("pulsoCsa.previewLink", { url: msg.preview_frontend_url })}
                          </a>
                        </p>
                      )}
                      {msg.role === "system" && msg.frontend_suggestion?.trim() && (
                        <p className="mt-2 text-xs text-muted-foreground italic border-l-2 border-primary/30 pl-2">
                          {msg.frontend_suggestion}
                        </p>
                      )}
                      <span className="pulso-chat-msg-timestamp mt-1">{msg.timestamp.toLocaleTimeString(timeLocale, { hour: "2-digit", minute: "2-digit" })}</span>
                    </div>
                  </div>
                ))}
                {loading && <LoaderGenerating className="mb-4" />}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input bar — igual aos outros chats */}
          <div className="pulso-chat-main-footer">
            <form
              onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}
              className="flex gap-2 items-end"
            >
              <div className="flex-1 min-w-0">
                <PromptSearchTextarea
                  id="prompt-input"
                  placeholder={loading ? t("pulsoCsa.placeholderWaiting") : t("pulsoCsa.placeholderPrompt")}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onSend={handleSubmit}
                  disabled={loading}
                  trailingActions={
                    <button
                      type="button"
                      onClick={() => setShowTestDialog(true)}
                      disabled={curlCommands.length === 0}
                      title={curlCommands.length === 0 ? t("pulsoCsa.testWaitBackend") : t("pulsoCsa.testApp")}
                      className="showcase-filter-icon showcase-send-icon cursor-pointer border-0 flex items-center justify-center text-white disabled:opacity-50 disabled:cursor-not-allowed"
                      aria-label={t("pulsoCsa.testAppAria")}
                    >
                      <TestTube className="h-5 w-5" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </button>
                  }
                />
              </div>
            </form>
          </div>
        </div>

        {requestId && (
          <div className="flex items-center gap-2 p-4 glass border-t border-primary/20 shrink-0">
            <span className="text-sm font-mono text-primary flex-1">ID: {requestId}</span>
            <Button variant="ghost" size="sm" onClick={handleCopyId} className="h-8 gap-1.5 text-xs">
              <Copy className="h-4 w-4 shrink-0" />
              <span>{t("pulsoCsa.copyId")}</span>
            </Button>
          </div>
        )}
      </div>

      {/* Dialog Renomear chat */}
      <Dialog open={showRenameDialog} onOpenChange={(open) => !open && (setShowRenameDialog(false), setRenameSessionId(null), setRenameValue(""))}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t("pulsoCsa.renameTitle")}</DialogTitle>
            <DialogDescription>{t("pulsoCsa.renameDesc")}</DialogDescription>
          </DialogHeader>
          <div className="flex gap-2 py-4">
            <Input
              value={renameValue}
              onChange={(e) => setRenameValue(e.target.value)}
              placeholder={t("pulsoCsa.renamePlaceholder")}
              onKeyDown={(e) => e.key === "Enter" && confirmRename()}
            />
            <Button variant="pulso" onClick={confirmRename}>{t("pulsoCsa.save")}</Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Dialog de Testes com cURL */}
      <Dialog open={showTestDialog} onOpenChange={setShowTestDialog}>
        <DialogContent className="w-[min(90vw,920px)] max-h-[85vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="text-xl font-semibold text-foreground flex items-center gap-2">
              <TestTube className="h-5 w-5 text-primary" />
              {t("pulsoCsa.curlDialogTitle")}
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              {t("pulsoCsa.curlDialogDesc")}
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
                        <span className="animate-pulse">{t("pulsoCsa.executing")}</span>
                      ) : (
                        <>
                          <Play className="h-3.5 w-3.5 mr-1.5" />
                          {t("pulsoCsa.run")}
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
                      {t("pulsoCsa.copy")}
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
