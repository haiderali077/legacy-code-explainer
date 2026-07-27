# Legacy Code Explained

AI-powered Git repository analysis that helps developers understand how a codebase has evolved over time. Analyze commit history, search repositories using natural language, and quickly discover when, why, and how code changed.

## What It Does

- Analyze GitHub repositories using AI-generated commit summaries
- Search commit history using natural language instead of keywords
- Combine semantic search with date and author filtering
- Generate vector embeddings using Snowflake Cortex for fast similarity search
- Visualize repository history with an interactive commit graph
- Connect securely to GitHub using OAuth
- View AI responses with relevant commit references

---

## Tech Stack

| Category | Technologies |
|----------|--------------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Backend | Python, FastAPI |
| Database | Snowflake |
| AI | Snowflake Cortex, OpenRouter |
| Authentication | GitHub OAuth |
| Secrets | 1Password Service Accounts |

---

## Quick Start

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

---

## Features

- GitHub OAuth authentication
- Repository selection and commit analysis
- AI-generated commit summaries
- Vector embeddings for semantic search
- Semantic, temporal, and hybrid search
- Interactive commit history visualization
- AI responses with supporting commit references

---

## How It Works

1. **Connect Repository**  
   Sign in with GitHub and select a repository.

2. **Analyze Commits**  
   Fetch the repository's commit history and generate AI summaries.

3. **Generate Embeddings**  
   Convert commit summaries into vector embeddings using Snowflake Cortex.

4. **Ask Questions**  
   Search your repository using natural language.

5. **Retrieve Relevant Commits**  
   The system performs semantic, temporal, or hybrid search to find the most relevant commits.

6. **Generate an Answer**  
   AI produces a contextual response with links to the supporting commits.

---

## Search Modes

| Mode | Example |
|------|---------|
| **Semantic** | "Why was the authentication system refactored?" |
| **Temporal** | "Show commits from last week." |
| **Hybrid** | "Authentication changes made during March." |

---

## Example Queries

- When was JWT authentication implemented?
- Why was the caching layer introduced?
- Show commits related to API performance.
- What database schema changes were made last month?
- Who implemented the notification system?

---

## Architecture

```text
                    GitHub Repository
                           │
                           ▼
                 Fetch Commit History
                           │
                           ▼
               AI Commit Summaries
                           │
                           ▼
      Snowflake Cortex Vector Embeddings
                           │
                           ▼
           Snowflake Vector Database
                           │
                           ▼
               Natural Language Query
                           │
                           ▼
     Semantic / Temporal / Hybrid Search
                           │
                           ▼
        AI Response + Relevant Commits
```

---

## Key Technologies

- **Snowflake Cortex** for AI-generated commit summaries and vector embeddings
- **Vector similarity search** using cosine similarity for semantic retrieval
- **Hybrid search** combining semantic similarity with metadata filters
- **FastAPI** backend for repository analysis and search APIs
- **React + TypeScript** frontend for an interactive user experience
- **GitHub OAuth** for secure repository authentication
- **OpenRouter** for natural language query classification

---

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── database/
│   │   ├── routers/
│   │   ├── security/
│   │   ├── services/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── assets/
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

---

## Future Improvements

- Support multiple branches and pull request analysis
- Repository-wide code search alongside commit history
- Team collaboration and shared workspaces
- Additional filtering by file path and contributor
- Export AI-generated reports and repository insights

---

## License

MIT
