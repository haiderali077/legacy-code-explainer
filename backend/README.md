# CodeAncestry Backend

FastAPI backend for CodeAncestry - Legacy Code Explainer

## Setup

1. Create virtual environment:
```bash
python -m venv venv
```

2. Activate virtual environment:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and fill in API keys:
```bash
cp .env.example .env
```

5. Run the server:
```bash
python main.py
```

Or with uvicorn:
```bash
uvicorn main:app --reload
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── app/
│   ├── core/
│   │   └── config.py      # Settings management
│   ├── models/
│   │   └── schemas.py     # Pydantic models
│   ├── routers/
│   │   ├── analyze.py     # Code analysis endpoints
│   │   ├── voice.py       # Voice generation endpoints
│   │   └── history.py     # History endpoints
│   ├── services/
│   │   ├── gemini_service.py      # Gemini AI integration
│   │   ├── voice_service.py       # ElevenLabs integration
│   │   └── audio_cache.py         # Audio caching
│   ├── database/
│   │   ├── snowflake_client.py    # Snowflake connection
│   │   ├── schema.sql             # Database schema
│   │   └── crud.py                # CRUD operations
│   ├── security/
│   │   ├── auth.py               # JWT authentication
│   │   ├── encryption.py         # 1Password integration
│   │   └── rate_limiter.py       # Rate limiting
│   ├── prompts/
│   │   └── analysis_prompts.py   # Gemini prompts
│   └── utils/
│       ├── code_analyzer.py      # Code analysis utilities
│       └── diagram_generator.py  # Mermaid diagram generation
```

## Team Assignments

See README in root directory for task assignments.
