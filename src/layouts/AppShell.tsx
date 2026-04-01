/**
 * AppShell — Shell padrão para todas as páginas
 * Header com logo, switch Layout A/B, tema claro/escuro
 * Usado em páginas públicas e protegidas
 */
import { useNavigate, useLocation, Outlet } from "react-router-dom";
import "@/styles/pulso-layouts.css";
import { UserSidebar } from "@/components/dashboard/UserSidebar";
import { HeaderControls } from "@/components/dashboard/HeaderControls";
import { useLayoutContext } from "@/contexts/LayoutContext";
import { cn } from "@/lib/utils";
import { useTranslation } from "react-i18next";

function LayoutWrapper() {
  const location = useLocation();
  const { layoutMode } = useLayoutContext();
  const path = location.pathname;
  const skipWrap = path === "/dashboard" || path === "/" || path === "/profile-selection";
  if (skipWrap) return <Outlet />;

  const isFuturistic = layoutMode === "A";
  return (
    <div
      data-pulso-layout={layoutMode}
      className={cn(
        "relative flex min-h-0 flex-1 flex-col",
        isFuturistic && "pulso-layout",
        !isFuturistic && "pulso-layout-b",
      )}
    >
      <div className="relative z-10 flex min-h-0 min-w-0 flex-1 flex-col">
        <Outlet />
      </div>
    </div>
  );
}

export function AppShell() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const isElectron = typeof window !== "undefined" && !!window.electronAPI;
  const showLogo = !isElectron;
  const isPublicPage = ["/", "/auth", "/auth/callback", "/forgot-password", "/reset-password", "/error"].some(
    (p) => location.pathname === p || location.hash.includes(p)
  );
  /** Login, recuperação e escolha de perfil: sem avatar/tema flutuante (UserSidebar) */
  const hideUserSidebar = [
    "/auth",
    "/auth/callback",
    "/forgot-password",
    "/reset-password",
    "/profile-selection",
  ].some((p) => location.pathname === p || location.hash.includes(p));
  /** Sem header nas telas que já têm layout próprio (login, início, dashboard, etc.) — evita faixa glass vazia no Electron em /auth */
  const hideHeader =
    location.pathname === "/" ||
    location.pathname === "/profile-selection" ||
    location.pathname === "/dashboard" ||
    location.pathname === "/auth" ||
    location.pathname === "/auth/callback" ||
    location.pathname === "/forgot-password" ||
    location.pathname === "/reset-password";

  return (
    <div className="relative flex min-h-0 min-w-0 flex-1 flex-col overflow-x-hidden overflow-y-hidden bg-space-if-dark text-foreground">
      {/* Fundo space + orbs (igual ProfileSelection) */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 pulso-orb animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 pulso-orb animate-pulse" style={{ animationDelay: "1s" }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 pulso-orb-sm animate-pulse" style={{ animationDelay: "2s" }} />
      </div>

      {!hideHeader && (
        <header
          className={cn(
            "sticky top-0 z-50 w-full",
            "glass-strong",
            "sticky-below-electron"
          )}
        >
          <div className="max-w-[1600px] mx-auto flex h-14 items-center gap-6 px-4 lg:px-6 min-w-0">
            {showLogo && (
              <button
                type="button"
                onClick={() => navigate("/")}
                className="flex items-center gap-2 hover:opacity-80 transition-opacity shrink-0"
                aria-label={t("appshell.homeAria")}
              >
                <img
                  src={import.meta.env.BASE_URL + "App.png"}
                  alt="Pulso"
                  className="h-8 w-8 object-contain"
                />
                <span className="text-lg font-semibold tracking-tight text-foreground hidden sm:inline">
                  {t("appshell.brand")}
                </span>
              </button>
            )}
            {!isPublicPage && <HeaderControls />}
          </div>
        </header>
      )}

      <main
        id="main-content"
        className="flex-1 flex flex-col min-w-0 min-h-0 overflow-y-auto overflow-x-hidden relative z-10 pulso-app-main-scroll"
        tabIndex={-1}
      >
        <LayoutWrapper />
      </main>

      {/* Avatar + tema: páginas autenticadas com header escondido, exceto dashboard e fluxo de login/seleção de perfil */}
      {!isPublicPage && hideHeader && location.pathname !== "/dashboard" && !hideUserSidebar && (
        <aside
          className={cn(
            "fixed z-40 flex flex-col pointer-events-none",
            "bottom-0 left-0 items-center justify-end pb-4 pl-4"
          )}
          aria-label={t("appshell.userArea")}
        >
          <div className="pointer-events-auto">
            <UserSidebar position="bottom-left" />
          </div>
        </aside>
      )}
    </div>
  );
}
