/**
 * Elemento 18 - Barra de Busca (search-poda)
 * Campo com bordas em gradiente animadas para envio de mensagem ao chat
 * Ícone de enviar no lugar do filtro
 */
import * as React from "react";
import { cn } from "@/lib/utils";
import { Send } from "lucide-react";

export interface PromptSearchInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  onSend?: () => void;
  /** Variante maior para área de prompt (largura total, altura maior) */
  variant?: "default" | "prompt";
}

const PromptSearchInput = React.forwardRef<HTMLInputElement, PromptSearchInputProps>(
  ({ className, onSend, onKeyDown, disabled, variant = "default", ...props }, ref) => {
    const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onSend?.();
      }
      onKeyDown?.(e);
    };

    return (
      <div className={cn("relative w-full overflow-hidden", variant === "prompt" && "showcase-search-poda--prompt")}>
        <div className="showcase-search-poda">
          <div className="showcase-search-glow" aria-hidden />
          <div className="showcase-search-darkBorderBg" aria-hidden />
          <div className="showcase-search-darkBorderBg" aria-hidden />
          <div className="showcase-search-darkBorderBg" aria-hidden />
          <div className="showcase-search-white" aria-hidden />
          <div className="showcase-search-border" aria-hidden />
          <div className="showcase-search-main">
            <input
              ref={ref}
              type="text"
              className={cn(
                "showcase-search-input showcase-search-input--no-lupa",
                variant === "prompt" && "showcase-search-input--prompt",
                className
              )}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              {...props}
            />
            <div className="showcase-input-mask" aria-hidden />
            <div className="showcase-pink-mask" aria-hidden />
            <div className="showcase-filter-border" aria-hidden />
            <button
              type="button"
              onClick={onSend}
              disabled={disabled}
              className="showcase-filter-icon showcase-send-icon cursor-pointer border-0 bg-transparent flex items-center justify-center text-muted-foreground hover:text-foreground disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Enviar"
            >
              <Send className="h-5 w-5" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
            </button>
          </div>
        </div>
      </div>
    );
  }
);
PromptSearchInput.displayName = "PromptSearchInput";

export { PromptSearchInput };
