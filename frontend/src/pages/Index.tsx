import { useState, useCallback, useEffect } from "react";

import {
  GitCommit,
  FileCode,
  ChevronRight,
  ChevronDown,
  Clock,
  ArrowLeft,
  ExternalLink,
  User,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ExplanationPanel } from "@/components/ExplanationPanel";
import { useNavigate } from "react-router-dom";
import { fetchCommitDetails } from "@/lib/api";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// High-level commit nodes for graph view
type CommitNode = {
  id: string;
  hash: string;
  summary: string;
  description: string;
  date: string;
  author: string;
  relevance: "high" | "medium" | "low";
  fileCount: number;
  linkedSections: string[]; // IDs of related code sections
};

// Relevant code sections across multiple files
type CodeSection = {
  id: string;
  file: string;
  path: string;
  functionName: string;
  lineStart: number;
  lineEnd: number;
  relevance: "high" | "medium" | "low";
  summary: string;
  lines: {
    type: "context" | "addition" | "deletion";
    line: number;
    content: string;
    relevant?: boolean;
  }[];
};

const relevantSections: CodeSection[] = [
  {
    id: "1",
    file: "OldSessionHandler.js",
    path: "src/legacy",
    functionName: "_validateToken()",
    lineStart: 33,
    lineEnd: 44,
    relevance: "high",
    summary: "Admin token bypass was made auditable",
    lines: [
      { type: "context", line: 33, content: "  _validateToken(token) {" },
      { type: "context", line: 34, content: "    if (!token) return false;" },
      {
        type: "context",
        line: 35,
        content: "    // HACK: Skip validation for admin tokens",
        relevant: true,
      },
      {
        type: "deletion",
        line: 36,
        content: "    if (token.startsWith('admin_')) return true;",
        relevant: true,
      },
      {
        type: "addition",
        line: 36,
        content: "    if (token.startsWith('admin_')) {",
        relevant: true,
      },
      {
        type: "addition",
        line: 37,
        content: "      console.warn('Admin token bypass used');",
        relevant: true,
      },
      { type: "addition", line: 38, content: "      return true;" },
      { type: "addition", line: 39, content: "    }" },
      { type: "context", line: 40, content: "" },
      {
        type: "context",
        line: 41,
        content: "    const parts = token.split('.');",
      },
      {
        type: "deletion",
        line: 42,
        content: "    return parts.length >= 2;",
        relevant: true,
      },
      {
        type: "addition",
        line: 42,
        content: "    // Should be 3 parts for JWT but legacy tokens have 2",
      },
      {
        type: "addition",
        line: 43,
        content: "    return parts.length >= 2 && parts.length <= 3;",
        relevant: true,
      },
      { type: "context", line: 44, content: "  }" },
    ],
  },
  {
    id: "2",
    file: "AuthProvider.tsx",
    path: "src/auth",
    functionName: "useAuthState()",
    lineStart: 45,
    lineEnd: 58,
    relevance: "high",
    summary: "Auth state now checks token validity",
    lines: [
      { type: "context", line: 45, content: "  const useAuthState = () => {" },
      {
        type: "context",
        line: 46,
        content: "    const [user, setUser] = useState(null);",
      },
      {
        type: "addition",
        line: 47,
        content: "    const [isValidating, setIsValidating] = useState(true);",
        relevant: true,
      },
      { type: "context", line: 48, content: "" },
      { type: "context", line: 49, content: "    useEffect(() => {" },
      {
        type: "deletion",
        line: 50,
        content: "      const session = sessionHandler.getSession();",
        relevant: true,
      },
      {
        type: "addition",
        line: 50,
        content: "      const session = await sessionHandler.getSession();",
        relevant: true,
      },
      {
        type: "addition",
        line: 51,
        content: "      setIsValidating(false);",
        relevant: true,
      },
      {
        type: "context",
        line: 52,
        content: "      if (session) setUser(session.user);",
      },
      { type: "context", line: 53, content: "    }, []);" },
    ],
  },
  {
    id: "3",
    file: "useAuth.ts",
    path: "src/hooks",
    functionName: "refreshToken()",
    lineStart: 22,
    lineEnd: 35,
    relevance: "medium",
    summary: "Token refresh now logs attempts",
    lines: [
      {
        type: "context",
        line: 22,
        content: "  async function refreshToken() {",
      },
      {
        type: "addition",
        line: 23,
        content: "    console.log('Refreshing auth token...');",
        relevant: true,
      },
      { type: "context", line: 24, content: "    try {" },
      {
        type: "context",
        line: 25,
        content: "      const newToken = await api.refresh();",
      },
      {
        type: "addition",
        line: 26,
        content: "      console.log('Token refreshed successfully');",
        relevant: true,
      },
      { type: "context", line: 27, content: "      return newToken;" },
      { type: "context", line: 28, content: "    } catch (e) {" },
      {
        type: "addition",
        line: 29,
        content: "      console.error('Token refresh failed:', e);",
        relevant: true,
      },
      { type: "context", line: 30, content: "      throw e;" },
      { type: "context", line: 31, content: "    }" },
      { type: "context", line: 32, content: "  }" },
    ],
  },
];

