import { LogOut, User, UserCircle, RefreshCw, Users, Keyboard, Settings } from "lucide-react";
import { useState, Dispatch, SetStateAction } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuLabel,
} from "@/components/ui/dropdown-menu";
import ProfileDialog from "./ProfileDialog";
import LayerSelection from "./LayerSelection";
import ThemeSelector from "@/components/ThemeSelector";
import { useAuth } from "@/contexts/AuthContext";

interface DashboardHeaderProps {
  activeLayers?: {
    preview: boolean;
    pulso: boolean;
    finops: boolean;
    data: boolean;
    cloud: boolean;
  };
  setActiveLayers?: Dispatch<SetStateAction<{
    preview: boolean;
    pulso: boolean;
    finops: boolean;
    data: boolean;
    cloud: boolean;
  }>>;
  showLayerSelection?: boolean;
  onShortcutsClick?: () => void;
  layoutToggle?: React.ReactNode;
  /** Oculta LayerSelection quando true (ex: layout compacto com sidebar) */
  hideLayerSelection?: boolean;
}

const DashboardHeader = ({ activeLayers, setActiveLayers, showLayerSelection = true, onShortcutsClick, layoutToggle, hideLayerSelection }: DashboardHeaderProps) => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);
  const { currentProfile, setCurrentProfile, logout } = useAuth();

  const handleLogout = async () => {
    await logout();
    toast({
      title: "Sessão encerrada",
      description: "Até logo!",
    });
    navigate("/auth");
  };

  const handleSwitchProfile = () => {
    setCurrentProfile(null);
    toast({
      title: "Trocar de perfil",
      description: "Selecione outro perfil",
    });
    navigate("/profile-selection");
  };

  const handleSwitchAccount = async () => {
    await logout();
    toast({
      title: "Trocar de conta",
      description: "Faça login com outra conta",
    });
    navigate("/auth");
  };


  return (
    <>
      <header className="sticky top-0 z-50 w-full backdrop-blur supports-[backdrop-filter]:bg-background/60 animate-slide-down transition-all duration-300 overflow-hidden">
        <div className="container mx-auto flex h-14 items-center justify-between px-4 min-w-0">
          <div className="flex items-center gap-4">
            <img
              src={import.meta.env.BASE_URL + "App.png"}
              alt="Pulso"
              className="h-8 w-8 object-contain shrink-0"
            />
            <h1 className="text-xl font-bold transition-all duration-300 hover:scale-105 text-primary">Pulso</h1>
            {currentProfile && (
              <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded-lg glass border border-primary/30">
                <Users className="h-3.5 w-3.5 text-primary" />
                <span className="text-sm font-medium text-foreground">{currentProfile.name}</span>
              </div>
            )}
          </div>

          
          <div className="flex items-center gap-2 transition-all duration-300 ease-out shrink-0">
            {layoutToggle}
            {onShortcutsClick && (
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 text-muted-foreground hover:text-foreground transition-all duration-300 ease-out hover:scale-105"
                onClick={onShortcutsClick}
                title="Atalhos de teclado (Alt+?)"
                aria-label="Abrir atalhos de teclado"
              >
                <Keyboard className="h-4 w-4" />
              </Button>
            )}
            <ThemeSelector />
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div className="relative group">
                  <div className="absolute inset-0 rounded-full blur-md bg-primary/40 group-hover:bg-primary/60 transition-all duration-300"></div>
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    aria-label="Menu do usuário"
                    className="relative z-10 border-2 border-primary/60 group-hover:border-primary pulso-glow-cta transition-all duration-300 group-hover:scale-105 group-active:scale-95"
                  >
                    <User className="h-5 w-5" />
                  </Button>
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
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
                  <UserCircle className="mr-2 h-4 w-4" />
                  Minha Conta
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleSwitchProfile}>
                  <Users className="mr-2 h-4 w-4" />
                  Trocar de Perfil
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleSwitchAccount}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Trocar de Conta
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => { navigate("/settings"); }}>
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

        {/* Layer Selection integrado no header - anima ao realocar entre layouts */}
        {activeLayers && setActiveLayers && (
          <div
            className={`
              grid overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]
              ${showLayerSelection && !hideLayerSelection
                ? "grid-rows-[1fr] opacity-100"
                : "grid-rows-[0fr] opacity-0"
              }
            `}
          >
            <div className="min-h-0 overflow-hidden">
              <div className="container mx-auto px-4 pb-3 pt-1">
                <LayerSelection
                  activeLayers={activeLayers}
                  setActiveLayers={setActiveLayers}
                />
              </div>
            </div>
          </div>
        )}
      </header>

      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
    </>
  );
};

export default DashboardHeader;
