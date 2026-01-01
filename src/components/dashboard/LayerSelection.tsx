import { Workflow, TrendingDown, Brain, CloudCog } from "lucide-react";

interface LayerSelectionProps {
  activeLayers: {
    preview: boolean;
    pulso: boolean;
    finops: boolean;
    data: boolean;
    cloud: boolean;
  };
  setActiveLayers: (layers: { preview: boolean; pulso: boolean; finops: boolean; data: boolean; cloud: boolean }) => void;
}

const LayerSelection = ({ activeLayers, setActiveLayers }: LayerSelectionProps) => {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold neon-text text-primary">
          Camadas Disponíveis
        </h2>
        <p className="text-sm text-foreground/80">
          Toque nos ícones para ativar/desativar
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8 max-w-7xl mx-auto">
        {/* Pulso CSA */}
        <div className="flex flex-col items-center text-center space-y-4 opacity-0 animate-slide-up stagger-1">
          <button
            onClick={() => setActiveLayers({ ...activeLayers, pulso: !activeLayers.pulso })}
            className={`
              group relative
              w-40 h-40 rounded-3xl
              transition-all duration-300 ease-out
              ${activeLayers.pulso 
                ? 'glass-strong bg-gradient-to-br from-primary/80 to-primary-deep/60 scale-105 border-2 border-primary shadow-[0_0_30px_hsl(var(--primary)/0.5)]' 
                : 'glass glass-hover shadow-lg hover:shadow-xl hover:scale-105 bg-gradient-to-br from-primary/20 to-primary-deep/10 border-2 border-primary/40'
              }
            `}
            aria-label="Toggle Pulso CSA"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <Workflow 
                className={`
                  transition-all duration-300 drop-shadow-[0_0_15px_hsl(var(--primary)/0.9)]
                  ${activeLayers.pulso 
                    ? 'w-20 h-20 text-primary-foreground' 
                    : 'w-16 h-16 text-primary group-hover:text-primary-foreground group-hover:w-18 group-hover:h-18'
                  }
                `}
                strokeWidth={1.5}
              />
            </div>
            
            {/* Pulse animation quando ativo */}
            {activeLayers.pulso && (
              <div className="absolute inset-0 rounded-3xl bg-primary/30 animate-pulse" />
            )}
          </button>
          
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 bg-primary/20 border-2 border-primary text-primary">
              Pulso CSA
            </div>
            
            <h3 className={`
              text-xl font-bold transition-colors duration-300
              ${activeLayers.pulso ? 'text-primary' : 'text-foreground'}
            `}>
              Blueprint & Estrutura
            </h3>
            
            <p className="text-sm text-muted-foreground max-w-xs">
              Gerar estrutura de pastas e endpoints
            </p>
          </div>
        </div>

        {/* Cloud Infrastructure */}
        <div className="flex flex-col items-center text-center space-y-4 opacity-0 animate-slide-up stagger-2">
          <button
            onClick={() => setActiveLayers({ ...activeLayers, cloud: !activeLayers.cloud })}
            className={`
              group relative
              w-40 h-40 rounded-3xl
              transition-all duration-300 ease-out
              ${activeLayers.cloud 
                ? 'glass-strong bg-gradient-to-br from-secondary/80 to-accent/60 scale-105 border-2 border-secondary shadow-[0_0_30px_hsl(var(--secondary)/0.5)]' 
                : 'glass glass-hover shadow-lg hover:shadow-xl hover:scale-105 bg-gradient-to-br from-secondary/20 to-accent/10 border-2 border-secondary/40'
              }
            `}
            aria-label="Toggle Cloud Infrastructure"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <CloudCog 
                className={`
                  transition-all duration-300 drop-shadow-[0_0_15px_hsl(var(--secondary)/0.9)]
                  ${activeLayers.cloud 
                    ? 'w-20 h-20 text-secondary-foreground' 
                    : 'w-16 h-16 text-secondary group-hover:text-secondary-foreground group-hover:w-18 group-hover:h-18'
                  }
                `}
                strokeWidth={1.5}
              />
            </div>
            
            {/* Pulse animation quando ativo */}
            {activeLayers.cloud && (
              <div className="absolute inset-0 rounded-3xl bg-secondary/30 animate-pulse" />
            )}
          </button>
          
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 bg-secondary/20 border-2 border-secondary text-secondary">
              Cloud IaC
            </div>
            
            <h3 className={`
              text-xl font-bold transition-colors duration-300
              ${activeLayers.cloud ? 'text-secondary' : 'text-foreground'}
            `}>
              Infraestrutura Cloud
            </h3>
            
            <p className="text-sm text-muted-foreground max-w-xs">
              Crie infra via chat · AWS, Azure, GCP
            </p>
          </div>
        </div>

        {/* Camada 5 - FinOps */}
        <div className="flex flex-col items-center text-center space-y-4 opacity-0 animate-slide-up stagger-3">
          <button
            onClick={() => setActiveLayers({ ...activeLayers, finops: !activeLayers.finops })}
            className={`
              group relative
              w-40 h-40 rounded-3xl
              transition-all duration-300 ease-out
              ${activeLayers.finops 
                ? 'glass-strong bg-gradient-to-br from-finops/80 to-success/60 scale-105 border-2 border-finops shadow-[0_0_30px_hsl(var(--finops)/0.5)]' 
                : 'glass glass-hover shadow-lg hover:shadow-xl hover:scale-105 bg-gradient-to-br from-finops/20 to-success/10 border-2 border-finops/40'
              }
            `}
            aria-label="Toggle Camada 5 - FinOps"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <TrendingDown 
                className={`
                  transition-all duration-300 drop-shadow-[0_0_15px_hsl(var(--finops)/0.9)]
                  ${activeLayers.finops 
                    ? 'w-20 h-20 text-finops-foreground' 
                    : 'w-16 h-16 text-finops group-hover:text-finops-foreground group-hover:w-18 group-hover:h-18'
                  }
                `}
                strokeWidth={1.5}
              />
            </div>
            
            {/* Pulse animation quando ativo */}
            {activeLayers.finops && (
              <div className="absolute inset-0 rounded-3xl bg-finops/30 animate-pulse" />
            )}
          </button>
          
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 bg-finops/20 border-2 border-finops text-finops">
              FinOps
            </div>
            
            <h3 className={`
              text-xl font-bold transition-colors duration-300
              ${activeLayers.finops ? 'text-finops' : 'text-foreground'}
            `}>
              Otimização de Custos
            </h3>
            
            <p className="text-sm text-muted-foreground max-w-xs">
              Insights de custo e otimizações em linguagem natural
            </p>
          </div>
        </div>

        {/* Camada 6 - Dados & IA */}
        <div className="flex flex-col items-center text-center space-y-4 opacity-0 animate-slide-up stagger-4">
          <button
            onClick={() => setActiveLayers({ ...activeLayers, data: !activeLayers.data })}
            className={`
              group relative
              w-40 h-40 rounded-3xl
              transition-all duration-300 ease-out
              ${activeLayers.data 
                ? 'glass-strong bg-gradient-to-br from-dataAi/80 to-accent/60 scale-105 border-2 border-dataAi shadow-[0_0_30px_hsl(var(--data-ai)/0.5)]' 
                : 'glass glass-hover shadow-lg hover:shadow-xl hover:scale-105 bg-gradient-to-br from-dataAi/20 to-accent/10 border-2 border-dataAi/40'
              }
            `}
            aria-label="Toggle Camada 6 - Dados & IA"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <Brain 
                className={`
                  transition-all duration-300 drop-shadow-[0_0_15px_hsl(var(--data-ai)/0.9)]
                  ${activeLayers.data 
                    ? 'w-20 h-20 text-data-ai-foreground' 
                    : 'w-16 h-16 text-dataAi group-hover:text-data-ai-foreground group-hover:w-18 group-hover:h-18'
                  }
                `}
                strokeWidth={1.5}
              />
            </div>
            
            {/* Pulse animation quando ativo */}
            {activeLayers.data && (
              <div className="absolute inset-0 rounded-3xl bg-dataAi/30 animate-pulse" />
            )}
          </button>
          
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 bg-dataAi/20 border-2 border-dataAi text-dataAi">
              Analytics
            </div>
            
            <h3 className={`
              text-xl font-bold transition-colors duration-300
              ${activeLayers.data ? 'text-dataAi' : 'text-foreground'}
            `}>
              Inteligência de Dados
            </h3>
            
            <p className="text-sm text-muted-foreground max-w-xs">
              Explore estrutura, estatísticas e modelos de IA
            </p>
          </div>
        </div>
      </div>

    </div>
  );
};

export default LayerSelection;
