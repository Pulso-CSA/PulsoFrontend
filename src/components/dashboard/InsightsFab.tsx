/**
 * FAB da aba Insights: criar, excluir, atualizar, deletar gráficos, reposicionar, zoom.
 * Só deve ser exibido quando o usuário está na aba de Insights (activeService === null).
 */
import { useState } from "react";
import { LayoutGrid, Plus, Trash2, RefreshCw, Move, ZoomIn, ZoomOut } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export interface InsightsFabProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onCreateChart: () => void;
  onDeleteChart: (id: string) => void;
  onUpdateChart: () => void;
  onToggleReposition: () => void;
  repositionMode: boolean;
  widgetIds: { id: string; title: string }[];
  zoomLevel: number;
  /** Controla abertura do menu (ex.: clique esquerdo na área insights) */
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  className?: string;
}

export function InsightsFab({
  onZoomIn,
  onZoomOut,
  onCreateChart,
  onDeleteChart,
  onUpdateChart,
  onToggleReposition,
  repositionMode,
  widgetIds,
  zoomLevel,
  open: openProp,
  onOpenChange: onOpenChangeProp,
  className,
}: InsightsFabProps) {
  const [openInternal, setOpenInternal] = useState(false);
  const isControlled = openProp !== undefined;
  const open = isControlled ? openProp : openInternal;
  const onOpenChange = (v: boolean) => {
    if (isControlled) onOpenChangeProp?.(v);
    else setOpenInternal(v);
  };

  return (
    <DropdownMenu open={open} onOpenChange={onOpenChange}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className={cn(
            "fixed bottom-6 left-6 z-50 flex h-14 w-14 items-center justify-center rounded-full shadow-lg transition-all duration-200",
            "bg-primary/90 text-primary-foreground hover:bg-primary hover:scale-110",
            "ring-2 ring-primary/50 ring-offset-2 ring-offset-background",
            "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
            className
          )}
          aria-label="Opções do dashboard de Insights"
        >
          <LayoutGrid className="h-6 w-6" strokeWidth={2} />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        side="top"
        sideOffset={8}
        className="min-w-[220px] pulso-dropdown-menu-glass"
      >
        <DropdownMenuItem onClick={() => { onCreateChart(); onOpenChange(false); }}>
          <Plus className="mr-2 h-4 w-4" />
          Criar gráfico
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => { onUpdateChart(); onOpenChange(false); }}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Atualizar
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => { onToggleReposition(); onOpenChange(false); }}>
          <Move className="mr-2 h-4 w-4" />
          {repositionMode ? "Desativar reposição" : "Reposicionar livremente"}
        </DropdownMenuItem>
        {widgetIds.length > 0 && (
          <>
            <DropdownMenuSeparator />
            <DropdownMenuSub>
              <DropdownMenuSubTrigger>
                <Trash2 className="mr-2 h-4 w-4" />
                Excluir gráfico
              </DropdownMenuSubTrigger>
              <DropdownMenuSubContent className="pulso-dropdown-menu-glass">
                {widgetIds.map((w) => (
                  <DropdownMenuItem
                    key={w.id}
                    onClick={() => { onDeleteChart(w.id); onOpenChange(false); }}
                    className="text-destructive focus:text-destructive"
                  >
                    {w.title}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuSubContent>
            </DropdownMenuSub>
          </>
        )}
        <DropdownMenuSeparator />
        <div className="flex items-center justify-between px-2 py-1.5 text-xs text-muted-foreground">
          <span>Zoom</span>
          <span className="font-mono">{Math.round(zoomLevel * 100)}%</span>
        </div>
        <DropdownMenuItem onClick={() => { onZoomIn(); onOpenChange(false); }}>
          <ZoomIn className="mr-2 h-4 w-4" />
          Aumentar zoom
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => { onZoomOut(); onOpenChange(false); }}>
          <ZoomOut className="mr-2 h-4 w-4" />
          Diminuir zoom
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
