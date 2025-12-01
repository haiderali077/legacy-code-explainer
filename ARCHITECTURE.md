# CodeAncestry - Technical Overview

## System Architecture

```
Frontend (React) → FastAPI (Vultr) → GitHub API
                          ↓              ↓
                     Gemini AI     Snowflake Vector DB
```

## Core Workflow

1. **Auth**: GitHub OAuth → Encrypt token → User session
2. **Select Repo**: Fetch user's GitHub repos → User picks one
3. **Analysis** (Background Job):
   - Fetch all commits/PRs from GitHub
   - Send each to Gemini: "Explain what changed and why"
   - Generate vector embedding from AI response
   - Store in Snowflake: `original_message` + `ai_enhanced_message` + `embedding`
4. **Query**:
   - User asks: "Why did we change X?"
   - Generate embedding of question
   - Vector search Snowflake for similar commits (top 10)
   - Send question + retrieved commits to Gemini
   - Gemini answers based on context
   - Display answer with citations

## Database Schema

### `commits_analysis`
```sql
id, repo_id, commit_hash, author_name, commit_date,
original_message, ai_enhanced_message, 
key_concepts[], affected_components[],
embedding VECTOR(384)
```

### `pr_analysis`
```sql
id, repo_id, pr_number, pr_title,
original_description, ai_summary,
architectural_changes[], embedding VECTOR(384)
```

### `repositories`
```sql
id, user_id, github_repo_url, repo_name,
analysis_status, total_commits, analyzed_commits
```

### `users`
```sql
id, github_id, github_username, 
encrypted_token_ref, created_at
```

## Tech Stack

- **Frontend**: Lovable (React)
- **Backend**: FastAPI (Python) on Vultr
- **Auth**: GitHub OAuth + JWT
- **AI**: Gemini API (analysis + Q&A)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector DB**: Snowflake Cortex
- **Voice**: ElevenLabs (read answers)

## API Endpoints

```
POST   /auth/github              # OAuth login
GET    /api/repositories         # List repos
POST   /api/repositories/analyze # Start analysis
POST   /api/query                # Ask question (RAG)
GET    /api/repositories/{id}/status  # Progress
```

## RAG Process (Retrieval-Augmented Generation)

```
User Question
    ↓
Generate embedding
    ↓
Vector similarity search (Snowflake)
    ↓
Retrieve top 10 relevant commits
    ↓
Gemini: Answer question using retrieved context
    ↓
Display answer + commit citations
```

## Key Features

- ✅ Auto-analyze entire repo history (commits + PRs)
- ✅ AI-enhanced commit messages stored in vector DB
- ✅ Natural language Q&A about codebase evolution
- ✅ Fast semantic search (vector similarity)
- ✅ Cite specific commits/PRs in answers
- ✅ Secure token storage (JWT + encryption)

## Performance

- **Analysis**: ~10 min for 1000 commits
- **Query Response**: 2-4 seconds
- **Vector Search**: <500ms
- **Caching**: Common questions cached

## Data Flow

```
Analysis: GitHub → Gemini → Vector Embedding → Snowflake
Query:    Question → Embedding → Vector Search → Context → Gemini → Answer
```
