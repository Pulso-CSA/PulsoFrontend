/**
 * Botão escolher arquivo — From Uiverse.io by 3bdel3ziz-T
 * Estilo pasta com animação; cores alteradas para a plataforma (primary).
 */
import * as React from "react";
import { FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

export interface FolderFileUploadProps {
  onFileChange?: (files: FileList | null) => void;
  accept?: string;
  multiple?: boolean;
  className?: string;
  children?: React.ReactNode;
  /** Versão compacta para toolbar (só ícone, sem animação grande) */
  compact?: boolean;
}

const FolderFileUpload = React.forwardRef<HTMLInputElement, FolderFileUploadProps>(
  ({ onFileChange, accept, multiple, className, children, compact }, ref) => {
    const inputRef = React.useRef<HTMLInputElement>(null);
    const mergedRef = (el: HTMLInputElement | null) => {
      (inputRef as React.MutableRefObject<HTMLInputElement | null>).current = el;
      if (typeof ref === "function") ref(el);
      else if (ref) (ref as React.MutableRefObject<HTMLInputElement | null>).current = el;
    };

    return (
      <label className={cn("pulso-folder-file-upload", compact && "pulso-folder-file-upload--compact", className)}>
        {!compact && (
          <div className="pulso-folder-file-upload-folder" aria-hidden>
            <div className="pulso-folder-file-upload-tip" />
            <div className="pulso-folder-file-upload-cover" />
          </div>
        )}
        <span className="pulso-folder-file-upload-label">
          {children ?? "Escolher arquivo"}
        </span>
        <input
          ref={mergedRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={(e) => onFileChange?.(e.target.files ?? null)}
          className="sr-only"
        />
      </label>
    );
  }
);
FolderFileUpload.displayName = "FolderFileUpload";

export { FolderFileUpload };
