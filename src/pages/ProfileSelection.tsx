import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { Check, Plus, ArrowRight, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import ProfileManagement from "@/components/dashboard/ProfileManagement";
import { Profile } from "@/components/dashboard/ProfileManagement";
import { useToast } from "@/hooks/use-toast";

const API_URL = "https://pulsoapi-production-d109.up.railway.app";
const PROFILES_URL = `${API_URL}/profiles`;

const ProfileSelection = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Buscar perfis do servidor
  const fetchProfiles = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        navigate("/auth");
        return;
      }

      const res = await fetch(`${PROFILES_URL}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!res.ok) {
        if (res.status === 401) {
          localStorage.removeItem("isAuthenticated");
          localStorage.removeItem("token");
          navigate("/auth");
          return;
        }
        throw new Error("Erro ao buscar perfis");
      }

      const data = await res.json();
      // A API pode retornar um array ou um objeto com perfis
      const profilesList = Array.isArray(data) ? data : (data.profiles || []);
      
      setProfiles(profilesList);
      // Atualizar localStorage como cache
      localStorage.setItem("profiles", JSON.stringify(profilesList));
    } catch (err: any) {
      toast({
        title: "Erro ao carregar perfis",
        description: err.message || "Não foi possível carregar os perfis. Tente novamente.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [navigate, toast]);

  useEffect(() => {
    const isAuthenticated = localStorage.getItem("isAuthenticated");
    if (!isAuthenticated) {
      navigate("/auth");
      return;
    }

    // Sempre buscar do servidor ao invés de usar apenas localStorage
    fetchProfiles();
  }, [navigate, fetchProfiles]);

  const handleProfilesChange = (updatedProfiles: Profile[]) => {
    setProfiles(updatedProfiles);
    // Atualizar localStorage como cache (mas a fonte de verdade é o servidor)
    localStorage.setItem("profiles", JSON.stringify(updatedProfiles));
  };

  const handleSelectProfile = (profileId: string) => {
    setSelectedProfileId(profileId);
  };

  const handleAccessPlatform = () => {
    if (!selectedProfileId) {
      toast({
        title: "Selecione um perfil",
        description: "Você precisa selecionar um perfil para continuar",
        variant: "destructive",
      });
      return;
    }

    const selectedProfile = profiles.find(p => p.id === selectedProfileId);
    localStorage.setItem("currentProfile", JSON.stringify(selectedProfile));
    navigate("/dashboard");
  };

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("currentProfile");
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
      <div className="glass-strong border-b relative z-10">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-primary">Pulso CSA</h1>
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

          {/* Loading State */}
          {loading && (
            <div className="text-center py-8">
              <p className="text-muted-foreground">Carregando perfis...</p>
            </div>
          )}

          {/* Profile Selection Grid */}
          {!loading && profiles.length > 0 && (
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
                      selectedProfileId === profile.id
                        ? "border-2 border-primary bg-primary/10 shadow-[0_0_20px_rgba(0,255,255,0.3)]"
                        : "border border-primary/20 hover:border-primary/40"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-bold text-lg text-foreground truncate flex items-center gap-2">
                          {profile.name}
                          {selectedProfileId === profile.id && (
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
                  disabled={!selectedProfileId}
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
          {!loading && (
            <div className="glass-strong rounded-2xl p-6 border-2 border-primary/20">
              <ProfileManagement
                profiles={profiles}
                onProfilesChange={handleProfilesChange}
                maxProfiles={5}
              />
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default ProfileSelection;
