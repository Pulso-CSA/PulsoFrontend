import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ArrowLeft, Download, Loader2, Package, RefreshCw, Server, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

type RuntimeStatus = {
  platform: string;
  supportsEmbeddedPythonDownload: boolean;
  apiRoot: string | null;
  requirementsFileExists: boolean;
  embeddedPythonPath: string | null;
  embeddedPythonOk: boolean;
  pipUvicornOk: boolean;
  ollamaCliAvailable: boolean;
  userEnvPath: string;
  userEnvExists: boolean;
  openAiKeyConfigured: boolean;
  useOllamaForced: boolean;
  defaultOllamaModels: string[];
  ollamaHost: string;
};

type ElectronRuntimeApi = {
  runtimeGetStatus?: () => Promise<RuntimeStatus>;
  runtimeInstallPython?: () => Promise<{ ok?: boolean; error?: string; pythonExe?: string; alreadyHad?: boolean }>;
  runtimePipInstall?: () => Promise<{ ok?: boolean; error?: string }>;
  runtimeOllamaPull?: () => Promise<{ ok?: boolean; error?: string }>;
  runtimeSaveLlmSettings?: (p: {
    openAiKey?: string;
    useOllama?: boolean;
    ollamaHost?: string;
  }) => Promise<{ ok?: boolean }>;
  runtimeRestartEngine?: () => Promise<{ ok?: boolean; error?: string }>;
  onRuntimeProgress?: (cb: (d: { phase?: string; detail?: string; pct?: number }) => void) => () => void;
  onRuntimeLogLine?: (cb: (line: string) => void) => () => void;
};

function getRuntimeApi(): ElectronRuntimeApi | null {
  if (typeof window === "undefined") return null;
  return (window as unknown as { electronAPI?: ElectronRuntimeApi }).electronAPI ?? null;
}

