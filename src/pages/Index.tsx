import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ArrowRight, Workflow, CloudCog, TrendingDown, Brain } from "lucide-react";
import ThemeSelector from "@/components/ThemeSelector";

const Index = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: Workflow,
      title: "Pulso CSA",
      description: "Gere código completo com IA",
      color: "primary",
    },
    {
      icon: CloudCog,
      title: "Cloud IaC",
      description: "Infraestrutura como código",
      color: "primary",
    },
    {
      icon: TrendingDown,
      title: "FinOps",
      description: "Otimize custos na nuvem",
      color: "finops",
    },
    {
      icon: Brain,
      title: "Data AI",
      description: "Explore dados com IA",
      color: "dataAi",
    }
  ];

  return (
    <div className="min-h-screen bg-background overflow-hidden relative flex flex-col">
      {/* Animated background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-[600px] h-[600px] bg-primary/10 rounded-full blur-[120px] animate-pulse" />
        <div className="absolute bottom-0 right-1/4 w-[500px] h-[500px] bg-finops/10 rounded-full blur-[100px] animate-pulse" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] bg-dataAi/8 rounded-full blur-[80px] animate-pulse" style={{ animationDelay: '3s' }} />
        
        {/* Grid pattern */}
        <div 
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage: `linear-gradient(hsl(var(--primary) / 0.3) 1px, transparent 1px), linear-gradient(90deg, hsl(var(--primary) / 0.3) 1px, transparent 1px)`,
            backgroundSize: '60px 60px'
          }}
        />
      </div>

      {/* Header */}
      <header className="relative z-10 flex items-center justify-between px-6 lg:px-12 py-5">
        <div /> {/* Spacer */}
        
        <div className="flex items-center gap-2">
          <ThemeSelector />
          <Button 
            variant="outline"
            onClick={() => navigate("/auth?mode=login")}
            className="border-primary/40 hover:border-primary hover:bg-primary/10 text-foreground"
          >
            Entrar
          </Button>
        </div>
      </header>

      {/* Hero Section - Centered */}
      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-6">
        <div className="text-center max-w-4xl mx-auto">
          {/* Main Title */}
          <h1 
            className="text-5xl md:text-7xl lg:text-8xl font-black mb-4 animate-fade-in tracking-tight"
            style={{ 
              background: 'linear-gradient(135deg, hsl(var(--primary)) 0%, hsl(var(--primary-deep)) 50%, hsl(var(--finops)) 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text',
            }}
          >
            Pulso
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto mb-10 animate-fade-in leading-relaxed" style={{ animationDelay: '0.1s' }}>
            Plataforma completa para desenvolvimento e gestão de aplicações com IA
          </p>

          {/* Features Grid - Inline */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 animate-fade-in" style={{ animationDelay: '0.2s' }}>
            {features.map((feature) => (
              <div 
                key={feature.title}
                className="flex flex-col items-center p-4 rounded-xl bg-card/20 backdrop-blur-sm border border-border/30 hover:border-primary/50 transition-all duration-300"
              >
                <feature.icon className={`w-8 h-8 text-${feature.color} mb-2`} strokeWidth={1.5} />
                <span className={`text-sm font-semibold text-${feature.color}`}>{feature.title}</span>
                <span className="text-xs text-muted-foreground text-center mt-1">{feature.description}</span>
              </div>
            ))}
          </div>

          {/* CTA Button */}
          <div className="animate-fade-in" style={{ animationDelay: '0.3s' }}>
            <Button 
              size="lg"
              onClick={() => navigate("/auth?mode=signup")}
              className="group relative px-8 py-6 text-lg font-semibold bg-gradient-to-r from-primary to-primary-deep hover:from-primary-light hover:to-primary text-primary-foreground rounded-xl transition-all duration-300 hover:scale-105 shadow-[0_0_40px_hsl(var(--primary)/0.3)] hover:shadow-[0_0_60px_hsl(var(--primary)/0.5)]"
            >
              <span>Começar Agora</span>
              <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Button>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Index;
