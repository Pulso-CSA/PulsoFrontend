import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { setStoredTokens } from "@/lib/api";
import { Loader2, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

/**
 * Rota de callback para OAuth (ex.: Google).
 * Espera access_token e refresh_token na query string.
 * O backend deve redirecionar para: {FRONTEND_URL}/auth/callback?access_token=...&refresh_token=...
 */
const AuthCallback = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const accessToken = searchParams.get("access_token");
    const refreshToken = searchParams.get("refresh_token");

    if (accessToken) {
      setStoredTokens(accessToken, refreshToken ?? undefined);
      navigate("/profile-selection", { replace: true });
    } else {
      setError("Token não recebido. O login com Google pode não estar configurado para redirecionar corretamente.");
    }
  }, [searchParams, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-background p-4 relative overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-20 left-20 w-72 h-72 pulso-orb animate-pulse" />
          <div className="absolute bottom-20 right-20 w-96 h-96 pulso-orb animate-pulse" style={{ animationDelay: "1s" }} />
        </div>
        <div className="glass-strong rounded-2xl p-8 max-w-md text-center border-2 border-destructive/30 relative z-10">
          <XCircle className="h-16 w-16 text-destructive mx-auto mb-4" />
          <h1 className="text-xl font-bold text-foreground mb-2">Erro no login</h1>
          <p className="text-muted-foreground mb-6">{error}</p>
          <Button asChild className="showcase-sparkle-btn gap-2">
            <Link to="/auth">
              <span className="showcase-spark" aria-hidden />
              Voltar ao login
            </Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background p-4 relative overflow-hidden">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 pulso-orb animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 pulso-orb animate-pulse" style={{ animationDelay: "1s" }} />
      </div>
      <div className="glass-strong rounded-2xl p-8 max-w-md text-center border-2 border-primary/30 relative z-10">
        <Loader2 className="h-16 w-16 text-primary animate-spin mx-auto mb-4" />
        <h1 className="text-xl font-bold text-foreground mb-2">Conectando...</h1>
        <p className="text-muted-foreground">Finalizando login com Google</p>
      </div>
    </div>
  );
};

export default AuthCallback;
