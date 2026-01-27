import { useState } from "react";
import { ArrowLeft, Mail, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { Link } from "react-router-dom";
import ThemeSelector from "@/components/ThemeSelector";
import { authApi } from "@/lib/api";
import { z } from "zod";

const emailSchema = z.string().email("E-mail inválido");

const ForgotPassword = () => {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate email
    try {
      emailSchema.parse(email);
    } catch {
      toast({
        title: "E-mail inválido",
        description: "Informe um e-mail válido",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    
    try {
      await authApi.requestPasswordReset(email);
      setEmailSent(true);
      toast({
        title: "E-mail enviado",
        description: "Verifique sua caixa de entrada para redefinir a senha",
      });
    } catch (error) {
      // Don't reveal if email exists or not for security
      toast({
        title: "Solicitação processada",
        description: "Se o e-mail estiver cadastrado, você receberá as instruções",
      });
      setEmailSent(true);
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
            Recuperação de senha
          </p>
        </div>

        <div className="glass-strong border-2 border-primary/30 rounded-2xl p-8 shadow-[0_0_30px_rgba(0,255,255,0.2)]">
          {emailSent ? (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-success/20 flex items-center justify-center mx-auto">
                <CheckCircle className="h-8 w-8 text-success" />
              </div>
              <h2 className="text-xl font-semibold">E-mail enviado!</h2>
              <p className="text-muted-foreground">
                Se o e-mail <strong>{email}</strong> estiver cadastrado, você receberá um link para redefinir sua senha.
              </p>
              <p className="text-sm text-muted-foreground">
                Não recebeu? Verifique a pasta de spam ou tente novamente em alguns minutos.
              </p>
              <div className="pt-4 space-y-2">
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setEmailSent(false)}
                >
                  Tentar outro e-mail
                </Button>
                <Link to="/auth" className="block">
                  <Button variant="ghost" className="w-full gap-2">
                    <ArrowLeft className="h-4 w-4" />
                    Voltar para login
                  </Button>
                </Link>
              </div>
            </div>
          ) : (
            <>
              <div className="text-center mb-6">
                <div className="w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center mx-auto mb-4">
                  <Mail className="h-8 w-8 text-primary" />
                </div>
                <p className="text-muted-foreground">
                  Digite seu e-mail e enviaremos instruções para redefinir sua senha.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Label htmlFor="email">E-mail</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="nome@empresa.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoFocus
                  />
                </div>

                <Button 
                  type="submit" 
                  className="w-full glass-strong border-2 border-primary hover:border-primary-light shadow-[0_0_20px_rgba(0,255,255,0.3)] hover:shadow-[0_0_30px_rgba(0,255,255,0.5)] bg-gradient-to-r from-primary/80 to-primary-deep/60 transition-all duration-200" 
                  disabled={loading}
                >
                  {loading ? "Enviando..." : "Enviar link de recuperação"}
                </Button>
              </form>

              <div className="mt-6 text-center">
                <Link 
                  to="/auth" 
                  className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                >
                  <ArrowLeft className="h-3 w-3" />
                  Voltar para login
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
