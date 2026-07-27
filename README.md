# CodeAncestry

Vector search and retrieval-augmented generation over Git repository history. Embeds commit data into 768-dimensional vectors using Snowflake Cortex for semantic similarity search across codebase evolution.

## Overview

CodeAncestry ingests GitHub commit history, generates AI-powered summaries, embeds them as vectors using Snowflake Cortex (`e5-base-v2`, 768-dim), and enables hybrid search — combining vector similarity with temporal/metadata filters. A query parser classifies natural language questions into semantic, temporal, or hybrid modes to route them through the appropriate retrieval pipeline.

## Core Architecture

```
User Question
    ↓
Query Parser (Gemini) → {temporal, semantic, hybrid}
    ↓
Embedding Generation → SNOWFLAKE.CORTEX.EMBED_TEXT_768('e5-base-v2', question)
    ↓
Vector Search → VECTOR_COSINE_SIMILARITY(embedding, query_embedding)
    ↓
Context Retrieval → Top-K similar commits
    ↓
Answer Generation → SNOWFLAKE.CORTEX.COMPLETE (LLM)
    ↓
Response + Citations
```

### Vector Pipeline

- **Embedding Model**: Snowflake Cortex `e5-base-v2` producing 768-dimensional vectors stored in `VECTOR(FLOAT, 768)` columns
- **Indexing**: Commits are embedded on ingest using `SNOWFLAKE.CORTEX.EMBED_TEXT_768()` — serverless, no external model hosting
- **Similarity Search**: `VECTOR_COSINE_SIMILARITY()` for ranked retrieval with configurable thresholds (0.70 default)

### Retrieval Modes

| Mode | Mechanism | Use Case |
|---|---|---|
| **Semantic** | Full vector similarity search | "Why was the auth system refactored?" |
| **Temporal** | SQL date/author filters only | "What did John commit last week?" |
| **Hybrid** | Filtered vector search | "Auth changes from last month" |

### Query Parser

Uses Gemini (via OpenRouter) to classify questions and extract structured filters — date ranges, authors, file paths — routing to the appropriate retrieval strategy without hardcoded rules.

## Data Pipeline

```
GitHub API → Raw Commits → Gemini Summarization → Snowflake Cortex Embedding (768-dim) → Vector DB
                                                                                           ↓
User Query → Embedding → Cosine Similarity Scan → Top-K Context → LLM Generation → Answer
```

## Vector Database Schema

```sql
CREATE TABLE commits_analysis (
    id            VARCHAR(255) PRIMARY KEY,
    sha           VARCHAR(255),
    message       TEXT,
    ai_summary    TEXT,
    embedding     VECTOR(FLOAT, 768),       -- Snowflake Cortex embedding
    files_changed VARIANT,
    additions     INT,
    deletions     INT,
    commit_date   TIMESTAMP_NTZ,
    author_name   VARCHAR(255)
);

-- Hybrid search query
SELECT *, VECTOR_COSINE_SIMILARITY(embedding, PARSE_JSON(%s)::VECTOR(FLOAT, 768)) as similarity
FROM commits_analysis
WHERE repo_id = %s AND embedding IS NOT NULL
  AND commit_date >= DATEADD(day, -7, CURRENT_TIMESTAMP())
ORDER BY similarity DESC
LIMIT 5;
```

## Tech Stack

- **Backend**: Python FastAPI, Uvicorn
- **Vector Database**: Snowflake with `VECTOR(FLOAT, 768)` columns and Cortex AI
- **Embeddings**: Snowflake Cortex `e5-base-v2` (768-dim, serverless)
- **LLM**: Snowflake Cortex `mistral-7b` for answer generation
- **Query Classification**: Gemini 2.0 Flash via OpenRouter
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Auth**: GitHub OAuth with JWT + Fernet token encryption

## Key Implementation Details

- **In-database embeddings**: No separate embedding service — `SNOWFLAKE.CORTEX.EMBED_TEXT_768()` runs directly in Snowflake, eliminating network overhead and external dependencies
- **Dual summarization pipeline**: Commit messages are enriched via Gemini before embedding, improving semantic search quality over raw messages
- **Query-time embedding**: User questions are embedded at query time (not pre-computed), routed through the same Cortex function for dimensional consistency
- **Fallback chain**: Redis → in-memory for rate limiting and OAuth state; Snowflake reconnection with automatic retry on token expiry

## Project Structure

```
backend/
├── main.py
├── app/
│   ├── core/               # Settings, GitHub OAuth config
│   ├── routers/
│   │   ├── auth.py         # OAuth flow, JWT issuance
│   │   ├── repositories.py # GitHub API integration, commit fetching
│   │   └── cortex_rag.py   # Embedding generation, vector search, RAG queries
│   ├── services/
│   │   ├── gemini_service.py      # Commit summarization
│   │   ├── snowflake_service.py   # Connection management, query execution
│   │   ├── query_parser.py        # Intent classification for retrieval routing
│   │   ├── github_service.py      # GitHub API client
│   │   └── redis_service.py       # Rate limiting state
│   ├── security/           # JWT, Fernet encryption, rate limiter
│   └── database/
│       └── snowflake_crud.py  # Parameterized CRUD with vector search support
frontend/
└── src/
    ├── pages/              # Landing, analysis, OAuth callback
    ├── components/         # Commit graph, code viewer, file tree
    └── lib/api.ts          # Typed fetch client
```

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env    # configure Snowflake + API keys
python main.py          # localhost:8000

# Frontend
cd frontend
npm install
npm run dev             # localhost:8080
```

## API Endpoints

| Method | Path | Function |
|---|---|---|
| GET | `/auth/github` | Initiate OAuth flow |
| GET | `/auth/github/callback` | Token exchange |
| GET | `/api/repositories` | List GitHub repos |
| POST | `/api/repositories/analyze` | Start analysis job |
| POST | `/api/repositories/{id}/fetch-commits` | Paginated commit ingest |
| POST | `/api/repositories/{id}/cortex-embed` | Generate vector embeddings for commits |
| POST | `/api/repositories/{id}/cortex-query` | Hybrid vector + temporal search |
| GET | `/api/repositories/{id}/embedding-status` | Embedding coverage metrics |
| GET | `/api/repositories/{id}/commits` | Paginated commit history |
| POST | `/api/repositories/{id}/commits/{sha}/enhance` | AI-enhanced commit message |

## Environment Variables

| Variable | Purpose |
|---|---|
| `SNOWFLAKE_ACCOUNT` | Snowflake account for vector DB |
| `SNOWFLAKE_USER` | Snowflake credentials |
| `SNOWFLAKE_PASSWORD` | Snowflake credentials |
| `OPENROUTER_API_KEY` | Gemini access via OpenRouter |
| `GITHUB_CLIENT_ID` | GitHub OAuth |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth |
| `JWT_SECRET_KEY` | Token signing |

## License

MIT
