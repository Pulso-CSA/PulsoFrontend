import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Activity, Database, Zap } from "lucide-react";

const Index = () => {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center max-w-2xl px-4">
        <h1 className="mb-4 text-5xl font-bold text-foreground">Pulso</h1>
        <p className="text-xl text-muted-foreground mb-8">
          Dashboard Operacional Inteligente
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="p-6 bg-card border border-border rounded-lg">
            <Zap className="h-8 w-8 text-primary mx-auto mb-3" />
            <h3 className="font-semibold text-foreground mb-2">Prompt Central</h3>
            <p className="text-sm text-muted-foreground">
              Descreva solicitações e receba blueprints estruturados
            </p>
          </div>
          
          <div className="p-6 bg-card border border-border rounded-lg">
            <Activity className="h-8 w-8 text-success mx-auto mb-3" />
            <h3 className="font-semibold text-foreground mb-2">FinOps</h3>
            <p className="text-sm text-muted-foreground">
              Insights de custos e otimizações em nuvem
            </p>
          </div>
          
          <div className="p-6 bg-card border border-border rounded-lg">
            <Database className="h-8 w-8 text-info mx-auto mb-3" />
            <h3 className="font-semibold text-foreground mb-2">Inteligência de Dados</h3>
            <p className="text-sm text-muted-foreground">
              Análises, correlações e modelos de ML
            </p>
          </div>
        </div>

        <Button size="lg" onClick={() => navigate("/auth")}>
          Acessar Dashboard
        </Button>
      </div>
    </div>
  );
};

export default Index;
