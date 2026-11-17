"""FastAPI application factory for ResearchPilot."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from researchpilot.api.routes_auth import router as auth_router
from researchpilot.api.routes_documents import router as documents_router
from researchpilot.api.routes_projects import router as projects_router
from researchpilot.api.routes_retrieval import router as retrieval_router
from researchpilot.api.routes_runs import router as runs_router
from researchpilot.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("researchpilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context."""
    settings = get_settings()
    settings.local_storage_path.mkdir(parents=True, exist_ok=True)
    logger.info("ResearchPilot API initialized. App Env: %s", settings.app_env)
    yield
    logger.info("ResearchPilot API shutting down.")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="ResearchPilot API",
        description="Agentic AI Research and Literature Review Assistant",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers with versioned prefix
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(projects_router, prefix="/api/v1")
    app.include_router(documents_router, prefix="/api/v1")
    app.include_router(retrieval_router, prefix="/api/v1")
    app.include_router(runs_router, prefix="/api/v1")

    @app.get("/health/live", tags=["Health"], status_code=status.HTTP_200_OK)
    async def health_live():
        """Liveness probe: verifies service process is running."""
        return {"status": "ok", "service": "researchpilot-api"}

    @app.get("/health/ready", tags=["Health"], status_code=status.HTTP_200_OK)
    async def health_ready():
        """Readiness probe: verifies dependencies and configurations."""
        return {
            "status": "ready",
            "storage": settings.local_storage_path.exists(),
            "env": settings.app_env,
        }

    @app.get("/system/capabilities", tags=["System"], status_code=status.HTTP_200_OK)
    async def system_capabilities():
        """Report available capabilities and active AI provider mode without leaking secrets."""
        has_ai = bool(settings.openai_api_key and settings.openai_api_key.strip())
        provider_mode = "live_openai" if has_ai else "offline_mock"
        return {
            "ai_configured": has_ai,
            "provider_mode": provider_mode,
            "chat_model": settings.openai_chat_model,
            "embedding_model": settings.openai_embedding_model,
            "embedding_dimensions": settings.embedding_dimensions,
            "max_upload_mb": settings.max_upload_mb,
            "max_pdf_pages": settings.max_pdf_pages,
            "citation_styles": ["numbered", "apa-like"],
        }

    return app


app = create_app()
