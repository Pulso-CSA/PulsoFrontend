import { Zap, Activity, BarChart3 } from "lucide-react";

interface LayerSelectionProps {
  activeLayers: {
    preview: boolean;
    pulso: boolean;
    finops: boolean;
    data: boolean;
  };
  setActiveLayers: (layers: { preview: boolean; pulso: boolean; finops: boolean; data: boolean }) => void;
}

const LayerSelection = ({ activeLayers, setActiveLayers }: LayerSelectionProps) => {
  return (
    <div className="space-y-8">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold neon-text" style={{ color: 'hsl(180 100% 70%)' }}>
          Camadas Disponíveis
        </h2>
        <p className="text-sm text-foreground/80">
          Toque nos ícones para ativar/desativar
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-7xl mx-auto">
        {/* Pulso CSA */}
        <div className="flex flex-col items-center text-center space-y-4">
          <button
            onClick={() => setActiveLayers({ ...activeLayers, pulso: !activeLayers.pulso })}
            className={`
              group relative
              w-40 h-40 rounded-3xl
              transition-all duration-500 ease-out
              ${activeLayers.pulso 
                ? 'glass-strong neon-glow-strong bg-gradient-to-br from-primary/80 to-primary-deep/60 scale-100 border-2 border-primary' 
                : 'glass glass-hover shadow-lg hover:shadow-xl hover:scale-105 bg-gradient-to-br from-primary/20 to-primary-deep/10 border-2 border-primary/40'
              }
            `}
            aria-label="Toggle Pulso CSA"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <Zap 
                className={`
                  transition-all duration-500 drop-shadow-[0_0_10px_rgba(0,255,255,0.7)]
                  ${activeLayers.pulso 
                    ? 'w-20 h-20 text-primary-light' 
                    : 'w-16 h-16 text-primary group-hover:text-primary-light group-hover:w-20 group-hover:h-20'
                  }
                `}
                strokeWidth={1.5}
              />
            </div>
            
            {/* Pulse animation quando ativo */}
            {activeLayers.pulso && (
              <div className="absolute inset-0 rounded-3xl bg-primary animate-ping opacity-20" />
            )}
          </button>
          
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 bg-primary/20 border-2 border-primary"
              style={{ color: 'hsl(180 100% 65%)' }}>
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

        {/* Camada 5 - FinOps */}
        <div className="flex flex-col items-center text-center space-y-4">
          <button
            onClick={() => setActiveLayers({ ...activeLayers, finops: !activeLayers.finops })}
            className={`
              group relative
              w-40 h-40 rounded-3xl
              transition-all duration-500 ease-out
              ${activeLayers.finops 
                ? 'glass-strong bg-gradient-to-br from-finops/80 to-success/60 scale-100 border-2 border-finops shadow-[0_0_40px_rgba(0,255,153,0.6),0_0_80px_rgba(0,255,153,0.3)]' 
                : 'glass glass-hover shadow-lg hover:shadow-xl hover:scale-105 bg-gradient-to-br from-finops/20 to-success/10 border-2 border-finops/40'
              }
            `}
            aria-label="Toggle Camada 5 - FinOps"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <Activity 
                className={`
                  transition-all duration-500 drop-shadow-[0_0_10px_rgba(0,255,153,0.7)]
                  ${activeLayers.finops 
                    ? 'w-20 h-20 text-white' 
                    : 'w-16 h-16 text-finops group-hover:text-white group-hover:w-20 group-hover:h-20'
                  }
                `}
                strokeWidth={1.5}
              />
            </div>
            
            {/* Pulse animation quando ativo */}
            {activeLayers.finops && (
              <div className="absolute inset-0 rounded-3xl bg-finops animate-ping opacity-20" />
            )}
          </button>
          
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 bg-finops/20 border-2 border-finops"
              style={{ color: 'hsl(150 100% 65%)' }}>
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
        <div className="flex flex-col items-center text-center space-y-4">
          <button
            onClick={() => setActiveLayers({ ...activeLayers, data: !activeLayers.data })}
            className={`
              group relative
              w-40 h-40 rounded-3xl
              transition-all duration-500 ease-out
              ${activeLayers.data 
                ? 'glass-strong bg-gradient-to-br from-dataAi/80 to-secondary/60 scale-100 border-2 border-dataAi shadow-[0_0_40px_rgba(191,0,255,0.6),0_0_80px_rgba(191,0,255,0.3)]' 
                : 'glass glass-hover shadow-lg hover:shadow-xl hover:scale-105 bg-gradient-to-br from-dataAi/20 to-secondary/10 border-2 border-dataAi/40'
              }
            `}
            aria-label="Toggle Camada 6 - Dados & IA"
          >
            <div className="absolute inset-0 flex items-center justify-center">
              <BarChart3 
                className={`
                  transition-all duration-500 drop-shadow-[0_0_10px_rgba(191,0,255,0.7)]
                  ${activeLayers.data 
                    ? 'w-20 h-20 text-white' 
                    : 'w-16 h-16 text-dataAi group-hover:text-white group-hover:w-20 group-hover:h-20'
                  }
                `}
                strokeWidth={1.5}
              />
            </div>
            
            {/* Pulse animation quando ativo */}
            {activeLayers.data && (
              <div className="absolute inset-0 rounded-3xl bg-dataAi animate-ping opacity-20" />
            )}
          </button>
          
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300 bg-dataAi/20 border-2 border-dataAi"
              style={{ color: 'hsl(270 100% 80%)' }}>
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
