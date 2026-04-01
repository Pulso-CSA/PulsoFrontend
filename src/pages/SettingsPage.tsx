import { useState, useEffect, type ComponentProps } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Save, Loader2, Trash2, RefreshCw, Shield, Cpu } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { updateVersion, fetchVersion, type VersionInfo } from "@/lib/version";
import { getStoredToken } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

function isElectron(): boolean {
  return typeof window !== "undefined" && !!(window as unknown as { electronAPI?: unknown }).electronAPI;
}

/** Texto de apoio legível no tema claro (evita muted demasiado fraco sobre card) */
function SettingsBody({ className, ...props }: ComponentProps<"p">) {
  return (
    <p
      className={cn(
        "text-sm text-foreground/80 leading-relaxed [&_strong]:font-semibold [&_strong]:text-foreground [&_code]:rounded [&_code]:bg-muted [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:text-xs [&_code]:font-mono",
        className
      )}
      {...props}
    />
  );
}

export default function SettingsPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [checkingUpdate, setCheckingUpdate] = useState(false);
  const [form, setForm] = useState<Partial<VersionInfo>>({
    platform: "win",
    minClientVersion: "",
    latestVersion: "",
    releaseNotes: "",
    forceUpgrade: false,
    downloadUrl: "",
  });

  const loadVersion = async () => {
    setLoading(true);
    try {
      const data = await fetchVersion("win");
      setForm({
        platform: data.platform,
        minClientVersion: data.minClientVersion,
        latestVersion: data.latestVersion,
        releaseNotes: data.releaseNotes ?? "",
        forceUpgrade: data.forceUpgrade,
        downloadUrl: data.downloadUrl ?? "",
      });
    } catch (e) {
      toast({
        title: "Erro ao carregar",
        description: e instanceof Error ? e.message : "Falha ao buscar versão",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadVersion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSave = async () => {
    const token = getStoredToken();
    if (!token) {
      toast({ title: "Não autenticado", variant: "destructive" });
      return;
    }
    setSaving(true);
    try {
      await updateVersion(token, {
        platform: form.platform ?? "win",
        minClientVersion: form.minClientVersion || undefined,
        latestVersion: form.latestVersion || undefined,
        releaseNotes: form.releaseNotes || null,
        forceUpgrade: form.forceUpgrade,
        downloadUrl: form.downloadUrl || null,
      });
      toast({ title: "Configuração salva", description: "Versão atualizada com sucesso." });
    } catch (e) {
      toast({
        title: "Erro ao salvar",
        description: e instanceof Error ? e.message : "Falha ao atualizar (verifique se você é admin)",
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleCheckForUpdates = async () => {
    if (typeof window === "undefined") return;
    const api = (window as unknown as { electronAPI?: { checkForUpdates: () => Promise<unknown> } }).electronAPI;
    if (!api?.checkForUpdates) {
      toast({
        title: "Verificação indisponível",
        description: "Esse recurso está disponível apenas no aplicativo desktop instalado.",
        variant: "destructive",
      });
      return;
    }

    setCheckingUpdate(true);
    try {
      const result = (await api.checkForUpdates()) as {
        ok?: boolean;
        hasUpdate?: boolean;
        version?: string | null;
        error?: string;
      };

      if (result?.ok && result.hasUpdate) {
        toast({
          title: "Atualização encontrada",
          description: result.version
            ? `Versão ${result.version} disponível. A tela de instalação será exibida em instantes.`
            : "Nova versão disponível. A tela de instalação será exibida em instantes.",
        });
      } else if (result?.ok) {
        toast({
          title: "Nenhuma atualização disponível",
          description: "Você já está utilizando a versão mais recente do Pulso.",
        });
      } else {
        const errMsg = result?.error || "Não foi possível buscar atualizações.";
        toast({
          title: "Erro ao verificar atualizações",
          description: errMsg,
          variant: "destructive",
        });
      }
    } catch (e) {
      toast({
        title: "Erro ao verificar atualizações",
        description: e instanceof Error ? e.message : "Não foi possível buscar atualizações.",
        variant: "destructive",
      });
    } finally {
      setCheckingUpdate(false);
    }
  };

  const electron = isElectron();
  const electronUninstall = typeof window !== "undefined" && window.electronAPI?.openUninstall;

  return (
    <div className="pulso-settings-page w-full max-w-3xl mx-auto px-4 sm:px-6 py-8 pb-20 space-y-8 text-foreground">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
        <div className="space-y-1 min-w-0">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => navigate(-1)}
            className="mb-3 w-fit border-border bg-card text-foreground shadow-sm hover:bg-muted hover:text-foreground [&_svg]:text-foreground"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Voltar
          </Button>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">Configurações</h1>
          <p className="text-sm text-foreground/70 max-w-xl">
            Preferências do aplicativo, atualizações no desktop e política de versão (administração).
          </p>
        </div>
      </div>

      {electron && (
        <Card className="border-border/80 shadow-sm overflow-hidden bg-card">
          <CardHeader className="space-y-1 pb-2 border-b border-border/60 bg-muted/30">
            <CardTitle className="text-lg text-foreground flex items-center gap-2">
              <Cpu className="h-5 w-5 text-primary shrink-0" />
              {t("settings.runtimeSetupLinkTitle")}
            </CardTitle>
            <CardDescription className="text-foreground/70 text-sm">
              {t("settings.runtimeSetupLinkDesc")}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-4 pb-6">
            <Button type="button" variant="default" asChild className="gap-2">
              <Link to="/settings/environment">{t("runtimeSetup.title")}</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {electron && (
        <Card className="border-border/80 shadow-sm overflow-hidden bg-card">
          <CardHeader className="space-y-1 pb-2 border-b border-border/60 bg-muted/30">
            <CardTitle className="text-lg text-foreground flex items-center gap-2">
              <RefreshCw className="h-5 w-5 text-primary shrink-0" />
              Aplicativo desktop
            </CardTitle>
            <CardDescription className="text-foreground/70 text-sm">
              Atualizações e remoção do Pulso instalado no Windows.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-foreground">Atualizações</h3>
              <SettingsBody>
                Verifique manualmente se há uma nova versão disponível. Seus dados locais (incluindo{" "}
                <code>localStorage</code>) são preservados durante a atualização. Com repositório{" "}
                <strong>público</strong> no GitHub, não é necessário configurar token. Se o repositório for{" "}
                <strong>privado</strong>, defina a variável de ambiente <strong>GH_TOKEN</strong> ou{" "}
                <strong>GITHUB_TOKEN</strong> com um Personal Access Token (escopo <code>repo</code>) e reinicie o
                aplicativo.
              </SettingsBody>
              <Button
                type="button"
                variant="default"
                onClick={handleCheckForUpdates}
                disabled={checkingUpdate}
                className="gap-2 bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
              >
                {checkingUpdate ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Verificando…
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    Verificar atualizações
                  </>
                )}
              </Button>
            </div>

            {electronUninstall && (
              <>
                <Separator />
                <div className="space-y-3 rounded-lg border border-destructive/25 bg-destructive/5 p-4">
                  <h3 className="text-sm font-semibold text-destructive flex items-center gap-2">
                    <Trash2 className="h-4 w-4 shrink-0" />
                    Desinstalar
                  </h3>
                  <SettingsBody className="text-foreground/80">
                    Remove o Pulso deste computador. O aplicativo será fechado e o assistente de desinstalação será
                    aberto.
                  </SettingsBody>
                  <Button
                    type="button"
                    variant="destructive"
                    onClick={() => window.electronAPI?.openUninstall?.()}
                    className="gap-2 w-fit"
                  >
                    <Trash2 className="h-4 w-4" />
                    Desinstalar Pulso
                  </Button>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      <Card className="border-border/80 shadow-sm bg-card">
        <CardHeader className="space-y-1 border-b border-border/60 bg-muted/25 pb-4">
          <CardTitle className="text-lg text-foreground flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary shrink-0" />
            Versão do cliente (administração)
          </CardTitle>
          <CardDescription className="text-foreground/70 text-sm">
            Apenas usuários autorizados podem alterar. O backend retornará 403 se você não tiver permissão.
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          {loading ? (
            <div className="flex items-center gap-2 text-foreground/80">
              <Loader2 className="h-4 w-4 animate-spin" />
              Carregando…
            </div>
          ) : (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="platform" className="text-foreground">
                    Plataforma
                  </Label>
                  <Input
                    id="platform"
                    className="bg-background border-border text-foreground"
                    value={form.platform ?? "win"}
                    onChange={(e) => setForm((f) => ({ ...f, platform: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="minClientVersion" className="text-foreground">
                    Versão mínima obrigatória
                  </Label>
                  <Input
                    id="minClientVersion"
                    className="bg-background border-border text-foreground placeholder:text-foreground/45"
                    value={form.minClientVersion ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, minClientVersion: e.target.value }))}
                    placeholder="1.0.0"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="latestVersion" className="text-foreground">
                    Última versão disponível
                  </Label>
                  <Input
                    id="latestVersion"
                    className="bg-background border-border text-foreground placeholder:text-foreground/45"
                    value={form.latestVersion ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, latestVersion: e.target.value }))}
                    placeholder="1.0.2"
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="releaseNotes" className="text-foreground">
                    Notas de release
                  </Label>
                  <Textarea
                    id="releaseNotes"
                    className="bg-background border-border text-foreground placeholder:text-foreground/45 min-h-[88px]"
                    value={form.releaseNotes ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, releaseNotes: e.target.value }))}
                    placeholder="Correções e melhorias."
                    rows={3}
                  />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="downloadUrl" className="text-foreground">
                    URL de download
                  </Label>
                  <Input
                    id="downloadUrl"
                    className="bg-background border-border text-foreground placeholder:text-foreground/45"
                    value={form.downloadUrl ?? ""}
                    onChange={(e) => setForm((f) => ({ ...f, downloadUrl: e.target.value }))}
                    placeholder="https://github.com/.../releases/..."
                  />
                </div>
              </div>
              <div className="flex items-center gap-3 rounded-lg border border-border/70 bg-muted/20 px-3 py-3">
                <Switch
                  id="forceUpgrade"
                  checked={form.forceUpgrade ?? false}
                  onCheckedChange={(v) => setForm((f) => ({ ...f, forceUpgrade: v }))}
                />
                <Label htmlFor="forceUpgrade" className="text-sm font-medium text-foreground cursor-pointer leading-snug">
                  Forçar atualização obrigatória
                </Label>
              </div>
            </>
          )}
        </CardContent>
        {!loading && (
          <CardFooter className="flex justify-end border-t border-border/60 bg-muted/15 py-4">
            <Button
              type="button"
              variant="default"
              onClick={handleSave}
              disabled={saving}
              className="gap-2 min-w-[140px] bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm"
            >
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              {saving ? "Salvando…" : "Salvar alterações"}
            </Button>
          </CardFooter>
        )}
      </Card>
    </div>
  );
}
