import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Github, ArrowRight, Code2, Sparkles, History, Users, Zap, GitBranch, MessageSquare, Clock, Search, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const startGithubLogin = async () => {
  try {
    const res = await fetch(`${API_BASE}/auth/github`);
    if (!res.ok) throw new Error(`Auth init failed: ${res.status}`);
    const data = await res.json();
    if (!data?.auth_url) throw new Error("Missing auth_url from backend");
    window.location.href = data.auth_url;
  } catch (e) {
    console.error(e);
    alert(e.message ?? "Failed to start GitHub login");
  }
};


function useOAuthCallback() {
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);

    console.log("[OAuth] callback params:", Object.fromEntries(params.entries()));
    const accessToken = params.get("access_token");

    if (accessToken) {
      localStorage.setItem("access_token", accessToken);

      // clean the URL (remove token from address bar)
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);
}

function parseGithubRepo(url: string) {
  // supports https://github.com/owner/repo or owner/repo
  const cleaned = url.replace("https://github.com/", "").replace(/^\//, "").replace(/\/$/, "");
  const [owner, repo] = cleaned.split("/");
  if (!owner || !repo) return null;
  return { owner, repo };
}


export default function LandingPage() {
  const navigate = useNavigate();
  const [repoUrl, setRepoUrl] = useState("");
  const [question, setQuestion] = useState("");
  const [isConnected, setIsConnected] = useState(false);
  const [user, setUser] = useState<{ github_username: string; user_id: string } | null>(null);
  const [showRepoSelector, setShowRepoSelector] = useState(false);
  const [showSignInDialog, setShowSignInDialog] = useState(false);
  const [availableRepos, setAvailableRepos] = useState<any[]>([]);
  const [loadingRepos, setLoadingRepos] = useState(false);
  const [selectedRepo, setSelectedRepo] = useState<any>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState("");
  const [showQuestionInput, setShowQuestionInput] = useState(false);
  const [userQuestion, setUserQuestion] = useState("");


  useOAuthCallback();

    useEffect(() => {
  setIsConnected(!!localStorage.getItem("access_token"));
}, []);


useEffect(() => {
  const run = async () => {
    const t = localStorage.getItem("access_token");
    if (!t) return;

    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { Authorization: `Bearer ${t}` },
    });

    if (!res.ok) {
      localStorage.removeItem("access_token");
      return;
    }

    const data = await res.json();
    setUser(data);
    setIsConnected(true);
  };

  run();
}, []);

  const fetchUserRepos = async () => {
    const t = localStorage.getItem("access_token");
    if (!t) return;

    setLoadingRepos(true);
    try {
      const res = await fetch(`${API_BASE}/api/repositories`, {
        headers: { Authorization: `Bearer ${t}` },
      });

      if (!res.ok) throw new Error("Failed to fetch repositories");
      const data = await res.json();
      setAvailableRepos(data.repositories || []);
    } catch (e) {
      console.error(e);
      alert("Failed to load repositories");
    } finally {
      setLoadingRepos(false);
    }
  };

  const handleConnectCodebase = async () => {
    const t = localStorage.getItem("access_token");
    
    if (!t) {
      // Not signed in - show sign in dialog
      setShowSignInDialog(true);
      return;
    }

    // Signed in - show repository selector
    setShowRepoSelector(true);
    fetchUserRepos();
  };

  const handleSelectRepo = (repo: any) => {
    setSelectedRepo(repo);
    setRepoUrl(repo.full_name);
    setShowRepoSelector(false);
    setShowQuestionInput(true);
    setIsConnected(true);
  };


  const handleAsk = async () => {
  const t = localStorage.getItem("access_token");
  if (!t || !selectedRepo) return;

  setAnalyzing(true);
  setAnalysisStep("Analyzing repository...");

  // Use selectedRepo info
  const [repoOwner, repoName] = selectedRepo.full_name.split('/');
  const owner = repoOwner;
  const repo_name = repoName || selectedRepo.name;
  const full_name = selectedRepo.full_name;
  const github_repo_id = selectedRepo.id;
  const html_url = selectedRepo.html_url;
  const default_branch = selectedRepo.default_branch || "main";

  try {
    const res = await fetch(`${API_BASE}/api/repositories/analyze`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${t}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        owner,
        repo_name,
        full_name,
        github_repo_id,
        html_url,
        default_branch
      }),
    });

    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: "Failed to analyze repository" }));
      alert(error.detail || "Failed to analyze repository");
      setAnalyzing(false);
      return;
    }

    const data = await res.json();
    const repoId = data.repository.id;

    // Store repo id and user question
    sessionStorage.setItem("last_question", userQuestion);
    sessionStorage.setItem("analysis_id", repoId);

    // Step 2: Fetch commits from GitHub
    setAnalysisStep("Fetching commits from GitHub...");
    const fetchRes = await fetch(`${API_BASE}/api/repositories/${repoId}/fetch-commits?page=1&per_page=100`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${t}`,
      },
    });

    if (!fetchRes.ok) {
      console.error("Failed to fetch commits");
    }

    // Step 3: Generate embeddings
    setAnalysisStep("Generating AI embeddings...");
    const embedRes = await fetch(`${API_BASE}/api/repositories/${repoId}/cortex-embed`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${t}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "e5-base-v2",
        batch_size: 100,
      }),
    });

    if (!embedRes.ok) {
      console.error("Failed to generate embeddings");
    } else {
      console.log("✅ Embeddings generated successfully");
    }

    navigate("/analyze");
  } catch (error) {
    console.error("Analysis error:", error);
    alert("Failed to analyze repository. Please try again.");
  } finally {
    setAnalyzing(false);
    setAnalysisStep("");
  }
};


  const exampleQuestions = [
    "Why was the authentication system refactored?",
    "Who introduced the caching layer and why?",
    "What was the original purpose of this function?",
    "Why did we switch from REST to GraphQL?"
  ];

  const features = [
    {
      icon: MessageSquare,
      title: "Ask a Question",
      description: "Ask anything about your codebase - architecture decisions, refactors, or mysterious functions."
    },
    {
      icon: Clock,
      title: "We Search History",
      description: "Our AI digs through commits, PRs, and code changes to find the relevant context."
    },
    {
      icon: Zap,
      title: "Get Answers",
      description: "See the code with highlights, linked commits, and explanations of why decisions were made."
    }
  ];

  return (
    <div className="min-h-screen bg-background overflow-hidden">
      {/* Animated background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-accent/5 rounded-full blur-3xl animate-pulse delay-1000" />
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-border/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Code2 className="w-5 h-5 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-display font-bold text-xl text-foreground">CodeAncestry</h1>
              <p className="text-xs text-muted-foreground">Brain for your Codebase</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {isConnected && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-500 text-sm">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Connected
              </div>
            )}
            {user ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-muted/50">
                  <img 
                    src={`https://github.com/${user.github_username}.png`} 
                    alt={user.github_username}
                    className="w-6 h-6 rounded-full"
                  />
                  <span className="text-sm font-medium text-foreground">{user.github_username}</span>
                </div>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => {
                    localStorage.removeItem("access_token");
                    setUser(null);
                    setIsConnected(false);
                    setSelectedRepo(null);
                    window.location.reload();
                  }}
                >
                  Log out
                </Button>
              </div>
            ) : (
              <Button variant="ghost" size="sm" onClick={startGithubLogin}>
                <Github className="w-4 h-4 mr-2" />
                Sign in
              </Button>
            )}
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="relative z-10 max-w-6xl mx-auto px-6 py-16">
        <div className="text-center mb-12 animate-fade-in">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm mb-6">
            <History className="w-4 h-4" />
            AI-Powered Code Archaeology
          </div>
          <h2 className="font-display text-4xl md:text-5xl lg:text-6xl font-bold text-foreground mb-4 leading-tight">
            Talk to your<br />
            <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              codebase 
            </span><br />
            like it's your teammate
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Connect your repo, ask a question. We'll dig through your commit history 
            to explain <span className="text-foreground font-medium">why</span> decisions were made, 
            not just what the code does.
          </p>
        </div>

        {/* Main Input Flow */}
        <div className="max-w-2xl mx-auto mb-16 space-y-4 animate-slide-in-right" style={{ animationDelay: "0.2s" }}>
          {/* Step 1: Connect Repo */}
          <div className={`p-6 rounded-2xl border-2 transition-all ${
            isConnected 
              ? 'border-primary/30 bg-primary/5' 
              : 'border-border bg-card/50 backdrop-blur-sm'
          }`}>
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                isConnected && selectedRepo
                  ? 'bg-primary text-primary-foreground' 
                  : 'bg-muted text-muted-foreground'
              }`}>
                {isConnected && selectedRepo ? '✓' : '1'}
              </div>
              <span className="font-semibold text-foreground">
                {isConnected && selectedRepo ? 'Repository Connected' : 'Select your repository'}
              </span>
            </div>
            
            {isConnected ? (
              <div className="space-y-3">
                {selectedRepo ? (
                  <>
                    <div className="flex items-center gap-3 p-4 bg-background border border-input rounded-lg">
                      <GitBranch className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                      <span className="font-medium text-foreground flex-1">{selectedRepo.full_name || selectedRepo.name}</span>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => {
                          setShowRepoSelector(true);
                          fetchUserRepos();
                        }}
                        className="gap-2"
                      >
                        Change Repository
                      </Button>
                    </div>
                    
                    {showQuestionInput ? (
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={userQuestion}
                          onChange={(e) => setUserQuestion(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" && userQuestion.trim()) {
                              handleAsk();
                            }
                          }}
                          placeholder="Ask a question about your codebase..."
                          className="w-full px-3 py-2.5 rounded-lg bg-background border border-input text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                          autoFocus
                        />
                        <div className="flex gap-2">
                          <Button 
                            onClick={handleAsk} 
                            disabled={analyzing || !userQuestion.trim()}
                            className="w-full h-10 gap-2"
                          >
                            {analyzing ? (
                              <>
                                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div>
                                {analysisStep}
                              </>
                            ) : (
                              <>
                                <Sparkles className="w-3 h-3" />
                                Analyze
                                <ArrowRight className="w-3 h-3" />
                              </>
                            )}
                          </Button>
                          <Button 
                            variant="outline" 
                            onClick={() => {
                              setShowQuestionInput(false);
                              setUserQuestion("");
                            }}
                            disabled={analyzing}
                            className="h-10"
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <Button 
                        onClick={() => setShowQuestionInput(true)}
                        className="w-full h-12 gap-2 text-base"
                      >
                        <Sparkles className="w-4 h-4" />
                        Analyze Repository
                        <ArrowRight className="w-4 h-4" />
                      </Button>
                    )}
                  </>
                ) : (
                  <Button 
                    onClick={() => {
                      setShowRepoSelector(true);
                      fetchUserRepos();
                    }}
                    className="w-full h-12 gap-2 text-base"
                  >
                    <GitBranch className="w-4 h-4" />
                    Select Repository
                  </Button>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">Login to select a repository</p>
                <Button onClick={handleConnectCodebase} className="h-12 px-6 gap-2">
                  <Github className="w-4 h-4" />
                  Sign in with GitHub
                </Button>
              </div>
            )}
          </div>
        </div>

        {/* How it works */}
        <div className="grid md:grid-cols-3 gap-6 animate-fade-in" style={{ animationDelay: "0.4s" }}>
          {features.map((feature) => (
            <div 
              key={feature.title}
              className="p-6 rounded-xl bg-card/30 border border-border/50 hover:border-primary/30 transition-colors group"
            >
              <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:bg-primary/20 transition-colors">
                <feature.icon className="w-6 h-6 text-primary" />
              </div>
              <h3 className="font-semibold text-foreground mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Social proof */}
        <div className="text-center mt-16 animate-fade-in" style={{ animationDelay: "0.6s" }}>
          <p className="text-sm text-muted-foreground mb-4">Built for developers who inherit code without context</p>
        </div>
      </main>

      {/* Sign In Dialog */}
      {showSignInDialog && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card rounded-2xl border border-border max-w-md w-full p-8 shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-2xl font-bold text-foreground">Sign in Required</h3>
              <button
                onClick={() => setShowSignInDialog(false)}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <p className="text-muted-foreground mb-6">
              Please sign in with your GitHub account to connect your codebase and start analyzing your repositories.
            </p>
            <Button
              onClick={() => {
                setShowSignInDialog(false);
                startGithubLogin();
              }}
              className="w-full h-12 gap-2"
              size="lg"
            >
              <Github className="w-5 h-5" />
              Sign in with GitHub
            </Button>
          </div>
        </div>
      )}

      {/* Repository Selector Dialog */}
      {showRepoSelector && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-card rounded-2xl border border-border max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl animate-fade-in">
            <div className="flex items-center justify-between p-6 border-b border-border">
              <h3 className="text-2xl font-bold text-foreground">Select Repository</h3>
              <button
                onClick={() => setShowRepoSelector(false)}
                className="p-2 hover:bg-muted rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {loadingRepos ? (
                <div className="text-center py-12">
                  <div className="inline-block w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin mb-4"></div>
                  <p className="text-muted-foreground">Loading your repositories...</p>
                </div>
              ) : availableRepos.length === 0 ? (
                <div className="text-center py-12">
                  <GitBranch className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">No repositories found</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {availableRepos.map((repo) => (
                    <button
                      key={repo.id}
                      onClick={() => handleSelectRepo(repo)}
                      className="w-full p-4 rounded-xl border border-border hover:border-primary hover:bg-primary/5 transition-all text-left group"
                    >
                      <div className="flex items-start gap-3">
                        <GitBranch className="w-5 h-5 text-muted-foreground group-hover:text-primary mt-0.5 transition-colors" />
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-foreground group-hover:text-primary transition-colors">
                            {repo.full_name || repo.name}
                          </div>
                          {repo.description && (
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                              {repo.description}
                            </p>
                          )}
                          <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                            {repo.language && (
                              <span className="flex items-center gap-1">
                                <div className="w-2 h-2 rounded-full bg-primary"></div>
                                {repo.language}
                              </span>
                            )}
                            {repo.stargazers_count !== undefined && (
                              <span>\u2b50 {repo.stargazers_count}</span>
                            )}
                            {repo.updated_at && (
                              <span>Updated {new Date(repo.updated_at).toLocaleDateString()}</span>
                            )}
                          </div>
                        </div>
                        <ArrowRight className="w-5 h-5 text-muted-foreground group-hover:text-primary opacity-0 group-hover:opacity-100 transition-all" />
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
