/**
 * Elemento 10 — Botão de deletar/excluir com estilo dos botões de envio de prompt
 * SVG: ícone de lixeira (trash)
 * Estilo: showcase-filter-icon (gradiente escuro, bordas arredondadas)
 */
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

const ELEMENTO_10_SVG = (
  <svg
    className="h-5 w-5 shrink-0 sm:h-6 sm:w-6"
    viewBox="0 0 448 512"
    fill="currentColor"
    aria-hidden
  >
    <path d="M135.2 17.7L128 32H32C14.3 32 0 46.3 0 64S14.3 96 32 96H416c17.7 0 32-14.3 32-32s-14.3-32-32-32H320l-7.2-14.3C307.4 6.8 296.3 0 284.2 0H163.8c-12.1 0-23.2 6.8-28.6 17.7zM416 128H32L53.2 467c1.6 25.3 22.6 45 47.9 45H346.9c25.3 0 46.3-19.7 47.9-45L416 128z" />
  </svg>
);

export interface Elemento10DeleteButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Variante compacta (apenas ícone) */
  compact?: boolean;
}

const Elemento10DeleteButton = forwardRef<
  HTMLButtonElement,
  Elemento10DeleteButtonProps
>(({ className, compact = false, children, disabled, ...props }, ref) => {
  return (
    <button
      ref={ref}
      type="button"
      disabled={disabled}
      className={cn(
        "showcase-elemento-10-delete shrink-0",
        compact && "showcase-elemento-10-delete--compact",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      aria-label="Excluir"
      {...props}
    >
      {ELEMENTO_10_SVG}
      {!compact && children}
    </button>
  );
});

Elemento10DeleteButton.displayName = "Elemento10DeleteButton";

export { Elemento10DeleteButton, ELEMENTO_10_SVG };
