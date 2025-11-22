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
      
      // Restaurar perfil selecionado do localStorage se existir e for válido
      const savedProfileId = localStorage.getItem("selectedProfileId");
      if (savedProfileId) {
        // Verificar se o perfil salvo existe na lista de perfis carregados
        const profileExists = profilesList.some((p: Profile) => p.id === savedProfileId);
        if (profileExists) {
          setSelectedProfileId(savedProfileId);
        } else {
          // Perfil salvo não existe mais (foi deletado ou é de outro dispositivo)
          // Limpar o ID salvo e deixar o usuário escolher
          localStorage.removeItem("selectedProfileId");
        }
      }
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
    // Não salvar perfis completos no localStorage - a fonte de verdade é o servidor
  };

  const handleSelectProfile = (profileId: string) => {
    setSelectedProfileId(profileId);
  };

  const handleAccessPlatform = async () => {
    if (!selectedProfileId) {
      toast({
        title: "Selecione um perfil",
        description: "Você precisa selecionar um perfil para continuar",
        variant: "destructive",
      });
      return;
    }

    try {
      const token = localStorage.getItem("token");
      if (!token) {
        toast({
          title: "Erro de autenticação",
          description: "Token não encontrado. Faça login novamente.",
          variant: "destructive",
        });
        navigate("/auth");
        return;
      }

      // Verificar se o perfil selecionado existe e pertence ao usuário
      const profileRes = await fetch(`${PROFILES_URL}/${selectedProfileId}`, {
        method: "GET",
        headers: {
          "Authorization": `Bearer ${token}`,
        },
      });

      if (!profileRes.ok) {
        if (profileRes.status === 404) {
          toast({
            title: "Perfil não encontrado",
            description: "O perfil selecionado não existe mais. Selecione outro perfil.",
            variant: "destructive",
          });
          // Recarregar lista de perfis
          fetchProfiles();
          return;
        }
        throw new Error("Erro ao validar perfil");
      }

      // ⚠️ PROBLEMA IDENTIFICADO:
      // As rotas para salvar o perfil selecionado no backend NÃO ESTÃO SENDO DISPARADAS
      // porque as rotas não existem no backend ou estão retornando erro.
      //
      // SOLUÇÃO NECESSÁRIA NO BACKEND:
      // O backend PRECISA implementar uma das seguintes rotas para sincronizar o perfil entre dispositivos:
      //
      // Opção 1 (Recomendada): PUT /auth/user/selected-profile
      //   - Body: { "selectedProfileId": "profile_id_aqui" }
      //   - Response: { "success": true, "selectedProfileId": "profile_id_aqui" }
      //
      // Opção 2: PUT /auth/user
      //   - Body: { "selectedProfileId": "profile_id_aqui" }
      //   - Deve atualizar o campo selectedProfileId no modelo User
      //
      // Opção 3: Adicionar campo selectedProfileId ao modelo User no banco e criar rota para atualizar
      //
      // IMPORTANTE: Sem essas rotas, o perfil será salvo APENAS no localStorage local,
      // o que significa que NÃO será sincronizado entre diferentes dispositivos/navegadores!
      
      console.log("🔍 Tentando salvar perfil selecionado no backend...");
      console.log("📤 Perfil ID:", selectedProfileId);
      console.log("📤 URL da API:", API_URL);
      
      let savedToBackend = false;
      let lastError: string | null = null;
      let lastStatus: number | null = null;
      
      try {
        // Tentativa 1: Rota específica para perfil selecionado
        console.log("🔄 Tentativa 1: PUT /auth/user/selected-profile");
        const saveRes = await fetch(`${API_URL}/auth/user/selected-profile`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${token}`,
          },
          body: JSON.stringify({ selectedProfileId }),
        });

        console.log("📥 Resposta recebida - Status:", saveRes.status, saveRes.statusText);

        if (saveRes.ok) {
          savedToBackend = true;
          console.log("✅ SUCESSO! Perfil selecionado salvo no backend via /auth/user/selected-profile");
          const responseData = await saveRes.json();
          console.log("📥 Dados da resposta:", responseData);
        } else {
          lastStatus = saveRes.status;
          
          if (saveRes.status === 404) {
            console.warn("⚠️ Rota /auth/user/selected-profile não existe (404). Tentando alternativa...");
            lastError = "Rota não encontrada (404)";
            
            // Tentativa 2: Rota de atualização de usuário
            console.log("🔄 Tentativa 2: PUT /auth/user");
            try {
              const userRes = await fetch(`${API_URL}/auth/user`, {
                method: "PUT",
                headers: {
                  "Content-Type": "application/json",
                  "Authorization": `Bearer ${token}`,
                },
                body: JSON.stringify({ selectedProfileId }),
              });

              console.log("📥 Resposta /auth/user - Status:", userRes.status, userRes.statusText);

              if (userRes.ok) {
                savedToBackend = true;
                console.log("✅ SUCESSO! Perfil selecionado salvo via /auth/user");
                const responseData = await userRes.json();
                console.log("📥 Dados da resposta:", responseData);
              } else {
                lastStatus = userRes.status;
                const errorText = await userRes.text();
                lastError = `Status ${userRes.status}: ${errorText.substring(0, 100)}`;
                console.error("❌ Falha ao salvar via /auth/user:", userRes.status, errorText);
              }
            } catch (userErr: any) {
              lastError = userErr.message || "Erro na requisição";
              console.error("❌ Erro ao tentar salvar via /auth/user:", userErr);
            }
          } else {
            // Outro erro (401, 403, 500, etc)
            const errorText = await saveRes.text();
            lastError = `Status ${saveRes.status}: ${errorText.substring(0, 100)}`;
            console.error("❌ Erro ao salvar perfil selecionado:", saveRes.status);
            console.error("❌ Detalhes do erro:", errorText);
          }
        }

        if (!savedToBackend) {
          console.error("============================================");
          console.error("❌ FALHA AO SALVAR PERFIL SELECIONADO NO BACKEND!");
          console.error("============================================");
          console.error("📊 Status HTTP:", lastStatus || "N/A");
          console.error("📝 Mensagem:", lastError || "Rota não encontrada");
          console.error("🔧 AÇÃO NECESSÁRIA: Implemente uma das rotas no backend:");
          console.error("   1. PUT /auth/user/selected-profile");
          console.error("   2. PUT /auth/user (com campo selectedProfileId no body)");
          console.error("⚠️  IMPACTO: Perfil será salvo APENAS no localStorage local");
          console.error("⚠️  CONSEQUÊNCIA: NÃO será sincronizado entre dispositivos!");
          console.error("============================================");
          
          // Mostrar aviso visual ao usuário (apenas em desenvolvimento)
          if (process.env.NODE_ENV === 'development') {
            toast({
              title: "⚠️ Backend: Rota não encontrada",
              description: `Status ${lastStatus || 'N/A'}: ${lastError || 'Rota para salvar perfil selecionado não existe'}`,
              variant: "default",
            });
          }
        } else {
          console.log("✅✅✅ Perfil selecionado salvo com SUCESSO no backend! ✅✅✅");
        }
      } catch (err: any) {
        console.error("============================================");
        console.error("❌ ERRO DE REDE ao salvar perfil selecionado!");
        console.error("============================================");
        console.error("📝 Erro:", err.message);
        console.error("📊 Tipo:", err.name);
        console.error("🔗 URL tentada:", `${API_URL}/auth/user/selected-profile`);
        console.error("⚠️  O perfil será salvo apenas no localStorage local");
        console.error("============================================");
        
        lastError = err.message || "Erro de rede";
        
        toast({
          title: "Erro de conexão",
          description: "Não foi possível conectar ao servidor. O perfil será salvo apenas localmente.",
          variant: "destructive",
        });
      }

      // Salvar no localStorage como fallback/cache local
      localStorage.setItem("selectedProfileId", selectedProfileId);
      
      toast({
        title: "Perfil selecionado",
        description: "Acessando a plataforma...",
      });

      navigate("/dashboard");
    } catch (err: any) {
      toast({
        title: "Erro ao selecionar perfil",
        description: err.message || "Não foi possível selecionar o perfil. Tente novamente.",
        variant: "destructive",
      });
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("isAuthenticated");
    localStorage.removeItem("token");
    localStorage.removeItem("selectedProfileId");
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
