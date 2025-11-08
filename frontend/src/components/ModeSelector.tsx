import { Brain, Search, Wrench, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

type Mode = "explain" | "review" | "fix" | "summarize";

interface ModeSelectorProps {
  activeMode: Mode;
  onModeChange: (mode: Mode) => void;
}

const modes = [
  { id: "explain" as Mode, label: "Explain", icon: Brain, color: "bg-mode-explain" },
  { id: "review" as Mode, label: "Review", icon: Search, color: "bg-mode-review" },
  { id: "fix" as Mode, label: "Fix", icon: Wrench, color: "bg-mode-fix" },
  { id: "summarize" as Mode, label: "Summarize", icon: FileText, color: "bg-mode-summarize" },
];

export function ModeSelector({ activeMode, onModeChange }: ModeSelectorProps) {
  return (
    <div className="flex items-center gap-1 p-1 bg-muted/50 rounded-lg">
      {modes.map((mode) => {
        const Icon = mode.icon;
        const isActive = activeMode === mode.id;
        
        return (
          <button
            key={mode.id}
            onClick={() => onModeChange(mode.id)}
            className={cn(
              "mode-pill flex items-center gap-2",
              isActive && "mode-pill-active"
            )}
            style={{
              backgroundColor: isActive ? `hsl(var(--mode-${mode.id}) / 0.15)` : undefined,
            }}
          >
            <Icon 
              className="w-4 h-4" 
              style={{ color: isActive ? `hsl(var(--mode-${mode.id}))` : undefined }}
            />
            <span 
              style={{ color: isActive ? `hsl(var(--mode-${mode.id}))` : undefined }}
            >
              {mode.label}
            </span>
          </button>
        );
      })}
    </div>
  );
}
