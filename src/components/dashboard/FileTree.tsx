import { Folder, File } from "lucide-react";

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
  return (
    <div className="space-y-1">
      {structure.map((node, index) => (
        <div key={`${node.name}-${index}`}>
          <div 
            className="flex items-center gap-2 py-1 px-2 rounded hover:bg-secondary/50 transition-colors"
            style={{ paddingLeft: `${level * 1.5 + 0.5}rem` }}
          >
            {node.type === "folder" ? (
              <Folder className="h-4 w-4 text-finops flex-shrink-0" />
            ) : (
              <File className="h-4 w-4 text-muted-foreground flex-shrink-0" />
            )}
            <span className="text-sm font-mono text-foreground">
              {node.name}
            </span>
          </div>
          {node.children && node.children.length > 0 && (
            <FileTree structure={node.children} level={level + 1} />
          )}
        </div>
      ))}
    </div>
  );
};

export default FileTree;
