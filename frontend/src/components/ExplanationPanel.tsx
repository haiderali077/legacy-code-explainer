// import { useState, useEffect } from "react";
// import { GitCommit, User, Calendar, FileCode, ArrowRight, Send, Sparkles, ExternalLink } from "lucide-react";
// import { Input } from "@/components/ui/input";
// import { Button } from "@/components/ui/button";
// import { cn } from "@/lib/utils";

// type Mode = "explain" | "review" | "fix" | "summarize";

// interface ExplanationPanelProps {
//   mode: Mode;
// }

// // Related commits that answer the question
// const relatedCommits = [
//   {
//     hash: "a7c3d2f",
//     message: "Refactor authentication flow",
//     author: "Sarah Chen",
//     date: "Jan 16, 2026",
//     relevance: "high",
//     snippet: "Added logging for admin token bypass"
//   },
//   {
//     hash: "f82b1e9",
//     message: "Fix session handling edge cases",
//     author: "Mike Johnson", 
//     date: "Jan 11, 2026",
//     relevance: "medium",
//     snippet: "Handles legacy token format migration"
//   },
//   {
//     hash: "c4e9a8b",
//     message: "Legacy payment processor migration",
//     author: "Alex Rivera",
//     date: "Jan 9, 2026",
//     relevance: "low",
//     snippet: "Updated auth dependencies"
//   },
// ];

// const relatedFiles = [
//   { name: "AuthProvider.tsx", path: "src/auth", changes: 45 },
//   { name: "useAuth.ts", path: "src/hooks", changes: 12 },
//   { name: "SessionManager.js", path: "src/legacy", changes: 8 },
// ];

// const explanations: Record<Mode, { title: string; content: React.ReactNode }> = {
//   explain: {
//     title: "AI Answer",
//     content: (
//       <div className="space-y-6 animate-fade-in p-4">
//         <div className="prose prose-sm prose-invert max-w-none">
//           <p className="text-foreground leading-relaxed">
//             The authentication system was refactored in early 2026 primarily due to <strong>security concerns with the admin token bypass</strong> and the need for better logging.
//           </p>
          
//           <p className="text-muted-foreground leading-relaxed">
//             The original implementation by John (who left in 2019) had a silent bypass for admin tokens that was added for a one-time data migration but never removed. Sarah Chen's refactor in commit <code className="bg-primary/20 text-primary px-1.5 py-0.5 rounded text-xs">a7c3d2f</code> addresses this by:
//           </p>
          
//           <ul className="text-muted-foreground space-y-2 mt-3">
//             <li className="flex items-start gap-2">
//               <ArrowRight className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
//               <span>Adding console warnings when admin bypass is used for audit trails</span>
//             </li>
//             <li className="flex items-start gap-2">
//               <ArrowRight className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
//               <span>Tightening JWT validation to reject malformed tokens</span>
//             </li>
//             <li className="flex items-start gap-2">
//               <ArrowRight className="w-4 h-4 mt-0.5 text-primary flex-shrink-0" />
//               <span>Preserving backward compatibility with legacy 2-part tokens</span>
//             </li>
//           </ul>
//         </div>

