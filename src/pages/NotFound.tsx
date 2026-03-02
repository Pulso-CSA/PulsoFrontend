import { useLocation, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Home, ArrowLeft, Rocket, Coffee, Bug, Compass } from "lucide-react";
import { Button } from "@/components/ui/button";
import ThemeSelector from "@/components/ThemeSelector";

const NotFound = () => {
  const location = useLocation();
  const [message, setMessage] = useState("");

  const funMessages = [
    "Ops! Essa página saiu para um café ☕",
    "Houston, temos um problema! 🚀",
    "Esta página está de férias 🏖️",
    "404: Página brincando de esconde-esconde",
    "Parece que você encontrou um bug... ou não? 🐛",
    "Esta rota não consta no mapa 🗺️",
  ];

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
    setMessage(funMessages[Math.floor(Math.random() * funMessages.length)]);
  }, [location.pathname]);

  const icons = [Rocket, Coffee, Bug, Compass];
  const RandomIcon = icons[Math.floor(Math.random() * icons.length)];

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4 relative overflow-hidden">
      <div className="absolute top-4 right-4 z-20">
        <ThemeSelector />
      </div>
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 pulso-orb animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 pulso-orb animate-pulse" style={{ animationDelay: "1s" }} />
      </div>
      <div className="glass-strong rounded-2xl p-8 md:p-12 max-w-2xl w-full text-center space-y-8 animate-fade-in relative z-10">
        <div className="flex justify-center">
          <div className="relative">
            <RandomIcon 
              className="w-24 h-24 text-primary animate-pulse" 
              strokeWidth={1.5} 
            />
            <div className="absolute inset-0 blur-xl bg-primary/30 animate-pulse" />
          </div>
        </div>
        
        <div className="space-y-4">
          <h1 className="text-8xl md:text-9xl font-bold neon-text bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent animate-scale-in">
            404
          </h1>
          <p className="text-2xl md:text-3xl font-semibold text-foreground animate-fade-in">
            {message}
          </p>
          <p className="text-muted-foreground text-lg max-w-md mx-auto">
            Parece que você navegou para uma dimensão paralela. Não se preocupe, podemos te trazer de volta!
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 justify-center pt-6">
          <Button asChild variant="default" size="lg" className="showcase-sparkle-btn gap-2 px-8">
            <Link to="/">
              <span className="showcase-spark" aria-hidden />
              <Home className="w-5 h-5" />
              Ir para o Início
            </Link>
          </Button>
          
          <Button
            variant="pulso"
            size="lg"
            onClick={() => window.history.back()}
            className="glass hover:glass-strong hover-scale"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            Voltar
          </Button>
        </div>

        <div className="pt-6 space-y-2">
          <p className="text-sm text-muted-foreground">
            Rota não encontrada:
          </p>
          <code className="glass px-4 py-2 rounded-lg text-primary inline-block break-all">
            {location.pathname}
          </code>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