const Index = () => {
  const navigate = useNavigate();
  const [selectedCommitNode, setSelectedCommitNode] = useState<string | null>(
    null
  );
  const [commitNodesState, setCommitNodesState] = useState<CommitNode[]>([]);
  const [commitDetails, setCommitDetails] = useState<any>(null);
  const [loadingCommitDetails, setLoadingCommitDetails] = useState(false);

  const [activeSection, setActiveSection] = useState("1");
  const [expandedSections, setExpandedSections] = useState<string[]>(["1"]);
  const [userQuestion, setUserQuestion] = useState(
    "Why was the authentication system refactored in 2023?"
  );
  const [answer, setAnswer] = useState("");
  const [loading, setLoading] = useState(false);
  const [questionInput, setQuestionInput] = useState("");

  const repoId = sessionStorage.getItem("analysis_id") || "";
  console.log("📊 Using repo ID:", repoId);

  // Load initial question from sessionStorage if available
  useEffect(() => {
    const savedQuestion = sessionStorage.getItem("last_question");
    if (savedQuestion) {
      console.log("📝 Loaded question from session:", savedQuestion);
      setUserQuestion(savedQuestion);
    }
  }, []);

  // Auto-load data when page mounts with saved question
  useEffect(() => {
    const runAutoQuery = async () => {
      const savedQuestion = sessionStorage.getItem("last_question");
      if (savedQuestion && repoId && commitNodesState.length === 0) {
        console.log("🚀 Auto-loading RAG query with question:", savedQuestion);
        await askRepoQuestion(savedQuestion);
      }
    };
    runAutoQuery();
  }, [repoId]);

  async function askRepoQuestion(question: string) {
    try {
      setLoading(true);

      const token = localStorage.getItem("access_token");
      if (!token) {
        console.error("❌ No access token found in localStorage");
        setAnswer("Please log in first - no authentication token found.");
        return;
      }

      console.log("🔑 Using token:", token.substring(0, 20) + "...");

      const res = await fetch(
        `${API_BASE}/api/repositories/${repoId}/cortex-query`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            question: question,
            top_k: 5,
            model: "mistral-7b",
          }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        console.error("❌ API Error:", res.status, errorData);
        setAnswer(`Error ${res.status}: ${errorData.detail || "Unknown error"}`);
        return;
      }

      const data = await res.json();

      setAnswer(data.answer || "No answer returned from backend.");

      // Map sources to commit nodes and update the graph
      if (data.sources && data.sources.length > 0) {
        const ragCommits: CommitNode[] = data.sources.map((source: any) => {
          // Determine relevance based on similarity score
          let relevance: "high" | "medium" | "low" = "low";
          if (source.similarity >= 0.7) relevance = "high";
          else if (source.similarity >= 0.5) relevance = "medium";

          // Format the date nicely
          let formattedDate = "Unknown";
          if (source.commit_date) {
            try {
              const date = new Date(source.commit_date);
              formattedDate = date.toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              });
            } catch (e) {
              formattedDate = source.commit_date;
            }
          }

          return {
            id: source.sha.substring(0, 7),
            hash: source.sha.substring(0, 7),
            summary: source.ai_summary || source.message,
            description: source.message,
            date: formattedDate,
            author: source.author_name || "Unknown",
            relevance,
            fileCount: 0,
            linkedSections: [],
          };
        });

        console.log("📊 Updating graph with", ragCommits.length, "RAG commits");
        setCommitNodesState(ragCommits);
      }
    } catch (err) {
      console.error(err);
      setAnswer("Failed to reach CodeAncestry backend.");
    } finally {
      setLoading(false);
    }
  }

  const handleAsk = () => {
    if (!questionInput.trim()) return;

    const q = questionInput.trim();
    setUserQuestion(q);
    setQuestionInput("");
    askRepoQuestion(q);
  };

  // Get active commit data based on selection
  const activeCommit = selectedCommitNode
    ? commitNodesState.find((n) => n.id === selectedCommitNode)
    : commitNodesState[0];

  const handleNodeClick = useCallback(
    async (nodeId: string) => {
      if (selectedCommitNode === nodeId) {
        // Clicking same node closes the panel
        setSelectedCommitNode(null);
        setCommitDetails(null);
      } else {
        setSelectedCommitNode(nodeId);
        
        // Fetch commit details from API
        const token = localStorage.getItem("access_token");
        if (token && repoId) {
          setLoadingCommitDetails(true);
          try {
            const data = await fetchCommitDetails(repoId, nodeId, token);
            console.log("📄 Commit details:", data);
            setCommitDetails(data.commit);
          } catch (error) {
            console.error("Failed to fetch commit details:", error);
          } finally {
            setLoadingCommitDetails(false);
          }
        }
        
        const node = commitNodesState.find((n) => n.id === nodeId);
        if (node && node.linkedSections.length > 0) {
          setExpandedSections(node.linkedSections);
          setActiveSection(node.linkedSections[0]);
        }
      }
    },
    [selectedCommitNode, commitNodesState, repoId]
  );

  const handleCloseDetails = useCallback(() => {
    setSelectedCommitNode(null);
  }, []);

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      {/* Commit Header - More Prominent */}
      <header className="border-b border-border bg-gradient-to-r from-primary/5 to-transparent flex-shrink-0">
        <div className="px-4 py-3">
          {/* Top row: Back + Commit hash */}
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate("/")}
                className="gap-1 text-muted-foreground hover:text-foreground"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </Button>
              <div className="h-4 w-px bg-border" />
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20">
                <GitCommit className="w-4 h-4 text-primary" />
                <code className="text-sm font-mono font-bold text-primary">
                  {activeCommit?.hash || "---"}
                </code>
              </div>
              <span className="text-xs text-muted-foreground font-mono">
                on main
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="gap-1 text-xs text-muted-foreground"
            >
              <ExternalLink className="w-3 h-3" />
              View on GitHub
            </Button>
          </div>

          {/* Commit message */}
          <h1 className="text-lg font-semibold text-foreground mb-1">
            {activeCommit?.summary || "Select a commit to view details"}
          </h1>
          <p className="text-sm text-muted-foreground mb-3">
            {activeCommit?.description || "No description available"}
          </p>

          {/* Meta row */}
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary font-medium text-[10px]">
                {activeCommit?.author
                  ? activeCommit.author
                      .split(" ")
                      .map((n) => n[0])
                      .join("")
                  : "?"}
              </div>
              <span className="text-foreground font-medium">
                {activeCommit?.author || "Unknown"}
              </span>
            </div>
            <span className="flex items-center gap-1 text-muted-foreground">
              <Clock className="w-3 h-3" />
              {activeCommit?.date || "---"}
            </span>
            <div className="flex items-center gap-2 ml-auto">
              <span className="flex items-center gap-1 text-muted-foreground">
                <FileCode className="w-3 h-3" />
                {activeCommit?.fileCount || 0} files
                changed
              </span>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel: Graph - Always visible */}
        <div
          className={cn(
            "flex flex-col border-r border-border transition-all duration-300",
            selectedCommitNode ? "w-[320px]" : "flex-1"
          )}
        >
          {/* Header */}
          <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-muted/30">
            <GitCommit className="w-4 h-4 text-primary" />
            <span className="text-sm font-medium text-foreground">
              Commit Graph
            </span>
            <div className="ml-auto text-xs text-muted-foreground">
              {commitNodesState.length} commits
            </div>
          </div>

          {/* Graph Content */}
          <div
            className={cn(
              "flex-1 overflow-auto",
              selectedCommitNode ? "p-4" : "p-6"
            )}
          >
            <div className="relative">
              {/* Graph nodes */}
              <div
                className={cn(
                  "flex flex-col",
                  selectedCommitNode ? "space-y-4" : "space-y-6"
                )}
              >                {commitNodesState.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => handleNodeClick(node.id)}
                    className={cn(
                      "relative flex items-start gap-4 rounded-xl transition-all duration-200 text-left",
                      "hover:bg-muted/50",
                      selectedCommitNode ? "p-2" : "p-4",
                      selectedCommitNode === node.id &&
                        "bg-primary/10 ring-1 ring-primary"
                    )}
                  >
                    {/* Circle Node */}
                    <div
                      className={cn(
                        "relative z-10 rounded-full border-4 flex items-center justify-center flex-shrink-0 transition-all",
                        selectedCommitNode ? "w-12 h-12" : "w-16 h-16",
                        node.relevance === "high" &&
                          "border-green-500 bg-green-500/20 shadow-green-500/50 shadow-lg",
                        node.relevance === "medium" &&
                          "border-amber-500 bg-amber-500/20 shadow-amber-500/50 shadow-md",
                        node.relevance === "low" &&
                          "border-slate-400 bg-slate-400/10",
                        selectedCommitNode === node.id && "scale-110 ring-2 ring-primary ring-offset-2"
                      )}
                    >
                      <GitCommit
                        className={cn(
                          selectedCommitNode ? "w-5 h-5" : "w-7 h-7",
                          node.relevance === "high" && "text-green-600 font-bold",
                          node.relevance === "medium" && "text-amber-600 font-semibold",
                          node.relevance === "low" && "text-slate-500"
                        )}
                      />
                    </div>

                    {/* Node info */}
                    <div className="flex-1 min-w-0 pt-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <code
                          className={cn(
                            "font-mono font-bold text-primary",
                            selectedCommitNode ? "text-xs" : "text-base"
                          )}
                        >
                          {node.hash}
                        </code>
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded-full font-semibold tracking-wide",
                            selectedCommitNode ? "text-[9px]" : "text-xs",
                            node.relevance === "high" &&
                              "bg-green-500/30 text-green-700 border border-green-500/50",
                            node.relevance === "medium" &&
                              "bg-amber-500/30 text-amber-700 border border-amber-500/50",
                            node.relevance === "low" &&
                              "bg-slate-300/30 text-slate-600 border border-slate-400/50"
                          )}
                        >
                          {node.relevance === "high" ? "🎯 HIGH" : node.relevance === "medium" ? "⚡ MEDIUM" : "📍 LOW"}
                        </span>
                      </div>
                      <p
                        className={cn(
                          "text-foreground font-medium mt-1",
                          selectedCommitNode ? "text-xs truncate" : "text-base"
                        )}
                      >
                        {node.summary}
                      </p>
                      {!selectedCommitNode && (
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {node.description}
                        </p>
                      )}
                      <div
                        className={cn(
                          "flex items-center gap-3 text-muted-foreground mt-2",
                          selectedCommitNode ? "text-[10px]" : "text-sm"
                        )}
                      >
                        <span className="flex items-center gap-1">
                          <User
                            className={
                              selectedCommitNode ? "w-3 h-3" : "w-4 h-4"
                            }
                          />
                          {selectedCommitNode
                            ? node.author.split(" ")[0]
                            : node.author}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock
                            className={
                              selectedCommitNode ? "w-3 h-3" : "w-4 h-4"
                            }
                          />
                          {node.date}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <FileCode
                            className={
                              selectedCommitNode ? "w-3 h-3" : "w-4 h-4"
                            }
                          />
                          {node.fileCount} files
                        </span>
                      </div>
                    </div>

                    <ChevronRight
                      className={cn(
                        "text-muted-foreground flex-shrink-0 transition-transform",
                        selectedCommitNode ? "w-4 h-4 mt-2" : "w-5 h-5 mt-3",
                        selectedCommitNode === node.id &&
                          "rotate-90 text-primary"
                      )}
                    />
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Middle Panel: Code Details - Slides in when commit selected */}
        <div
          className={cn(
            "flex flex-col border-r border-border bg-card/50 transition-all duration-300 overflow-hidden",
            selectedCommitNode ? "flex-1 opacity-100" : "w-0 opacity-0"
          )}
        >
          {selectedCommitNode && (
            <>
              {/* Details Header */}
              <div className="flex items-center gap-2 px-4 py-2 border-b border-border bg-primary/5">
                <FileCode className="w-4 h-4 text-primary" />
                <span className="text-sm font-medium text-foreground">
                  Files Changed
                </span>
                <span className="text-xs text-muted-foreground ml-1">
                  {commitDetails?.files_changed?.length || 0} files
                </span>
                <button
                  onClick={handleCloseDetails}
                  className="ml-auto p-1 rounded hover:bg-muted/50 transition-colors"
                >
                  <X className="w-4 h-4 text-muted-foreground" />
                </button>
              </div>

              {/* Details Content */}
              <div className="flex-1 overflow-auto p-3 space-y-3 animate-fade-in">
                {loadingCommitDetails ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <div className="animate-pulse">Loading commit details...</div>
                  </div>
                ) : commitDetails?.files_changed ? (
                  commitDetails.files_changed.map((file: any, idx: number) => {
                    const isExpanded = expandedSections.includes(String(idx));
                    return (
                      <div
                        key={idx}
                        className={cn(
                          "rounded-lg border overflow-hidden transition-all duration-200",
                          activeSection === String(idx)
                            ? "border-primary/50 bg-primary/5 shadow-sm"
                            : "border-border bg-card/50 hover:border-muted-foreground/30"
                        )}
                      >
                        {/* File header */}
                        <button
                          onClick={() => {
                            setActiveSection(String(idx));
                            setExpandedSections((prev) =>
                              prev.includes(String(idx))
                                ? prev.filter((id) => id !== String(idx))
                                : [...prev, String(idx)]
                            );
                          }}
                          className="w-full px-3 py-2.5 flex items-center justify-between text-left hover:bg-muted/30 transition-colors"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <div
                              className={cn(
                                "w-2 h-2 rounded-full flex-shrink-0",
                                file.status === "added" && "bg-green-500",
                                file.status === "modified" && "bg-yellow-500",
                                file.status === "removed" && "bg-red-500"
                              )}
                            />
                            <div className="min-w-0">
                              <div className="flex items-center gap-2 text-sm">
                                <FileCode className="w-4 h-4 text-primary flex-shrink-0" />
                                <span className="font-medium text-foreground truncate">
                                  {file.filename}
                                </span>
                                <span className="text-xs text-muted-foreground">
                                  {file.status}
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2 flex-shrink-0">
                            <span className="text-xs text-green-500">+{file.additions}</span>
                            <span className="text-xs text-red-500">-{file.deletions}</span>
                            <ChevronDown
                              className={cn(
                                "w-3.5 h-3.5 text-muted-foreground transition-transform duration-200",
                                isExpanded && "rotate-180"
                              )}
                            />
                          </div>
                        </button>

                        {/* Code diff */}
                        <div
                          className={cn(
                            "overflow-hidden transition-all duration-200",
                            isExpanded ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0"
                          )}
                        >
                          <div className="border-t border-border bg-code-bg">
                            <pre className="p-3 text-xs font-mono overflow-x-auto max-h-[500px] overflow-y-auto">
                              {file.patch ? (
                                file.patch.split('\n').map((line: string, i: number) => (
                                  <div
                                    key={i}
                                    className={cn(
                                      "px-2 -mx-2",
                                      line.startsWith('+') && !line.startsWith('+++') && "bg-green-500/10 text-green-400",
                                      line.startsWith('-') && !line.startsWith('---') && "bg-red-500/10 text-red-400",
                                      line.startsWith('@@') && "text-blue-400 bg-blue-500/10"
                                    )}
                                  >
                                    {line || ' '}
                                  </div>
                                ))
                              ) : (
                                <div className="text-muted-foreground italic">No diff available</div>
                              )}
                            </pre>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Select a commit to view file changes
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Right Panel: Answer + Context */}
        <div
          className={cn(
            "flex-shrink-0 flex flex-col h-full overflow-hidden transition-all duration-300",
            selectedCommitNode ? "w-[340px]" : "w-[480px]"
          )}
        >
          {/* User's Question - Fixed at top */}
          <div className="px-4 py-3 border-b border-border bg-primary/5 flex-shrink-0">
            <div className="text-xs text-muted-foreground mb-1">
              Your question
            </div>
            <p className="text-sm font-medium text-foreground">
              "{userQuestion}"
            </p>
          </div>

          {/* Scrollable Answer Area */}
          <div className="flex-1 overflow-auto min-h-0">
            <ExplanationPanel
              mode="explain"
              answer={answer}
              loading={loading}
            />
          </div>

          {/* Follow-up Question Input - Fixed at bottom */}
          <div className="p-3 border-t border-border bg-card/50 flex-shrink-0">
            <div className="relative">
              <input
                type="text"
                value={questionInput}
                onChange={(e) => setQuestionInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && questionInput.trim()) {
                    const q = questionInput.trim();
                    setUserQuestion(q);
                    setQuestionInput("");
                    askRepoQuestion(q);
                  }
                }}
                placeholder="Ask a follow-up question..."
                className="w-full px-3 py-2.5 pr-16 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
              <Button
                size="sm"
                className="absolute right-1 top-1"
                onClick={() => {
                  if (questionInput.trim()) {
                    const q = questionInput.trim();
                    setUserQuestion(q);
                    setQuestionInput("");
                    askRepoQuestion(q);
                  }
                }}
              >
                Ask
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
