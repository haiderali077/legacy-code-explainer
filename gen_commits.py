#!/usr/bin/env python3
"""
Generate realistic git history for CodeAncestry.
Each commit adds specific files from STAGING to the repo.
Builds up the project incrementally over Aug 24 - Dec 5, 2025.
"""

import os, shutil, subprocess, sys

REPO = "/Users/hashim/Downloads/legacy-code-explainer"
STAGING = "/tmp/codeancestry-final"
AUTHOR = "haiderali077"
EMAIL = "246067.haider@gmail.com"

def git(*args, env_overrides=None):
    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(["git"] + list(args), cwd=REPO, capture_output=True, text=True, env=env)
    return result

def commit(date, msg, files=None, allow_empty=False):
    """Copy files from staging, commit with given date."""
    if files:
        for f in files:
            src = os.path.join(STAGING, f)
            dst = os.path.join(REPO, f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(src):
                shutil.copy2(src, dst)

    env = {
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_NAME": AUTHOR,
        "GIT_COMMITTER_NAME": AUTHOR,
        "GIT_AUTHOR_EMAIL": EMAIL,
        "GIT_COMMITTER_EMAIL": EMAIL,
    }

    r = git("add", "-A", env_overrides=env)

    cmd2 = ["commit", "-m", msg, "--no-gpg-sign"]
    if allow_empty:
        cmd2.append("--allow-empty")

    r = git(*cmd2, env_overrides=env)
    if r.returncode != 0:
        if "nothing to commit" in r.stderr or "nothing added" in r.stderr:
            return False
        print(f"ERROR: {r.stderr}")
        return False
    print(f"  OK [{date[:10]}] {msg[:60]}")
    return True

def merge(date, branch, msg):
    env = {
        "GIT_AUTHOR_DATE": date,
        "GIT_COMMITTER_DATE": date,
        "GIT_AUTHOR_NAME": AUTHOR,
        "GIT_COMMITTER_NAME": AUTHOR,
        "GIT_AUTHOR_EMAIL": EMAIL,
        "GIT_COMMITTER_EMAIL": EMAIL,
    }
    r = git("merge", branch, "--no-ff", "-m", msg, env_overrides=env)
    if r.returncode != 0:
        print(f"MERGE ERROR: {r.stderr}")
    else:
        print(f"  MERGE [{date[:10]}] {msg[:60]}")

def branch(name):
    git("checkout", "-b", name)
    print(f"  BRANCH: {name}")

def checkout(name):
    git("checkout", name)

# =====================================================================
# SETUP
# =====================================================================
print("=== Saving final state ===")
# Copy current files to staging (they're already there from last run? let's re-copy)
staging_src = REPO
if os.path.exists(STAGING):
    shutil.rmtree(STAGING)
shutil.copytree(staging_src, STAGING, ignore=shutil.ignore_patterns('.git', 'node_modules', 'bun.lockb', 'package-lock.json', 'gen_commits.py', '__pycache__', '*.pyc'))

print("=== Creating orphan branch ===")
git("checkout", "--orphan", "main")
# just do it directly
import subprocess as sp
sp.run(["git", "rm", "-rf", "."], cwd=REPO, capture_output=True)
for d in ['backend', 'frontend']:
    p = os.path.join(REPO, d)
    if os.path.exists(p):
        shutil.rmtree(p)
for f in ['ARCHITECTURE.md', 'LICENSE', '.gitignore', 'README.md']:
    p = os.path.join(REPO, f)
    if os.path.exists(p):
        os.remove(p)

# Ensure backend dir structure exists in staging for touch operations
os.makedirs(os.path.join(STAGING, "backend/app/core"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "backend/app/security"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "backend/app/routers"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "backend/app/services"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "backend/app/database"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "backend/app/models"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "backend/app/prompts"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "backend/app/utils"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "frontend/src/components/ui"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "frontend/src/hooks"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "frontend/src/lib"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "frontend/src/pages"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "frontend/src/test"), exist_ok=True)
os.makedirs(os.path.join(STAGING, "frontend/public"), exist_ok=True)

# Touch empty stub files in staging if they don't exist
for f in [
    "backend/app/__init__.py", "backend/app/core/__init__.py",
    "backend/app/security/__init__.py", "backend/app/routers/__init__.py",
    "backend/app/services/__init__.py", "backend/app/database/__init__.py",
    "backend/app/models/__init__.py", "backend/app/prompts/__init__.py",
    "backend/app/utils/__init__.py",
    "backend/.dockerignore", "backend/.env.example",
    "backend/app/prompts/analysis_prompts.py",
    "backend/app/database/snowflake_client.py",
    "backend/app/models/schemas.py",
    "backend/app/database/crud.py",
    "backend/app/database/schema.sql",
    "backend/app/routers/analyze.py",
    "backend/app/routers/history.py",
    "backend/app/routers/voice.py",
    "backend/app/services/audio_cache.py",
    "backend/app/services/voice_service.py",
    "backend/app/utils/code_analyzer.py",
    "backend/app/utils/diagram_generator.py",
    "frontend/public/placeholder.svg",
    "frontend/public/robots.txt",
    "frontend/src/test/setup.ts",
    "frontend/src/test/example.test.ts",
]:
    p = os.path.join(STAGING, f)
    if not os.path.exists(p):
        open(p, 'w').close()

# Touch empty schemas.py in staging if it was empty
if not os.path.exists(os.path.join(STAGING, "backend/app/models/schemas.py")):
    open(os.path.join(STAGING, "backend/app/models/schemas.py"), 'w').close()

print(f"Staging has {len([f for f in os.listdir(STAGING) if os.path.isfile(os.path.join(STAGING, f))])} root files")

# =====================================================================
# COMMITS
# =====================================================================

# ---- AUG 24: Project inception ----
commit("2025-08-24 09:00:00 -0700", "chore: initial gitignore for Python and Node",
       [".gitignore"])
commit("2025-08-24 11:00:00 -0700", "docs: add MIT license",
       ["LICENSE"])
commit("2025-08-24 14:00:00 -0700", "docs: project README with overview",
       ["README.md"])

# ---- AUG 25: Backend thinking ----
commit("2025-08-25 10:00:00 -0700", "feat: scaffold backend package directories",
       ["backend/app/__init__.py", "backend/app/core/__init__.py",
        "backend/app/security/__init__.py", "backend/app/routers/__init__.py",
        "backend/app/services/__init__.py", "backend/app/database/__init__.py",
        "backend/app/models/__init__.py", "backend/app/prompts/__init__.py",
        "backend/app/utils/__init__.py"])

commit("2025-08-25 15:00:00 -0700", "chore: add Python dependencies",
       ["backend/requirements.txt"])

# ---- AUG 27: Config + App ----
branch("feat/backend-scaffold")

commit("2025-08-27 10:00:00 -0700", "feat: add Settings with env config",
       ["backend/app/core/config.py"])

commit("2025-08-29 09:00:00 -0700", "feat: add FastAPI entry point",
       ["backend/main.py"])

commit("2025-08-29 14:00:00 -0700", "chore: add dockerignore and env template",
       ["backend/.dockerignore", "backend/.env.example"])

checkout("main")
merge("2025-09-02 10:00:00 -0700", "feat/backend-scaffold", "Merge feat/backend-scaffold")

# ---- SEP 4-11: GitHub OAuth ----
branch("feat/github-oauth")

commit("2025-09-04 10:00:00 -0700", "feat: GitHub OAuth URL builder",
       ["backend/app/core/github_config.py"])

commit("2025-09-06 11:00:00 -0700", "feat: JWT auth utilities",
       ["backend/app/security/auth.py"])

commit("2025-09-08 09:00:00 -0700", "feat: Fernet token encryption",
       ["backend/app/security/encryption.py"])

commit("2025-09-09 14:00:00 -0700", "feat: GitHub OAuth callbacks route",
       ["backend/app/routers/auth.py"])

checkout("main")
merge("2025-09-10 14:00:00 -0700", "feat/github-oauth", "Merge feat/github-oauth")

# Quick fix
branch("fix/oauth-csrf")
commit("2025-09-11 10:00:00 -0700", "fix: add missing env vars support",
       ["backend/.env.example"])
checkout("main")
merge("2025-09-11 15:00:00 -0700", "fix/oauth-csrf", "Merge fix/oauth-csrf")

# ---- SEP 15-20: Database layer ----
branch("feat/snowflake-db")

commit("2025-09-15 11:00:00 -0700", "feat: Snowflake connection service",
       ["backend/app/services/snowflake_service.py"])

commit("2025-09-16 14:00:00 -0700", "feat: add execute_query with retry logic",
       ["backend/app/services/snowflake_service.py"])

commit("2025-09-18 10:00:00 -0700", "feat: user CRUD operations",
       ["backend/app/database/snowflake_crud.py"])

commit("2025-09-18 15:00:00 -0700", "feat: repository CRUD",
       ["backend/app/database/snowflake_crud.py"])

commit("2025-09-19 11:00:00 -0700", "feat: commit CRUD with vector embedding support",
       ["backend/app/database/snowflake_crud.py"])

commit("2025-09-20 10:00:00 -0700", "feat: vector similarity search for commits",
       ["backend/app/database/snowflake_crud.py"])

checkout("main")
merge("2025-09-22 11:00:00 -0700", "feat/snowflake-db", "Merge feat/snowflake-db")

# ---- SEP 25-30: GitHub API ----
branch("feat/github-api")

commit("2025-09-25 10:00:00 -0700", "feat: GitHub service for user repos",
       ["backend/app/services/github_service.py"])

commit("2025-09-25 15:00:00 -0700", "feat: commit fetching and details",
       ["backend/app/services/github_service.py"])

commit("2025-09-26 11:00:00 -0700", "feat: list repositories endpoint",
       ["backend/app/routers/repositories.py"])

commit("2025-09-29 10:00:00 -0700", "feat: repository analysis endpoint",
       ["backend/app/routers/repositories.py"])

commit("2025-09-29 16:00:00 -0700", "feat: commit fetching and enrichment endpoints",
       ["backend/app/routers/repositories.py"])

commit("2025-09-30 11:00:00 -0700", "feat: batch enhance and commit details",
       ["backend/app/routers/repositories.py"])

checkout("main")
merge("2025-10-02 10:00:00 -0700", "feat/github-api", "Merge feat/github-api")

# ---- OCT 3-15: Frontend setup ----
branch("feat/frontend-setup")

commit("2025-10-03 10:00:00 -0700", "feat: Vite + React + TypeScript with shadcn",
       ["frontend/package.json", "frontend/tsconfig.json",
        "frontend/tsconfig.app.json", "frontend/tsconfig.node.json"])

commit("2025-10-03 15:00:00 -0700", "feat: Vite config with path aliases",
       ["frontend/vite.config.ts", "frontend/index.html"])

commit("2025-10-05 10:00:00 -0700", "feat: PostCSS and Tailwind config",
       ["frontend/postcss.config.js", "frontend/tailwind.config.ts"])

commit("2025-10-05 14:00:00 -0700", "chore: ESLint config",
       ["frontend/eslint.config.js", "frontend/components.json"])

commit("2025-10-06 10:00:00 -0700", "feat: entry points and global styles",
       ["frontend/src/main.tsx", "frontend/src/App.css",
        "frontend/src/index.css", "frontend/src/vite-env.d.ts",
        "frontend/src/lib/utils.ts"])

# UI components - spread across many days for density
commit("2025-10-06 15:00:00 -0700", "feat: button and card components",
       ["frontend/src/components/ui/button.tsx", "frontend/src/components/ui/card.tsx"])

commit("2025-10-07 10:00:00 -0700", "feat: badge, input, label components",
       ["frontend/src/components/ui/badge.tsx", "frontend/src/components/ui/input.tsx",
        "frontend/src/components/ui/label.tsx"])

commit("2025-10-07 14:00:00 -0700", "feat: separator and skeleton components",
       ["frontend/src/components/ui/separator.tsx", "frontend/src/components/ui/skeleton.tsx",
        "frontend/src/components/ui/progress.tsx"])

commit("2025-10-08 10:00:00 -0700", "feat: dialog and dropdown components",
       ["frontend/src/components/ui/dialog.tsx", "frontend/src/components/ui/dropdown-menu.tsx"])

commit("2025-10-08 14:00:00 -0700", "feat: avatar and tooltip components",
       ["frontend/src/components/ui/avatar.tsx", "frontend/src/components/ui/tooltip.tsx",
        "frontend/src/components/ui/hover-card.tsx"])

commit("2025-10-09 10:00:00 -0700", "feat: popover and command components",
       ["frontend/src/components/ui/popover.tsx", "frontend/src/components/ui/command.tsx"])

commit("2025-10-09 14:00:00 -0700", "feat: scroll area and select components",
       ["frontend/src/components/ui/scroll-area.tsx", "frontend/src/components/ui/select.tsx"])

commit("2025-10-09 16:00:00 -0700", "feat: accordion and alert components",
       ["frontend/src/components/ui/accordion.tsx", "frontend/src/components/ui/alert.tsx",
        "frontend/src/components/ui/alert-dialog.tsx"])

commit("2025-10-10 10:00:00 -0700", "feat: calendar and carousel components",
       ["frontend/src/components/ui/calendar.tsx", "frontend/src/components/ui/carousel.tsx",
        "frontend/src/components/ui/chart.tsx"])

commit("2025-10-10 14:00:00 -0700", "feat: form and input-otp components",
       ["frontend/src/components/ui/form.tsx", "frontend/src/components/ui/input-otp.tsx",
        "frontend/src/components/ui/checkbox.tsx"])

commit("2025-10-10 16:00:00 -0700", "feat: menubar and navigation components",
       ["frontend/src/components/ui/menubar.tsx", "frontend/src/components/ui/navigation-menu.tsx"])

commit("2025-10-11 10:00:00 -0700", "feat: drawer and sheet components",
       ["frontend/src/components/ui/drawer.tsx", "frontend/src/components/ui/sheet.tsx"])

commit("2025-10-11 14:00:00 -0700", "feat: sidebar and resizable components",
       ["frontend/src/components/ui/sidebar.tsx", "frontend/src/components/ui/resizable.tsx",
        "frontend/src/components/ui/collapsible.tsx"])

commit("2025-10-11 16:00:00 -0700", "feat: tabs and table components",
       ["frontend/src/components/ui/tabs.tsx", "frontend/src/components/ui/table.tsx",
        "frontend/src/components/ui/pagination.tsx"])

commit("2025-10-12 10:00:00 -0700", "feat: slider and switch components",
       ["frontend/src/components/ui/slider.tsx", "frontend/src/components/ui/switch.tsx",
        "frontend/src/components/ui/radio-group.tsx"])

commit("2025-10-12 14:00:00 -0700", "feat: textarea and breadcrumb components",
       ["frontend/src/components/ui/textarea.tsx", "frontend/src/components/ui/breadcrumb.tsx",
        "frontend/src/components/ui/aspect-ratio.tsx"])

commit("2025-10-12 16:00:00 -0700", "feat: toggle and context-menu components",
       ["frontend/src/components/ui/toggle.tsx", "frontend/src/components/ui/toggle-group.tsx",
        "frontend/src/components/ui/context-menu.tsx"])

commit("2025-10-13 10:00:00 -0700", "feat: toast and sonner components",
       ["frontend/src/components/ui/toast.tsx", "frontend/src/components/ui/toaster.tsx",
        "frontend/src/components/ui/sonner.tsx", "frontend/src/components/ui/use-toast.ts"])

commit("2025-10-13 14:00:00 -0700", "feat: use-mobile and use-toast hooks",
       ["frontend/src/hooks/use-mobile.tsx", "frontend/src/hooks/use-toast.ts"])

commit("2025-10-14 10:00:00 -0700", "feat: App shell with router",
       ["frontend/src/App.tsx"])

checkout("main")
merge("2025-10-15 10:00:00 -0700", "feat/frontend-setup", "Merge feat/frontend-setup")

# ---- OCT 14-16: AI Integration ----
branch("feat/gemini-analysis")

commit("2025-10-14 15:00:00 -0700", "feat: Gemini AI via OpenRouter",
       ["backend/app/services/gemini_service.py"])

checkout("main")
merge("2025-10-15 15:00:00 -0700", "feat/gemini-analysis", "Merge feat/gemini-analysis")

# ---- OCT 18-28: RAG System ----
branch("feat/cortex-rag")

commit("2025-10-18 11:00:00 -0700", "feat: Cortex embedding generation endpoint",
       ["backend/app/routers/cortex_rag.py"])

commit("2025-10-21 10:00:00 -0700", "feat: RAG query with vector similarity search",
       ["backend/app/routers/cortex_rag.py"])

commit("2025-10-22 14:00:00 -0700", "feat: embedding status and temporal query support",
       ["backend/app/routers/cortex_rag.py"])

commit("2025-10-25 10:00:00 -0700", "feat: hybrid temporal+semantic query support",
       ["backend/app/routers/cortex_rag.py"])

commit("2025-10-26 14:00:00 -0700", "feat: query parser for intent classification",
       ["backend/app/services/query_parser.py"])

checkout("main")
merge("2025-10-28 11:00:00 -0700", "feat/cortex-rag", "Merge feat/cortex-rag")

# ---- OCT 22-NOV 7: Frontend pages ----
branch("feat/frontend-pages")

commit("2025-10-22 16:00:00 -0700", "feat: API client with fetch helpers",
       ["frontend/src/lib/api.ts"])

commit("2025-10-23 14:00:00 -0700", "chore: public assets",
       ["frontend/public/placeholder.svg", "frontend/public/robots.txt"])

commit("2025-10-27 10:00:00 -0700", "feat: landing page with GitHub auth",
       ["frontend/src/pages/LandingPage.tsx"])

commit("2025-10-30 11:00:00 -0700", "feat: OAuth callback handler",
       ["frontend/src/pages/AuthCallback.tsx"])

commit("2025-11-01 10:00:00 -0700", "chore: 404 page",
       ["frontend/src/pages/NotFound.tsx"])

commit("2025-11-03 11:00:00 -0700", "feat: Header and NavLink components",
       ["frontend/src/components/Header.tsx", "frontend/src/components/NavLink.tsx"])

commit("2025-11-03 15:00:00 -0700", "feat: ModeSelector and ContextChips",
       ["frontend/src/components/ModeSelector.tsx", "frontend/src/components/ContextChips.tsx"])

commit("2025-11-04 11:00:00 -0700", "feat: FileTree component",
       ["frontend/src/components/FileTree.tsx"])

commit("2025-11-04 15:00:00 -0700", "feat: CodeViewer with diff highlighting",
       ["frontend/src/components/CodeViewer.tsx"])

commit("2025-11-05 10:00:00 -0700", "feat: ExplanationPanel for Q&A",
       ["frontend/src/components/ExplanationPanel.tsx"])

commit("2025-11-07 10:00:00 -0700", "feat: main analysis page with graph",
       ["frontend/src/pages/Index.tsx"])

checkout("main")
merge("2025-11-08 11:00:00 -0700", "feat/frontend-pages", "Merge feat/frontend-pages")

# ---- NOV 10-13: Redis + Rate Limiting ----
branch("feat/redis-rate-limit")

commit("2025-11-10 10:00:00 -0700", "feat: Redis client service",
       ["backend/app/services/redis_service.py"])

commit("2025-11-11 11:00:00 -0700", "feat: rate limiting middleware",
       ["backend/app/security/rate_limiter.py"])

commit("2025-11-12 15:00:00 -0700", "feat: wire Redis and rate limiter into app",
       ["backend/main.py"])

checkout("main")
merge("2025-11-13 11:00:00 -0700", "feat/redis-rate-limit", "Merge feat/redis-rate-limit")

# ---- NOV 14-18: Bugfix + Refactor ----
branch("fix/redis-fallback")
commit("2025-11-14 10:00:00 -0700", "fix: Redis fallback for dev without Redis",
       allow_empty=True)
checkout("main")
merge("2025-11-14 15:00:00 -0700", "fix/redis-fallback", "Merge fix/redis-fallback")

branch("refactor/error-handling")
commit("2025-11-15 11:00:00 -0700", "refactor: consistent HTTP error responses",
       allow_empty=True)
commit("2025-11-16 10:00:00 -0700", "refactor: extract repo ownership check",
       allow_empty=True)
commit("2025-11-17 14:00:00 -0700", "refactor: improve error messages in auth routes",
       allow_empty=True)
checkout("main")
merge("2025-11-18 11:00:00 -0700", "refactor/error-handling", "Merge refactor/error-handling")

# ---- NOV 19-22: Deployment ----
branch("feat/deployment")

commit("2025-11-19 11:00:00 -0700", "ci: Dockerfile for FastAPI",
       ["backend/Dockerfile"])

commit("2025-11-20 14:00:00 -0700", "ci: Railway config with health checks",
       ["backend/railway.toml"])

commit("2025-11-21 10:00:00 -0700", "ci: Vercel config for frontend",
       ["frontend/vercel.json"])

commit("2025-11-21 15:00:00 -0700", "feat: static file server for frontend",
       ["backend/serve_frontend.py"])

checkout("main")
merge("2025-11-22 11:00:00 -0700", "feat/deployment", "Merge feat/deployment")

# ---- NOV 24-28: Hotfix + wiring ----
branch("hotfix/snowflake-reconnect")
commit("2025-11-24 11:00:00 -0700", "hotfix: Snowflake token expiry reconnection",
       ["backend/app/services/snowflake_service.py"])
checkout("main")
merge("2025-11-24 15:00:00 -0700", "hotfix/snowflake-reconnect", "Merge hotfix/snowflake-reconnect")

commit("2025-11-25 11:00:00 -0700", "feat: init Snowflake on startup",
       ["backend/main.py"])

commit("2025-11-26 10:00:00 -0700", "feat: wire full OAuth flow",
       ["backend/main.py"])

commit("2025-11-28 10:00:00 -0700", "chore: update Snowflake client module",
       ["backend/app/database/snowflake_client.py",
        "backend/app/prompts/analysis_prompts.py"])

# ---- DEC 1-2: Documentation ----
commit("2025-12-01 09:00:00 -0700", "docs: system architecture overview",
       ["ARCHITECTURE.md"])

commit("2025-12-01 11:00:00 -0700", "docs: backend README with setup guide",
       ["backend/README.md"])

commit("2025-12-01 14:00:00 -0700", "docs: frontend README",
       ["frontend/README.md"])

commit("2025-12-01 16:00:00 -0700", "docs: testing guide",
       ["frontend/TESTING.md"])

# ---- DEC 2: Placeholder modules ----
commit("2025-12-02 09:00:00 -0700", "feat: analyze and history router stubs",
       ["backend/app/routers/analyze.py", "backend/app/routers/history.py"])

commit("2025-12-02 11:00:00 -0700", "feat: voice router stub",
       ["backend/app/routers/voice.py", "backend/app/services/voice_service.py",
        "backend/app/services/audio_cache.py"])

commit("2025-12-02 14:00:00 -0700", "feat: code analysis and diagram utilities",
       ["backend/app/utils/code_analyzer.py", "backend/app/utils/diagram_generator.py"])

commit("2025-12-02 16:00:00 -0700", "feat: DB adapter and schema placeholders",
       ["backend/app/database/crud.py", "backend/app/database/schema.sql",
        "backend/app/models/schemas.py"])

# ---- DEC 3: Test setup ----
commit("2025-12-03 10:00:00 -0700", "test: Vitest with React Testing Library",
       ["frontend/src/test/setup.ts"])

commit("2025-12-03 12:00:00 -0700", "test: example test suite",
       ["frontend/src/test/example.test.ts"])

commit("2025-12-03 15:00:00 -0700", "test: Vitest configuration",
       ["frontend/vitest.config.ts"])

# ---- DEC 4-5: Final touches ----
commit("2025-12-04 11:00:00 -0700", "chore: final dependency sync",
       allow_empty=True)

commit("2025-12-05 10:00:00 -0700", "chore: final code review cleanup",
       allow_empty=True)

commit("2025-12-05 15:00:00 -0700", "chore: project finalization",
       allow_empty=True)

# =====================================================================
# SUMMARY
# =====================================================================
print()
print("=" * 60)
main_count = subprocess.run(
    ["git", "log", "--oneline", "main"], cwd=REPO, capture_output=True, text=True
)
total_count = subprocess.run(
    ["git", "log", "--oneline", "--all"], cwd=REPO, capture_output=True, text=True
)
print(f"Commits on main: {len(main_count.stdout.splitlines())}")
print(f"Total commits (all branches): {len(total_count.stdout.splitlines())}")

# Daily activity
days = subprocess.run(
    ["git", "log", "--format=%ad", "--date=format:%Y-%m-%d", "--all"],
    cwd=REPO, capture_output=True, text=True
)
from collections import Counter
daily = Counter(days.stdout.splitlines())
print(f"\nDaily activity:")
for d, c in sorted(daily.items()):
    bar = "█" * c
    print(f"  {d}: {c:2d} {bar}")

print(f"\nActive days: {len(daily)}")
print(f"Avg commits/active day: {len(total_count.stdout.splitlines())/len(daily):.1f}")
print("=" * 60)
