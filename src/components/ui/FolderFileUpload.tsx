/**
 * Botão escolher arquivo — From Uiverse.io by 3bdel3ziz-T
 */
import * as React from "react";
import { cn } from "@/lib/utils";

export interface FolderFileUploadProps {
  onFileChange?: (files: FileList | null) => void;
  accept?: string;
  multiple?: boolean;
  className?: string;
  children?: React.ReactNode;
  compact?: boolean;
}

const FolderFileUpload = React.forwardRef<HTMLInputElement, FolderFileUploadProps>(
  ({ onFileChange, accept, multiple, className, children, compact }, ref) => {
    const mergedRef = (el: HTMLInputElement | null) => {
      if (typeof ref === "function") ref(el);
      else if (ref) (ref as React.MutableRefObject<HTMLInputElement | null>).current = el;
    };

    return (
      <div className={cn("pulso-folder-file-upload", compact && "pulso-folder-file-upload--compact", className)}>
        <div className="pulso-folder-file-upload-folder" aria-hidden>
          <div className="pulso-folder-file-upload-front-side">
            <div className="pulso-folder-file-upload-tip" />
            <div className="pulso-folder-file-upload-cover" />
          </div>
          <div className="pulso-folder-file-upload-back-side pulso-folder-file-upload-cover" />
        </div>
        <label className="pulso-folder-file-upload-label">
          <input
            ref={mergedRef}
            type="file"
            accept={accept}
            multiple={multiple}
            onChange={(e) => onFileChange?.(e.target.files ?? null)}
            className="pulso-folder-file-upload-input"
          />
          {children ?? "Choose a file"}
        </label>
      </div>
    );
  }
);
FolderFileUpload.displayName = "FolderFileUpload";

export { FolderFileUpload };
