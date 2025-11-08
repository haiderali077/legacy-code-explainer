import { GitBranch, Settings, Bell } from "lucide-react";
import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="h-14 border-b border-border bg-card/50 backdrop-blur-sm flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <span className="text-primary font-mono font-bold text-sm">CA</span>
          </div>
          <span className="font-semibold text-foreground">CodeAncestry</span>
        </div>
        
        <div className="h-6 w-px bg-border mx-2" />
        
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <GitBranch className="w-4 h-4" />
          <span>main</span>
          <span className="text-primary/70">•</span>
          <span className="font-mono text-xs">legacy-auth-service</span>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
          <Bell className="w-4 h-4" />
        </Button>
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
          <Settings className="w-4 h-4" />
        </Button>
      </div>
    </header>
  );
}
