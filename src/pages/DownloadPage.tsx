/**
 * Tela HTTPS para download da ferramenta Pulso.
 * Especificação: docs/tela-download-https.md
 * Elementos docs: 23 (glass), 24 (botão download), 22 (botão padrão), 12 (Get Started), 14 (card analytics), 13 (card menu), 01 (loader).
 */
import { useState } from "react";
import { Link } from "react-router-dom";
import {
  Shield,
  Zap,
  Workflow,
  CheckCircle2,
  FileText,
  HelpCircle,
  ChevronRight,
} from "lucide-react";
import "@/styles/components-showcase.css";
import { DownloadProgressCard } from "@/components/ui/DownloadProgressCard";

type DownloadOS = "windows" | "linux" | "mac";

const DOWNLOAD_URL_WINDOWS =
  import.meta.env.VITE_DOWNLOAD_URL_WINDOWS ||
  "https://github.com/your-org/PulsoFrontend/releases/latest/download/Pulso-Setup.exe";

const DOWNLOAD_URL_LINUX =
  import.meta.env.VITE_DOWNLOAD_URL_LINUX ||
  "https://github.com/your-org/PulsoFrontend/releases/latest/download/Pulso.AppImage";

const DOWNLOAD_URL_MAC =
  import.meta.env.VITE_DOWNLOAD_URL_MAC ||
  "https://github.com/your-org/PulsoFrontend/releases/latest/download/Pulso.dmg";

const DOWNLOAD_URLS: Record<DownloadOS, string> = {
  windows: DOWNLOAD_URL_WINDOWS,
  linux: DOWNLOAD_URL_LINUX,
  mac: DOWNLOAD_URL_MAC,
};

const DOWNLOAD_METADATA: Record<DownloadOS, { fileName: string; fileSize: string }> =
  {
    windows: { fileName: "Pulso-Setup.exe", fileSize: "85 MB" },
    linux: { fileName: "Pulso.AppImage", fileSize: "90 MB" },
    mac: { fileName: "Pulso.dmg", fileSize: "95 MB" },
  };

