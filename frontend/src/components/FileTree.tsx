import { useState } from "react";
import { ChevronRight, ChevronDown, FileCode, Folder, FolderOpen } from "lucide-react";
import { cn } from "@/lib/utils";

interface FileNode {
  name: string;
  type: "file" | "folder";
  children?: FileNode[];
  path: string;
}

const mockFileTree: FileNode[] = [
  {
    name: "src",
    type: "folder",
    path: "src",
    children: [
      {
        name: "auth",
        type: "folder",
        path: "src/auth",
        children: [
          { name: "AuthProvider.tsx", type: "file", path: "src/auth/AuthProvider.tsx" },
          { name: "useAuth.ts", type: "file", path: "src/auth/useAuth.ts" },
          { name: "TokenManager.ts", type: "file", path: "src/auth/TokenManager.ts" },
        ],
      },
      {
        name: "legacy",
        type: "folder",
        path: "src/legacy",
        children: [
          { name: "OldSessionHandler.js", type: "file", path: "src/legacy/OldSessionHandler.js" },
          { name: "DeprecatedAuth.js", type: "file", path: "src/legacy/DeprecatedAuth.js" },
        ],
      },
      { name: "App.tsx", type: "file", path: "src/App.tsx" },
      { name: "index.ts", type: "file", path: "src/index.ts" },
    ],
  },
  {
    name: "tests",
    type: "folder",
    path: "tests",
    children: [
      { name: "auth.test.ts", type: "file", path: "tests/auth.test.ts" },
    ],
  },
];

interface FileTreeItemProps {
  node: FileNode;
  depth: number;
  selectedFile: string;
  onSelectFile: (path: string) => void;
}

function FileTreeItem({ node, depth, selectedFile, onSelectFile }: FileTreeItemProps) {
  const [isOpen, setIsOpen] = useState(depth < 2);
  
  const isFolder = node.type === "folder";
  const isSelected = selectedFile === node.path;
  
  return (
    <div>
      <button
        onClick={() => {
          if (isFolder) {
            setIsOpen(!isOpen);
          } else {
            onSelectFile(node.path);
          }
        }}
        className={cn(
          "w-full flex items-center gap-1.5 px-2 py-1 text-sm rounded-md transition-colors",
          "hover:bg-muted/50 text-muted-foreground hover:text-foreground",
          isSelected && "bg-primary/10 text-primary"
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {isFolder ? (
          <>
            {isOpen ? (
              <ChevronDown className="w-3.5 h-3.5 flex-shrink-0" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" />
            )}
            {isOpen ? (
              <FolderOpen className="w-4 h-4 flex-shrink-0 text-primary/70" />
            ) : (
              <Folder className="w-4 h-4 flex-shrink-0 text-muted-foreground" />
            )}
          </>
        ) : (
          <>
            <span className="w-3.5" />
            <FileCode className="w-4 h-4 flex-shrink-0" />
          </>
        )}
        <span className="truncate font-mono text-xs">{node.name}</span>
      </button>
      
      {isFolder && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeItem
              key={child.path}
              node={child}
              depth={depth + 1}
              selectedFile={selectedFile}
              onSelectFile={onSelectFile}
            />
          ))}
        </div>
      )}
    </div>
  );
}

interface FileTreeProps {
  selectedFile: string;
  onSelectFile: (path: string) => void;
}

export function FileTree({ selectedFile, onSelectFile }: FileTreeProps) {
  return (
    <div className="py-2 scrollbar-thin overflow-auto h-full">
      {mockFileTree.map((node) => (
        <FileTreeItem
          key={node.path}
          node={node}
          depth={0}
          selectedFile={selectedFile}
          onSelectFile={onSelectFile}
        />
      ))}
    </div>
  );
}
