/**
 * UserSidebar — Avatar do usuário que, ao hover, revela painel glass com tema e layout
 */
import { LogOut, User, Users, Settings, Sun, Moon, LayoutGrid, PanelLeft } from "lucide-react";
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

export function UserSidebar() {
  const navigate = useNavigate();
  const { layoutMode, setLayoutMode, themeMode, toggleTheme } = useLayoutContext();
  const { user, currentProfile, setCurrentProfile, logout } = useAuth();
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);
  const [isHovered, setIsHovered] = useState(false);

  const displayName = currentProfile?.name || user?.name || "";
  const avatarSrc = user?.picture;
  const initial = getInitial(displayName || user?.name);

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

  return (
    <>
      <div
        className="relative group pr-48"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Avatar — sempre visível, círculo com foto ou inicial */}
        <div className="relative z-10 shrink-0">
          <Avatar className="h-12 w-12 rounded-full ring-2 ring-primary/40 ring-offset-2 ring-offset-background/80 cursor-pointer transition-all duration-500 group-hover:ring-primary/60 group-hover:scale-105">
            <AvatarImage src={avatarSrc} alt={displayName} />
            <AvatarFallback className="bg-primary/20 text-primary font-semibold text-sm">
              {initial}
            </AvatarFallback>
          </Avatar>
        </div>

        {/* Bola glass — opções anexadas ao avatar */}
        <div
          className={cn(
            "absolute left-full bottom-1/2 translate-y-1/2 -ml-1 flex flex-row items-center gap-1.5 rounded-full glass border border-border/50 p-2 pr-3",
            "pulso-user-panel-diagonal",
            isHovered
              ? "pulso-user-panel-diagonal-visible pointer-events-auto"
              : "pulso-user-panel-diagonal-hidden pointer-events-none"
          )}
        >
          {/* Switch Layout A/B */}
          <div
            className="flex items-center rounded-full border border-primary/40 bg-muted/30 p-0.5"
            role="group"
            aria-label="Layout A ou B"
          >
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-7 px-3 text-xs font-medium transition-colors rounded-full flex-1",
                layoutMode === "A"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
              onClick={() => {
                setLayoutMode("A");
                toast({ title: "Layout A", description: "Futurista — sidebar e efeitos" });
              }}
              aria-pressed={layoutMode === "A"}
            >
              <PanelLeft className="h-3.5 w-3.5 mr-1" />
              A
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className={cn(
                "h-7 px-3 text-xs font-medium transition-colors rounded-full flex-1",
                layoutMode === "B"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
              onClick={() => {
                setLayoutMode("B");
                toast({ title: "Layout B", description: "Clássico — carrossel corporativo" });
              }}
              aria-pressed={layoutMode === "B"}
            >
              <LayoutGrid className="h-3.5 w-3.5 mr-1" />
              B
            </Button>
          </div>

          {/* Tema claro/escuro */}
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={toggleTheme}
            aria-label={themeMode === "dark" ? "Modo claro" : "Modo escuro"}
          >
            {themeMode === "dark" ? (
              <Sun className="h-4 w-4" />
            ) : (
              <Moon className="h-4 w-4" />
            )}
          </Button>

          {/* Menu usuário */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Menu do usuário">
                <User className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" side="bottom">
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
        </div>
      </div>

      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
    </>
  );
}
