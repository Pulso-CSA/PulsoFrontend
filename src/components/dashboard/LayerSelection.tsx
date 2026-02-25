import { LAYER_CONFIG, LayerCard } from "./LayerCard";

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
    <div className="space-y-5">
      <div>
        <h2 className="text-base font-medium text-foreground">Módulos</h2>
        <p className="text-sm text-muted-foreground mt-0.5">Clique para ativar ou desativar</p>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 max-w-5xl">
        {LAYER_CONFIG.map((layer) => (
          <LayerCard
            key={layer.key}
            layer={layer}
            isActive={activeLayers[layer.key]}
            onClick={() => setActiveLayers({ ...activeLayers, [layer.key]: !activeLayers[layer.key] })}
            variant="default"
          />
        ))}
      </div>
    </div>
  );
};

export default LayerSelection;
