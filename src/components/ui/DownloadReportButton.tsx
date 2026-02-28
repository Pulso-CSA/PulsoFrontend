/**
 * Botão "Baixar Relatório" — Elemento 24 (Uiverse.io by barisdogansutcu)
 * Animação: área Docs sobe no hover, revela área Download com ícone animado
 */
import { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface DownloadReportButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children?: React.ReactNode;
}

const DocIcon = () => (
  <svg
    viewBox="0 0 24 24"
    width="22"
    height="22"
    stroke="currentColor"
    strokeWidth="2"
    fill="none"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <polyline points="10 9 9 9 8 9" />
  </svg>
);

const DownloadIcon = () => (
  <svg
    viewBox="0 0 24 24"
    width="26"
    height="26"
    stroke="currentColor"
    strokeWidth="2"
    fill="none"
    strokeLinecap="round"
    strokeLinejoin="round"
  >
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
    <polyline points="7 10 12 15 17 10" />
    <line x1="12" y1="15" x2="12" y2="3" />
  </svg>
);

const DownloadReportButton = forwardRef<HTMLButtonElement, DownloadReportButtonProps>(
  ({ className, children = "Baixar Relatório", disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        type="button"
        disabled={disabled}
        className={cn(
          "showcase-download-report-btn shrink-0",
          disabled && "opacity-50 cursor-not-allowed",
          className
        )}
        {...props}
      >
        <div className="showcase-docs">
          <DocIcon />
          <span>{children}</span>
        </div>
        <div className="showcase-download" aria-hidden>
          <DownloadIcon />
        </div>
      </button>
    );
  }
);

DownloadReportButton.displayName = "DownloadReportButton";

export { DownloadReportButton };
