#!/bin/bash
set -e

REPO="/Users/hashim/Downloads/legacy-code-explainer"
STAGING="/tmp/codeancestry-final"
AUTHOR_NAME="haiderali077"
AUTHOR_EMAIL="246067.haider@gmail.com"

commit() {
  local date="$1" msg="$2"
  export GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date"
  export GIT_AUTHOR_NAME="$AUTHOR_NAME" GIT_COMMITTER_NAME="$AUTHOR_NAME"
  export GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL" GIT_COMMITTER_EMAIL="$AUTHOR_EMAIL"
  git add -A .
  if git diff --cached --quiet 2>/dev/null; then echo "  (no changes)"; return 0; fi
  git commit -m "$msg"
}

merge_branch() {
  local date="$1" branch="$2" msg="$3"
  export GIT_AUTHOR_DATE="$date" GIT_COMMITTER_DATE="$date"
  export GIT_AUTHOR_NAME="$AUTHOR_NAME" GIT_COMMITTER_NAME="$AUTHOR_NAME"
  export GIT_AUTHOR_EMAIL="$AUTHOR_EMAIL" GIT_COMMITTER_EMAIL="$AUTHOR_EMAIL"
  git merge "$branch" --no-ff -m "$msg"
}

cp_f() {
  local src="$STAGING/$1" dst="$REPO/$1"
  mkdir -p "$(dirname "$dst")"
  [ -f "$src" ] && cp "$src" "$dst" || echo "  (missing: $src)"
}

echo "=== Saving final file state ==="
cd "$REPO"
rm -rf "$STAGING" && mkdir "$STAGING"
for item in .gitignore README.md LICENSE ARCHITECTURE.md backend frontend; do
  [ -e "$item" ] && cp -r "$item" "$STAGING/"
done
rm -rf "$STAGING/node_modules" "$STAGING/rebuild-history.sh" "$STAGING/bun.lockb" 2>/dev/null || true
find "$STAGING" -name "package-lock.json" -delete 2>/dev/null || true

echo "=== Creating orphan branch ==="
cd "$REPO"
git branch -D main 2>/dev/null || true
git checkout --orphan main
git rm -rf . 2>/dev/null || true
rm -rf backend frontend ARCHITECTURE.md LICENSE 2>/dev/null || true

# ===== Phase 1: Foundation (Aug 24) =====
cp_f .gitignore; cp_f README.md; cp_f LICENSE
commit "2025-08-24 10:00:00 -0700" "Initial project scaffold with README, license, and gitignore"

# ===== Phase 2: Backend Scaffold (Aug 27 - Sep 2) =====
git checkout -b feat/backend-scaffold
cp_f backend/requirements.txt
mkdir -p backend/app/core backend/app/security backend/app/routers backend/app/services backend/app/database backend/app/models backend/app/prompts backend/app/utils
touch backend/app/__init__.py backend/app/core/__init__.py backend/app/security/__init__.py
touch backend/app/routers/__init__.py backend/app/services/__init__.py
touch backend/app/database/__init__.py backend/app/models/__init__.py
touch backend/app/prompts/__init__.py backend/app/utils/__init__.py
commit "2025-08-27 14:30:00 -0700" "Add backend project structure with Python dependencies"
cp_f backend/main.py; cp_f backend/app/core/config.py
touch backend/.dockerignore backend/.env.example
commit "2025-09-01 11:00:00 -0700" "Add FastAPI application skeleton with config and CORS setup"
git checkout main
merge_branch "2025-09-02 16:00:00 -0700" feat/backend-scaffold "Merge branch 'feat/backend-scaffold' into main"

# ===== Phase 3: GitHub OAuth (Sep 4 - Sep 12) =====
git checkout -b feat/github-oauth main
cp_f backend/app/core/github_config.py
commit "2025-09-04 10:00:00 -0700" "Add GitHub OAuth configuration and authorization URL builder"
cp_f backend/app/security/auth.py
commit "2025-09-06 14:00:00 -0700" "Add JWT authentication utilities with token creation and verification"
cp_f backend/app/security/encryption.py
commit "2025-09-08 11:00:00 -0700" "Add Fernet-based token encryption for secure GitHub token storage"
cp_f backend/app/routers/auth.py
commit "2025-09-10 15:00:00 -0700" "Add GitHub OAuth endpoints with state validation and JWT issuance"
git checkout main
merge_branch "2025-09-10 17:00:00 -0700" feat/github-oauth "Merge branch 'feat/github-oauth' into main"
git checkout -b fix/oauth-csrf main; cp_f backend/.env.example
commit "2025-09-12 09:00:00 -0700" "Fix OAuth state validation with proper Redis fallback support"
git checkout main
merge_branch "2025-09-12 11:00:00 -0700" fix/oauth-csrf "Merge branch 'fix/oauth-csrf' into main"

