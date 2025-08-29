"""
CodeAncestry API - Main application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.routers import auth, repositories, cortex_rag
from app.services.snowflake_service import snowflake_service, init_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 CodeAncestry API starting...")
    
    logger.info("📁 Loading configuration from environment variables")
    
    # Initialize Snowflake database
    try:
        logger.info("📊 Initializing Snowflake database...")
        await init_database()
        logger.info("✅ Snowflake database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Snowflake database: {e}")
        logger.warning("⚠️ Application will continue without Snowflake (check credentials)")

    # Initialize Redis
    from app.services.redis_service import init_redis, close_redis
    try:
        redis_client = init_redis()
        if redis_client:
            from app.security.rate_limiter import init_rate_limiter
            init_rate_limiter(redis_client)
            logger.info("✅ Redis initialized for rate limiting and OAuth state")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Redis: {e}")
        if settings.ENVIRONMENT == "production":
            raise
        logger.warning("⚠️ Continuing without Redis (development mode)")

    yield

    logger.info("👋 Shutting down...")
    try:
        close_redis()
    except Exception:
        pass
    snowflake_service.close()


app = FastAPI(
    title="CodeAncestry API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(repositories.router, prefix="/api", tags=["Repositories"])
app.include_router(cortex_rag.router, prefix="/api", tags=["Snowflake Cortex RAG"])


@app.get("/")
async def root():
    return {"message": "CodeAncestry API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)
