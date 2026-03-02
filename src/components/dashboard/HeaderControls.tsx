/**
 * HeaderControls — A/B, tema, menu usuário (versão compacta para o header)
 * Mantém os elementos próximos entre si
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
import { useLayoutContext } from "@/contexts/LayoutContext";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import ProfileDialog from "./ProfileDialog";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

export function HeaderControls() {
  const navigate = useNavigate();
  const { themeMode, toggleTheme } = useLayoutContext();
  const { currentProfile, setCurrentProfile, logout } = useAuth();
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);

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
      <div className="flex items-center gap-1.5 shrink-0 rounded-full glass px-2.5 py-1.5 border border-border/50">
        {/* Tema claro/escuro */}
        <Button
          variant="ghost"
          size="sm"
          className="h-8 gap-1.5 px-2 text-xs font-medium"
          onClick={toggleTheme}
          aria-label={themeMode === "dark" ? "Modo claro" : "Modo escuro"}
        >
          {themeMode === "dark" ? (
            <Sun className="h-4 w-4 shrink-0" />
          ) : (
            <Moon className="h-4 w-4 shrink-0" />
          )}
          <span className="hidden sm:inline">Tema</span>
        </Button>

        {/* Menu usuário */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm" className="h-8 gap-1.5 px-2 text-xs font-medium" aria-label="Menu do usuário">
              <User className="h-4 w-4 shrink-0" />
              <span className="hidden sm:inline">Perfil</span>
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
      </div>

      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
    </>
  );
}
