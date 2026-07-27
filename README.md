# Legacy Code Explained

An AI-powered Git repository analysis tool that helps developers understand how a codebase has evolved. Analyze commit history, search repositories using natural language, and discover when and why changes were made.

## Features

- Analyze GitHub repositories using AI-generated commit summaries
- Search commit history using natural language
- Combine semantic search with date and author filters
- View interactive commit history
- Find the most relevant commits with vector similarity search
- Authenticate securely with GitHub OAuth

## How It Works

```
GitHub Repository
        │
        ▼
Fetch Commit History
        │
        ▼
Generate AI Summaries
        │
        ▼
Create Vector Embeddings
        │
        ▼
Store in Snowflake
        │
        ▼
User Question
        │
        ▼
Semantic / Temporal Search
        │
        ▼
AI Response with Relevant Commits
```

Each commit is summarized using AI and converted into vector embeddings with Snowflake Cortex. When a user asks a question, the system retrieves the most relevant commits using vector similarity search before generating a contextual response.

## Search Modes

| Mode | Description |
|------|-------------|
| Semantic | Search using natural language such as "When was authentication added?" |
| Temporal | Filter commits by date or author |
| Hybrid | Combine semantic search with metadata filters |

## Tech Stack

| Category | Technologies |
|----------|--------------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | Snowflake |
| AI | Snowflake Cortex, OpenRouter |
| Authentication | GitHub OAuth |

## Project Structure

```text
backend/
├── app/
│   ├── routers/
│   ├── services/
│   ├── database/
│   ├── security/
│   └── main.py

frontend/
└── src/
    ├── components/
    ├── pages/
    └── lib/
```

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the application at:

```
http://localhost:8080
```

## API Overview

| Endpoint | Description |
|----------|-------------|
| `/auth/github` | GitHub OAuth authentication |
| `/api/repositories` | List user repositories |
| `/api/repositories/analyze` | Analyze repository commits |
| `/api/repositories/{id}/cortex-query` | Ask questions about repository history |
| `/api/repositories/{id}/commits` | Retrieve commit history |

## Key Technologies

- Snowflake Cortex for AI summaries and vector embeddings
- Snowflake Vector Search for semantic retrieval
- FastAPI REST backend
- React + TypeScript frontend
- GitHub OAuth authentication
- OpenRouter for query classification

## License

MIT
