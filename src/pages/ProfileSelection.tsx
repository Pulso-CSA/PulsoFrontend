import { useNavigate } from "react-router-dom";
import { ArrowRight, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import ProfileManagement from "@/components/dashboard/ProfileManagement";
import { useToast } from "@/hooks/use-toast";
import ThemeSelector from "@/components/ThemeSelector";
import { useAuth } from "@/contexts/AuthContext";
import { electronFloatingToolbarClass } from "@/lib/electronClient";

const ProfileSelection = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { currentProfile, logout } = useAuth();

  const handleAccessPlatform = () => {
    if (!currentProfile) {
      toast({
        title: "Selecione um perfil",
        description: "Escolha um perfil na lista para continuar.",
        variant: "destructive",
      });
      return;
    }
    navigate("/dashboard");
  };

  const handleLogout = async () => {
    await logout();
    navigate("/auth");
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 pb-10 relative overflow-hidden">
      <div className={electronFloatingToolbarClass()}>
        <ThemeSelector />
        <Button
          type="button"
          onClick={handleLogout}
          variant="outline"
          size="sm"
          className="gap-2 border-destructive/30 hover:border-destructive hover:bg-destructive/10 text-destructive"
        >
          <LogOut className="h-4 w-4" />
          Sair
        </Button>
      </div>

      <main className="w-full max-w-lg relative z-10 flex flex-col gap-8 animate-fade-in">
        <header className="text-center space-y-3 px-1">
          <img
            src={import.meta.env.BASE_URL + "App.png"}
            alt=""
            className="h-16 w-16 mx-auto object-contain drop-shadow-[0_0_20px_hsl(var(--primary)/0.35)]"
          />
          <div className="space-y-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight">
              Selecione seu perfil
            </h1>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto leading-relaxed">
              Um perfil guarda o seu contexto na plataforma. Escolha um existente ou crie outro.
            </p>
          </div>
        </header>

        <section
          className="rounded-2xl border-2 border-primary/25 bg-card/70 backdrop-blur-xl shadow-[0_0_40px_-12px_hsl(var(--primary)/0.25)] overflow-hidden"
          aria-labelledby="profile-picker-heading"
        >
          <h2 id="profile-picker-heading" className="sr-only">
            Lista de perfis
          </h2>
          <div className="p-5 sm:p-6">
            <ProfileManagement maxProfiles={5} selectionMode />
          </div>
          <div className="px-5 sm:px-6 pb-5 sm:pb-6 pt-0">
            <div className="border-t border-primary/15 pt-5">
              <button
                type="button"
                onClick={handleAccessPlatform}
                disabled={!currentProfile}
                className="showcase-sparkle-btn w-full justify-center gap-2 min-h-[48px] disabled:opacity-45 disabled:cursor-not-allowed disabled:pointer-events-none"
              >
                <span className="showcase-spark" aria-hidden />
                <span className="absolute inset-[0.1em] rounded-[100px] bg-background/80 pointer-events-none" />
                <span className="relative z-10 font-medium">Acessar plataforma</span>
                <ArrowRight className="w-5 h-5 relative z-10 shrink-0" aria-hidden />
              </button>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
};

export default ProfileSelection;
