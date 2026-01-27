import { useNavigate } from "react-router-dom";
import { Check, ArrowRight, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import ProfileManagement from "@/components/dashboard/ProfileManagement";
import { useToast } from "@/hooks/use-toast";
import ThemeSelector from "@/components/ThemeSelector";
import { useAuth } from "@/contexts/AuthContext";

const ProfileSelection = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { 
    profiles, 
    currentProfile,
    setCurrentProfile,
    logout 
  } = useAuth();

  const handleSelectProfile = (profileId: string) => {
    const profile = profiles.find(p => p.id === profileId);
    if (profile) {
      setCurrentProfile(profile);
    }
  };

  const handleAccessPlatform = () => {
    if (!currentProfile) {
      toast({
        title: "Selecione um perfil",
        description: "Você precisa selecionar um perfil para continuar",
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
    <div className="min-h-screen flex flex-col bg-background relative overflow-hidden">
      {/* Background animated elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-finops/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-dataAi/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* Header */}
      <div className="glass-strong relative z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">Pulso</h1>
          <div className="flex items-center gap-2">
            <ThemeSelector />
            <Button
            onClick={handleLogout}
            variant="outline"
            size="sm"
            className="gap-2 border-destructive/30 hover:border-destructive hover:bg-destructive/10 text-destructive"
          >
              <LogOut className="h-4 w-4" />
              Sair
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="flex-1 container mx-auto p-4 lg:p-6 relative z-10">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Title Section */}
          <div className="text-center space-y-2">
            <h2 className="text-3xl font-bold text-foreground">
              Selecione seu Perfil
            </h2>
            <p className="text-muted-foreground">
              Escolha ou crie um perfil para acessar a plataforma
            </p>
          </div>

          {/* Profile Selection Grid */}
          {profiles.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-foreground">
                Perfis Disponíveis
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profiles.map((profile) => (
                  <Card
                    key={profile.id}
                    onClick={() => handleSelectProfile(profile.id)}
                    className={`glass p-6 cursor-pointer transition-all hover:scale-105 ${
                      currentProfile?.id === profile.id
                        ? "border-2 border-primary bg-primary/10 shadow-[0_0_20px_rgba(0,255,255,0.3)]"
                        : "border border-primary/20 hover:border-primary/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-bold text-lg text-foreground truncate flex items-center gap-2">
                          {profile.name}
                          {currentProfile?.id === profile.id && (
                            <Check className="h-5 w-5 text-primary flex-shrink-0" />
                          )}
                        </h4>
                        {profile.description && (
                          <p className="text-sm text-muted-foreground mt-2">
                            {profile.description}
                          </p>
                        )}
                        <p className="text-xs text-muted-foreground mt-3">
                          Criado em: {new Date(profile.createdAt).toLocaleDateString('pt-BR')}
                        </p>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>

              {/* Access Button */}
              <div className="flex justify-center pt-4">
                <Button
                  onClick={handleAccessPlatform}
                  disabled={!currentProfile}
                  size="lg"
                  className="gap-2 bg-primary hover:bg-primary/90 px-8"
                >
                  Acessar Plataforma
                  <ArrowRight className="h-5 w-5" />
                </Button>
              </div>
            </div>
          )}

          {/* Profile Management */}
          <div className="glass-strong rounded-2xl p-6 border-2 border-primary/20">
            <ProfileManagement
              maxProfiles={5}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default ProfileSelection;
