import { LogOut, User, UserCircle, RefreshCw } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { useToast } from "@/hooks/use-toast";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import ProfileDialog from "./ProfileDialog";

const DashboardHeader = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [profileOpen, setProfileOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    toast({
      title: "Sessão encerrada",
      description: "Até logo!",
    });
    navigate("/auth");
  };

  const handleSwitchAccount = () => {
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("userProfile");
    toast({
      title: "Trocar de conta",
      description: "Faça login com outra conta",
    });
    navigate("/auth");
  };

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-primary/30 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto flex h-14 items-center justify-between px-4">
          <h1 className="text-xl font-bold neon-text" style={{ color: 'hsl(180 100% 65%)' }}>Pulso Tech</h1>
          
          <div className="flex items-center gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <div className="relative group">
                  {/* Círculo neon que muda de cor */}
                  <div className="absolute inset-0 rounded-full blur-md bg-primary/50 group-hover:bg-primary/70 group-active:bg-dataAi/70 transition-all duration-300 group-hover:blur-lg group-active:blur-xl"></div>
                  
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    aria-label="Menu do usuário"
                    className="relative z-10 border-2 border-primary group-hover:border-primary group-active:border-dataAi shadow-[0_0_20px_rgba(0,255,255,0.6)] group-hover:shadow-[0_0_35px_rgba(0,255,255,0.9)] group-active:shadow-[0_0_45px_rgba(191,0,255,1)] transition-all duration-300 group-hover:scale-105 group-active:scale-95"
                  >
                    <User className="h-5 w-5" />
                  </Button>
                </div>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => setProfileOpen(true)}>
                  <UserCircle className="mr-2 h-4 w-4" />
                  Perfil
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleSwitchAccount}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Trocar de conta
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
      </header>

      <ProfileDialog open={profileOpen} onOpenChange={setProfileOpen} />
    </>
  );
};

export default DashboardHeader;
