from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.core.middleware import RequestIDMiddleware
from backend.app.core.exceptions import register_exception_handlers
from backend.app.core.dependencies import get_knowledge_loader, get_policy_loader
from backend.app.api import health, compliance, knowledge


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup phase
    logger.info("Starting up Civora AI API Backend Platform...")
    
    # Pre-warm loader singletons to test directories
    try:
        get_knowledge_loader()
        get_policy_loader()
        logger.info("Knowledge and Policy loader interfaces pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"Failed to pre-warm loader singletons: {str(e)}")

    yield

    # Shutdown phase
    logger.info("Shutting down Civora AI API Backend Platform...")
    # Clear loader caches to free memory
    get_knowledge_loader().clear_cache()
    get_policy_loader().clear_cache()
    logger.info("Cleanup completed successfully.")


def create_app() -> FastAPI:
    """Application Factory creating the FastAPI app instance."""
    # Setup structured logging configuration
    setup_logging()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # Register Middlewares
    app.add_middleware(RequestIDMiddleware)
    
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Register Exceptions Handler Routing
    register_exception_handlers(app)

    # Register Routers
    app.include_router(health.router)
    app.include_router(compliance.router)
    app.include_router(knowledge.router)

    return app
