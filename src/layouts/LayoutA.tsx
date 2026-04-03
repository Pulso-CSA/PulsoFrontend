/**
 * Layout A — Sidebar futurista e elegante
 * 4 serviços no topo, avatar de perfil no meio (hover: mini navbar Perfil + Tema)
 * Paleta Pulso: #222023, #420d95, #a54bce, #60bcd5, #1897a0
 */
import { useState, useRef, useEffect, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import { Workflow, CloudCog, TrendingDown, Brain, User, LogOut, Users, Settings, Sun, Moon, Key, UserPlus, DollarSign, type LucideIcon } from "lucide-react";
import { SiAmazonwebservices } from "react-icons/si";
import { TbBrandAzure } from "react-icons/tb";
import { SiGooglecloud } from "react-icons/si";
import { cn } from "@/lib/utils";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useAuth } from "@/contexts/AuthContext";
import { useLayoutContext } from "@/contexts/LayoutContext";
import { useToast } from "@/hooks/use-toast";
import ProfileDialog from "@/components/dashboard/ProfileDialog";
import { NotificationBell } from "@/components/dashboard/NotificationBell";
import { useSfapAllowed } from "@/hooks/useSfapAllowed";
import "@/styles/pulso-layouts.css";

function getInitial(name: string | undefined): string {
  if (!name?.trim()) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase().slice(0, 2);
  return name[0].toUpperCase();
}

export type ServiceKey = "pulso" | "cloud" | "finops" | "data";

const CLOUD_OPTIONS = [
  { id: "aws", label: "AWS", Icon: SiAmazonwebservices },
  { id: "azure", label: "Azure", Icon: TbBrandAzure },
  { id: "gcp", label: "GCP", Icon: SiGooglecloud },
] as const;

interface LayoutAProps {
  activeService: ServiceKey | null;
  onServiceChange: (key: ServiceKey | null) => void;
  children: React.ReactNode;
  className?: string;
}

