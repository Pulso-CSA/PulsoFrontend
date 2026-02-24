import { useState, useEffect } from "react";
import { Send, Trash2, Copy, FolderOpen, FileCode, Key, MapPin, Eye, EyeOff, CloudCog, MessageSquare, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChatTextarea } from "@/components/ui/chat-textarea";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/AuthContext";
import { infraApi } from "@/lib/api";
import { getAllCloudCredentials, setCloudCredentials, getRootPath, setRootPath, getCloudChatSessions, setCloudChatSessions, type ChatSession } from "@/lib/connectionStorage";
import { FaAws } from "react-icons/fa";
import { VscAzure } from "react-icons/vsc";
import { SiGooglecloud } from "react-icons/si";

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

interface ProviderCredentials {
  aws: { region: string; accessKeyId: string; secretAccessKey: string; accountId: string };
  azure: { region: string; tenantId: string; clientId: string; clientSecret: string; subscriptionId: string };
  gcp: { region: string; projectId: string; clientEmail: string; privateKey: string };
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
  const [showSecrets, setShowSecrets] = useState<{ aws: boolean; azure: boolean; gcp: boolean }>({ aws: false, azure: false, gcp: false });
  const [expandedProvider, setExpandedProvider] = useState<"aws" | "azure" | "gcp" | null>(null);
  const [credentials, setCredentials] = useState<ProviderCredentials>(getAllCloudCredentials);

