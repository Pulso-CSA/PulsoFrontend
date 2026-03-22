/**
 * Barra de busca cosmic — From Uiverse.io by Amankrah
 * Efeito galaxy, stardust, cosmic-ring, starfield, nebula; ícone wormhole à direita com borda rotativa.
 */
import * as React from "react";
import { Search } from "lucide-react";
import { cn } from "@/lib/utils";

export interface CosmicSearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onSearch?: () => void;
  /** "pulso" = estilo glass sem galaxy/wormhole; "cosmic" = efeito completo Uiverse. */
  variant?: "cosmic" | "pulso";
}

const CosmicSearchInput = React.forwardRef<HTMLInputElement, CosmicSearchInputProps>(
  ({ className, onSearch, onKeyDown, variant = "cosmic", ...props }, ref) => {
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        onSearch?.();
      }
      onKeyDown?.(e);
    };

    const isPulso = variant === "pulso";

    return (
      <div
        className={cn(
          "cosmic-search-container w-full max-w-full",
          isPulso && "cosmic-search--pulso",
          className
        )}
      >
        {!isPulso && <div className="cosmic-galaxy" aria-hidden />}
        <div className="cosmic-nebula" aria-hidden />
        <div className="cosmic-starfield" aria-hidden />
        <div className="cosmic-dust" aria-hidden />
        <div className="cosmic-dust" aria-hidden />
        <div className="cosmic-dust" aria-hidden />
        <div className="cosmic-stardust" aria-hidden />
        <div className="cosmic-ring" aria-hidden />
        <div className="cosmic-main">
          <input
            ref={ref}
            type="text"
            className="cosmic-input"
            onKeyDown={handleKeyDown}
            {...props}
          />
          <div className="cosmic-input-mask" aria-hidden />
          <div className="cosmic-glow" aria-hidden />
          {!isPulso && (
            <>
              <div className="cosmic-wormhole-border" aria-hidden />
              <div className="cosmic-wormhole-icon" aria-hidden>
                <Search className="h-5 w-5" strokeWidth={2} />
              </div>
            </>
          )}
        </div>
      </div>
    );
  }
);
CosmicSearchInput.displayName = "CosmicSearchInput";

export { CosmicSearchInput };
