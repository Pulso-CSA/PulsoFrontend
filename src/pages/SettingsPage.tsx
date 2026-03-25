import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Save, Loader2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { updateVersion, fetchVersion, type VersionInfo } from "@/lib/version";
import { getStoredToken } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export default function SettingsPage() {
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
    const api = (window as any).electronAPI;
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
      const result = await api.checkForUpdates();

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

  return (
    <div className="pulso-page-container container max-w-2xl py-8">
      <Button variant="pulso" onClick={() => navigate(-1)} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Voltar
      </Button>

      <h1 className="text-2xl font-bold mb-6">Configurações</h1>

      {typeof window !== "undefined" && (window as any).electronAPI && (
        <section className="space-y-4 mb-8 p-4 rounded-lg border border-primary/30 bg-primary/5">
          <h2 className="text-lg font-semibold">Atualizações do aplicativo</h2>
          <p className="text-sm text-muted-foreground">
            Verifique manualmente se há uma nova versão disponível. Seus dados locais (incluindo localStorage) são preservados durante a atualização.
            Com repositório <strong>público</strong> no GitHub, não é necessário configurar token. Se o repositório for <strong>privado</strong>, defina a variável de ambiente{" "}
            <strong>GH_TOKEN</strong> ou <strong>GITHUB_TOKEN</strong> com um Personal Access Token (escopo <code>repo</code>) e reinicie o aplicativo.
          </p>
          <Button
            variant="pulso"
            onClick={handleCheckForUpdates}
            disabled={checkingUpdate}
            className="gap-2"
          >
            {checkingUpdate ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Verificando...
              </>
            ) : (
              <>
                Verificar atualizações
              </>
            )}
          </Button>
        </section>
      )}

      {typeof window !== "undefined" && window.electronAPI?.openUninstall && (
        <section className="space-y-4 mb-8 p-4 rounded-lg border border-destructive/30 bg-destructive/5">
          <h2 className="text-lg font-semibold text-destructive">Desinstalar</h2>
          <p className="text-sm text-muted-foreground">
            Remover o Pulso do seu computador. O aplicativo será fechado e o assistente de desinstalação será aberto.
          </p>
          <Button
            variant="destructive"
            onClick={() => window.electronAPI?.openUninstall?.()}
            className="gap-2"
          >
            <Trash2 className="h-4 w-4" />
            Desinstalar Pulso
          </Button>
        </section>
      )}

      <section className="pulso-page-card space-y-6 p-6 rounded-xl border">
        <h2 className="text-lg font-semibold">Configuração de versão (admin)</h2>
        <p className="text-sm text-muted-foreground">
          Apenas usuários autorizados podem alterar. O backend retornará 403 se você não tiver permissão.
        </p>

        {loading ? (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            Carregando…
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <Label htmlFor="platform">Plataforma</Label>
              <Input
                id="platform"
                value={form.platform ?? "win"}
                onChange={(e) => setForm((f) => ({ ...f, platform: e.target.value }))}
              />
            </div>
            <div>
              <Label htmlFor="minClientVersion">Versão mínima obrigatória</Label>
              <Input
                id="minClientVersion"
                value={form.minClientVersion ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, minClientVersion: e.target.value }))}
                placeholder="1.0.0"
              />
            </div>
            <div>
              <Label htmlFor="latestVersion">Última versão disponível</Label>
              <Input
                id="latestVersion"
                value={form.latestVersion ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, latestVersion: e.target.value }))}
                placeholder="1.0.2"
              />
            </div>
            <div>
              <Label htmlFor="releaseNotes">Notas de release</Label>
              <Textarea
                id="releaseNotes"
                value={form.releaseNotes ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, releaseNotes: e.target.value }))}
                placeholder="Correções e melhorias."
                rows={3}
              />
            </div>
            <div>
              <Label htmlFor="downloadUrl">URL de download</Label>
              <Input
                id="downloadUrl"
                value={form.downloadUrl ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, downloadUrl: e.target.value }))}
                placeholder="https://github.com/.../releases/..."
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch
                id="forceUpgrade"
                checked={form.forceUpgrade ?? false}
                onCheckedChange={(v) => setForm((f) => ({ ...f, forceUpgrade: v }))}
              />
              <Label htmlFor="forceUpgrade">Forçar atualização obrigatória</Label>
            </div>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="showcase-sparkle-btn gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <span className="showcase-spark" aria-hidden />
              <span className="absolute inset-[0.1em] rounded-[100px] bg-background/80 pointer-events-none" />
              {saving ? <Loader2 className="w-5 h-5 relative z-10 animate-spin" /> : <Save className="w-5 h-5 relative z-10" />}
              <span className="relative z-10">{saving ? "Salvando..." : "Salvar"}</span>
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
