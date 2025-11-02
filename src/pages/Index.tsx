import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Activity, Database, Zap, Sparkles } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background overflow-hidden relative">
      {/* Background animated elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-20 w-72 h-72 bg-primary/20 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-finops/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-dataAi/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      <div className="text-center max-w-4xl px-4 relative z-10 animate-fade-in">
        <div className="mb-6 inline-flex items-center gap-2 px-4 py-2 glass rounded-full border border-primary/30">
          <Sparkles className="h-4 w-4 text-primary animate-pulse" />
          <span className="text-sm text-primary font-medium">Dashboard Operacional de Nova Geração</span>
        </div>

        <h1 className="mb-6 text-7xl font-bold neon-text animate-fade-in" style={{ 
          background: 'linear-gradient(135deg, hsl(180 100% 70%) 0%, hsl(150 100% 65%) 50%, hsl(270 100% 80%) 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          backgroundClip: 'text',
          animationDelay: '0.2s'
        }}>
          Pulso
        </h1>
        
        <p className="text-2xl text-foreground/90 mb-12 font-light animate-fade-in" style={{ animationDelay: '0.4s' }}>
          Transforme ideias em arquiteturas completas com inteligência artificial
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="group glass glass-hover p-8 rounded-2xl border-2 border-primary/40 hover:border-primary transition-all duration-200 hover:scale-105 animate-fade-in" style={{ animationDelay: '0.6s' }}>
            <div className="relative mb-4">
              <Zap className="h-12 w-12 text-primary mx-auto drop-shadow-[0_0_15px_rgba(0,255,255,0.8)] group-hover:scale-110 transition-transform duration-200" strokeWidth={1.5} />
              <div className="absolute inset-0 bg-primary/20 rounded-full blur-xl group-hover:bg-primary/30 transition-colors duration-200" />
            </div>
            <h3 className="font-bold text-xl text-primary mb-3">Prompt Central</h3>
            <p className="text-sm text-foreground/80 leading-relaxed">
              Descreva sua aplicação em linguagem natural e receba blueprints técnicos completos com estrutura de pastas, endpoints REST e arquitetura de microserviços
            </p>
          </div>
          
          <div className="group glass glass-hover p-8 rounded-2xl border-2 border-finops/40 hover:border-finops transition-all duration-200 hover:scale-105 animate-fade-in" style={{ animationDelay: '0.8s' }}>
            <div className="relative mb-4">
              <Activity className="h-12 w-12 text-finops mx-auto drop-shadow-[0_0_15px_rgba(0,255,153,0.8)] group-hover:scale-110 transition-transform duration-200" strokeWidth={1.5} />
              <div className="absolute inset-0 bg-finops/20 rounded-full blur-xl group-hover:bg-finops/30 transition-colors duration-200" />
            </div>
            <h3 className="font-bold text-xl text-finops mb-3">FinOps Inteligente</h3>
            <p className="text-sm text-foreground/80 leading-relaxed">
              Otimize custos na nuvem com análises em tempo real, sugestões de economia automáticas e insights sobre recursos subutilizados em AWS, Azure e GCP
            </p>
          </div>
          
          <div className="group glass glass-hover p-8 rounded-2xl border-2 border-dataAi/40 hover:border-dataAi transition-all duration-200 hover:scale-105 animate-fade-in" style={{ animationDelay: '1s' }}>
            <div className="relative mb-4">
              <Database className="h-12 w-12 text-dataAi mx-auto drop-shadow-[0_0_15px_rgba(191,0,255,0.8)] group-hover:scale-110 transition-transform duration-200" strokeWidth={1.5} />
              <div className="absolute inset-0 bg-dataAi/20 rounded-full blur-xl group-hover:bg-dataAi/30 transition-colors duration-200" />
            </div>
            <h3 className="font-bold text-xl text-dataAi mb-3">Inteligência de Dados</h3>
            <p className="text-sm text-foreground/80 leading-relaxed">
              Explore dados com IA, crie visualizações automatizadas, descubra correlações ocultas e construa modelos de machine learning sem código
            </p>
          </div>
        </div>

        <Button 
          size="lg" 
          onClick={() => navigate("/auth")}
          className="glass-strong text-lg px-12 py-7 rounded-xl font-bold border-2 border-primary hover:border-primary-light shadow-[0_0_30px_rgba(0,255,255,0.4)] hover:shadow-[0_0_50px_rgba(0,255,255,0.6)] transition-all duration-200 hover:scale-105 animate-fade-in bg-gradient-to-r from-primary/80 to-primary-deep/60 text-white"
          style={{ animationDelay: '1.2s' }}
        >
          <Sparkles className="mr-2 h-5 w-5" />
          Acessar Dashboard
        </Button>
      </div>
    </div>
  );
};

export default Index;
