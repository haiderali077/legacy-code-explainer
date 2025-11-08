import { cn } from "@/lib/utils";

interface CodeViewerProps {
  filePath: string;
  highlightedLines?: number[];
}

const mockCode = `// Legacy Session Handler - Created 2019
// TODO: Refactor this mess someday
// Author: John (no longer with company)

const SESSION_KEY = 'usr_session_v2';
const LEGACY_KEY = 'usr_session'; // Don't remove - breaks old clients

class OldSessionHandler {
  constructor() {
    this._cache = {};
    this._listeners = [];
    // Magic number: 3600000 = 1 hour in ms
    this._timeout = 3600000;
  }

  // WARNING: Do not modify without checking AuthProvider.tsx
  getSession() {
    let session = localStorage.getItem(SESSION_KEY);
    if (!session) {
      // Fallback for users with old session format
      session = localStorage.getItem(LEGACY_KEY);
      if (session) {
        // Migrate to new format (silently)
        this._migrateSession(session);
      }
    }
    return session ? JSON.parse(session) : null;
  }

  // This function has a bug but fixing it breaks mobile
  _validateToken(token) {
    if (!token) return false;
    // HACK: Skip validation for admin tokens
    if (token.startsWith('admin_')) return true;
    
    const parts = token.split('.');
    // Should be 3 parts for JWT but legacy tokens have 2
    return parts.length >= 2;
  }

  // Called from 47 different places - good luck
  refreshSession() {
    const session = this.getSession();
    if (!session) return Promise.reject('No session');
    
    // Mysterious 500ms delay - removing breaks auth
    return new Promise((resolve) => {
      setTimeout(() => {
        this._cache.lastRefresh = Date.now();
        resolve(session);
      }, 500);
    });
  }
}

export default OldSessionHandler;`;

const codeLines = mockCode.split('\n');

export function CodeViewer({ filePath, highlightedLines = [6, 7, 23, 24, 25, 35, 36, 37] }: CodeViewerProps) {
  return (
    <div className="h-full flex flex-col bg-code-bg rounded-lg border border-border overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-muted/30 border-b border-border">
        <span className="font-mono text-xs text-muted-foreground">{filePath}</span>
        <span className="text-xs text-muted-foreground">{codeLines.length} lines</span>
      </div>
      
      <div className="flex-1 overflow-auto scrollbar-thin">
        <pre className="p-4">
          <code className="text-sm font-mono">
            {codeLines.map((line, index) => {
              const lineNumber = index + 1;
              const isHighlighted = highlightedLines.includes(lineNumber);
              
              return (
                <div
                  key={lineNumber}
                  className={cn(
                    "flex",
                    isHighlighted && "code-line-highlight -mx-4 px-4"
                  )}
                >
                  <span className="w-8 text-right text-muted-foreground/50 select-none pr-4 flex-shrink-0">
                    {lineNumber}
                  </span>
                  <span className={cn(
                    "flex-1",
                    line.includes('//') && "text-muted-foreground",
                    line.includes('TODO') && "text-mode-review",
                    line.includes('WARNING') && "text-mode-review",
                    line.includes('HACK') && "text-destructive",
                    line.includes('const ') && "text-cyan-400",
                    line.includes('class ') && "text-purple-400",
                    line.includes('function') && "text-blue-400",
                    line.includes('return') && "text-pink-400",
                  )}>
                    {line || ' '}
                  </span>
                </div>
              );
            })}
          </code>
        </pre>
      </div>
    </div>
  );
}