  useEffect(() => {
    setCredentials(getAllCloudCredentials());
    setRootPathState(getRootPath());
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

  const awsRegions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "sa-east-1", "eu-west-1", "eu-central-1", "ap-southeast-1"];
  const azureRegions = ["eastus", "eastus2", "westus", "westus2", "brazilsouth", "westeurope", "northeurope", "southeastasia"];
  const gcpRegions = ["us-east1", "us-west1", "us-central1", "southamerica-east1", "europe-west1", "asia-southeast1"];

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

  const handleSaveCredentials = (provider: "aws" | "azure" | "gcp") => {
    setCloudCredentials(provider, credentials[provider]);
    toast({
      title: "Credenciais salvas",
      description: `Configuração ${provider.toUpperCase()} salva com sucesso`,
    });
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

      let infraSpec: unknown = null;
      const analyzeRes = await infraApi.analyze({
        root_path: rootPath.trim() || undefined,
        tenant_id: tenantId,
        id_requisicao: idRequisicao,
        user_request: promptText,
        providers: [activeProvider],
      });

      if (analyzeRes?.infra_spec_draft) {
        infraSpec = analyzeRes.infra_spec_draft;
      }

      const generateRes = await infraApi.generate({
        infra_spec: infraSpec,
        user_request: promptText,
        root_path: rootPath.trim() || undefined,
        tenant_id: tenantId,
        id_requisicao: idRequisicao,
      });

      const terraformCode = generateRes?.terraform_code ?? "";
      const content = generateRes?.message ?? `Infraestrutura gerada para ${activeProvider.toUpperCase()}.`;

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

  const hasCredentials = (provider: "aws" | "azure" | "gcp") => {
    const creds = credentials[provider];
    return Object.values(creds).some(v => v && v.length > 0);
  };

  const providerInfo = {
    aws: { 
      name: "Amazon Web Services", 
      gradient: "from-orange-500 to-yellow-500",
      glow: "rgba(249, 115, 22, 0.4)",
      border: "border-orange-500",
      bg: "bg-orange-500"
    },
    azure: { 
      name: "Microsoft Azure", 
      gradient: "from-blue-500 to-cyan-400",
      glow: "rgba(59, 130, 246, 0.4)",
      border: "border-blue-500",
      bg: "bg-blue-500"
    },
    gcp: { 
      name: "Google Cloud Platform", 
      gradient: "from-red-500 to-yellow-400",
      glow: "rgba(239, 68, 68, 0.4)",
      border: "border-red-500",
      bg: "bg-red-500"
    },
  };

  const renderProviderButton = (provider: "aws" | "azure" | "gcp", icon: React.ReactNode, label: string) => {
    const info = providerInfo[provider];
    const isActive = activeProvider === provider;
    const isExpanded = expandedProvider === provider;
    const configured = hasCredentials(provider);

    return (
      <div className="flex items-center gap-1">
        <button
          onClick={() => setActiveProvider(provider)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all duration-200 ${
            isActive 
              ? `bg-gradient-to-r ${info.gradient} text-white shadow-lg` 
              : 'bg-background/50 hover:bg-background/80 border border-border/50'
          }`}
          style={{ boxShadow: isActive ? `0 0 12px ${info.glow}` : 'none' }}
        >
          <div className={`text-xl ${isActive ? 'text-white' : providerColors[provider].text}`}>
            {icon}
          </div>
          <span className={`font-semibold text-xs ${isActive ? 'text-white' : 'text-foreground'}`}>{label}</span>
          {configured && (
            <span className={`w-1.5 h-1.5 rounded-full ${isActive ? 'bg-white' : 'bg-green-500'}`} />
          )}
        </button>
        
        <button
          onClick={() => setExpandedProvider(isExpanded ? null : provider)}
          className={`p-1.5 rounded-lg transition-all ${isExpanded ? info.bg + ' text-white' : 'hover:bg-accent text-muted-foreground'}`}
        >
          <Key className="h-3 w-3" />
        </button>
      </div>
    );
  };

  const renderCredentialsPanel = (provider: "aws" | "azure" | "gcp") => {
    const info = providerInfo[provider];
    
    return (
      <Collapsible open={expandedProvider === provider}>
        <CollapsibleContent className="animate-accordion-down">
          <div className={`space-y-3 p-3 mt-2 rounded-xl border ${info.border}/30 bg-background/80 backdrop-blur-sm`}>
            {provider === "aws" && (
              <>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs flex items-center gap-1"><MapPin className="h-3 w-3" />Região</Label>
                    <Select value={credentials.aws.region} onValueChange={(v) => setCredentials({ ...credentials, aws: { ...credentials.aws, region: v } })}>
                      <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Selecione" /></SelectTrigger>
                      <SelectContent>{awsRegions.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Account ID</Label>
                    <Input className="h-8 text-xs" placeholder="123456789012" value={credentials.aws.accountId} onChange={(e) => setCredentials({ ...credentials, aws: { ...credentials.aws, accountId: e.target.value } })} />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs flex items-center gap-1"><Key className="h-3 w-3" />Access Key ID</Label>
                  <Input className="h-8 text-xs" placeholder="AKIAIOSFODNN7EXAMPLE" value={credentials.aws.accessKeyId} onChange={(e) => setCredentials({ ...credentials, aws: { ...credentials.aws, accessKeyId: e.target.value } })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Secret Access Key</Label>
                  <div className="relative">
                    <Input className="h-8 text-xs pr-8" type={showSecrets.aws ? "text" : "password"} placeholder="••••••••" value={credentials.aws.secretAccessKey} onChange={(e) => setCredentials({ ...credentials, aws: { ...credentials.aws, secretAccessKey: e.target.value } })} />
                    <button type="button" onClick={() => setShowSecrets({ ...showSecrets, aws: !showSecrets.aws })} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary">
                      {showSecrets.aws ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
                <Button size="sm" className={`w-full h-8 text-xs bg-gradient-to-r ${info.gradient} hover:opacity-90 text-white`} onClick={() => handleSaveCredentials("aws")}>Salvar AWS</Button>
              </>
            )}
            {provider === "azure" && (
              <>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs flex items-center gap-1"><MapPin className="h-3 w-3" />Região</Label>
                    <Select value={credentials.azure.region} onValueChange={(v) => setCredentials({ ...credentials, azure: { ...credentials.azure, region: v } })}>
                      <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Selecione" /></SelectTrigger>
                      <SelectContent>{azureRegions.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Subscription ID</Label>
                    <Input className="h-8 text-xs" placeholder="xxxxxxxx-xxxx" value={credentials.azure.subscriptionId} onChange={(e) => setCredentials({ ...credentials, azure: { ...credentials.azure, subscriptionId: e.target.value } })} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs">Tenant ID</Label>
                    <Input className="h-8 text-xs" placeholder="xxxxxxxx-xxxx" value={credentials.azure.tenantId} onChange={(e) => setCredentials({ ...credentials, azure: { ...credentials.azure, tenantId: e.target.value } })} />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs flex items-center gap-1"><Key className="h-3 w-3" />Client ID</Label>
                    <Input className="h-8 text-xs" placeholder="xxxxxxxx-xxxx" value={credentials.azure.clientId} onChange={(e) => setCredentials({ ...credentials, azure: { ...credentials.azure, clientId: e.target.value } })} />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Client Secret</Label>
                  <div className="relative">
                    <Input className="h-8 text-xs pr-8" type={showSecrets.azure ? "text" : "password"} placeholder="••••••••" value={credentials.azure.clientSecret} onChange={(e) => setCredentials({ ...credentials, azure: { ...credentials.azure, clientSecret: e.target.value } })} />
                    <button type="button" onClick={() => setShowSecrets({ ...showSecrets, azure: !showSecrets.azure })} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary">
                      {showSecrets.azure ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
                <Button size="sm" className={`w-full h-8 text-xs bg-gradient-to-r ${info.gradient} hover:opacity-90 text-white`} onClick={() => handleSaveCredentials("azure")}>Salvar Azure</Button>
              </>
            )}
            {provider === "gcp" && (
              <>
                <div className="grid grid-cols-2 gap-2">
                  <div className="space-y-1">
                    <Label className="text-xs flex items-center gap-1"><MapPin className="h-3 w-3" />Região</Label>
                    <Select value={credentials.gcp.region} onValueChange={(v) => setCredentials({ ...credentials, gcp: { ...credentials.gcp, region: v } })}>
                      <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Selecione" /></SelectTrigger>
                      <SelectContent>{gcpRegions.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Project ID</Label>
                    <Input className="h-8 text-xs" placeholder="my-project-123" value={credentials.gcp.projectId} onChange={(e) => setCredentials({ ...credentials, gcp: { ...credentials.gcp, projectId: e.target.value } })} />
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs flex items-center gap-1"><Key className="h-3 w-3" />Client Email</Label>
                  <Input className="h-8 text-xs" placeholder="sa@project.iam.gserviceaccount.com" value={credentials.gcp.clientEmail} onChange={(e) => setCredentials({ ...credentials, gcp: { ...credentials.gcp, clientEmail: e.target.value } })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Private Key</Label>
                  <div className="relative">
                    <Input className="h-8 text-xs pr-8" type={showSecrets.gcp ? "text" : "password"} placeholder="••••••••" value={credentials.gcp.privateKey} onChange={(e) => setCredentials({ ...credentials, gcp: { ...credentials.gcp, privateKey: e.target.value } })} />
                    <button type="button" onClick={() => setShowSecrets({ ...showSecrets, gcp: !showSecrets.gcp })} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-primary">
                      {showSecrets.gcp ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    </button>
                  </div>
                </div>
                <Button size="sm" className={`w-full h-8 text-xs bg-gradient-to-r ${info.gradient} hover:opacity-90 text-white`} onClick={() => handleSaveCredentials("gcp")}>Salvar GCP</Button>
              </>
            )}
          </div>
        </CollapsibleContent>
      </Collapsible>
    );
  };

  return (
    <div className="glass-strong rounded-2xl overflow-hidden border-2 border-cyan-500/30" style={{ boxShadow: '0 0 30px rgba(0, 200, 255, 0.2)' }}>
      {/* Header */}
      <div className="p-4 border-b border-cyan-500/30 bg-gradient-to-r from-cyan-500/10 to-blue-600/10">
        <h2 className="text-lg font-semibold flex items-center gap-2" style={{ color: 'hsl(190 100% 65%)' }}>
          <CloudCog className="h-5 w-5" style={{ color: 'hsl(190 100% 65%)' }} />
          Cloud Infrastructure
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          Crie infraestruturas usando linguagem natural ou caminhos de arquivo
        </p>
      </div>

      {/* Provider Selection */}
      <div className="p-3 border-b border-cyan-500/20">
        <div className="flex items-center gap-2 flex-wrap">
          {renderProviderButton("aws", <FaAws className="h-6 w-6" />, "AWS")}
          {renderProviderButton("azure", <VscAzure className="h-6 w-6" />, "Azure")}
          {renderProviderButton("gcp", <SiGooglecloud className="h-6 w-6" />, "GCP")}
        </div>
        {renderCredentialsPanel("aws")}
        {renderCredentialsPanel("azure")}
        {renderCredentialsPanel("gcp")}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
        {/* Chat Area */}
        <div className="lg:col-span-2 border-r border-cyan-500/20">
          <div className="min-h-[624px] overflow-y-auto p-5 space-y-5">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <CloudCog className="h-12 w-12 text-cyan-400/50" />
                <div>
                  <p className="text-sm text-foreground font-medium">Descreva a infraestrutura que deseja criar</p>
                  <p className="text-xs text-muted-foreground mt-1">Use linguagem natural ou informe o caminho de um arquivo</p>
                </div>
                <div className="pt-4 w-full max-w-md">
                  <p className="text-xs text-muted-foreground mb-2">Sugestões:</p>
                  <div className="flex flex-wrap gap-2 justify-center">
                    {quickActions.map((action, idx) => (
                      <Button key={idx} variant="outline" size="sm" onClick={() => handleQuickAction(action)} className="text-xs border-cyan-500/30 hover:border-cyan-500 hover:bg-cyan-500/10">
                        {action}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`max-w-[85%] rounded-lg p-3 ${message.role === "user" ? "bg-cyan-500/20 border border-cyan-500/30" : "bg-background/50 border border-border/50"}`}>
                    {message.provider && (
                      <Badge variant="outline" className="mb-2 text-xs" style={{ borderColor: providerColors[message.provider].hsl, color: providerColors[message.provider].hsl }}>
                        {message.provider.toUpperCase()}
                      </Badge>
                    )}
                    <p className="text-sm text-foreground whitespace-pre-wrap">{message.content}</p>
                    {message.resources && (
                      <div className="mt-3 space-y-2 p-3 bg-background/30 rounded border border-cyan-500/20">
                        <p className="text-xs font-semibold flex items-center gap-1 text-cyan-400"><FolderOpen className="h-3 w-3" />Recursos criados:</p>
                        <ul className="space-y-1 text-xs">
                          {message.resources.map((resource, idx) => (
                            <li key={idx} className="flex items-start gap-2 text-muted-foreground"><span className="text-cyan-400 mt-0.5">•</span><span>{resource}</span></li>
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
                        <pre className="bg-background/50 rounded p-3 text-xs font-mono overflow-x-auto border border-cyan-500/20">{message.codeBlock}</pre>
                      </div>
                    )}
                    <p className="text-xs text-muted-foreground mt-2">{message.timestamp.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start animate-slide-up">
                <div className="bg-background/50 border border-cyan-500/20 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1.5 items-end h-4">
                      <div
                        className="w-2 h-2 rounded-full animate-typing-bounce bg-cyan-400"
                        style={{ animationDelay: "0ms" }}
                      />
                      <div
                        className="w-2 h-2 rounded-full animate-typing-bounce bg-cyan-400"
                        style={{ animationDelay: "200ms" }}
                      />
                      <div
                        className="w-2 h-2 rounded-full animate-typing-bounce bg-cyan-400"
                        style={{ animationDelay: "400ms" }}
                      />
                    </div>
                    <span className="text-sm text-muted-foreground">Digitando...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-cyan-500/20 space-y-2">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex gap-2 items-end"
            >
              <Input
                placeholder="Caminho do projeto (opcional)"
                value={rootPath}
                onChange={(e) => handleRootPathChange(e.target.value)}
                className="border-cyan-500/30 focus-visible:ring-cyan-500 max-w-[200px]"
              />
              <ChatTextarea
                placeholder="Ex.: 'Criar VPC com 2 subnets públicas e 2 privadas'"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onSend={handleSend}
                className="border-cyan-500/30 focus-visible:ring-cyan-500 flex-1 py-2"
              />
              <Button type="submit" disabled={!input.trim() || loading} className="shrink-0 bg-cyan-500 hover:bg-cyan-600">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>

        {/* Chats Sidebar */}
        <div className="bg-background/30">
          <div className="p-3 border-b border-cyan-500/20 flex items-center justify-between">
            <h3 className="text-sm font-semibold flex items-center gap-2 text-cyan-400"><MessageSquare className="h-4 w-4" />Chats</h3>
            <Button variant="ghost" size="sm" onClick={handleNewChat} className="h-7 px-2 text-xs text-cyan-400 hover:bg-cyan-500/10">
              <Plus className="h-3.5 w-3.5" />
            </Button>
          </div>
          <div className="min-h-[500px] overflow-y-auto p-2 space-y-2">
            {sessions.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-4">
                <MessageSquare className="h-8 w-8 text-muted-foreground/30 mb-2" />
                <p className="text-xs text-muted-foreground">Nenhum chat ainda</p>
                <p className="text-[10px] text-muted-foreground mt-1">Envie uma mensagem para começar</p>
              </div>
            ) : (
              [...sessions].reverse().map((session) => (
                <div key={session.id} className="group relative">
                  <button
                    onClick={() => handleOpenChat(session)}
                    className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${
                      currentSessionId === session.id
                        ? "bg-cyan-500/20 border border-cyan-500/40"
                        : "bg-background/50 hover:bg-cyan-500/10 border border-transparent hover:border-cyan-500/30"
                    }`}
                  >
                    <p className="text-xs text-foreground line-clamp-2 pr-6">{session.title || "Novo chat"}</p>
                    <p className="text-[10px] text-muted-foreground mt-1">{new Date(session.updatedAt).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" })}</p>
                  </button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => { e.stopPropagation(); handleDeleteChat(session.id); }}
                    className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CloudChat;
