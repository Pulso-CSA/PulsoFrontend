/**
 * Elemento 18 — Área de prompt com textarea (design search-poda)
 * Para CloudChat, DataChat, FinOpsChat
 */
import * as React from "react";
import { Send } from "lucide-react";
import { cn } from "@/lib/utils";

const MAX_HEIGHT = 384;

export interface PromptSearchTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  onSend?: () => void;
  /** Ações extras ao lado do botão enviar (mesmo estilo da barra), ex.: botão Testar */
  trailingActions?: React.ReactNode;
}

const PromptSearchTextarea = React.forwardRef<HTMLTextAreaElement, PromptSearchTextareaProps>(
  ({ className, onSend, onKeyDown, trailingActions, ...props }, ref) => {
    const internalRef = React.useRef<HTMLTextAreaElement | null>(null);
    const mergedRef = (el: HTMLTextAreaElement | null) => {
      (internalRef as React.MutableRefObject<HTMLTextAreaElement | null>).current = el;
      if (typeof ref === "function") ref(el);
      else if (ref) (ref as React.MutableRefObject<HTMLTextAreaElement | null>).current = el;
    };

    const adjustHeight = React.useCallback(() => {
      const el = internalRef.current;
      if (!el) return;
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, MAX_HEIGHT)}px`;
    }, []);

    React.useEffect(() => {
      adjustHeight();
    }, [props.value, adjustHeight]);

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onSend?.();
      }
      onKeyDown?.(e);
    };

    return (
      <div className={cn("relative w-full overflow-visible", "showcase-search-poda--prompt")}>
        <div className="showcase-search-poda w-full">
          <div className="showcase-search-glow" aria-hidden />
          <div className="showcase-search-darkBorderBg" aria-hidden />
          <div className="showcase-search-darkBorderBg" aria-hidden />
          <div className="showcase-search-darkBorderBg" aria-hidden />
          <div className="showcase-search-white" aria-hidden />
          <div className="showcase-search-border" aria-hidden />
          <div className="showcase-search-main flex-1 min-w-0">
            <textarea
              ref={mergedRef}
              className={cn(
                "showcase-search-input showcase-search-input--prompt showcase-search-input--no-lupa resize-none",
                "min-h-[56px] py-3",
                className
              )}
              onKeyDown={handleKeyDown}
              style={{ maxHeight: MAX_HEIGHT }}
              rows={1}
              {...props}
            />
            <div className="showcase-input-mask" aria-hidden />
            <div className="showcase-pink-mask" aria-hidden />
            <div className="showcase-filter-border" aria-hidden />
            <div className="showcase-trailing-actions">
              {trailingActions}
              <button
                type="button"
                onClick={onSend}
                disabled={props.disabled}
                className="showcase-filter-icon showcase-send-icon cursor-pointer border-0 flex items-center justify-center text-white disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Enviar mensagem"
                title="Enviar mensagem"
              >
                <Send className="h-5 w-5" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
);
PromptSearchTextarea.displayName = "PromptSearchTextarea";

export { PromptSearchTextarea };
