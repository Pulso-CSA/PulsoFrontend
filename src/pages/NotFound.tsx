import { useLocation, Link } from "react-router-dom";
import { useEffect } from "react";
import { AlertCircle, Home, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";

const NotFound = () => {
  const location = useLocation();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="glass-strong rounded-2xl p-12 max-w-md w-full mx-4 text-center space-y-6 animate-fade-in">
        <div className="flex justify-center">
          <div className="relative">
            <AlertCircle className="w-20 h-20 text-destructive animate-pulse" strokeWidth={1.5} />
            <div className="absolute inset-0 blur-xl bg-destructive/30 animate-pulse" />
          </div>
        </div>
        
        <div className="space-y-2">
          <h1 className="text-7xl font-bold neon-text bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
            404
          </h1>
          <p className="text-2xl font-semibold text-foreground">
            Página não encontrada
          </p>
          <p className="text-muted-foreground">
            A página que você está procurando não existe ou foi movida.
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 justify-center pt-4">
          <Button
            variant="default"
            size="lg"
            asChild
            className="neon-glow group"
          >
            <Link to="/">
              <Home className="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
              Voltar ao Início
            </Link>
          </Button>
          
          <Button
            variant="outline"
            size="lg"
            onClick={() => window.history.back()}
            className="glass hover:glass-strong"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Voltar
          </Button>
        </div>

        <p className="text-xs text-muted-foreground pt-4">
          Caminho: <code className="glass px-2 py-1 rounded text-primary">{location.pathname}</code>
        </p>
      </div>
    </div>
  );
};

export default NotFound;