export function LayoutA({ activeService, onServiceChange, children, className }: LayoutAProps) {
  const { t, i18n } = useTranslation();
  const services = useMemo(
    () =>
      [
        { key: "pulso" as const, label: t("layout.services.pulso"), icon: Workflow },
        { key: "cloud" as const, label: t("layout.services.cloud"), icon: CloudCog },
        { key: "finops" as const, label: t("layout.services.finops"), icon: TrendingDown },
        { key: "data" as const, label: t("layout.services.data"), icon: Brain },
      ] as const,
    [t, i18n.language]
  );
  const [serviceHover, setServiceHover] = useState<ServiceKey | null>(null);
  const [selectedProviderByService, setSelectedProviderByService] = useState<{
    cloud: "aws" | "azure" | "gcp";
    finops: "aws" | "azure" | "gcp";
  }>({
    cloud: "aws",
    finops: "aws",
  });
  const [avatarHover, setAvatarHover] = useState(false);
  const [profileDialogOpen, setProfileDialogOpen] = useState(false);
  const avatarRef = useRef<HTMLDivElement>(null);
  const leaveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const serviceLeaveTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [avatarRect, setAvatarRect] = useState<DOMRect | null>(null);

  const setAvatarHoverWithDelay = (value: boolean) => {
    if (leaveTimeoutRef.current) {
      clearTimeout(leaveTimeoutRef.current);
      leaveTimeoutRef.current = null;
    }
    if (value) {
      setAvatarHover(true);
    } else {
      leaveTimeoutRef.current = setTimeout(() => setAvatarHover(false), 150);
    }
  };

  const setServiceHoverWithDelay = (value: ServiceKey | null) => {
    if (serviceLeaveTimeoutRef.current) {
      clearTimeout(serviceLeaveTimeoutRef.current);
      serviceLeaveTimeoutRef.current = null;
    }
    if (value) {
      setServiceHover(value);
    } else {
      serviceLeaveTimeoutRef.current = setTimeout(() => setServiceHover(null), 180);
    }
  };

  useEffect(() => {
    if (!avatarHover || !avatarRef.current) {
      setAvatarRect(null);
      return;
    }
    const el = avatarRef.current;
    const update = () => setAvatarRect(el.getBoundingClientRect());
    update();
    const obs = new ResizeObserver(update);
    obs.observe(el);
    const onScroll = () => update();
    window.addEventListener("scroll", onScroll, true);
    return () => {
      obs.disconnect();
      window.removeEventListener("scroll", onScroll, true);
    };
  }, [avatarHover]);
  const navigate = useNavigate();
  const { user, currentProfile, setCurrentProfile, logout } = useAuth();
  const sfapAllowed = useSfapAllowed();
  const { themeMode, toggleTheme } = useLayoutContext();
  const { toast } = useToast();
  const displayName = currentProfile?.name || user?.name || "";
  const avatarSrc = user?.picture;
  const initial = getInitial(displayName || user?.name);

  const INVITES_KEY = "pulso_invites_count";
  const maxInvites = 5;
  const [inviteCount, setInviteCount] = useState(() =>
    typeof window !== "undefined" ? Math.min(maxInvites, Math.max(0, parseInt(localStorage.getItem(INVITES_KEY) || "0", 10))) : 0
  );
  const handleInviteUser = () => {
    if (inviteCount >= maxInvites) return;
    const next = inviteCount + 1;
    localStorage.setItem(INVITES_KEY, String(next));
    setInviteCount(next);
    toast({
      title: t("layout.toastInviteSent"),
      description: t("layout.toastInviteDesc", { next, max: maxInvites }),
    });
  };

  const handleLogout = async () => {
    await logout();
    toast({ title: t("layout.toastSessionClosed"), description: t("layout.toastSessionClosedDesc") });
    navigate("/auth");
  };

  const handleSwitchProfile = () => {
    setCurrentProfile(null);
    toast({ title: t("layout.toastSwitchProfile"), description: t("layout.toastSwitchProfileDesc") });
    navigate("/profile-selection");
  };

  const dispatchOpenCredentials = (target: "cloud" | "finops") => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("pulso-open-cloud-credentials", { detail: { target } }));
    }
  };

  const dispatchSelectProvider = (target: "cloud" | "finops", provider: "aws" | "azure" | "gcp") => {
    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("pulso-select-cloud-provider", { detail: { target, provider } }));
    }
  };

  return (
    <div className={cn("pulso-layout pulso-layout-a", className)}>
      {/* Barra de serviços fixa no topo (navbar glass) */}
      <div className="pulso-layout-a-services-bar flex-shrink-0" aria-label={t("layout.servicesBarAria")}>
        <div className="pulso-layout-a-services-inner" data-pulso-main-services-inner>
          {services.slice(0, 2).map(({ key, label, icon: Icon }) => {
            const isActive = activeService === key;
            const supportsCloudMenu = key === "cloud" || key === "finops";
            return (
              <div
                key={key}
                className="relative flex items-center justify-center"
                onMouseEnter={() => supportsCloudMenu && setServiceHoverWithDelay(key)}
                onMouseLeave={() => supportsCloudMenu && setServiceHoverWithDelay(null)}
              >
                <div className="relative flex items-center justify-center">
                  <button
                    type="button"
                    data-pulso-tab={key}
                    onClick={() => onServiceChange(isActive ? null : key)}
                    className={cn(
                      "pulso-layout-a-btn pulso-layout-a-btn-horizontal text-foreground",
                      isActive && "pulso-active"
                    )}
                    title={label}
                    aria-pressed={isActive}
                    aria-label={`${label} ${isActive ? t("layout.serviceActive") : t("layout.serviceInactive")}`}
                  >
                    <Icon className="h-5 w-5 shrink-0 pulso-service-tab-icon" strokeWidth={1.5} />
                    <span className="text-xs font-medium truncate">{label}</span>
                  </button>
                  {/* Efeito hover embaixo do botão com submenu de cloud */}
                  {supportsCloudMenu && serviceHover === key && (
                    <div
                      className="absolute left-1/2 -translate-x-1/2 top-full mt-1 w-8 h-0.5 rounded-full bg-primary/60 shadow-[0_0_12px_hsl(var(--primary)/0.5)] pointer-events-none"
                      aria-hidden
                    />
                  )}
                </div>
                {/* Mini navbar (Provedores + Credenciais) abaixo da aba ao hover */}
                {supportsCloudMenu && serviceHover === key && (
                  <div
                    className="absolute top-full left-1/2 -translate-x-1/2 mt-2 py-2 px-2 rounded-xl glass border border-border/50 shadow-xl z-50 flex items-center gap-1 min-w-[160px] justify-center flex-wrap"
                    onMouseEnter={() => setServiceHoverWithDelay(key)}
                    onMouseLeave={() => setServiceHoverWithDelay(null)}
                  >
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground px-2 pb-1">{t("layout.providers")}</span>
                      <div className="flex flex-wrap gap-1 justify-center">
                        {CLOUD_OPTIONS.map(({ id, label: optLabel, Icon: OptIcon }) => (
                          <button
                            key={id}
                            type="button"
                            onClick={() => {
                              setSelectedProviderByService((prev) => ({ ...prev, cloud: id }));
                            }}
                            className={cn(
                              "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors",
                              selectedProviderByService.cloud === id
                                ? "bg-primary/20 text-primary border border-primary/35"
                                : "text-foreground hover:bg-primary/15 hover:text-primary border border-transparent"
                            )}
                          >
                            <OptIcon className="h-3.5 w-3.5 shrink-0" />
                            {optLabel}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        onServiceChange("cloud");
                        dispatchSelectProvider("cloud", selectedProviderByService.cloud);
                        dispatchOpenCredentials("cloud");
                        setServiceHover(null);
                      }}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-foreground hover:bg-primary/15 hover:text-primary transition-colors"
                      aria-label={t("layout.openCloudCredentials")}
                    >
                      <Key className="h-4 w-4 shrink-0" />
                      {t("layout.credentials")}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
          <div className="flex items-center justify-center shrink-0 mr-1">
            <NotificationBell />
          </div>
          {/* Avatar: efeito mantido (anel + brilho). Hover mostra painel de configurações (portal) sobrepondo tudo */}
          <div
            ref={avatarRef}
            className="relative flex items-center justify-center"
            onMouseEnter={() => setAvatarHoverWithDelay(true)}
            onMouseLeave={() => setAvatarHoverWithDelay(false)}
          >
            <div className="relative flex items-center justify-center">
              <Avatar
                className={cn(
                  "h-11 w-11 shrink-0 rounded-full ring-2 ring-border/80 transition-all duration-300",
                  avatarHover && "ring-primary/50 ring-offset-2 ring-offset-background scale-105",
                  avatarHover && "shadow-[0_0_20px_hsl(var(--primary)/0.35)]"
                )}
                aria-label={t("layout.profileAria")}
              >
                <AvatarImage src={avatarSrc} alt={displayName} />
                <AvatarFallback className="bg-primary/20 text-primary text-sm font-semibold">
                  {initial}
                </AvatarFallback>
              </Avatar>
              {avatarHover && (
                <div
                  className="absolute left-1/2 -translate-x-1/2 top-full mt-1 w-8 h-0.5 rounded-full bg-primary/60 shadow-[0_0_12px_hsl(var(--primary)/0.5)] pointer-events-none"
                  aria-hidden
                />
              )}
            </div>
          </div>
          {/* Painel de configurações em portal: sempre sobrepõe qualquer conteúdo */}
          {avatarHover &&
            avatarRect &&
            typeof document !== "undefined" &&
            createPortal(
              <div
                className="fixed min-w-[200px] py-3 px-1 rounded-xl pulso-dropdown-menu-glass border border-border/50 shadow-2xl"
                style={{
                  left: avatarRect.left + avatarRect.width / 2,
                  top: avatarRect.bottom + 8,
                  transform: "translateX(-50%)",
                  zIndex: 99999,
                }}
                role="menu"
                onMouseEnter={() => setAvatarHoverWithDelay(true)}
                onMouseLeave={() => setAvatarHoverWithDelay(false)}
              >
                {currentProfile && (
                  <>
                    <div className="px-3 py-1.5 mb-1">
                      <p className="text-sm font-semibold text-foreground">{t("layout.currentProfile")}</p>
                      <p className="text-xs text-muted-foreground font-normal">{currentProfile.name}</p>
                    </div>
                    <div className="h-px bg-border/60 my-2 mx-2" aria-hidden />
                  </>
                )}
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => { setAvatarHover(false); toggleTheme(); }}
                  className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-primary/20 hover:text-primary transition-colors text-left"
                >
                  {themeMode === "dark" ? <Sun className="h-4 w-4 shrink-0" /> : <Moon className="h-4 w-4 shrink-0" />}
                  {t("layout.theme")}
                </button>
                {currentProfile && sfapAllowed && (
                  <button
                    type="button"
                    role="menuitem"
                    onClick={() => { setAvatarHover(false); navigate("/sfap"); }}
                    className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-primary/20 hover:text-primary transition-colors text-left"
                    title={t("layout.sfapTitle")}
                  >
                    <DollarSign className="h-4 w-4 shrink-0" />
                    {t("layout.sfap")}
                  </button>
                )}
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => { setAvatarHover(false); setProfileDialogOpen(true); }}
                  className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-primary/20 hover:text-primary transition-colors text-left"
                >
                  <User className="h-4 w-4 shrink-0" />
                  {t("layout.account")}
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => { setAvatarHover(false); navigate("/settings"); }}
                  className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-primary/20 hover:text-primary transition-colors text-left"
                >
                  <Settings className="h-4 w-4 shrink-0" />
                  {t("layout.settings")}
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={handleInviteUser}
                  disabled={inviteCount >= maxInvites}
                  className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-primary/20 hover:text-primary transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <UserPlus className="h-4 w-4 shrink-0" />
                  {t("layout.inviteUser")}{inviteCount > 0 && ` (${inviteCount}/${maxInvites})`}
                </button>
                <div className="h-px bg-border/60 my-2 mx-2" aria-hidden />
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => { setAvatarHover(false); handleSwitchProfile(); }}
                  className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-primary/20 hover:text-primary transition-colors text-left"
                >
                  <Users className="h-4 w-4 shrink-0" />
                  {t("layout.switchProfile")}
                </button>
                <button
                  type="button"
                  role="menuitem"
                  onClick={() => { setAvatarHover(false); handleLogout(); }}
                  className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-foreground hover:bg-primary/20 hover:text-primary transition-colors text-left"
                >
                  <LogOut className="h-4 w-4 shrink-0" />
                  {t("layout.logout")}
                </button>
              </div>,
              document.body
            )}
          {services.slice(2, 4).map(({ key, label, icon: Icon }) => {
            const isActive = activeService === key;
            const supportsCloudMenu = key === "finops";
            return (
              <div
                key={key}
                className="relative flex items-center justify-center"
                onMouseEnter={() => supportsCloudMenu && setServiceHoverWithDelay(key)}
                onMouseLeave={() => supportsCloudMenu && setServiceHoverWithDelay(null)}
              >
                <div className="relative">
                  <button
                    type="button"
                    data-pulso-tab={key}
                    onClick={() => onServiceChange(isActive ? null : key)}
                    className={cn("pulso-layout-a-btn pulso-layout-a-btn-horizontal text-foreground", isActive && "pulso-active")}
                    title={label}
                    aria-pressed={isActive}
                    aria-label={`${label} ${isActive ? t("layout.serviceActive") : t("layout.serviceInactive")}`}
                  >
                    <Icon className="h-5 w-5 shrink-0 pulso-service-tab-icon" strokeWidth={1.5} />
                    <span className="text-xs font-medium truncate">{label}</span>
                  </button>
                  {supportsCloudMenu && serviceHover === key && (
                    <div
                      className="absolute left-1/2 -translate-x-1/2 top-full mt-1 w-8 h-0.5 rounded-full bg-primary/60 shadow-[0_0_12px_hsl(var(--primary)/0.5)] pointer-events-none"
                      aria-hidden
                    />
                  )}
                </div>
                {supportsCloudMenu && serviceHover === key && (
                  <div
                    className="absolute top-full left-1/2 -translate-x-1/2 mt-2 py-2 px-2 rounded-xl glass border border-border/50 shadow-xl z-50 flex items-center gap-1 min-w-[160px] justify-center flex-wrap"
                    onMouseEnter={() => setServiceHoverWithDelay(key)}
                    onMouseLeave={() => setServiceHoverWithDelay(null)}
                  >
                    <div className="flex flex-col gap-0.5">
                      <span className="text-[10px] uppercase tracking-wider text-muted-foreground px-2 pb-1">{t("layout.providers")}</span>
                      <div className="flex flex-wrap gap-1 justify-center">
                        {CLOUD_OPTIONS.map(({ id, label: optLabel, Icon: OptIcon }) => (
                          <button
                            key={id}
                            type="button"
                            onClick={() => {
                              setSelectedProviderByService((prev) => ({ ...prev, finops: id }));
                            }}
                            className={cn(
                              "flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors",
                              selectedProviderByService.finops === id
                                ? "bg-primary/20 text-primary border border-primary/35"
                                : "text-foreground hover:bg-primary/15 hover:text-primary border border-transparent"
                            )}
                          >
                            <OptIcon className="h-3.5 w-3.5 shrink-0" />
                            {optLabel}
                          </button>
                        ))}
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        onServiceChange("finops");
                        dispatchSelectProvider("finops", selectedProviderByService.finops);
                        dispatchOpenCredentials("finops");
                        setServiceHover(null);
                      }}
                      className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-foreground hover:bg-primary/15 hover:text-primary transition-colors"
                      aria-label={t("layout.openCloudCredentials")}
                    >
                      <Key className="h-4 w-4 shrink-0" />
                      {t("layout.credentials")}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Área inferior: conteúdo (sidebar conta/tema/layout fica no AppShell) */}
      <div className="pulso-layout-a-body flex-1 flex min-h-0">
        {/* Área principal centralizada */}
        <main className="pulso-layout-a-main flex-1 bg-transparent w-full">
          <div className="pulso-layout-a-content">{children}</div>
        </main>
      </div>
      <ProfileDialog open={profileDialogOpen} onOpenChange={setProfileDialogOpen} />
    </div>
  );
}
