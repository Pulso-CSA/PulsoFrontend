import { useState } from "react";
import { Eye, EyeOff, Key, MapPin } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export type CloudProvider = "aws" | "azure" | "gcp";

export interface CloudCredentialsState {
  aws: { region: string; accessKeyId: string; secretAccessKey: string; accountId: string };
  azure: { region: string; tenantId: string; clientId: string; clientSecret: string; subscriptionId: string };
  gcp: { region: string; projectId: string; clientEmail: string; privateKey: string };
}

interface CloudCredentialsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  provider: CloudProvider;
  credentials: CloudCredentialsState;
  onCredentialsChange: (next: CloudCredentialsState) => void;
  onSave: (provider: CloudProvider) => void;
  title?: string;
  description?: string;
}

const awsRegions = ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "sa-east-1", "eu-west-1", "eu-central-1", "ap-southeast-1"];
const azureRegions = ["eastus", "eastus2", "westus", "westus2", "brazilsouth", "westeurope", "northeurope", "southeastasia"];
const gcpRegions = ["us-east1", "us-west1", "us-central1", "southamerica-east1", "europe-west1", "asia-southeast1"];

export default function CloudCredentialsDialog({
  open,
  onOpenChange,
  provider,
  credentials,
  onCredentialsChange,
  onSave,
  title = "Credenciais Cloud",
  description = "Preencha as credenciais do provedor selecionado.",
}: CloudCredentialsDialogProps) {
  const [showSecrets, setShowSecrets] = useState<{ aws: boolean; azure: boolean; gcp: boolean }>({
    aws: false,
    azure: false,
    gcp: false,
  });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="glass-strong border border-primary/20 sm:max-w-[560px]">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-primary">
          Provedor selecionado: {provider}
        </div>

        {provider === "aws" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs flex items-center gap-1"><MapPin className="h-3 w-3" />Regiao</Label>
                <Select value={credentials.aws.region} onValueChange={(v) => onCredentialsChange({ ...credentials, aws: { ...credentials.aws, region: v } })}>
                  <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>{awsRegions.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Account ID</Label>
                <Input className="h-8 text-xs" value={credentials.aws.accountId} onChange={(e) => onCredentialsChange({ ...credentials, aws: { ...credentials.aws, accountId: e.target.value } })} />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Access Key ID</Label>
              <Input className="h-8 text-xs" value={credentials.aws.accessKeyId} onChange={(e) => onCredentialsChange({ ...credentials, aws: { ...credentials.aws, accessKeyId: e.target.value } })} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Secret Access Key</Label>
              <div className="relative">
                <Input className="h-8 text-xs pr-8" type={showSecrets.aws ? "text" : "password"} value={credentials.aws.secretAccessKey} onChange={(e) => onCredentialsChange({ ...credentials, aws: { ...credentials.aws, secretAccessKey: e.target.value } })} />
                <button type="button" onClick={() => setShowSecrets((s) => ({ ...s, aws: !s.aws }))} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground">
                  {showSecrets.aws ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                </button>
              </div>
            </div>
          </div>
        )}

        {provider === "azure" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs flex items-center gap-1"><MapPin className="h-3 w-3" />Regiao</Label>
                <Select value={credentials.azure.region} onValueChange={(v) => onCredentialsChange({ ...credentials, azure: { ...credentials.azure, region: v } })}>
                  <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>{azureRegions.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Subscription ID</Label>
                <Input className="h-8 text-xs" value={credentials.azure.subscriptionId} onChange={(e) => onCredentialsChange({ ...credentials, azure: { ...credentials.azure, subscriptionId: e.target.value } })} />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs">Tenant ID</Label>
                <Input className="h-8 text-xs" value={credentials.azure.tenantId} onChange={(e) => onCredentialsChange({ ...credentials, azure: { ...credentials.azure, tenantId: e.target.value } })} />
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Client ID</Label>
                <Input className="h-8 text-xs" value={credentials.azure.clientId} onChange={(e) => onCredentialsChange({ ...credentials, azure: { ...credentials.azure, clientId: e.target.value } })} />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Client Secret</Label>
              <div className="relative">
                <Input className="h-8 text-xs pr-8" type={showSecrets.azure ? "text" : "password"} value={credentials.azure.clientSecret} onChange={(e) => onCredentialsChange({ ...credentials, azure: { ...credentials.azure, clientSecret: e.target.value } })} />
                <button type="button" onClick={() => setShowSecrets((s) => ({ ...s, azure: !s.azure }))} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground">
                  {showSecrets.azure ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                </button>
              </div>
            </div>
          </div>
        )}

        {provider === "gcp" && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label className="text-xs flex items-center gap-1"><MapPin className="h-3 w-3" />Regiao</Label>
                <Select value={credentials.gcp.region} onValueChange={(v) => onCredentialsChange({ ...credentials, gcp: { ...credentials.gcp, region: v } })}>
                  <SelectTrigger className="h-8 text-xs"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>{gcpRegions.map((r) => <SelectItem key={r} value={r}>{r}</SelectItem>)}</SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Project ID</Label>
                <Input className="h-8 text-xs" value={credentials.gcp.projectId} onChange={(e) => onCredentialsChange({ ...credentials, gcp: { ...credentials.gcp, projectId: e.target.value } })} />
              </div>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Client Email</Label>
              <Input className="h-8 text-xs" value={credentials.gcp.clientEmail} onChange={(e) => onCredentialsChange({ ...credentials, gcp: { ...credentials.gcp, clientEmail: e.target.value } })} />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Private Key</Label>
              <div className="relative">
                <Input className="h-8 text-xs pr-8" type={showSecrets.gcp ? "text" : "password"} value={credentials.gcp.privateKey} onChange={(e) => onCredentialsChange({ ...credentials, gcp: { ...credentials.gcp, privateKey: e.target.value } })} />
                <button type="button" onClick={() => setShowSecrets((s) => ({ ...s, gcp: !s.gcp }))} className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground">
                  {showSecrets.gcp ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button
            type="button"
            size="sm"
            className="gap-2 min-w-[170px] justify-center font-semibold text-white"
            onClick={() => onSave(provider)}
          >
            <Key className="h-3.5 w-3.5" />
            <span className="whitespace-nowrap">Salvar credenciais</span>
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
