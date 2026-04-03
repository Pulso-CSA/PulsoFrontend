/**
 * HeaderControls — A/B, tema, menu usuário (versão compacta para o header)
 * Mantém os elementos próximos entre si
 */
import { LogOut, User, Users, Settings, Sun, Moon, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { useLayoutContext } from "@/contexts/LayoutContext";
import { useAuth } from "@/contexts/AuthContext";
import { useSfapAllowed } from "@/hooks/useSfapAllowed";
import { useToast } from "@/hooks/use-toast";
import ProfileDialog from "./ProfileDialog";
import { NotificationBell } from "@/components/dashboard/NotificationBell";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function HeaderControls() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { themeMode, toggleTheme } = useLayoutContext();
  const { currentProfile, setCurrentProfile, logout } = useAuth();
  const sfapAllowed = useSfapAllowed();
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);

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

  return (
    <>
      <div className="flex items-center gap-1.5 shrink-0 rounded-full glass px-2.5 py-1.5 border border-border/50">
        <NotificationBell />
        {/* Tema claro/escuro */}
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-1.5 px-2 text-xs font-medium"
          onClick={toggleTheme}
          aria-label={themeMode === "dark" ? t("layout.themeLightAria") : t("layout.themeDarkAria")}
        >
          {themeMode === "dark" ? (
            <Sun className="h-4 w-4 shrink-0" />
          ) : (
            <Moon className="h-4 w-4 shrink-0" />
          )}
          <span className="hidden sm:inline">{t("layout.theme")}</span>
        </Button>

        {/* Menu usuário */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 gap-1.5 px-2 text-xs font-medium text-foreground" aria-label={t("layout.headerUserMenuAria")} title={t("layout.account")}>
              <User className="h-4 w-4 shrink-0" />
              <span>{t("layout.headerProfileButton")}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" side="bottom" className="pulso-dropdown-menu-glass">
            {currentProfile && (
              <>
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{t("layout.currentProfile")}</span>
                    <span className="text-xs text-muted-foreground font-normal">{currentProfile.name}</span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
              </>
            )}
            {sfapAllowed && (
              <DropdownMenuItem onClick={() => navigate("/sfap")} title={t("layout.sfapTitle")}>
                <DollarSign className="mr-2 h-4 w-4" />
                {t("layout.sfap")}
              </DropdownMenuItem>
            )}
            <DropdownMenuItem onClick={() => setProfileOpen(true)}>
              <User className="mr-2 h-4 w-4" />
              {t("profile.title")}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={handleSwitchProfile}>
              <Users className="mr-2 h-4 w-4" />
              {t("layout.switchProfile")}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate("/settings")}>
              <Settings className="mr-2 h-4 w-4" />
              {t("layout.settings")}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={handleLogout}>
              <LogOut className="mr-2 h-4 w-4" />
              {t("layout.logout")}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
    </>
  );
}
