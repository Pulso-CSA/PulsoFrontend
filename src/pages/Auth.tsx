import { useState, useEffect } from "react";
import { Eye, EyeOff, CheckCircle2, XCircle, Chrome, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import { useToast } from "@/hooks/use-toast";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { z } from "zod";
import ThemeSelector from "@/components/ThemeSelector";
import { useAuth } from "@/contexts/AuthContext";
import { useProfiles } from "@/hooks/useProfiles";

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
  const [searchParams] = useSearchParams();
  const [isLogin, setIsLogin] = useState(() => searchParams.get("mode") !== "signup");
  const { isAuthenticated, isLoading: authLoading, login, loginWithGoogle, signup, profiles } = useAuth();
  const { createProfile } = useProfiles();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  useEffect(() => {
    const mode = searchParams.get("mode");
    setIsLogin(mode !== "signup");
  }, [searchParams]);

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      if (profiles.length === 0) {
        setShowProfileDialog(true);
      } else {
        navigate("/profile-selection");
      }
    }
  }, [isAuthenticated, authLoading, profiles, navigate]);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
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

  const validateEmail = (email: string) => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  };

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

    setLoading(true);
    try {
      await createProfile({
        name: profileData.name.trim(),
        description: profileData.description.trim(),
      });

      setShowProfileDialog(false);
      toast({
        title: "Conta criada com sucesso",
        description: `Perfil "${profileData.name}" criado. Bem-vindo!`,
      });
      navigate("/profile-selection");
    } catch (error) {
      toast({
        title: "Erro ao criar perfil",
        description: error instanceof Error ? error.message : "Tente novamente",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    // Validações
    if (!validateEmail(formData.email)) {
      toast({
        title: "E-mail inválido",
        description: "Informe um e-mail válido",
        variant: "destructive",
      });
      setLoading(false);
      return;
    }

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

    try {
      if (isLogin) {
        await login({ email: formData.email, password: formData.password });
        toast({
          title: "Login realizado",
          description: "Bem-vindo de volta!",
        });
        // Navigation handled by useEffect
      } else {
        await signup({ 
          email: formData.email, 
          password: formData.password,
          name: formData.name,
        });
        // Show profile dialog for new users
        setShowProfileDialog(true);
      }
    } catch (error) {
      toast({
        title: isLogin ? "Erro no login" : "Erro no cadastro",
        description: error instanceof Error ? error.message : "Tente novamente",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setLoading(true);
    try {
      await loginWithGoogle();
    } catch (error) {
      // Error handling is done in the auth context
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      {/* Theme Selector */}
      <div className="absolute top-4 right-4 z-20">
        <ThemeSelector />
      </div>

      {/* Background animated elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-20 w-72 h-72 bg-finops/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="w-full max-w-md relative z-10 animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-2 neon-text" style={{ 
            background: 'linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--finops)) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>Pulso</h1>
          <p className="text-foreground/80">
            {isLogin ? "Acesse sua conta" : "Crie sua conta"}
          </p>
        </div>

        <div className="glass-strong border-2 border-primary/30 rounded-2xl p-8 shadow-[0_0_30px_rgba(0,255,255,0.2)]">
          {/* Google Login Button */}
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
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
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
                  aria-label={showPassword ? "Ocultar senha" : "Mostrar senha"}
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
                    aria-label={showConfirmPassword ? "Ocultar senha" : "Mostrar senha"}
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

      {/* Create First Profile Dialog */}
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
              disabled={loading}
              className="w-full gap-2 bg-primary hover:bg-primary/90 neon-glow transition-all duration-300 hover:scale-105 mt-6"
            >
              <UserPlus className="h-4 w-4" />
              {loading ? "Criando..." : "Criar Perfil e Começar"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Auth;
