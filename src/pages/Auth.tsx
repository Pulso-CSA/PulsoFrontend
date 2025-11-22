import { useState } from "react";
import { Eye, EyeOff, CheckCircle2, XCircle, Chrome, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { useNavigate } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { z } from "zod";

// ⭐ BACKEND REAL
const API_URL = "https://pulsoapi-production-d109.up.railway.app";
const AUTH_URL = `${API_URL}/auth`;
const PROFILES_URL = `${API_URL}/profiles`;

const profileSchema = z.object({
  name: z.string()
    .trim()
    .min(1, "Nome é obrigatório")
    .max(50, "Nome deve ter no máximo 50 caracteres"),
  description: z.string()
    .trim()
    .max(200, "Descrição deve ter no máximo 200 caracteres")
    .optional(),
});

const Auth = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [profileData, setProfileData] = useState({ name: "", description: "" });
  const [profileErrors, setProfileErrors] = useState<{ name?: string; description?: string }>({});
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
  });
  const { toast } = useToast();
  const navigate = useNavigate();

  const passwordStrength = (password: string) => {
    let strength = 0;
    if (password.length >= 8) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^A-Za-z0-9]/.test(password)) strength++;
    
    if (strength <= 1) return { level: "Fraca", color: "text-destructive" };
    if (strength <= 2) return { level: "Ok", color: "text-warning" };
    return { level: "Forte", color: "text-success" };
  };

  const passwordChecklist = [
    { label: "8+ caracteres", valid: formData.password.length >= 8 },
    { label: "Letra maiúscula", valid: /[A-Z]/.test(formData.password) },
    { label: "Número", valid: /[0-9]/.test(formData.password) },
    { label: "Símbolo", valid: /[^A-Za-z0-9]/.test(formData.password) },
  ];

  const validateEmail = (email: string) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

  const validateProfile = () => {
    try {
      profileSchema.parse(profileData);
      setProfileErrors({});
      return true;
    } catch (error) {
      if (error instanceof z.ZodError) {
        const newErrors: { name?: string; description?: string } = {};
        error.errors.forEach((err) => {
          if (err.path[0]) {
            newErrors[err.path[0] as keyof typeof newErrors] = err.message;
          }
        });
        setProfileErrors(newErrors);
      }
      return false;
    }
  };

  const handleCreateProfile = async () => {
    if (!validateProfile()) return;

    setProfileLoading(true);

    try {
      const token = localStorage.getItem("token");
      
      if (!token) {
        toast({
          title: "Erro de autenticação",
          description: "Token não encontrado. Faça login novamente.",
          variant: "destructive",
        });
        setProfileLoading(false);
        return;
      }

      const res = await fetch(`${PROFILES_URL}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          name: profileData.name.trim(),
          description: profileData.description.trim() || undefined,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || "Erro ao criar perfil");
      }

      // Salva apenas o ID do perfil selecionado no localStorage
      localStorage.setItem("selectedProfileId", data.id);
      
      // Recarrega os perfis do servidor para garantir sincronização
      try {
        const profilesRes = await fetch(`${PROFILES_URL}`, {
          method: "GET",
          headers: {
            "Authorization": `Bearer ${token}`,
          },
        });

        if (profilesRes.ok) {
          // Perfis são carregados do backend, não salvos no localStorage
          // O ID do perfil selecionado já foi salvo acima
        }
      } catch (err) {
        // Se falhar, continuar mesmo assim
        console.error("Erro ao recarregar perfis:", err);
      }

      setShowProfileDialog(false);
      toast({
        title: "Conta criada com sucesso",
        description: `Perfil "${data.name}" criado. Bem-vindo!`,
      });
      navigate("/profile-selection");

    } catch (err: any) {
      toast({
        title: "Erro ao criar perfil",
        description: err.message || "Não foi possível criar o perfil. Tente novamente.",
        variant: "destructive",
      });
    } finally {
      setProfileLoading(false);
    }
  };

  // ⭐ FLUXO DE LOGIN/REGISTRO
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Prevenir múltiplos envios
    if (loading) return;
    
    setLoading(true);

    // Normalizar email (lowercase e trim)
    const normalizedEmail = formData.email.toLowerCase().trim();

    if (!validateEmail(normalizedEmail)) {
      toast({
        title: "E-mail inválido",
        description: "Informe um e-mail válido",
        variant: "destructive",
      });
      setLoading(false);
      return;
    }

    try {
      const endpoint = isLogin ? "/login" : "/register";

      if (!isLogin) {
        if (formData.password !== formData.confirmPassword) {
          toast({
            title: "Senhas não coincidem",
            description: "As senhas devem ser iguais",
            variant: "destructive",
          });
          setLoading(false);
          return;
        }

        if (!formData.acceptTerms) {
          toast({
            title: "Aceite os termos",
            description: "É necessário concordar com a política de uso",
            variant: "destructive",
          });
          setLoading(false);
          return;
        }
      }

      const res = await fetch(`${AUTH_URL}${endpoint}`, {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
        },
        cache: "no-store", // Prevenir cache
        body: JSON.stringify({
          name: formData.name.trim(),
          email: normalizedEmail, // Email normalizado
          password: formData.password,
        }),
      });

      const data = await res.json();

      // Tratamento específico para erro 409 (email já cadastrado)
      if (!res.ok) {
        if (res.status === 409) {
          toast({
            title: "E-mail já cadastrado",
            description: "Este e-mail já está cadastrado. Faça login ou use outro e-mail.",
            variant: "destructive",
          });
          setLoading(false);
          return;
        }
        throw new Error(data.detail || data.message || "Erro inesperado");
      }

      localStorage.setItem("isAuthenticated", "true");
      if (data.access_token) localStorage.setItem("token", data.access_token);

      if (!isLogin) {
        setShowProfileDialog(true);
      } else {
        // Ao fazer login, buscar perfil selecionado do backend (se existir)
        try {
          // Tentar buscar o perfil selecionado do backend
          const userRes = await fetch(`${API_URL}/auth/user`, {
            method: "GET",
            headers: {
              "Authorization": `Bearer ${data.access_token}`,
            },
          });

          if (userRes.ok) {
            const userData = await userRes.json();
            // Se o usuário tem um perfil selecionado salvo no backend
            if (userData.selectedProfileId) {
              // Verificar se o perfil ainda existe
              const profileCheckRes = await fetch(`${PROFILES_URL}/${userData.selectedProfileId}`, {
                method: "GET",
                headers: {
                  "Authorization": `Bearer ${data.access_token}`,
                },
              });

              if (profileCheckRes.ok) {
                // Perfil existe, salvar no localStorage
                localStorage.setItem("selectedProfileId", userData.selectedProfileId);
              } else {
                // Perfil não existe mais, limpar do localStorage
                localStorage.removeItem("selectedProfileId");
              }
            }
          } else if (userRes.status !== 404) {
            // Se a rota não existir (404), ignoramos e continuamos
            // Outros erros também são ignorados para não bloquear o login
            console.warn("Não foi possível buscar dados do usuário do backend:", userRes.status);
          }
        } catch (err) {
          // Se não houver rota disponível, apenas logamos e continuamos
          console.warn("Rota para buscar perfil selecionado não disponível, usando localStorage:", err);
        }

        // Navegar para seleção de perfis
        navigate("/profile-selection");
      }

      toast({
        title: isLogin ? "Login realizado" : "Conta criada",
        description: "Bem-vindo!",
      });

    } catch (err: any) {
      toast({
        title: "Erro",
        description: err.message,
        variant: "destructive",
      });
    }

    setLoading(false);
  };

  // ⭐ LOGIN COM GOOGLE
  const handleGoogleLogin = () => {
    window.location.href = `${AUTH_URL}/login/google`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Background animated elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-20 w-72 h-72 bg-finops/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="w-full max-w-md relative z-10 animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 neon-text" style={{ 
            background: 'linear-gradient(135deg, hsl(180 100% 70%) 0%, hsl(150 100% 65%) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>Pulso</h1>
          <p className="text-foreground/80">
            {isLogin ? "Acesse sua conta" : "Crie sua conta"}
          </p>
        </div>

        <div className="glass-strong border-2 border-primary/30 rounded-2xl p-8 shadow-[0_0_30px_rgba(0,255,255,0.2)]">
          <Button
            type="button"
            variant="outline"
            className="w-full glass glass-hover border-2 hover:border-primary/50 mb-4 transition-all duration-200"
            onClick={handleGoogleLogin}
            disabled={loading}
          >
            <Chrome className="mr-2 h-5 w-5" />
            Continuar com Google
          </Button>

          <div className="relative my-6">
            <Separator />
            <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-3 text-xs text-muted-foreground">
              ou continue com e-mail
            </span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <Label htmlFor="name">Nome</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Seu nome completo"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required={!isLogin}
                />
              </div>
            )}

            <div>
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="nome@empresa.com"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value.trim() })}
                required
              />
            </div>

            <div>
              <Label htmlFor="password">Senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>

              {!isLogin && formData.password && (
                <div className="mt-2 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Força:</span>
                    <span className={`text-sm font-medium ${passwordStrength(formData.password).color}`}>
                      {passwordStrength(formData.password).level}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs">
                    {passwordChecklist.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-1">
                        {item.valid ? (
                          <CheckCircle2 className="h-3 w-3 text-success" />
                        ) : (
                          <XCircle className="h-3 w-3 text-muted-foreground" />
                        )}
                        <span className={item.valid ? "text-foreground" : "text-muted-foreground"}>
                          {item.label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {!isLogin && (
              <div>
                <Label htmlFor="confirmPassword">Confirmar Senha</Label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    required={!isLogin}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
            )}

            {!isLogin && (
              <div className="flex items-start gap-2">
                <Checkbox
                  id="terms"
                  checked={formData.acceptTerms}
                  onCheckedChange={(checked) => 
                    setFormData({ ...formData, acceptTerms: checked as boolean })
                  }
                />
                <Label htmlFor="terms" className="text-sm font-normal cursor-pointer">
                  Li e concordo com a política de uso
                </Label>
              </div>
            )}

            <Button 
              type="submit" 
              className="w-full glass-strong border-2 border-primary hover:border-primary-light shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)] bg-gradient-to-r from-primary/80 to-primary-deep/60 transition-all duration-200" 
              disabled={loading}
            >
              {loading ? "Carregando..." : isLogin ? "Entrar" : "Criar conta"}
            </Button>
          </form>

          <div className="mt-4 text-center space-y-2">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm text-primary hover:underline"
            >
              {isLogin ? "Criar conta" : "Já tenho conta"}
            </button>
            
            {isLogin && (
              <div>
                <button
                  type="button"
                  className="text-sm text-muted-foreground hover:text-foreground hover:underline"
                >
                  Esqueci minha senha
                </button>
              </div>
            )}
          </div>

          {!isLogin && (
            <p className="mt-4 text-xs text-muted-foreground text-center">
              Use uma senha única e nunca a compartilhe
            </p>
          )}
        </div>
      </div>

      <Dialog open={showProfileDialog} onOpenChange={() => {}}>
        <DialogContent className="sm:max-w-[500px]" onInteractOutside={(e) => e.preventDefault()}>
          <DialogHeader className="space-y-3">
            <DialogTitle className="text-2xl font-bold neon-text flex items-center gap-2" style={{ color: 'hsl(180 100% 65%)' }}>
              <UserPlus className="h-6 w-6" />
              Crie seu Primeiro Perfil
            </DialogTitle>
            <DialogDescription className="text-base">
              Para começar a usar a plataforma, você precisa criar pelo menos um perfil de trabalho.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="profile-name">Nome do Perfil*</Label>
              <Input
                id="profile-name"
                placeholder="Ex: Produção, Desenvolvimento"
                value={profileData.name}
                onChange={(e) => setProfileData({ ...profileData, name: e.target.value })}
                className={profileErrors.name ? "border-destructive" : "border-primary/20 focus:border-primary"}
              />
              {profileErrors.name && (
                <p className="text-xs text-destructive">{profileErrors.name}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile-description">Descrição</Label>
              <Input
                id="profile-description"
                placeholder="Breve descrição do perfil"
                value={profileData.description}
                onChange={(e) => setProfileData({ ...profileData, description: e.target.value })}
                className={profileErrors.description ? "border-destructive" : "border-primary/20 focus:border-primary"}
              />
              {profileErrors.description && (
                <p className="text-xs text-destructive">{profileErrors.description}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Você poderá criar até 5 perfis no total
              </p>
            </div>

            <Button
              onClick={handleCreateProfile}
              className="w-full gap-2 bg-primary hover:bg-primary/90 neon-glow transition-all duration-300 hover:scale-105 mt-6"
              disabled={profileLoading}
            >
              <UserPlus className="h-4 w-4" />
              {profileLoading ? "Criando perfil..." : "Criar Perfil e Começar"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Auth;