export default function LocalRuntimeSetupPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const logRef = useRef<HTMLPreElement>(null);

  const [status, setStatus] = useState<RuntimeStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [log, setLog] = useState("");
  const [progressPct, setProgressPct] = useState(0);
  const [progressLabel, setProgressLabel] = useState("");

  const [useOllama, setUseOllama] = useState(false);
  const [ollamaHost, setOllamaHost] = useState("http://127.0.0.1:11434");
  const [openAiKey, setOpenAiKey] = useState("");
  const [openAiTouched, setOpenAiTouched] = useState(false);

  const refreshStatus = useCallback(async () => {
    const api = getRuntimeApi();
    if (!api?.runtimeGetStatus) {
      setStatus(null);
      setLoadingStatus(false);
      return;
    }
    setLoadingStatus(true);
    try {
      const s = await api.runtimeGetStatus();
      setStatus(s);
      setUseOllama(s.useOllamaForced);
      setOllamaHost(s.ollamaHost || "http://127.0.0.1:11434");
    } catch {
      setStatus(null);
    } finally {
      setLoadingStatus(false);
    }
  }, []);

  useEffect(() => {
    void refreshStatus();
  }, [refreshStatus]);

  useEffect(() => {
    const api = getRuntimeApi();
    if (!api?.onRuntimeProgress || !api?.onRuntimeLogLine) return;
    const offP = api.onRuntimeProgress((d) => {
      setProgressPct(typeof d.pct === "number" ? Math.min(100, Math.round(d.pct * 100)) : 0);
      setProgressLabel([d.phase, d.detail].filter(Boolean).join(" — "));
    });
    const offL = api.onRuntimeLogLine((line) => {
      setLog((prev) => (prev + line).slice(-200_000));
    });
    return () => {
      offP?.();
      offL?.();
    };
  }, []);

  useEffect(() => {
    logRef.current?.scrollTo({ top: logRef.current.scrollHeight });
  }, [log]);

  const appendLog = (s: string) => setLog((prev) => (prev + s + "\n").slice(-200_000));

  const notElectron = !getRuntimeApi()?.runtimeGetStatus;

  const runInstallPython = async () => {
    const api = getRuntimeApi();
    if (!api?.runtimeInstallPython) return;
    setBusy("python");
    setProgressPct(0);
    setProgressLabel("");
    try {
      const r = await api.runtimeInstallPython();
      if (r?.ok) {
        toast({
          title: t("runtimeSetup.toastPythonOk"),
          description: r.alreadyHad ? t("runtimeSetup.toastPythonAlready") : t("runtimeSetup.toastPythonInstalled"),
        });
        await refreshStatus();
      } else {
        toast({ title: t("runtimeSetup.errorTitle"), description: r?.error || "—", variant: "destructive" });
      }
    } catch (e) {
      toast({
        title: t("runtimeSetup.errorTitle"),
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    } finally {
      setBusy(null);
      setProgressPct(0);
      setProgressLabel("");
    }
  };

  const runPip = async () => {
    const api = getRuntimeApi();
    if (!api?.runtimePipInstall) return;
    setBusy("pip");
    appendLog("\n--- pip ---\n");
    try {
      const r = await api.runtimePipInstall();
      if (r?.ok) {
        toast({ title: t("runtimeSetup.toastPipOk") });
        await refreshStatus();
      } else {
        toast({
          title: t("runtimeSetup.errorTitle"),
          description: t(`runtimeSetup.errors.${r?.error}`, { defaultValue: r?.error }),
          variant: "destructive",
        });
      }
    } catch (e) {
      toast({
        title: t("runtimeSetup.errorTitle"),
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    } finally {
      setBusy(null);
    }
  };

  const runOllamaPull = async () => {
    const api = getRuntimeApi();
    if (!api?.runtimeOllamaPull) return;
    setBusy("ollama");
    appendLog("\n--- ollama pull ---\n");
    try {
      const r = await api.runtimeOllamaPull();
      if (r?.ok) {
        toast({ title: t("runtimeSetup.toastOllamaOk") });
      } else {
        toast({
          title: t("runtimeSetup.errorTitle"),
          description: t(`runtimeSetup.errors.${r?.error}`, { defaultValue: r?.error }),
          variant: "destructive",
        });
      }
    } catch (e) {
      toast({
        title: t("runtimeSetup.errorTitle"),
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    } finally {
      setBusy(null);
    }
  };

  const saveLlm = async () => {
    const api = getRuntimeApi();
    if (!api?.runtimeSaveLlmSettings) return;
    setBusy("saveLlm");
    try {
      await api.runtimeSaveLlmSettings({
        openAiKey: openAiTouched ? openAiKey : undefined,
        useOllama,
        ollamaHost: ollamaHost.trim() || undefined,
      });
      setOpenAiTouched(false);
      setOpenAiKey("");
      toast({ title: t("runtimeSetup.toastLlmSaved") });
      await refreshStatus();
    } catch (e) {
      toast({
        title: t("runtimeSetup.errorTitle"),
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    } finally {
      setBusy(null);
    }
  };

  const restartEngine = async () => {
    const api = getRuntimeApi();
    if (!api?.runtimeRestartEngine) return;
    setBusy("restart");
    try {
      const r = await api.runtimeRestartEngine();
      if (r?.ok) {
        toast({ title: t("runtimeSetup.toastRestartOk") });
      } else {
        toast({
          title: t("runtimeSetup.errorTitle"),
          description: r?.error || "—",
          variant: "destructive",
        });
      }
      await refreshStatus();
    } catch (e) {
      toast({
        title: t("runtimeSetup.errorTitle"),
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    } finally {
      setBusy(null);
    }
  };

  if (notElectron) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 space-y-4">
        <Button type="button" variant="outline" size="sm" onClick={() => navigate(-1)} className="gap-2">
          <ArrowLeft className="h-4 w-4" />
          {t("runtimeSetup.back")}
        </Button>
        <p className="text-sm text-foreground/80">{t("runtimeSetup.onlyElectron")}</p>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 pb-24 space-y-6 text-foreground">
      <div className="flex flex-col gap-3">
        <Button type="button" variant="outline" size="sm" onClick={() => navigate(-1)} className="w-fit gap-2">
          <ArrowLeft className="h-4 w-4" />
          {t("runtimeSetup.back")}
        </Button>
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">{t("runtimeSetup.title")}</h1>
        <p className="text-sm text-foreground/75 max-w-2xl leading-relaxed">{t("runtimeSetup.intro")}</p>
      </div>

      {loadingStatus ? (
        <div className="flex items-center gap-2 text-foreground/70">
          <Loader2 className="h-5 w-5 animate-spin" />
          {t("runtimeSetup.loading")}
        </div>
      ) : null}

      {busy && progressLabel ? (
        <div className="space-y-2">
          <Progress value={progressPct} className="h-2" />
          <p className="text-xs text-foreground/65 font-mono truncate">{progressLabel}</p>
        </div>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Package className="h-5 w-5 text-primary" />
            {t("runtimeSetup.pythonTitle")}
          </CardTitle>
          <CardDescription>{t("runtimeSetup.pythonDesc")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <ul className="text-xs text-foreground/70 space-y-1 font-mono break-all">
            <li>
              API root: {status?.apiRoot ?? "—"}
            </li>
            <li>
              requirements.txt: {status?.requirementsFileExists ? "ok" : "—"}
            </li>
            <li>
              Python (app): {status?.embeddedPythonPath ?? t("runtimeSetup.systemPython")}
            </li>
            <li>uvicorn import: {status?.pipUvicornOk ? "ok" : "—"}</li>
          </ul>
          <div className="flex flex-wrap gap-2">
            {status?.supportsEmbeddedPythonDownload ? (
              <Button type="button" disabled={!!busy} onClick={() => void runInstallPython()} className="gap-2">
                {busy === "python" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
                {t("runtimeSetup.downloadPython")}
              </Button>
            ) : (
              <p className="text-sm text-amber-700 dark:text-amber-300">{t("runtimeSetup.pythonManualOnly")}</p>
            )}
            <Button type="button" variant="secondary" disabled={!!busy} onClick={() => void runPip()} className="gap-2">
              {busy === "pip" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Package className="h-4 w-4" />}
              {t("runtimeSetup.pipInstall")}
            </Button>
            <Button type="button" variant="outline" size="sm" onClick={() => void refreshStatus()} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              {t("runtimeSetup.refresh")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Server className="h-5 w-5 text-primary" />
            {t("runtimeSetup.ollamaTitle")}
          </CardTitle>
          <CardDescription>{t("runtimeSetup.ollamaDesc")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-xs text-foreground/70">
            {t("runtimeSetup.ollamaCli")}:{" "}
            <span className={status?.ollamaCliAvailable ? "text-emerald-600 dark:text-emerald-400" : ""}>
              {status?.ollamaCliAvailable ? t("runtimeSetup.found") : t("runtimeSetup.notFound")}
            </span>
          </p>
          <p className="text-xs text-foreground/60 font-mono">
            {(status?.defaultOllamaModels ?? []).join(", ")}
          </p>
          <div className="flex flex-wrap gap-2">
            <Button type="button" variant="secondary" disabled={!!busy} onClick={() => void runOllamaPull()} className="gap-2">
              {busy === "ollama" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
              {t("runtimeSetup.ollamaPull")}
            </Button>
            <Button type="button" variant="link" className="px-0 h-auto" asChild>
              <a href="https://ollama.com/download" target="_blank" rel="noreferrer">
                {t("runtimeSetup.ollamaDownloadPage")}
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-5 w-5 text-primary" />
            {t("runtimeSetup.llmTitle")}
          </CardTitle>
          <CardDescription>{t("runtimeSetup.llmDesc")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-xs text-foreground/65 break-all">
            {t("runtimeSetup.userEnv")}: {status?.userEnvPath}
          </p>
          <div className="space-y-2">
            <Label htmlFor="openai-key">{t("runtimeSetup.openAiKey")}</Label>
            <Input
              id="openai-key"
              type="password"
              autoComplete="off"
              placeholder={status?.openAiKeyConfigured ? "••••••••" : ""}
              value={openAiKey}
              onChange={(e) => {
                setOpenAiKey(e.target.value);
                setOpenAiTouched(true);
              }}
              className="font-mono text-sm"
            />
            <p className="text-xs text-foreground/60">{t("runtimeSetup.openAiHint")}</p>
          </div>
          <div className="flex items-center gap-3">
            <Switch id="use-ollama" checked={useOllama} onCheckedChange={setUseOllama} />
            <Label htmlFor="use-ollama">{t("runtimeSetup.forceOllama")}</Label>
          </div>
          <div className="space-y-2">
            <Label htmlFor="ollama-host">{t("runtimeSetup.ollamaHost")}</Label>
            <Input
              id="ollama-host"
              value={ollamaHost}
              onChange={(e) => setOllamaHost(e.target.value)}
              className="font-mono text-sm"
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => void saveLlm()} disabled={!!busy} className="gap-2">
              {busy === "saveLlm" ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {t("runtimeSetup.saveLlm")}
            </Button>
            <Button type="button" variant="outline" onClick={() => void restartEngine()} disabled={!!busy} className="gap-2">
              {busy === "restart" ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              {t("runtimeSetup.restartEngine")}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-lg">{t("runtimeSetup.logTitle")}</CardTitle>
          <CardDescription>{t("runtimeSetup.logDesc")}</CardDescription>
        </CardHeader>
        <CardContent>
          <pre
            ref={logRef}
            className={cn(
              "max-h-64 overflow-auto rounded-md border border-border bg-muted/40 p-3 text-[11px] font-mono",
              "text-foreground/85 whitespace-pre-wrap break-all",
            )}
          >
            {log || t("runtimeSetup.logEmpty")}
          </pre>
        </CardContent>
      </Card>

      <p className="text-xs text-foreground/55">
        <Link to="/settings" className="text-primary underline-offset-4 hover:underline">
          {t("runtimeSetup.backToSettings")}
        </Link>
      </p>
    </div>
  );
}
