# CodeAncestry - AI-Powered Git Repository Analysis

Analyze GitHub repositories using AI to understand code evolution, find relevant commits, and ask semantic questions about your codebase history.

## What It Does

- 🔍 **Semantic Search**: Ask questions about your repository in natural language
- 📊 **Commit Analysis**: Automatically analyzes all commits with AI summaries
- 🔗 **Hybrid Queries**: Search by temporal filters, semantic relevance, or both
- 📈 **Vector Embeddings**: Uses Snowflake Cortex for fast, accurate similarity matching
- 🎯 **GitHub Integration**: Connect directly to your GitHub repositories via OAuth

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: Python FastAPI
- **Database**: Snowflake (Vector Search + Analytics)
- **AI**: Snowflake Cortex (Embeddings & LLM) + OpenRouter (Query Classification)
- **Auth**: GitHub OAuth
- **Secrets**: Encrypted environment variables

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend/story-code-ai-main
npm install
npm run dev
```

Visit `http://localhost:8080` to get started.

## Features

✅ GitHub OAuth login  
✅ Repository selection & commit analysis  
✅ AI-powered commit summaries (Cortex)  
✅ Vector embeddings for semantic search  
✅ Temporal, semantic, and hybrid query types  
✅ Interactive commit graph visualization  
✅ Source citation with similarity scores  

## How It Works

1. **Connect GitHub** → OAuth login and select a repository
2. **Analyze Commits** → Fetch all commits and generate embeddings
3. **Ask Questions** → Query your repository with natural language
4. **Get Answers** → AI finds relevant commits and explains the context

## Architecture

- **Cortex RAG**: Retrieval-Augmented Generation using Snowflake Cortex
  - Temporal search: Date/author filtering
  - Semantic search: Vector similarity matching
  - Hybrid search: Combined filtering + semantic relevance
- **Query Parser**: Uses Gemini to classify user questions
- **Commit Summarization**: Cortex-powered summaries for code context

---