export default function DownloadPage() {
  const [preparing, setPreparing] = useState(false);
  const [currentOs, setCurrentOs] = useState<DownloadOS>("windows");

  const handleDownload = (os: DownloadOS) => {
    setCurrentOs(os);
    setPreparing(true);
    window.open(DOWNLOAD_URLS[os], "_blank", "noopener,noreferrer");
  };

  const handleClose = () => setPreparing(false);

  return (
    <div className="min-h-screen text-foreground overflow-x-hidden relative bg-background">
      {/* Card de progresso — glassmorphism (docs/download-progress-card.md) */}
      {preparing && (
        <DownloadProgressCard
          fileName="Pulso-Setup.exe"
          fileSize="85 MB"
          onClose={handleClose}
          onComplete={() => setTimeout(handleClose, 600)}
          durationMs={2200}
        />
      )}

      {/* Header — Elemento 23 Glass */}
      <header className="sticky top-0 z-40 flex items-center justify-between px-4 sm:px-6 py-4 glass-strong border-b border-border sticky-below-electron">
        <Link to="/" className="flex items-center gap-2">
          <img
            src={import.meta.env.BASE_URL + "App.png"}
            alt="Pulso"
            className="h-10 w-10 object-contain"
          />
          <span className="text-lg font-semibold text-foreground">
            Pulso Tech
          </span>
        </Link>
        <div className="flex items-center gap-2">
          <Link
            to="/auth"
            className="btn-aurora text-white hover:opacity-90 border-0 px-4 py-2 rounded-full text-sm font-medium"
          >
            Entrar
          </Link>
        </div>
      </header>

      <main id="main-content">
        {/* Hero — Elemento 01 decorativo + CTA Elemento 24 */}
        <section className="relative max-w-4xl mx-auto px-6 py-16 sm:py-24 text-center">
          <div
            className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-30"
            aria-hidden
          >
            <div className="showcase-loader1-bg">
              <div className="showcase-loader1" />
            </div>
          </div>
          <div className="relative z-10">
            <img
              src={import.meta.env.BASE_URL + "App.png"}
              alt=""
              className="h-20 w-20 sm:h-24 sm:w-24 mx-auto object-contain"
            />
            <h1
              className="mt-6 text-4xl sm:text-5xl font-bold text-foreground"
              style={{
                background:
                  "linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--secondary)) 100%)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}
            >
              Baixe o Pulso
            </h1>
            <p className="mt-4 text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto">
              Assistente de código e dados na sua máquina. Rápido, seguro e
              offline quando precisar.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row sm:justify-center">
              <button
                type="button"
                onClick={() => handleDownload("windows")}
                className="showcase-download-report-btn shrink-0 text-foreground"
                aria-label="Baixar instalador do Pulso para Windows"
              >
                <div className="showcase-docs">
                  <DocIcon />
                  <span>Baixar para Windows</span>
                </div>
                <div className="showcase-download" aria-hidden>
                  <DownloadIcon />
                </div>
              </button>
              <button
                type="button"
                onClick={() => handleDownload("linux")}
                className="showcase-download-report-btn shrink-0 text-foreground"
                aria-label="Baixar instalador do Pulso para Linux"
              >
                <div className="showcase-docs">
                  <DocIcon />
                  <span>Baixar para Linux</span>
                </div>
                <div className="showcase-download" aria-hidden>
                  <DownloadIcon />
                </div>
              </button>
              <button
                type="button"
                onClick={() => handleDownload("mac")}
                className="showcase-download-report-btn shrink-0 text-foreground"
                aria-label="Baixar instalador do Pulso para macOS"
              >
                <div className="showcase-docs">
                  <DocIcon />
                  <span>Baixar para macOS</span>
                </div>
                <div className="showcase-download" aria-hidden>
                  <DownloadIcon />
                </div>
              </button>
            </div>
            <p className="mt-6 text-sm text-muted-foreground">
              Download via HTTPS. Windows, Linux e macOS. Verifique a origem
              antes de instalar.
            </p>
          </div>
        </section>

        {/* Por que baixar? — 3 cards Elemento 23 Glass */}
        <section className="max-w-[1400px] mx-auto px-6 py-16">
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">
            Por que baixar?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: Shield,
                title: "Seguro",
                text: "Conexão HTTPS e controle dos seus dados.",
              },
              {
                icon: Zap,
                title: "Rápido",
                text: "Roda local. Menos latência, mais produtividade.",
              },
              {
                icon: Workflow,
                title: "Feito para devs",
                text: "Pulso CSA, FinOps e Data & AI no mesmo lugar.",
              },
            ].map(({ icon: Icon, title, text }) => (
              <div
                key={title}
                className="glass rounded-xl border border-border p-6"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary mb-4">
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold text-foreground">{title}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Recursos — Card estilo Elemento 14 + lista */}
        <section className="max-w-[1400px] mx-auto px-6 py-16">
          <h2 className="text-2xl font-bold text-foreground mb-8 text-center">
            O que você tem no Pulso
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
            <div className="glass rounded-xl border border-border p-6 card-bottom-glow">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/20 text-primary">
                    <Workflow className="h-4 w-4" />
                  </div>
                  <h3 className="text-lg font-semibold text-foreground">
                    Recursos incluídos
                  </h3>
                </div>
                <span className="flex items-center gap-1 rounded-full bg-success/10 px-2 py-1 text-xs font-medium text-success">
                  <span className="h-1.5 w-1.5 rounded-full bg-success" />
                  Incluído
                </span>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Pulso CSA, FinOps e Data & AI em um único app.
              </p>
              <Link
                to="/auth"
                className="inline-flex items-center gap-1 rounded-lg bg-primary/20 px-3 py-2 text-sm font-medium text-primary hover:bg-primary/30 transition-colors"
              >
                Ver detalhes
                <ChevronRight className="h-4 w-4" />
              </Link>
            </div>
            <ul className="space-y-3">
              {[
                "Pulso CSA (estrutura de projeto)",
                "FinOps (custos cloud)",
                "Data & AI (métricas e ML)",
                "Temas claro/escuro",
                "Atualizações automáticas",
              ].map((item) => (
                <li
                  key={item}
                  className="flex items-center gap-3 text-foreground"
                >
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-primary" />
                  <span className="text-sm">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* Comece agora — Elemento 12 + Elemento 22 */}
        <section className="max-w-3xl mx-auto px-6 py-16 text-center">
          <p className="text-muted-foreground mb-6">
            Já tem conta? Entre e acesse o dashboard.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/auth"
              className="relative inline-flex items-center justify-center gap-2 rounded-xl bg-gray-900 px-6 py-3 font-semibold text-white transition-all duration-200 hover:bg-gray-800 hover:shadow-lg hover:-translate-y-0.5 hover:shadow-primary/20 border border-border"
            >
              <span className="absolute inset-0 rounded-xl bg-gradient-to-r from-primary/30 via-secondary/30 to-primary/30 blur-lg opacity-60 -z-10" />
              Entrar
              <ChevronRight className="h-4 w-4" />
            </Link>
            <a
              href="https://docs.pulso.tech"
              target="_blank"
              rel="noopener noreferrer"
              className="btn-padrao-gradient text-white text-sm font-medium px-5 py-2.5"
            >
              Documentação
            </a>
          </div>
        </section>

        {/* Footer — links mínimos */}
        <footer className="border-t border-border bg-card/30 py-6 px-6">
          <div className="max-w-[1400px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <img
                src={import.meta.env.BASE_URL + "App.png"}
                alt=""
                className="h-8 w-8 object-contain"
              />
              <span className="text-sm font-medium text-foreground">
                Pulso Tech
              </span>
            </div>
            <nav className="flex flex-wrap items-center justify-center gap-4 text-sm text-muted-foreground">
              <a
                href="https://docs.pulso.tech"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-primary transition-colors flex items-center gap-1"
              >
                <FileText className="h-4 w-4" />
                Documentação
              </a>
              <a
                href="mailto:suporte@pulso.tech"
                className="hover:text-primary transition-colors flex items-center gap-1"
              >
                <HelpCircle className="h-4 w-4" />
                Suporte
              </a>
              <Link to="/" className="hover:text-primary transition-colors">
                Termos de uso
              </Link>
            </nav>
          </div>
          <p className="text-center text-xs text-muted-foreground mt-4">
            © {new Date().getFullYear()} Pulso Tech. Download seguro via HTTPS.
          </p>
        </footer>
      </main>
    </div>
  );
}

function DocIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width={22}
      height={22}
      stroke="currentColor"
      strokeWidth={2}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1={16} y1={13} x2={8} y2={13} />
      <line x1={16} y1={17} x2={8} y2={17} />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  );
}

function DownloadIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      width={26}
      height={26}
      stroke="currentColor"
      strokeWidth={2}
      fill="none"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1={12} y1={15} x2={12} y2={3} />
    </svg>
  );
}
