import { LogOut, User, UserCircle, RefreshCw, Users, Keyboard, Settings, DollarSign } from "lucide-react";
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
import { useSfapAllowed } from "@/hooks/useSfapAllowed";

interface DashboardHeaderProps {
  /** Oculta logo quando true (ex: Electron já exibe no title bar) */
  hideLogo?: boolean;
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

const DashboardHeader = ({ hideLogo, activeLayers, setActiveLayers, showLayerSelection = true, onShortcutsClick, layoutToggle, hideLayerSelection }: DashboardHeaderProps) => {
  const isElectron = typeof window !== "undefined" && !!window.electronAPI;
  const showLogo = !hideLogo && !isElectron;
  const navigate = useNavigate();
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);
  const { currentProfile, setCurrentProfile, logout } = useAuth();
  const sfapAllowed = useSfapAllowed();

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
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/90 backdrop-blur-xl overflow-hidden">
        <div className="max-w-[1600px] mx-auto flex h-14 items-center justify-between px-4 lg:px-6 min-w-0">
          <div className="flex items-center gap-4">
            {showLogo && (
              <img
                src={import.meta.env.BASE_URL + "App.png"}
                alt="Pulso"
                className="h-6 w-6 object-contain shrink-0"
              />
            )}
            <h1 className="text-lg font-semibold tracking-tight text-foreground">Pulso Tech</h1>
            {currentProfile && (
              <div className="hidden md:flex items-center gap-2 px-2.5 py-1 rounded-md bg-muted/50 border border-border">
                <Users className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-xs font-medium text-foreground">{currentProfile.name}</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-1.5 transition-all duration-300 ease-out shrink-0">
            {layoutToggle}
            {onShortcutsClick && (
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-foreground hover:bg-muted/80 rounded-lg"
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
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="Menu do usuário (Perfil)"
                  title="Perfil e conta"
                  className="h-8 gap-1.5 px-2 rounded-lg hover:bg-muted/80 text-foreground"
                >
                  <User className="h-4 w-4 shrink-0" />
                  <span className="hidden sm:inline text-xs font-medium">Perfil</span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="pulso-dropdown-menu-glass">
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
                {sfapAllowed && (
                  <DropdownMenuItem onClick={() => navigate("/sfap")} title="Sistema Financeiro Administrativo Pulso">
                    <DollarSign className="mr-2 h-4 w-4" />
                    SFAP
                  </DropdownMenuItem>
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
              grid overflow-hidden transition-all duration-500 ease-fluid
              ${showLayerSelection && !hideLayerSelection
                ? "grid-rows-[1fr] opacity-100"
                : "grid-rows-[0fr] opacity-0"
              }
            `}
          >
            <div className="min-h-0 overflow-hidden">
              <div className="max-w-[1600px] mx-auto px-4 lg:px-6 pb-4 pt-3">
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
