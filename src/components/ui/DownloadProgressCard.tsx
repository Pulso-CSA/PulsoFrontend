/**
 * Card de progresso de download — Estilo glassmorphism
 * Doc: docs/download-progress-card.md
 */
import { useEffect, useState } from "react";
import { X, FileDown, Loader2 } from "lucide-react";

export interface DownloadProgressCardProps {
  fileName?: string;
  fileSize?: string;
  onClose?: () => void;
  onComplete?: () => void;
  durationMs?: number;
}

export function DownloadProgressCard({
  fileName = "Pulso-Setup.exe",
  fileSize = "85 MB",
  onClose,
  onComplete,
  durationMs = 2000,
}: DownloadProgressCardProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const start = Date.now();
    const tick = () => {
      const elapsed = Date.now() - start;
      const p = Math.min(100, Math.round((elapsed / durationMs) * 100));
      setProgress(p);
      if (p < 100) {
        requestAnimationFrame(tick);
      } else {
        onComplete?.();
      }
    };
    const id = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(id);
  }, [durationMs, onComplete]);

  return (
    <div className="download-progress-card-backdrop" role="dialog" aria-label="Progresso do download">
      <div className="download-progress-card">
        <button
          type="button"
          className="download-progress-card__close"
          onClick={onClose}
          aria-label="Fechar"
        >
          <X className="w-4 h-4" />
        </button>
        <div className="download-progress-card__file">
          <div className="download-progress-card__icon">
            <FileDown />
          </div>
          <span className="download-progress-card__type">EXE</span>
          <span className="download-progress-card__name">{fileName}</span>
          <span className="download-progress-card__size">{fileSize}</span>
        </div>
        <div className="download-progress-card__progress">
          <div className="download-progress-card__status">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Baixando...</span>
          </div>
          <div className="download-progress-card__bar">
            <div
              className="download-progress-card__bar-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <span className="download-progress-card__percent">{progress}%</span>
        </div>
      </div>
    </div>
  );
}
