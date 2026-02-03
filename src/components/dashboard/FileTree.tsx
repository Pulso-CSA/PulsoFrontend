import { useState } from "react";
import { Folder, File, ChevronRight, ChevronDown } from "lucide-react";

export interface FileNode {
  name: string;
  type: "file" | "folder";
  children?: FileNode[];
  /** Criado neste run (veio com * na árvore da API) */
  isNew?: boolean;
}

interface FileTreeProps {
  structure: FileNode[];
  level?: number;
}

const FileTree = ({ structure, level = 0 }: FileTreeProps) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  const toggleFolder = (path: string) => {
    setExpandedFolders((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(path)) {
        newSet.delete(path);
      } else {
        newSet.add(path);
      }
      return newSet;
    });
  };

  return (
    <div className="space-y-1">
      {structure.map((node, index) => {
        const nodePath = `${level}-${node.name}-${index}`;
        const isExpanded = expandedFolders.has(nodePath);
        const isFolder = node.type === "folder";

        return (
          <div key={nodePath}>
            <div
              className={`flex items-center gap-2 py-1 px-2 rounded transition-colors ${
                isFolder ? "cursor-pointer hover:bg-primary/10" : "hover:bg-primary/5"
              } ${node.isNew ? "bg-emerald-500/10" : ""}`}
              style={{ paddingLeft: `${level * 1.5 + 0.5}rem` }}
              onClick={() => isFolder && toggleFolder(nodePath)}
            >
              {isFolder && (
                <div className="flex-shrink-0">
                  {isExpanded ? (
                    <ChevronDown className={`h-4 w-4 ${node.isNew ? "text-emerald-500" : "text-primary"}`} />
                  ) : (
                    <ChevronRight className={`h-4 w-4 ${node.isNew ? "text-emerald-500" : "text-primary"}`} />
                  )}
                </div>
              )}
              {!isFolder && <div className="w-4 flex-shrink-0" />}
              {isFolder ? (
                <Folder className={`h-4 w-4 flex-shrink-0 ${node.isNew ? "text-emerald-500" : "text-finops"}`} />
              ) : (
                <File className={`h-4 w-4 flex-shrink-0 ${node.isNew ? "text-emerald-500" : "text-muted-foreground"}`} />
              )}
              <span className={`text-sm font-mono ${node.isNew ? "text-emerald-600 dark:text-emerald-400 font-medium" : "text-foreground"}`}>
                {node.name}
              </span>
            </div>
            {isFolder && isExpanded && node.children && node.children.length > 0 && (
              <FileTree structure={node.children} level={level + 1} />
            )}
          </div>
        );
      })}
    </div>
  );
};

export default FileTree;