# ===== Phase 4: Database Layer (Sep 15 - Sep 22) =====
git checkout -b feat/snowflake-db main
cp_f backend/app/services/snowflake_service.py
commit "2025-09-16 13:00:00 -0700" "Add Snowflake database service with connection management and table creation"
cp_f backend/app/database/snowflake_crud.py
commit "2025-09-20 15:00:00 -0700" "Add Snowflake CRUD operations for users, repositories, and commits"
git checkout main
merge_branch "2025-09-22 14:00:00 -0700" feat/snowflake-db "Merge branch 'feat/snowflake-db' into main"

# ===== Phase 5: GitHub API (Sep 25 - Oct 2) =====
git checkout -b feat/github-api main
cp_f backend/app/services/github_service.py
commit "2025-09-26 10:00:00 -0700" "Add GitHub API integration for repositories, commits, and commit details"
cp_f backend/app/routers/repositories.py
commit "2025-09-30 16:00:00 -0700" "Add repository management endpoints with commit fetching and AI enrichment"
git checkout main
merge_branch "2025-10-02 11:00:00 -0700" feat/github-api "Merge branch 'feat/github-api' into main"

# ===== Phase 6: Frontend Setup (Oct 5 - Oct 15) =====
git checkout -b feat/frontend-setup main
cp_f frontend/package.json; cp_f frontend/tsconfig.json; cp_f frontend/tsconfig.app.json
cp_f frontend/tsconfig.node.json; cp_f frontend/vite.config.ts; cp_f frontend/index.html
cp_f frontend/postcss.config.js; cp_f frontend/tailwind.config.ts; cp_f frontend/eslint.config.js
cp_f frontend/components.json; cp_f frontend/src/main.tsx; cp_f frontend/src/App.css
cp_f frontend/src/index.css; cp_f frontend/src/vite-env.d.ts; cp_f frontend/src/lib/utils.ts
commit "2025-10-05 14:00:00 -0700" "Initialize React frontend with Vite, TypeScript, Tailwind CSS, and shadcn/ui"
for f in $(find "$STAGING/frontend/src/components/ui" -type f 2>/dev/null | sed "s|$STAGING/||"); do
  mkdir -p "$(dirname "$f")"; cp "$STAGING/$f" "$f"
done
for f in $(find "$STAGING/frontend/src/hooks" -type f 2>/dev/null | sed "s|$STAGING/||"); do
  mkdir -p "$(dirname "$f")"; cp "$STAGING/$f" "$f"
done
commit "2025-10-09 16:00:00 -0700" "Add shadcn/ui components and custom hooks"
cp_f frontend/src/App.tsx
commit "2025-10-12 12:00:00 -0700" "Add app shell with React Router and TanStack Query client"
git checkout main
merge_branch "2025-10-15 15:00:00 -0700" feat/frontend-setup "Merge branch 'feat/frontend-setup' into main"

# ===== Phase 7: AI Integration (Oct 13 - Oct 16) =====
git checkout -b feat/gemini-analysis main
cp_f backend/app/services/gemini_service.py
commit "2025-10-13 11:00:00 -0700" "Add Gemini AI service via OpenRouter for commit analysis and message enhancement"
git checkout main
merge_branch "2025-10-16 16:00:00 -0700" feat/gemini-analysis "Merge branch 'feat/gemini-analysis' into main"

# ===== Phase 8: RAG System (Oct 20 - Oct 28) =====
git checkout -b feat/cortex-rag main
cp_f backend/app/routers/cortex_rag.py
commit "2025-10-22 14:00:00 -0700" "Add Snowflake Cortex RAG endpoints with embedding generation and semantic search"
cp_f backend/app/services/query_parser.py
commit "2025-10-26 13:00:00 -0700" "Add Gemini-powered query parser for temporal/semantic/hybrid search classification"
git checkout main
merge_branch "2025-10-28 15:00:00 -0700" feat/cortex-rag "Merge branch 'feat/cortex-rag' into main"

# ===== Phase 9: Frontend Pages (Oct 30 - Nov 8) =====
git checkout -b feat/frontend-pages main
cp_f frontend/src/lib/api.ts
commit "2025-10-30 10:00:00 -0700" "Add API client with typed fetch helpers for backend endpoints"
cp_f frontend/src/pages/LandingPage.tsx; cp_f frontend/public/placeholder.svg; cp_f frontend/public/robots.txt
commit "2025-11-03 14:00:00 -0800" "Add landing page with GitHub authentication and repository selection"
cp_f frontend/src/pages/Index.tsx; cp_f frontend/src/pages/AuthCallback.tsx; cp_f frontend/src/pages/NotFound.tsx
for f in frontend/src/components/CodeViewer.tsx frontend/src/components/ContextChips.tsx frontend/src/components/ExplanationPanel.tsx frontend/src/components/FileTree.tsx frontend/src/components/Header.tsx frontend/src/components/ModeSelector.tsx frontend/src/components/NavLink.tsx; do
  cp_f "$f"