//         <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
//           <div className="flex items-center gap-2 text-xs text-primary mb-2">
//             <Sparkles className="w-3 h-3" />
//             Key Insight
//           </div>
//           <p className="text-sm text-muted-foreground">
//             The 500ms delay in <code className="bg-muted px-1 rounded text-xs">refreshSession()</code> was kept because mobile apps depend on this timing. This was confirmed in PR #847 comments.
//           </p>
//         </div>
//       </div>
//     ),
//   },
//   summarize: {
//     title: "Commit History",
//     content: (
//       <div className="p-4 space-y-3 animate-fade-in">
//         <p className="text-xs text-muted-foreground mb-4">
//           Found {relatedCommits.length} commits related to your question
//         </p>
//         {relatedCommits.map((commit) => (
//           <button
//             key={commit.hash}
//             className="w-full p-3 rounded-lg border border-border bg-card/50 hover:bg-muted/50 transition-colors text-left group"
//           >
//             <div className="flex items-center justify-between mb-2">
//               <div className="flex items-center gap-2">
//                 <GitCommit className="w-3 h-3 text-primary" />
//                 <code className="text-xs font-mono text-primary">{commit.hash}</code>
//                 <span className={cn(
//                   "px-1.5 py-0.5 rounded text-[10px] font-medium",
//                   commit.relevance === "high" && "bg-green-500/20 text-green-500",
//                   commit.relevance === "medium" && "bg-yellow-500/20 text-yellow-600",
//                   commit.relevance === "low" && "bg-muted text-muted-foreground"
//                 )}>
//                   {commit.relevance} relevance
//                 </span>
//               </div>
//               <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
//             </div>
//             <p className="text-sm font-medium text-foreground mb-1">{commit.message}</p>
//             <p className="text-xs text-muted-foreground mb-2">{commit.snippet}</p>
//             <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
//               <span className="flex items-center gap-1">
//                 <User className="w-3 h-3" />
//                 {commit.author}
//               </span>
//               <span className="flex items-center gap-1">
//                 <Calendar className="w-3 h-3" />
//                 {commit.date}
//               </span>
//             </div>
//           </button>
//         ))}
//       </div>
//     ),
//   },
//   review: {
//     title: "Related Files",
//     content: (
//       <div className="p-4 space-y-3 animate-fade-in">
//         <p className="text-xs text-muted-foreground mb-4">
//           Files that may contain additional context
//         </p>
//         {relatedFiles.map((file) => (
//           <button
//             key={file.name}
//             className="w-full p-3 rounded-lg border border-border bg-card/50 hover:bg-muted/50 transition-colors text-left flex items-center justify-between group"
//           >
//             <div className="flex items-center gap-3">
//               <FileCode className="w-4 h-4 text-primary" />
//               <div>
//                 <p className="text-sm font-medium text-foreground">{file.name}</p>
//                 <p className="text-xs text-muted-foreground">{file.path}</p>
//               </div>
//             </div>
//             <div className="text-right">
//               <p className="text-xs text-muted-foreground">{file.changes} changes</p>
//               <ExternalLink className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity ml-auto" />
//             </div>
//           </button>
//         ))}
        
//         <div className="mt-4 p-3 rounded-lg bg-muted/30 border border-border">
//           <p className="text-xs text-muted-foreground">
//             💡 Click on a file to see how it relates to your question and the highlighted commit.
//           </p>
//         </div>
//       </div>
//     ),
//   },
//   fix: {
//     title: "Context",
//     content: (
//       <div className="p-4 animate-fade-in">
//         <p className="text-sm text-muted-foreground">Additional context about the codebase.</p>
//       </div>
//     ),
//   },
// };

// export function ExplanationPanel({ mode }: ExplanationPanelProps) {
//   const [isTyping, setIsTyping] = useState(true);

//   useEffect(() => {
//     setIsTyping(true);
//     const timer = setTimeout(() => setIsTyping(false), 1200);
//     return () => clearTimeout(timer);
//   }, [mode]);

//   const { content } = explanations[mode];

//   return (
//     <div className="h-full flex flex-col bg-card overflow-hidden">
//       <div className="flex-1 overflow-auto scrollbar-thin">
//         {!isTyping && content}
//         {isTyping && (
//           <div className="p-4 space-y-3">
//             <div className="flex items-center gap-2 text-xs text-primary mb-4">
//               <Sparkles className="w-3 h-3 animate-pulse" />
//               <span>Searching through commits...</span>
//             </div>
//             <div className="h-4 bg-muted/50 rounded animate-pulse w-3/4" />
//             <div className="h-4 bg-muted/50 rounded animate-pulse w-full" />
//             <div className="h-4 bg-muted/50 rounded animate-pulse w-5/6" />
//             <div className="h-4 bg-muted/50 rounded animate-pulse w-2/3" />
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }
import { useState, useEffect } from "react";
import { Sparkles, ArrowRight } from "lucide-react";

