"""
main.py
===========
FastAPI application factory and entrypoint — `uvicorn app.main:app`.

This module is intentionally thin: it wires together configuration,
logging, middleware, exception handlers, rate limiting, and every feature
router, but contains no business logic itself. Each feature's actual
behavior lives in its own router (app/api/routes/*.py) backed by its own
LangGraph agent team (app/agents/<feature>/graph.py).
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.routes import auth, chatbot, cv_builder, health, job_search, profile, roadmap
from app.api.routes import apply as apply_router
from app.api.routes import badges as badges_router
from app.api.routes import queue as queue_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestContextMiddleware

configure_logging()
logger = get_logger(__name__)

# Shared rate limiter instance (per-IP by default; per-user tiers are applied
# via decorator overrides on individual routes — see core/config.py for the
# three configured tiers: unauthenticated / authenticated / LLM-heavy).
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager: handles startup and shutdown events.
    This replaces the old @app.on_event("startup") decorator.
    Everything before the `yield` runs when the server starts.
    Everything after the `yield` runs when the server stops.
    """
    logger.info("starting_careerkundi_backend")

    # We import these here (inside the function) rather than at the top of the file
    # to avoid "circular imports" where two files try to import each other at the same time.
    from app.tools.rag import get_vector_store
    from app.tools.graph_rag import get_knowledge_graph

    # Pre-load the vector store (FAISS) and knowledge graph into memory.
    # If they don't exist yet, these functions will build them.
    # Doing this on startup ensures the first search request doesn't stall.
    get_vector_store()
    get_knowledge_graph()

    # Seed static badge definitions into the database.
    # Badges are achievements users can earn. We ensure they exist in the DB on boot.
    from app.db.session import AsyncSessionLocal
    from app.services.badges import seed_badge_definitions
    async with AsyncSessionLocal() as db:
        await seed_badge_definitions(db)

    logger.info("startup_complete")
    yield  # The server is now running and accepting requests!

    # Server is shutting down (e.g. you pressed Ctrl+C)
    from app.db.session import engine

    # Close all database connections cleanly so we don't leave zombie connections.
    await engine.dispose()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Construct and fully configure the FastAPI application instance."""
    app = FastAPI(
        title="Careerkundi API",
        description="Agentic AI Career Platform — multi-agent backend powering job search, "
        "CV building, career roadmaps, and the AI career assistant.",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # --- Security headers + CORS -------------------------------------------------
    # CORS (Cross-Origin Resource Sharing) prevents random websites from making API
    # requests to our backend. We only allow the frontend URL (e.g. localhost:5173).
    # allow_origins: comes from settings.cors_origins_list (set in .env)
    # allow_methods: only the HTTP verbs our API actually uses (not wildcard)
    # allow_headers: only Authorization (JWT) and Content-Type (JSON bodies)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    # Injects a unique ID into every request for tracing logs
    app.add_middleware(RequestContextMiddleware)

    # --- Rate limiting ------------------------------------------------------------
    # Attach the slowapi limiter to the app state so it can block spam requests
    app.state.limiter = limiter

    # --- Error handling -------------------------------------------------------------
    # Register custom error handlers (e.g. turning AuthenticationError into HTTP 401)
    register_exception_handlers(app)

    # --- Prometheus metrics endpoint (§6.1 "Monitoring Ready") ------------------------
    app.mount("/metrics", make_asgi_app())

    # --- Feature routers, all under /api/v1 -------------------------------------------
    app.include_router(health.router)  # /health (unversioned, for container healthchecks)
    api_v1_prefix = "/api/v1"
    app.include_router(auth.router, prefix=api_v1_prefix)
    app.include_router(profile.router, prefix=api_v1_prefix)
    app.include_router(job_search.router, prefix=api_v1_prefix)
    app.include_router(cv_builder.router, prefix=api_v1_prefix)
    app.include_router(roadmap.router, prefix=api_v1_prefix)
    app.include_router(chatbot.router, prefix=api_v1_prefix)
    app.include_router(apply_router.router, prefix=api_v1_prefix)
    app.include_router(badges_router.router, prefix=api_v1_prefix)
    app.include_router(queue_router.router, prefix=api_v1_prefix)

    return app


app = create_app()
