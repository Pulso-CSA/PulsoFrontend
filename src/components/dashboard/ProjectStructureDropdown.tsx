/**
 * Elemento 11 - Botão Project Structure
 * Dropdown que exibe estrutura de projeto (pastas e arquivos)
 */
import { useState } from "react";
import { Folder, File, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { FileNode } from "./FileTree";

interface ProjectStructureDropdownProps {
  structure: FileNode[] | null;
  className?: string;
}

function renderNode(node: FileNode, level: number): React.ReactNode {
  if (node.type === "folder") {
    return (
      <div key={node.name} className="space-y-0.5">
        <div className="flex items-center gap-2 py-1 text-sm" style={{ paddingLeft: `${level * 12}px` }}>
          <Folder className="h-4 w-4 text-amber-500 flex-shrink-0" />
          <span className="text-foreground">📁 {node.name}</span>
        </div>
        {node.children?.map((child) => renderNode(child, level + 1))}
      </div>
    );
  }
  return (
    <div key={node.name} className="flex items-center gap-2 py-1 text-sm text-muted-foreground" style={{ paddingLeft: `${level * 12}px` }}>
      <File className="h-4 w-4 flex-shrink-0" />
      <span>📄 {node.name}</span>
      {node.isNew && <span className="text-emerald-500 text-xs font-medium">*</span>}
    </div>
  );
}

export function ProjectStructureDropdown({ structure, className }: ProjectStructureDropdownProps) {
  const [open, setOpen] = useState(false);

  if (!structure || structure.length === 0) return null;

  return (
    <div className={cn("relative inline-block", className)}>
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2 rounded-md border border-border bg-card hover:bg-muted/50 transition-colors"
      >
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 18 14" className="h-5 w-5 flex-shrink-0">
          <path fill="#FFA000" d="M16.2 1.75H8.1L6.3 0H1.8C0.81 0 0 0.7875 0 1.75V12.25C0 13.2125 0.81 14 1.8 14H15.165L18 9.1875V3.5C18 2.5375 17.19 1.75 16.2 1.75Z" />
          <path fill="#FFCA28" d="M16.2 2H1.8C0.81 2 0 2.77143 0 3.71429V12.2857C0 13.2286 0.81 14 1.8 14H16.2C17.19 14 18 13.2286 18 12.2857V3.71429C18 2.77143 17.19 2 16.2 2Z" />
        </svg>
        <span className="text-sm font-medium text-foreground">Estrutura do Projeto</span>
        <ChevronDown className={cn("h-4 w-4 transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" aria-hidden onClick={() => setOpen(false)} />
          <div className="absolute left-0 mt-2 w-72 max-h-80 overflow-y-auto bg-card border border-border rounded-lg shadow-lg z-50 p-4">
            <p className="text-xs text-muted-foreground mb-2">
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">*</span> = criado neste run
            </p>
            <div className="space-y-0.5">
              {structure.map((node) => renderNode(node, 0))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