type Mode = "explain" | "review" | "fix" | "summarize";

interface ExplanationPanelProps {
  mode: Mode;
  answer?: string;
  loading?: boolean;
}

// Parse the RAG response to extract answer and key insights
function parseAnswer(answer: string) {
  const lines = answer.split("\n");
  const sections = {
    mainAnswer: [] as string[],
    keyInsight: null as string | null,
  };

  let inKeyInsight = false;

  for (const line of lines) {
    if (line.includes("Key Insight") || line.includes("**Key Insight**")) {
      inKeyInsight = true;
      continue;
    }

    if (inKeyInsight) {
      if (line.trim() === "") continue;
      sections.keyInsight = line.replace(/^\*\*Key Insight\*\*:\s*/, "").trim();
      inKeyInsight = false;
    } else {
      sections.mainAnswer.push(line);
    }
  }

  return sections;
}

// Format text with markdown-like styling
function formatText(text: string) {
  // Match **bold text** and `code`
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="bg-primary/20 text-primary px-1.5 py-0.5 rounded text-xs font-mono">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export function ExplanationPanel({ mode, answer, loading }: ExplanationPanelProps) {
  const [isTyping, setIsTyping] = useState(true);

  useEffect(() => {
    setIsTyping(true);
    const timer = setTimeout(() => setIsTyping(false), 800);
    return () => clearTimeout(timer);
  }, [mode, answer]);

  const { mainAnswer, keyInsight } = parseAnswer(answer || "");

  return (
    <div className="h-full flex flex-col bg-card overflow-hidden">
      <div className="flex-1 overflow-auto scrollbar-thin">
        {/* LOADING STATE */}
        {(loading || isTyping) && (
          <div className="p-4 space-y-3">
            <div className="flex items-center gap-2 text-xs text-primary mb-4">
              <Sparkles className="w-3 h-3 animate-pulse" />
              <span>Searching through code history...</span>
            </div>
            <div className="h-4 bg-muted/50 rounded animate-pulse w-3/4" />
            <div className="h-4 bg-muted/50 rounded animate-pulse w-full" />
            <div className="h-4 bg-muted/50 rounded animate-pulse w-5/6" />
            <div className="h-4 bg-muted/50 rounded animate-pulse w-2/3" />
          </div>
        )}

        {/* REAL AI ANSWER */}
        {!loading && !isTyping && answer && (
          <div className="p-4 animate-fade-in space-y-4">
            {/* Main answer text */}
            <div className="space-y-3">
              {mainAnswer.map((line, i) => {
                const trimmed = line.trim();

                // Bullet points with arrows
                if (trimmed.startsWith("-") || trimmed.startsWith("•")) {
                  const bulletText = trimmed.replace(/^[-•]\s*/, "");
                  return (
                    <div key={i} className="flex items-start gap-2.5">
                      <ArrowRight className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                      <p className="text-muted-foreground text-sm leading-relaxed">
                        {formatText(bulletText)}
                      </p>
                    </div>
                  );
                }

                // Regular paragraphs
                if (trimmed && !trimmed.startsWith("#")) {
                  return (
                    <p key={i} className="text-foreground text-sm leading-relaxed">
                      {formatText(trimmed)}
                    </p>
                  );
                }

                return null;
              })}
            </div>

            {/* Key Insight Box */}
            {keyInsight && (
              <div className="p-3 rounded-lg border border-primary/30 bg-primary/5 space-y-2 mt-6">
                <div className="flex items-center gap-2 text-xs text-primary font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  Key Insight
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed">
                  {formatText(keyInsight)}
                </p>
              </div>
            )}
          </div>
        )}

        {/* EMPTY STATE */}
        {!loading && !isTyping && !answer && (
          <div className="p-4 text-xs text-muted-foreground">
            Ask a question about this repository to see AI explanations based on commit history
            and code summaries.
          </div>
        )}
      </div>
    </div>
  );
}
