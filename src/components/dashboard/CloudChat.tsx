import { useState } from "react";
import { Send, History, Trash2, Copy, FolderOpen, FileCode, Key, MapPin, Eye, EyeOff, ChevronDown, ChevronUp, CloudCog } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

interface HistoryItem {
  id: string;
  prompt: string;
  provider: "aws" | "azure" | "gcp";
  timestamp: Date;
  status: "success" | "pending" | "error";
}

interface ProviderCredentials {
  aws: { region: string; accessKeyId: string; secretAccessKey: string; accountId: string };
  azure: { region: string; tenantId: string; clientId: string; clientSecret: string; subscriptionId: string };
  gcp: { region: string; projectId: string; clientEmail: string; privateKey: string };
}

const CloudChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeProvider, setActiveProvider] = useState<"aws" | "azure" | "gcp">("aws");
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showSecrets, setShowSecrets] = useState<{ aws: boolean; azure: boolean; gcp: boolean }>({ aws: false, azure: false, gcp: false });
  const [expandedProvider, setExpandedProvider] = useState<"aws" | "azure" | "gcp" | null>(null);
  const [credentials, setCredentials] = useState<ProviderCredentials>({
    aws: { region: "", accessKeyId: "", secretAccessKey: "", accountId: "" },
    azure: { region: "", tenantId: "", clientId: "", clientSecret: "", subscriptionId: "" },
    gcp: { region: "", projectId: "", clientEmail: "", privateKey: "" },
  });
  const { toast } = useToast();

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
    localStorage.setItem(`cloudConfig_${provider}`, JSON.stringify(credentials[provider]));
    toast({
      title: "Credenciais salvas",
      description: `Configuração ${provider.toUpperCase()} salva com sucesso`,
    });
  };

  const handleSend = () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date(),
      provider: activeProvider,
    };

    setMessages([...messages, userMessage]);
    setInput("");
    setLoading(true);

    const historyItem: HistoryItem = {
      id: Date.now().toString(),
      prompt: input,
      provider: activeProvider,
      timestamp: new Date(),
      status: "pending",
    };
    setHistory([historyItem, ...history.slice(0, 9)]);

    setTimeout(() => {
      const terraformCode = `# Terraform - ${activeProvider.toUpperCase()}
resource "${activeProvider === 'aws' ? 'aws_vpc' : activeProvider === 'azure' ? 'azurerm_virtual_network' : 'google_compute_network'}" "main" {
  name       = "main-network"
  cidr_block = "10.0.0.0/16"
  
  tags = {
    Name        = "main"
    Environment = "production"
  }
}`;

      const systemMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "system",
        content: `Infraestrutura gerada para ${activeProvider.toUpperCase()}. Baseado no seu prompt, criei os seguintes recursos:`,
        timestamp: new Date(),
        provider: activeProvider,
        resources: [
          "VPC com CIDR 10.0.0.0/16",
          "2 Subnets públicas (10.0.1.0/24, 10.0.2.0/24)",
          "2 Subnets privadas (10.0.10.0/24, 10.0.20.0/24)",
          "Internet Gateway",
          "NAT Gateway",
          "Route Tables configuradas",
        ],
        codeBlock: terraformCode,
      };

      setMessages((prev) => [...prev, systemMessage]);
      setHistory((prev) => prev.map((item, idx) => idx === 0 ? { ...item, status: "success" as const } : item));
      setLoading(false);
    }, 2000);
  };

  const handleQuickAction = (action: string) => setInput(action);

  const handleReuseHistory = (item: HistoryItem) => {
    setActiveProvider(item.provider);
    setInput(item.prompt);
  };

  const handleCopyCode = (code: string) => {
    navigator.clipboard.writeText(code);
    toast({ title: "Código copiado", description: "Terraform copiado para a área de transferência" });
  };

  const handleClearHistory = () => {
    setHistory([]);
    toast({ title: "Histórico limpo", description: "Todo o histórico foi removido" });
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
          <div className="h-[350px] overflow-y-auto p-4 space-y-4">
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
                    <p className="text-sm text-foreground">{message.content}</p>
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
              <div className="flex justify-start">
                <div className="bg-background/50 border border-border/50 rounded-lg p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-75" />
                      <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-150" />
                    </div>
                    <span className="text-sm text-muted-foreground">Gerando infraestrutura...</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="p-4 border-t border-cyan-500/20">
            <div className="flex gap-2">
              <Input placeholder="Ex.: 'Criar VPC com 2 subnets públicas e 2 privadas' ou 'C:\infra\main.tf'" value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()} className="border-cyan-500/30 focus-visible:ring-cyan-500" />
              <Button onClick={handleSend} disabled={!input.trim() || loading} className="bg-cyan-500 hover:bg-cyan-600"><Send className="h-4 w-4" /></Button>
            </div>
          </div>
        </div>

        {/* History Sidebar */}
        <div className="bg-background/30">
          <div className="p-3 border-b border-cyan-500/20 flex items-center justify-between">
            <h3 className="text-sm font-semibold flex items-center gap-2 text-cyan-400"><History className="h-4 w-4" />Histórico</h3>
            {history.length > 0 && (
              <Button variant="ghost" size="sm" onClick={handleClearHistory} className="h-7 px-2 text-xs text-muted-foreground hover:text-destructive"><Trash2 className="h-3 w-3" /></Button>
            )}
          </div>
          <div className="h-[350px] overflow-y-auto p-2 space-y-2">
            {history.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-center p-4">
                <History className="h-8 w-8 text-muted-foreground/30 mb-2" />
                <p className="text-xs text-muted-foreground">Nenhum histórico ainda</p>
              </div>
            ) : (
              history.map((item) => (
                <button key={item.id} onClick={() => handleReuseHistory(item)} className="w-full text-left p-3 rounded-lg bg-background/50 hover:bg-cyan-500/10 border border-transparent hover:border-cyan-500/30 transition-all duration-200 group">
                  <div className="flex items-start justify-between gap-2">
                    <Badge variant="outline" className="text-[10px] shrink-0" style={{ borderColor: providerColors[item.provider].hsl, color: providerColors[item.provider].hsl }}>{item.provider.toUpperCase()}</Badge>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${item.status === 'success' ? 'bg-green-500/20 text-green-400' : item.status === 'error' ? 'bg-red-500/20 text-red-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                      {item.status === 'success' ? '✓' : item.status === 'error' ? '✗' : '...'}
                    </span>
                  </div>
                  <p className="text-xs text-foreground line-clamp-2 mt-2">{item.prompt}</p>
                  <p className="text-[10px] text-muted-foreground mt-1">{item.timestamp.toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}</p>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CloudChat;