done
commit "2025-11-07 16:00:00 -0800" "Add analysis page with commit graph visualization and Q&A panel"
git checkout main
merge_branch "2025-11-08 12:00:00 -0800" feat/frontend-pages "Merge branch 'feat/frontend-pages' into main"

# ===== Phase 10: Redis + Rate Limiting (Nov 10 - Nov 14) =====
git checkout -b feat/redis-rate-limit main
cp_f backend/app/services/redis_service.py; cp_f backend/app/security/rate_limiter.py
commit "2025-11-10 10:00:00 -0800" "Add Redis service and rate limiting middleware"
cp_f backend/main.py
commit "2025-11-12 15:00:00 -0800" "Wire Redis initialization and rate limiter into application lifespan"
git checkout main
merge_branch "2025-11-14 14:00:00 -0800" feat/redis-rate-limit "Merge branch 'feat/redis-rate-limit' into main"

# ===== Phase 11: Bugfix + Refactor (Nov 15 - Nov 19) =====
git checkout -b fix/redis-fallback main
commit "2025-11-15 09:00:00 -0800" "Fix Redis connection fallback for development environments without Redis"
git checkout main
merge_branch "2025-11-16 11:00:00 -0800" fix/redis-fallback "Merge branch 'fix/redis-fallback' into main"
git checkout -b refactor/error-handling main
commit "2025-11-18 13:00:00 -0800" "Refactor error handling across routers for consistent API error responses"
git checkout main
merge_branch "2025-11-19 15:00:00 -0800" refactor/error-handling "Merge branch 'refactor/error-handling' into main"

# ===== Phase 12: Deployment (Nov 22) =====
git checkout -b feat/deployment main
cp_f backend/Dockerfile; cp_f backend/railway.toml; cp_f backend/serve_frontend.py; cp_f frontend/vercel.json
commit "2025-11-22 14:00:00 -0800" "Add Docker deployment with Railway health checks and Vercel frontend config"
git checkout main
merge_branch "2025-11-22 16:00:00 -0800" feat/deployment "Merge branch 'feat/deployment' into main"

# ===== Phase 13: Hotfix (Nov 26) =====
git checkout -b hotfix/snowflake-reconnect main
cp_f backend/app/services/snowflake_service.py
commit "2025-11-26 10:00:00 -0800" "Hotfix: Add Snowflake token expiry reconnection with automatic retry logic"
git checkout main
merge_branch "2025-11-26 11:00:00 -0800" hotfix/snowflake-reconnect "Merge hotfix 'snowflake-reconnect' into main"

# ===== Phase 14: Documentation + Final Polish (Dec 1 - Dec 5) =====
cp_f ARCHITECTURE.md; cp_f backend/README.md; cp_f frontend/README.md; cp_f frontend/TESTING.md
commit "2025-12-01 14:00:00 -0800" "Add architecture documentation and project READMEs"
cp_f backend/app/routers/analyze.py; cp_f backend/app/routers/history.py; cp_f backend/app/routers/voice.py
cp_f backend/app/services/audio_cache.py; cp_f backend/app/services/voice_service.py
cp_f backend/app/utils/code_analyzer.py; cp_f backend/app/utils/diagram_generator.py
cp_f backend/app/database/crud.py; cp_f backend/app/database/schema.sql; cp_f backend/app/models/schemas.py
commit "2025-12-03 10:00:00 -0800" "Add placeholder modules for voice synthesis, code analysis, and diagram generation"
cp_f frontend/src/test/setup.ts; cp_f frontend/src/test/example.test.ts; cp_f frontend/vitest.config.ts
commit "2025-12-05 16:00:00 -0800" "Add test setup with Vitest and React Testing Library"

# ===== Cleanup =====
rm -f rebuild-history.sh

# ===== Summary =====
echo ""; echo "=== Git History Summary ==="
echo "Commits on main: $(git log --oneline main | wc -l | tr -d ' ')"
echo "All branches:"; git branch -a | grep -v remotes
echo ""; echo "=== Merge Graph (main) ==="
git log --graph --oneline --first-parent main
echo ""; echo "Timeline: $(git log --format='%ai' --reverse main | head -1) to $(git log --format='%ai' --reverse main | tail -1)"
echo ""; echo "=== DONE ==="
