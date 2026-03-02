import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import ThemeSelector from "@/components/ThemeSelector";
import { UploadDemoModal } from "@/components/UploadDemoModal";
import { Download } from "lucide-react";
import "@/styles/components-showcase.css";

const Index = () => {
  const navigate = useNavigate();
  const [uploadModalOpen, setUploadModalOpen] = useState(false);

  return (
    <div className="min-h-screen text-foreground overflow-x-hidden relative z-10">
      {/* Header — efeito glass */}
      <header className="sticky top-0 z-40 flex items-center justify-between px-6 py-4 glass-strong border-b border-border sticky-below-electron">
        <img
          src={import.meta.env.BASE_URL + "App.png"}
          alt="Pulso"
          className="h-10 w-10 object-contain"
        />
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => navigate("/download")}>
            Baixar
          </Button>
          <button
            type="button"
            onClick={() => setUploadModalOpen(true)}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-transparent text-foreground transition-colors hover:bg-muted/80 hover:border-primary/40"
            aria-label="Ver exemplo de download"
          >
            <Download className="h-5 w-5" />
          </button>
          <ThemeSelector />
          <Button onClick={() => navigate("/auth?mode=login")} className="btn-aurora text-white hover:opacity-90 border-0">
            Entrar
          </Button>
        </div>
      </header>

      <UploadDemoModal open={uploadModalOpen} onOpenChange={setUploadModalOpen} />

      {/* Conteúdo longo - todos os componentes */}
      <main className="max-w-[1600px] mx-auto px-6 py-12 space-y-20">
        {/* Seção: Telas de Carregamento */}
        <section>
          <h2 className="text-2xl font-bold mb-8 text-foreground">Telas de Carregamento</h2>
          <div className="flex flex-wrap gap-12 items-start justify-start">
            {/* Loader 1 - Anel fixo no fundo (sem texto) */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border relative overflow-hidden min-h-[280px]">
              <span className="text-sm font-medium text-muted-foreground relative z-10">Loader 1</span>
              <div className="showcase-loader1-bg">
                <div className="showcase-loader1" aria-hidden />
              </div>
              <p className="text-xs text-muted-foreground relative z-10">Anel ampliado no fundo</p>
            </div>

            {/* Loader 2 - Words */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Loader 2</span>
              <div className="showcase-loader2-card">
                <div className="showcase-loader2">
                  <p>loading</p>
                  <div className="showcase-loader2-words">
                    <span className="showcase-loader2-word">buttons</span>
                    <span className="showcase-loader2-word">forms</span>
                    <span className="showcase-loader2-word">switches</span>
                    <span className="showcase-loader2-word">cards</span>
                    <span className="showcase-loader2-word">buttons</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Loader 3 - Liquid */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Loader 3</span>
              <div className="showcase-liquid-loader">
                <div className="showcase-loading-text">
                  Loading<span className="showcase-dot">.</span><span className="showcase-dot">.</span><span className="showcase-dot">.</span>
                </div>
                <div className="showcase-loader-track">
                  <div className="showcase-liquid-fill" />
                </div>
              </div>
            </div>

            {/* Loader 4 - Documents */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Loader 4</span>
              <div className="showcase-docs-loader">
                <div>
                  <ul>
                    {[1, 2, 3, 4, 5, 6].map((i) => (
                      <li key={i}>
                        <svg fill="currentColor" viewBox="0 0 90 120">
                          <path d="M90,0 L90,120 L11,120 C4.92486775,120 0,115.075132 0,109 L0,11 C0,4.92486775 4.92486775,0 11,0 L90,0 Z M71.5,81 L18.5,81 C17.1192881,81 16,82.1192881 16,83.5 C16,84.8254834 17.0315359,85.9100387 18.3356243,85.9946823 L18.5,86 L71.5,86 C72.8807119,86 74,84.8807119 74,83.5 C74,82.1745166 72.9684641,81.0899613 71.6643757,81.0053177 L71.5,81 Z M71.5,57 L18.5,57 C17.1192881,57 16,58.1192881 16,59.5 C16,60.8254834 17.0315359,61.9100387 18.3356243,61.9946823 L18.5,62 L71.5,62 C72.8807119,62 74,60.8807119 74,59.5 C74,58.1192881 72.8807119,57 71.5,57 Z M71.5,33 L18.5,33 C17.1192881,33 16,34.1192881 16,35.5 C16,36.8254834 17.0315359,37.9100387 18.3356243,37.9946823 L18.5,38 L71.5,38 C72.8807119,38 74,36.8807119 74,35.5 C74,34.1192881 72.8807119,33 71.5,33 Z" />
                        </svg>
                      </li>
                    ))}
                  </ul>
                </div>
                <span>Loading</span>
              </div>
            </div>

            {/* Loader 5 - Typewriter */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Loader 5</span>
              <div className="showcase-typewriter">
                <div className="showcase-slide"><i /></div>
                <div className="showcase-paper" />
                <div className="showcase-keyboard" />
              </div>
            </div>

            {/* Loader 6 - Spinner gradient */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Loader 6</span>
              <div className="showcase-spinner-gradient">
                <div className="showcase-spinner-inner" />
              </div>
            </div>
          </div>
        </section>

        {/* Seção: Botões */}
        <section>
          <h2 className="text-2xl font-bold mb-8 text-foreground">Botões</h2>
          <div className="flex flex-wrap gap-8 items-center justify-start">
            {/* Botão 1 - Sparkle */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Botão 1</span>
              <div className="relative">
                <button className="showcase-sparkle-btn" type="button">
                  <span className="showcase-spark" />
                  <span className="absolute inset-[0.1em] rounded-[100px] bg-background/80" />
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14.187 8.096L15 5.25L15.813 8.096C16.0231 8.83114 16.4171 9.50062 16.9577 10.0413C17.4984 10.5819 18.1679 10.9759 18.903 11.186L21.75 12L18.904 12.813C18.1689 13.0231 17.4994 13.4171 16.9587 13.9577C16.4181 14.4984 16.0241 15.1679 15.814 15.903L15 18.75L14.187 15.904C13.9769 15.1689 13.5829 14.4994 13.0423 13.9587C12.5016 13.4181 11.8321 13.0241 11.097 12.814L8.25 12L11.096 11.187C11.8311 10.9769 12.5006 10.5829 13.0413 10.0423C13.5819 9.50162 13.9759 8.83214 14.186 8.097L14.187 8.096Z" />
                  </svg>
                  <span className="relative z-10">Generate Site</span>
                </button>
              </div>
            </div>

            {/* Botão 2 - Save */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Botão 2</span>
              <button className="showcase-save-btn" type="button" aria-label="save">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" strokeLinejoin="round" strokeLinecap="round" strokeWidth="2" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                  <path d="m19,21H5c-1.1,0-2-.9-2-2V5c0-1.1.9-2,2-2h11l5,5v11c0,1.1-.9,2-2,2Z" data-path="box" />
                  <path d="M7 3L7 8L15 8" data-path="line-top" />
                  <path d="M17 20L17 13L7 13L7 20" data-path="line-bottom" />
                </svg>
              </button>
            </div>

            {/* Botão 3 - Documents */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Botão 3</span>
              <button className="showcase-docs-btn" type="button">
                <span className="showcase-folder-container">
                  <svg className="showcase-file-back" width="146" height="113" viewBox="0 0 146 113" fill="none">
                    <path d="M0 4C0 1.79086 1.79086 0 4 0H50.3802C51.8285 0 53.2056 0.627965 54.1553 1.72142L64.3303 13.4371C65.2799 14.5306 66.657 15.1585 68.1053 15.1585H141.509C143.718 15.1585 145.509 16.9494 145.509 19.1585V109C145.509 111.209 143.718 113 141.509 113H3.99999C1.79085 113 0 111.209 0 109V4Z" fill="url(#paint0_linear_117_4)" />
                    <defs>
                      <linearGradient id="paint0_linear_117_4" x1="0" y1="0" x2="72.93" y2="95.4804" gradientUnits="userSpaceOnUse">
                        <stop stopColor="#8F88C2" />
                        <stop offset="1" stopColor="#5C52A2" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <svg className="showcase-file-page" width="88" height="99" viewBox="0 0 88 99" fill="none">
                    <rect width="88" height="99" fill="url(#paint0_linear_117_6)" />
                    <defs>
                      <linearGradient id="paint0_linear_117_6" x1="0" y1="0" x2="81" y2="160.5" gradientUnits="userSpaceOnUse">
                        <stop stopColor="white" />
                        <stop offset="1" stopColor="#686868" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <svg className="showcase-file-front" width="160" height="79" viewBox="0 0 160 79" fill="none">
                    <path d="M0.29306 12.2478C0.133905 9.38186 2.41499 6.97059 5.28537 6.97059H30.419H58.1902C59.5751 6.97059 60.9288 6.55982 62.0802 5.79025L68.977 1.18034C70.1283 0.410771 71.482 0 72.8669 0H77H155.462C157.87 0 159.733 2.1129 159.43 4.50232L150.443 75.5023C150.19 77.5013 148.489 79 146.474 79H7.78403C5.66106 79 3.9079 77.3415 3.79019 75.2218L0.29306 12.2478Z" fill="url(#paint0_linear_117_5)" />
                    <defs>
                      <linearGradient id="paint0_linear_117_5" x1="38.7619" y1="8.71323" x2="66.9106" y2="82.8317" gradientUnits="userSpaceOnUse">
                        <stop stopColor="#C3BBFF" />
                        <stop offset="1" stopColor="#51469A" />
                      </linearGradient>
                    </defs>
                  </svg>
                </span>
                <p className="text-foreground text-sm font-semibold">Documents</p>
              </button>
            </div>

            {/* Botão 4 - Delete */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Botão 4</span>
              <button className="showcase-delete-btn" type="button">
                <svg className="showcase-delete-svg" viewBox="0 0 448 512" fill="currentColor">
                  <path d="M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z" />
                </svg>
              </button>
            </div>

            {/* Botão 5 - Project Structure */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Botão 5</span>
              <div className="relative group inline-block">
                <div className="bg-card py-2 rounded-md shadow-lg hover:cursor-pointer flex justify-center items-center gap-4 px-4 border border-border">
                  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 14" height="25" width="25">
                    <path fill="#FFA000" d="M16.2 1.75H8.1L6.3 0H1.8C0.81 0 0 0.7875 0 1.75V12.25C0 13.2125 0.81 14 1.8 14H15.165L18 9.1875V3.5C18 2.5375 17.19 1.75 16.2 1.75Z" />
                    <path fill="#FFCA28" d="M16.2 2H1.8C0.81 2 0 2.77143 0 3.71429V12.2857C0 13.2286 0.81 14 1.8 14H16.2C17.19 14 18 13.2286 18 12.2857V3.71429C18 2.77143 17.19 2 16.2 2Z" />
                  </svg>
                  <p className="text-foreground">Project Structure</p>
                </div>
                <div className="absolute left-0 mt-2 w-64 bg-card border border-border rounded-md shadow-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                  <ul className="p-4 space-y-1 text-sm text-muted-foreground">
                    <li className="py-1">📁 src</li>
                    <li className="pl-4 py-1">📁 app</li>
                    <li className="pl-8 py-1">📄 layout.js</li>
                    <li className="pl-8 py-1">📄 page.js</li>
                    <li className="pl-4 py-1">📁 components</li>
                    <li className="pl-8 py-1">📄 header.js</li>
                    <li className="pl-8 py-1">📄 footer.js</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Seção: Área Chats / Cards */}
        <section>
          <h2 className="text-2xl font-bold mb-8 text-foreground">Área Chats / Cards</h2>
          <div className="flex flex-wrap gap-10 items-start justify-start">
            {/* Card Menu */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Menu Card</span>
              <div className="showcase-menu-card">
                <ul className="showcase-list">
                  <li className="showcase-element">
                    <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" />
                      <path d="m15 5 4 4" />
                    </svg>
                    <p className="label font-semibold">Rename</p>
                  </li>
                  <li className="showcase-element">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M2 21a8 8 0 0 1 13.292-6" />
                      <circle r="5" cy="8" cx="10" />
                      <path d="M19 16v6" />
                      <path d="M22 19h-6" />
                    </svg>
                    <p className="label font-semibold">Add Member</p>
                  </li>
                </ul>
                <div className="showcase-separator" />
                <ul className="showcase-list">
                  <li className="showcase-element">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                      <circle r="3" cy="12" cx="12" />
                    </svg>
                    <p className="label font-semibold">Settings</p>
                  </li>
                  <li className="showcase-element delete">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M3 6h18" />
                      <path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" />
                      <path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                      <line y2="17" y1="11" x2="10" x1="10" />
                      <line y2="17" y1="11" x2="14" x1="14" />
                    </svg>
                    <p className="label font-semibold">Delete</p>
                  </li>
                </ul>
                <div className="showcase-separator" />
                <ul className="showcase-list">
                  <li className="showcase-element">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M18 21a8 8 0 0 0-16 0" />
                      <circle r="5" cy="8" cx="10" />
                      <path d="M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3" />
                    </svg>
                    <p className="label font-semibold">Team Access</p>
                  </li>
                </ul>
              </div>
            </div>

            {/* Performance Analytics Card */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Analytics Card</span>
              <div className="group relative flex w-80 flex-col rounded-xl bg-slate-950 p-4 shadow-2xl transition-all duration-300 hover:scale-[1.02] border border-border">
                <div className="mb-4 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[linear-gradient(135deg,#2E1A47,#4B2F7F,#6A4BCF,#8E78E6,#B89AF6)]">
                      <svg className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                      </svg>
                    </div>
                    <h3 className="text-sm font-semibold text-white">Performance Analytics</h3>
                  </div>
                  <span className="flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-500">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                    Live
                  </span>
                </div>
                <div className="mb-4 grid grid-cols-2 gap-4">
                  <div className="rounded-lg bg-slate-900/50 p-3">
                    <p className="text-xs font-medium text-slate-400">Total Views</p>
                    <p className="text-lg font-semibold text-white">24.5K</p>
                    <span className="text-xs font-medium text-emerald-500">+12.3%</span>
                  </div>
                  <div className="rounded-lg bg-slate-900/50 p-3">
                    <p className="text-xs font-medium text-slate-400">Conversions</p>
                    <p className="text-lg font-semibold text-white">1.2K</p>
                    <span className="text-xs font-medium text-emerald-500">+8.1%</span>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-400">Last 7 days</span>
                  <button className="flex items-center gap-1 rounded-lg bg-[linear-gradient(90deg,#2E1A47,#4B2F7F,#6A4BCF,#8E78E6,#B89AF6)] px-3 py-1 text-xs font-medium text-white">
                    View Details
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Sales Card */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Sales Card</span>
              <div className="showcase-sales-card">
                <div className="showcase-sales-title">
                  <span>
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" fill="currentColor" height="20" viewBox="0 0 1792 1792">
                      <path d="M1362 1185q0 153-99.5 263.5t-258.5 136.5v175q0 14-9 23t-23 9h-135q-13 0-22.5-9.5t-9.5-22.5v-175q-66-9-127.5-31t-101.5-44.5-74-48-46.5-37.5-17.5-18q-17-21-2-41l103-135q7-10 23-12 15-2 24 9l2 2q113 99 243 125 37 8 74 8 81 0 142.5-43t61.5-122q0-28-15-53t-33.5-42-58.5-37.5-66-32-80-32.5q-39-16-61.5-25t-61.5-26.5-62.5-31-56.5-35.5-53.5-42.5-43.5-49-35.5-58-21-66.5-8.5-78q0-138 98-242t255-134v-180q0-13 9.5-22.5t22.5-9.5h135q14 0 23 9t9 23v176q57 6 110.5 23t87 33.5 63.5 37.5 39 29 15 14q17 18 5 38l-81 146q-8 15-23 16-14 3-27-7z" />
                    </svg>
                  </span>
                  <p className="title-text ml-2 text-lg text-foreground">Sales</p>
                  <p className="percent ml-2 text-success font-semibold flex items-center gap-1">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1792 1792" fill="currentColor" height="20" width="20">
                      <path d="M1408 1216q0 26-19 45t-45 19h-896q-26 0-45-19t-19-45 19-45l448-448q19-19 45-19t45 19l448 448q19 19 19 45z" />
                    </svg>
                    20%
                  </p>
                </div>
                <div className="data">
                  <p className="mt-4 mb-4 text-foreground text-3xl font-bold">39,500</p>
                  <div className="showcase-sales-range">
                    <div className="showcase-sales-fill" />
                  </div>
                </div>
              </div>
            </div>

            {/* Post Views Card */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Post Views</span>
              <div className="showcase-postviews-grid">
                <div className="showcase-postviews-area" />
                <div className="showcase-postviews-wrap">
                  <div className="showcase-postviews-card">
                    <div className="showcase-postviews-card-bg" />
                    <div className="showcase-postviews-content">
                      <header className="mb-3">
                        <p className="text-xs text-muted-foreground">Post views</p>
                        <div className="flex items-center gap-2 text-xl font-bold text-foreground">
                          <span>2,012</span>
                          <span className="text-xs text-muted-foreground font-normal">views</span>
                        </div>
                      </header>
                      <div className="h-24 bg-muted/30 rounded-lg mb-4" />
                      <footer className="flex justify-between text-xs text-muted-foreground">
                        <span>8am</span>
                        <span>10am</span>
                        <span>12pm</span>
                        <span>2pm</span>
                        <span>4pm</span>
                        <span>6pm</span>
                      </footer>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Browser Loader (chat loading) */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Chat Loading</span>
              <div className="showcase-browser-loader">
                <svg viewBox="0 0 900 900" xmlns="http://www.w3.org/2000/svg" preserveAspectRatio="none" className="w-full h-full">
                  <defs>
                    <linearGradient id="traceGradient1" x1="250" y1="120" x2="100" y2="200" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stopColor="#00ccff" stopOpacity="1" />
                      <stop offset="100%" stopColor="#00ccff" stopOpacity="0.5" />
                    </linearGradient>
                    <linearGradient id="traceGradient2" x1="650" y1="120" x2="800" y2="300" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stopColor="#00ccff" stopOpacity="1" />
                      <stop offset="100%" stopColor="#00ccff" stopOpacity="0.5" />
                    </linearGradient>
                    <linearGradient id="traceGradient3" x1="250" y1="380" x2="400" y2="400" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stopColor="#00ccff" stopOpacity="1" />
                      <stop offset="100%" stopColor="#00ccff" stopOpacity="0.5" />
                    </linearGradient>
                    <linearGradient id="traceGradient4" x1="650" y1="120" x2="500" y2="100" gradientUnits="userSpaceOnUse">
                      <stop offset="0%" stopColor="#00ccff" stopOpacity="1" />
                      <stop offset="100%" stopColor="#00ccff" stopOpacity="0.5" />
                    </linearGradient>
                  </defs>
                  <g id="grid">
                    <g>
                      {[0, 100, 200, 300, 400, 500, 600, 700, 800, 900].map((x) => (
                        <line key={x} x1={x} y1="0" x2={x} y2="100%" className="showcase-grid-line" />
                      ))}
                    </g>
                    <g>
                      {[100, 200, 300, 400, 500, 600, 700, 800].map((y) => (
                        <line key={y} x1="0" y1={y} x2="100%" y2={y} className="showcase-grid-line" />
                      ))}
                    </g>
                  </g>
                  <g id="browser" transform="translate(0, 200)">
                    <rect x="250" y="120" width="400" height="260" rx="8" ry="8" className="showcase-browser-frame" />
                    <rect x="250" y="120" width="400" height="30" rx="8" ry="8" className="showcase-browser-top" />
                    <text x="450" y="140" textAnchor="middle" className="showcase-loading-text">Loading...</text>
                    <rect x="270" y="160" width="360" height="20" className="showcase-skeleton" rx="4" ry="4" />
                    <rect x="270" y="190" width="200" height="15" className="showcase-skeleton" rx="4" ry="4" />
                    <rect x="270" y="215" width="300" height="15" className="showcase-skeleton" rx="4" ry="4" />
                    <rect x="270" y="240" width="360" height="90" className="showcase-skeleton" rx="4" ry="4" />
                    <rect x="270" y="340" width="180" height="20" className="showcase-skeleton" rx="4" ry="4" />
                  </g>
                  <g id="traces" transform="translate(0, 200)">
                    <path d="M100 300 H250 V120" className="showcase-trace-flow" stroke="url(#traceGradient1)" />
                    <path d="M800 200 H650 V380" className="showcase-trace-flow" stroke="url(#traceGradient2)" />
                    <path d="M400 520 V380 H250" className="showcase-trace-flow" stroke="url(#traceGradient3)" />
                    <path d="M500 50 V120 H650" className="showcase-trace-flow" stroke="url(#traceGradient4)" />
                  </g>
                </svg>
              </div>
            </div>
          </div>
        </section>

        {/* Seção: Barra de Busca */}
        <section>
          <h2 className="text-2xl font-bold mb-8 text-foreground">Barra de Busca</h2>
          <div className="flex flex-wrap gap-8 items-center justify-start">
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border relative overflow-visible">
              <span className="text-sm font-medium text-muted-foreground">Search</span>
              <div className="showcase-search-grid" aria-hidden />
              <div className="showcase-search-poda" id="poda">
                <div className="showcase-search-glow" aria-hidden />
                <div className="showcase-search-darkBorderBg" aria-hidden />
                <div className="showcase-search-darkBorderBg" aria-hidden />
                <div className="showcase-search-darkBorderBg" aria-hidden />
                <div className="showcase-search-white" aria-hidden />
                <div className="showcase-search-border" aria-hidden />
                <div className="showcase-search-main">
                  <input placeholder="Search..." type="text" className="showcase-search-input" />
                  <div className="showcase-input-mask" aria-hidden />
                  <div className="showcase-pink-mask" aria-hidden />
                  <div className="showcase-filter-border" aria-hidden />
                  <div className="showcase-filter-icon">
                    <svg preserveAspectRatio="none" height="27" width="27" viewBox="4.8 4.56 14.832 15.408" fill="none">
                      <path d="M8.16 6.65002H15.83C16.47 6.65002 16.99 7.17002 16.99 7.81002V9.09002C16.99 9.56002 16.7 10.14 16.41 10.43L13.91 12.64C13.56 12.93 13.33 13.51 13.33 13.98V16.48C13.33 16.83 13.1 17.29 12.81 17.47L12 17.98C11.24 18.45 10.2 17.92 10.2 16.99V13.91C10.2 13.5 9.97 12.98 9.73 12.69L7.52 10.36C7.23 10.08 7 9.55002 7 9.20002V7.87002C7 7.17002 7.52 6.65002 8.16 6.65002Z" stroke="#d6d6e6" strokeWidth="1" strokeMiterlimit="10" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                  <div className="showcase-search-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" viewBox="0 0 24 24" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" height="24" fill="none" className="feather feather-search">
                      <circle stroke="url(#searchGrad)" r="8" cy="11" cx="11" />
                      <line stroke="url(#searchGradL)" y2="16.65" y1="22" x2="16.65" x1="22" />
                      <defs>
                        <linearGradient gradientTransform="rotate(50)" id="searchGrad">
                          <stop stopColor="#f8e7f8" offset="0%" />
                          <stop stopColor="#b6a9b7" offset="50%" />
                        </linearGradient>
                        <linearGradient id="searchGradL">
                          <stop stopColor="#b6a9b7" offset="0%" />
                          <stop stopColor="#837484" offset="50%" />
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Seção: Botões e Cards adicionais */}
        <section>
          <h2 className="text-2xl font-bold mb-8 text-foreground">Botões e Cards</h2>
          <div className="flex flex-wrap gap-12 items-start justify-start">
            {/* Get Started com gradiente */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Get Started</span>
              <div className="relative inline-flex items-center justify-center gap-4 group">
                <div className="absolute inset-0 duration-1000 opacity-60 transition-all bg-[linear-gradient(90deg,#2E1A47,#4B2F7F,#6A4BCF,#8E78E6,#B89AF6)] rounded-xl blur-lg filter group-hover:opacity-100 group-hover:duration-200" />
                <a
                  role="button"
                  className="group/btn relative inline-flex items-center justify-center text-base rounded-xl bg-gray-900 px-8 py-3 font-semibold text-white transition-all duration-200 hover:bg-gray-800 hover:shadow-lg hover:-translate-y-0.5 hover:shadow-gray-600/30"
                  href="#"
                >
                  Get Started For Free
                  <svg aria-hidden viewBox="0 0 10 10" height="10" width="10" fill="none" className="mt-0.5 ml-2 -mr-1 stroke-white stroke-2">
                    <path d="M0 5h7" className="transition opacity-0 group-hover/btn:opacity-100" />
                    <path d="M1 1l4 4-4 4" className="transition group-hover/btn:translate-x-[3px]" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Card Starter */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Pricing Card</span>
              <div className="flex flex-col bg-card rounded-3xl border border-border overflow-hidden">
                <div className="px-6 py-8 sm:p-10 sm:pb-6">
                  <div className="grid items-center justify-center w-full grid-cols-1 text-left">
                    <div>
                      <h2 className="text-lg font-medium tracking-tighter text-foreground lg:text-3xl">Starter</h2>
                      <p className="mt-2 text-sm text-muted-foreground">Suitable to grow steadily.</p>
                    </div>
                    <div className="mt-6">
                      <p>
                        <span className="text-5xl font-light tracking-tight text-foreground">$25</span>
                        <span className="text-base font-medium text-muted-foreground"> /mo </span>
                      </p>
                    </div>
                  </div>
                </div>
                <div className="flex px-6 pb-8 sm:px-8">
                  <a
                    className="flex items-center justify-center w-full px-6 py-2.5 text-center text-white duration-200 bg-foreground border-2 border-foreground rounded-full hover:bg-transparent hover:text-foreground focus:outline-none text-sm"
                    href="#"
                  >
                    Get started
                  </a>
                </div>
              </div>
            </div>

            {/* Glider multi-select (4 opções) */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Multi-select (4)</span>
              <div className="showcase-glider-multi">
                <div className="showcase-glider-track" aria-hidden />
                <div className="showcase-glider-item">
                  <input type="checkbox" id="glider-1" name="glider" />
                  <label htmlFor="glider-1">Opção 1</label>
                  <div className="showcase-glider-glow" aria-hidden />
                </div>
                <div className="showcase-glider-item">
                  <input type="checkbox" id="glider-2" name="glider" />
                  <label htmlFor="glider-2">Opção 2</label>
                  <div className="showcase-glider-glow" aria-hidden />
                </div>
                <div className="showcase-glider-item">
                  <input type="checkbox" id="glider-3" name="glider" />
                  <label htmlFor="glider-3">Opção 3</label>
                  <div className="showcase-glider-glow" aria-hidden />
                </div>
                <div className="showcase-glider-item">
                  <input type="checkbox" id="glider-4" name="glider" />
                  <label htmlFor="glider-4">Opção 4</label>
                  <div className="showcase-glider-glow" aria-hidden />
                </div>
              </div>
            </div>

            {/* Glass selector */}
            <div className="flex flex-col items-center gap-4 p-6 rounded-xl bg-card border border-border">
              <span className="text-sm font-medium text-muted-foreground">Glass Selector</span>
              <div className="showcase-glass-selector">
                <div className="showcase-glass">
                  <div className="showcase-glass-inner" />
                </div>
                <div className="showcase-glass-choices">
                  <div className="showcase-glass-choice">
                    <div>
                      <input className="showcase-glass-radio" type="radio" name="glass-select" id="glass-one" defaultChecked />
                      <div className="showcase-glass-ball" />
                    </div>
                    <label htmlFor="glass-one" className="showcase-glass-label">1</label>
                  </div>
                  <div className="showcase-glass-choice">
                    <div>
                      <input className="showcase-glass-radio" type="radio" name="glass-select" id="glass-two" />
                      <div className="showcase-glass-ball" />
                    </div>
                    <label htmlFor="glass-two" className="showcase-glass-label">2</label>
                  </div>
                  <div className="showcase-glass-choice">
                    <div>
                      <input className="showcase-glass-radio" type="radio" name="glass-select" id="glass-three" />
                      <div className="showcase-glass-ball" />
                    </div>
                    <label htmlFor="glass-three" className="showcase-glass-label">3</label>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Botão para Login no final */}
        <section className="flex justify-center py-12">
          <Button variant="pulso" size="lg" onClick={() => navigate("/auth?mode=login")}>
            Ir para Login
          </Button>
        </section>
      </main>
    </div>
  );
};

export default Index;
