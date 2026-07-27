# CodeAncestry

AI-powered semantic search and analysis tool for Git repository history. Built with FastAPI, Snowflake Cortex, and React.

## Overview

CodeAncestry connects to GitHub repositories, analyzes commit history using AI, and enables natural language querying across your codebase evolution. Uses Snowflake Cortex for vector embeddings and LLM-powered retrieval-augmented generation (RAG).

## Tech Stack

- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui
- **Backend**: Python FastAPI, Uvicorn
- **Database**: Snowflake (vector search + relational)
- **AI**: Snowflake Cortex (embeddings + LLM), OpenRouter/Gemini (query classification)
- **Auth**: GitHub OAuth with JWT tokens
- **Infrastructure**: Docker, Railway, Redis (rate limiting + state)

## Key Features

- **Semantic Commit Search** — Ask questions about your repository in natural language
- **Commit Analysis** — Automatically analyzes all commits with AI-powered summaries
- **Hybrid Queries** — Search by temporal filters, semantic relevance, or both
- **Vector Embeddings** — Snowflake Cortex for fast, accurate similarity matching
- **GitHub Integration** — Connect directly to GitHub repositories via OAuth
- **Source Citation** — Every answer references specific commits with similarity scores
- **Interactive Visualization** — Commit graph with relevance scoring, code diff viewer, and file tree

## How It Works

1. **Connect GitHub** — OAuth login and select a repository
2. **Analyze Commits** — Fetch all commits and generate AI summaries and embeddings
3. **Ask Questions** — Query your repository with natural language
4. **Get Answers** — AI finds relevant commits and explains the context with citations

## Architecture

```
Frontend (React) → FastAPI → GitHub API
                   ↓              ↓
              Snowflake Cortex  Gemini/OpenRouter
                   ↓
              Vector DB + Relational Tables
```

### RAG Pipeline

Question is converted to an embedding via Snowflake Cortex, matched against commit embeddings using cosine similarity, and the top results are fed to an LLM for answer generation.

- **Semantic search**: Vector similarity matching against commit embeddings
- **Temporal search**: Date and author filtering with SQL constraints
- **Hybrid search**: Combined temporal filtering plus semantic relevance scoring

### Query Parser

Uses Gemini to classify user questions into three categories: temporal (time-based), semantic (meaning-based), or hybrid (both). Extracts filters like author, file paths, and date ranges from natural language.

### Data Flow

```
GitHub commits → Gemini summarization → Snowflake embeddings → Cortex-powered Q&A
```

## Project Structure

```
backend/
├── main.py                 # FastAPI entry point with lifespan management
├── app/
│   ├── core/               # Settings, GitHub OAuth config
│   ├── routers/            # Auth, repositories, Cortex RAG endpoints
│   ├── services/           # Gemini, GitHub, Snowflake, Redis, query parser
│   ├── security/           # JWT auth, Fernet encryption, rate limiting
│   ├── database/           # Snowflake CRUD operations
│   └── models/             # Pydantic schemas
frontend/
├── src/
│   ├── pages/              # Landing, analysis, auth callback
│   ├── components/         # Code viewer, file tree, explanation panel, commit graph
│   ├── hooks/              # Mobile detection, toast notifications
│   └── lib/                # API client, utility functions
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Snowflake account with Cortex access
- OpenRouter API key
- GitHub OAuth app credentials

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configure your .env with API keys and credentials
python main.py
```

Server starts at `http://localhost:8000` with Swagger docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:8080`.

## Environment Variables

| Variable | Description |
|---|---|
| `GITHUB_CLIENT_ID` | GitHub OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth app client secret |
| `SNOWFLAKE_ACCOUNT` | Snowflake account identifier |
| `SNOWFLAKE_USER` | Snowflake username |
| `SNOWFLAKE_PASSWORD` | Snowflake password |
| `OPENROUTER_API_KEY` | OpenRouter API key for Gemini access |
| `JWT_SECRET_KEY` | Secret for JWT token signing |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/auth/github` | Initiate GitHub OAuth flow |
| GET | `/auth/github/callback` | OAuth callback handler |
| GET | `/auth/me` | Current user info |
| GET | `/api/repositories` | List user's GitHub repos |
| POST | `/api/repositories/analyze` | Start repository analysis |
| GET | `/api/repositories/{id}/status` | Analysis progress |
| POST | `/api/repositories/{id}/cortex-query` | RAG query against commit history |
| POST | `/api/repositories/{id}/cortex-embed` | Generate vector embeddings |

## License

MIT
