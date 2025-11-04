import { useState, useRef } from "react";
import { Send, Trash2, Copy, Clock, FolderOpen, FileCode, Plus, X, Upload, PlayCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import FileTree from "./FileTree";

interface EnvVariable {
  name: string;
  value: string;
}

interface FileNode {
  name: string;
  type: "file" | "folder";
  children?: FileNode[];
}

interface PromptHistory {
  id: string;
  text: string;
  timestamp: Date;
}

const PromptPanel = () => {
  const [prompt, setPrompt] = useState("");
  const [envVars, setEnvVars] = useState<EnvVariable[]>([]);
  const [newVarName, setNewVarName] = useState("");
  const [newVarValue, setNewVarValue] = useState("");
  const [folderPath, setFolderPath] = useState("");
  const [requestId, setRequestId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<PromptHistory[]>([]);
  const [fileStructure, setFileStructure] = useState<FileNode[] | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
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

  const handleSubmit = () => {
    if (!prompt.trim()) return;

    setLoading(true);
    
    // Simular envio e geração de estrutura de arquivos
    setTimeout(() => {
      const id = `REQ-${Date.now().toString(36).toUpperCase()}`;
      setRequestId(id);
      
      const newEntry: PromptHistory = {
        id,
        text: prompt,
        timestamp: new Date(),
      };
      
      setHistory([newEntry, ...history.slice(0, 4)]);
      
      // Estrutura de arquivos de exemplo baseada no prompt
      const mockStructure: FileNode[] = [
        {
          name: "src",
          type: "folder",
          children: [
            {
              name: "components",
              type: "folder",
              children: [
                { name: "Header.tsx", type: "file" },
                { name: "Footer.tsx", type: "file" },
              ],
            },
            {
              name: "pages",
              type: "folder",
              children: [
                { name: "Home.tsx", type: "file" },
                { name: "Dashboard.tsx", type: "file" },
              ],
            },
            {
              name: "services",
              type: "folder",
              children: [
                { name: "api.ts", type: "file" },
              ],
            },
            { name: "App.tsx", type: "file" },
          ],
        },
        { name: "package.json", type: "file" },
        { name: "README.md", type: "file" },
      ];
      
      setFileStructure(mockStructure);
      setLoading(false);
      
      toast({
        title: "Prompt enviado",
        description: `ID da requisição: ${id}`,
      });
    }, 1000);
  };

  const handleClear = () => {
    setPrompt("");
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
    setPrompt(text);
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

        {/* Prompt Principal */}
        <div className="space-y-2">
          <Label htmlFor="prompt-input" className="text-sm font-medium text-foreground flex items-center gap-2">
            <Send className="h-4 w-4 text-primary" />
            Descrição do Projeto
          </Label>
          <Textarea
            id="prompt-input"
            placeholder="Ex.: 'Gerar blueprint de pastas e endpoints para um sistema de gestão de pedidos...'"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="min-h-[120px] resize-none border-0 focus-visible:ring-0 bg-transparent text-base"
          />
        </div>

        <div className="flex gap-3">
          <Button 
            onClick={handleSubmit} 
            disabled={!prompt.trim() || loading}
            className="flex-1 h-12 text-base font-medium"
          >
            {loading ? "Enviando..." : (
              <>
                <Send className="mr-2 h-5 w-5" />
                Enviar Prompt
              </>
            )}
          </Button>
          <Button
            variant="outline"
            className="h-12 px-6 border-finops/40 hover:border-finops hover:bg-finops/10 text-finops"
            title="Testar aplicação"
          >
            <PlayCircle className="h-5 w-5 mr-2" />
            Testar
          </Button>
          <Button 
            variant="outline" 
            onClick={handleClear}
            disabled={!prompt && !requestId}
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
              Estrutura de Arquivos Gerada
            </h3>
            <span className="text-xs text-muted-foreground font-mono">
              {requestId}
            </span>
          </div>
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

      {!prompt && !requestId && history.length === 0 && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            Descreva sua solicitação para começarmos
          </p>
        </div>
      )}
    </div>
  );
};

export default PromptPanel;
