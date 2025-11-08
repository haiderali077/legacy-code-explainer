import { GitCommit, FileCode, FunctionSquare, TestTube } from "lucide-react";
import { cn } from "@/lib/utils";

type ChipType = "commit" | "file" | "function" | "test";

interface ContextChipsProps {
  activeChips: ChipType[];
  onChipToggle: (chip: ChipType) => void;
}

const chips = [
  { id: "commit" as ChipType, label: "Commit", icon: GitCommit },
  { id: "file" as ChipType, label: "File", icon: FileCode },
  { id: "function" as ChipType, label: "Function", icon: FunctionSquare },
  { id: "test" as ChipType, label: "Test", icon: TestTube },
];

export function ContextChips({ activeChips, onChipToggle }: ContextChipsProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted-foreground uppercase tracking-wider">Context:</span>
      <div className="flex items-center gap-2">
        {chips.map((chip) => {
          const Icon = chip.icon;
          const isActive = activeChips.includes(chip.id);
          
          return (
            <button
              key={chip.id}
              onClick={() => onChipToggle(chip.id)}
              className={cn(
                "chip flex items-center gap-1.5",
                isActive && "chip-active"
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{chip.label}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
