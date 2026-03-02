import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogPortal,
  DialogOverlay,
} from "@/components/ui/dialog";
import { X } from "lucide-react";

interface UploadDemoModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function UploadDemoModal({ open, onOpenChange }: UploadDemoModalProps) {
  const [progress, setProgress] = useState(0);
  const [displayPercent, setDisplayPercent] = useState(0);

  useEffect(() => {
    if (!open) {
      setProgress(0);
      setDisplayPercent(0);
      return;
    }
    const target = 74;
    const duration = 2000;
    const steps = 60;
    const stepDuration = duration / steps;
    const increment = target / steps;

    let current = 0;
    const interval = setInterval(() => {
      current += increment;
      if (current >= target) {
        setProgress(target);
        setDisplayPercent(target);
        clearInterval(interval);
      } else {
        setProgress(current);
        setDisplayPercent(Math.round(current));
      }
    }, stepDuration);

    return () => clearInterval(interval);
  }, [open]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogPortal>
        <DialogOverlay className="bg-black/60 backdrop-blur-sm" />
        <DialogContent
          className="upload-demo-content border-0 bg-transparent p-0 shadow-none [&>button]:hidden"
        >
          <div className="upload-demo-card">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="upload-demo-close"
              aria-label="Fechar"
            >
              <X className="h-4 w-4" />
            </button>

            <div className="upload-demo-body">
              <div className="upload-demo-file">
                <div className="upload-demo-icon-wrap">
                  <svg className="upload-demo-doc-icon" viewBox="0 0 48 56" fill="none">
                    <path d="M8 0h28l12 12v36a4 4 0 0 1-4 4H8a4 4 0 0 1-4-4V4a4 4 0 0 1 4-4z" fill="currentColor" fillOpacity="0.9" />
                    <path d="M36 0v12h12L36 0z" fill="currentColor" fillOpacity="0.6" />
                  </svg>
                  <span className="upload-demo-badge">TEXT</span>
                </div>
                <div className="upload-demo-info">
                  <p className="upload-demo-filename">Project Brief.txt</p>
                  <p className="upload-demo-filesize">97.45 KB</p>
                </div>
              </div>

              <div className="upload-demo-progress-section">
                <div className="upload-demo-uploading">
                  <svg className="upload-demo-spinner" viewBox="0 0 24 24">
                    <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeDasharray="20 50" />
                  </svg>
                  <span className="upload-demo-uploading-text">Uploading...</span>
                </div>
                <div className="upload-demo-progress-row">
                  <div className="upload-demo-progress-wrap">
                    <div
                      className="upload-demo-progress-fill"
                      style={{ width: `${progress}%` }}
                    >
                      <div className="upload-demo-progress-shine" />
                    </div>
                  </div>
                  <span className="upload-demo-percent">{displayPercent}%</span>
                </div>
              </div>
            </div>
          </div>
        </DialogContent>
      </DialogPortal>
    </Dialog>
  );
}
