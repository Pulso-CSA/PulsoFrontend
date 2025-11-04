import { useState } from "react";
import { Folder, File, ChevronRight, ChevronDown } from "lucide-react";

interface FileNode {
  name: string;
  type: "file" | "folder";
  children?: FileNode[];
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
              }`}
              style={{ paddingLeft: `${level * 1.5 + 0.5}rem` }}
              onClick={() => isFolder && toggleFolder(nodePath)}
            >
              {isFolder && (
                <div className="flex-shrink-0">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-primary" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-primary" />
                  )}
                </div>
              )}
              {!isFolder && <div className="w-4 flex-shrink-0" />}
              {isFolder ? (
                <Folder className="h-4 w-4 text-finops flex-shrink-0" />
              ) : (
                <File className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              )}
              <span className="text-sm font-mono text-foreground">
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
