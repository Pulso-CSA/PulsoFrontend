/**
 * UserSidebar — Avatar do usuário que, ao hover, revela painel glass com tema e layout
 */
import { LogOut, User, Users, Settings, Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useLayoutContext } from "@/contexts/LayoutContext";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import ProfileDialog from "@/components/dashboard/ProfileDialog";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { cn } from "@/lib/utils";

function getInitial(name: string | undefined): string {
  if (!name?.trim()) return "?";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase().slice(0, 2);
  }
  return name[0].toUpperCase();
}

interface UserSidebarProps {
  /** Quando "top-right", perfil fica no canto superior direito e botões secundários aparecem na região central abaixo do avatar */
  position?: "bottom-left" | "top-right";
}

export function UserSidebar({ position = "bottom-left" }: UserSidebarProps) {
  const navigate = useNavigate();
  const { themeMode, toggleTheme } = useLayoutContext();
  const { user, currentProfile, setCurrentProfile, logout } = useAuth();
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const displayName = currentProfile?.name || user?.name || "";
  const avatarSrc = user?.picture;
  const initial = getInitial(displayName || user?.name);
  const isTopRight = position === "top-right";

  const handleLogout = async () => {
    await logout();
    toast({ title: "Sessão encerrada", description: "Até logo!" });
    navigate("/auth");
  };

  const handleSwitchProfile = () => {
    setCurrentProfile(null);
    toast({ title: "Trocar de perfil", description: "Selecione outro perfil" });
    navigate("/profile-selection");
  };

  const panelContent = (
    <>
          {/* Tema claro/escuro */}
          <Button
            variant="ghost"
            size="sm"
            className="h-8 gap-1.5 px-2 text-white text-xs font-medium"
            onClick={toggleTheme}
            aria-label={themeMode === "dark" ? "Modo claro" : "Modo escuro"}
          >
            {themeMode === "dark" ? (
              <Sun className="h-4 w-4 shrink-0" />
            ) : (
              <Moon className="h-4 w-4 shrink-0" />
            )}
            <span>Tema</span>
          </Button>

          {/* Menu usuário — escondido no dashboard (top-right); perfil fica na navbar */}
          {!isTopRight && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 gap-1.5 px-2 text-white text-xs font-medium" aria-label="Menu do usuário">
                  <User className="h-4 w-4 shrink-0" />
                  <span>Perfil</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" side="bottom" className="pulso-dropdown-menu-glass">
                {currentProfile && (
                  <>
                    <DropdownMenuLabel>
                      <div className="flex flex-col">
                        <span className="text-sm font-medium">Perfil Atual</span>
                        <span className="text-xs text-muted-foreground font-normal">{currentProfile.name}</span>
                      </div>
                    </DropdownMenuLabel>
                    <DropdownMenuSeparator />
                  </>
                )}
                <DropdownMenuItem onClick={() => setProfileOpen(true)}>
                  <User className="mr-2 h-4 w-4" />
                  Minha Conta
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleSwitchProfile}>
                  <Users className="mr-2 h-4 w-4" />
                  Trocar de Perfil
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => navigate("/settings")}>
                  <Settings className="mr-2 h-4 w-4" />
                  Configurações
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Sair
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </>
  );

  return (
    <>
      <div
        className={cn(
          "relative group",
          isTopRight ? "flex flex-col items-center" : "pr-48"
        )}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Avatar — sempre visível */}
        <div className="relative z-10 shrink-0">
          <Avatar className="h-12 w-12 rounded-full ring-2 ring-primary/40 ring-offset-2 ring-offset-background/80 cursor-pointer transition-all duration-500 group-hover:ring-primary/60 group-hover:scale-105">
            <AvatarImage src={avatarSrc} alt={displayName} />
            <AvatarFallback className="bg-primary/20 text-primary font-semibold text-sm">
              {initial}
            </AvatarFallback>
          </Avatar>
        </div>

        {/* Botões secundários: à direita do avatar (bottom-left) ou centralizados abaixo (top-right) */}
        <div
          className={cn(
            "flex items-center gap-1.5 rounded-full glass border border-border/50 p-2",
            isTopRight ? "flex-row mt-3" : "absolute left-full bottom-1/2 translate-y-1/2 -ml-1 flex-row pr-3",
            isTopRight
              ? cn("pulso-user-panel-below", isHovered ? "opacity-100" : "opacity-0 pointer-events-none")
              : "pulso-user-panel-diagonal",
            !isTopRight && (isHovered ? "pulso-user-panel-diagonal-visible pointer-events-auto" : "pulso-user-panel-diagonal-hidden pointer-events-none"),
            "transition-all duration-300"
          )}
        >
          {panelContent}
        </div>
      </div>

      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
    </>
  );
}
