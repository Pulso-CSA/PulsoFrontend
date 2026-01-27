import { useState, useEffect } from "react";
import { Eye, EyeOff, CheckCircle2, XCircle, Lock, CheckCircle, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import ThemeSelector from "@/components/ThemeSelector";
import { authApi } from "@/lib/api";

const ResetPassword = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [token, setToken] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [invalidToken, setInvalidToken] = useState(false);

  useEffect(() => {
    const tokenParam = searchParams.get("token");
    if (!tokenParam) {
      setInvalidToken(true);
    } else {
      setToken(tokenParam);
    }
  }, [searchParams]);

  const passwordStrength = (pwd: string) => {
    let strength = 0;
    if (pwd.length >= 8) strength++;
    if (/[A-Z]/.test(pwd)) strength++;
    if (/[0-9]/.test(pwd)) strength++;
    if (/[^A-Za-z0-9]/.test(pwd)) strength++;
    
    if (strength <= 1) return { level: "Fraca", color: "text-destructive" };
    if (strength <= 2) return { level: "Ok", color: "text-warning" };
    return { level: "Forte", color: "text-success" };
  };

  const passwordChecklist = [
    { label: "8+ caracteres", valid: password.length >= 8 },
    { label: "Letra maiúscula", valid: /[A-Z]/.test(password) },
    { label: "Número", valid: /[0-9]/.test(password) },
    { label: "Símbolo", valid: /[^A-Za-z0-9]/.test(password) },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (password !== confirmPassword) {
      toast({
        title: "Senhas não coincidem",
        description: "As senhas devem ser iguais",
        variant: "destructive",
      });
      return;
    }

    if (password.length < 8) {
      toast({
        title: "Senha muito curta",
        description: "A senha deve ter pelo menos 8 caracteres",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    
    try {
      await authApi.resetPassword(token, password);
      setSuccess(true);
      toast({
        title: "Senha alterada",
        description: "Sua senha foi redefinida com sucesso",
      });
    } catch (error) {
      toast({
        title: "Erro ao redefinir senha",
        description: error instanceof Error ? error.message : "Link inválido ou expirado",
        variant: "destructive",
      });
      setInvalidToken(true);
    } finally {
      setLoading(false);
    }
  };

  if (invalidToken) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
        <div className="absolute top-4 right-4 z-20">
          <ThemeSelector />
        </div>

        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-20 right-20 w-72 h-72 bg-finops/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>

        <div className="w-full max-w-md relative z-10">
          <div className="glass-strong border-2 border-destructive/30 rounded-2xl p-8 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-destructive/20 flex items-center justify-center mx-auto">
              <AlertCircle className="h-8 w-8 text-destructive" />
            </div>
            <h2 className="text-xl font-semibold">Link inválido ou expirado</h2>
            <p className="text-muted-foreground">
              O link de recuperação de senha não é válido ou já expirou. Solicite um novo link.
            </p>
            <div className="pt-4">
              <Link to="/forgot-password">
                <Button className="w-full">
                  Solicitar novo link
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
        <div className="absolute top-4 right-4 z-20">
          <ThemeSelector />
        </div>

        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-20 right-20 w-72 h-72 bg-finops/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        </div>

        <div className="w-full max-w-md relative z-10">
          <div className="glass-strong border-2 border-success/30 rounded-2xl p-8 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mx-auto">
              <CheckCircle className="h-8 w-8 text-success" />
            </div>
            <h2 className="text-xl font-semibold">Senha redefinida!</h2>
            <p className="text-muted-foreground">
              Sua senha foi alterada com sucesso. Agora você pode fazer login com a nova senha.
            </p>
            <div className="pt-4">
              <Link to="/auth">
                <Button className="w-full glass-strong border-2 border-primary hover:border-primary-light shadow-[0_0_20px_rgba(0,255,255,0.3)]">
                  Ir para login
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4 relative overflow-hidden">
      <div className="absolute top-4 right-4 z-20">
        <ThemeSelector />
      </div>

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
            Criar nova senha
          </p>
        </div>

        <div className="glass-strong border-2 border-primary/30 rounded-2xl p-8 shadow-[0_0_30px_rgba(0,255,255,0.2)]">
          <div className="text-center mb-6">
            <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4">
              <Lock className="h-8 w-8 text-primary" />
            </div>
            <p className="text-muted-foreground">
              Digite sua nova senha abaixo.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="password">Nova senha</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  autoFocus
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
              
              {password && (
                <div className="mt-2 space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">Força:</span>
                    <span className={`text-sm font-medium ${passwordStrength(password).color}`}>
                      {passwordStrength(password).level}
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

            <div>
              <Label htmlFor="confirmPassword">Confirmar senha</Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
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
              {confirmPassword && password !== confirmPassword && (
                <p className="text-xs text-destructive mt-1">As senhas não coincidem</p>
              )}
            </div>

            <Button 
              type="submit" 
              className="w-full glass-strong border-2 border-primary hover:border-primary-light shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)] bg-gradient-to-r from-primary/80 to-primary-deep/60 transition-all duration-200" 
              disabled={loading}
            >
              {loading ? "Salvando..." : "Redefinir senha"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ResetPassword;
