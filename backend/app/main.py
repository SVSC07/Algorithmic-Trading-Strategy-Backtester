"""
main.py
FastAPI application factory.

Assembles all routers under /api, adds /health, CORS for http://localhost:5173,
error handlers, and the get_session dependency.
Interactive docs are served at /docs.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, backtests, instruments, strategies
from app.core.errors import register_error_handlers

app = FastAPI(
    title="Algorithmic Trading Strategy Backtester",
    description="JSS University Noida — Software Engineering Mini Project",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Error handlers  (must be registered before routers)
# ---------------------------------------------------------------------------
register_error_handlers(app)

# ---------------------------------------------------------------------------
# Routers — all under /api
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api")
app.include_router(strategies.router, prefix="/api")
app.include_router(instruments.router, prefix="/api")
app.include_router(backtests.router, prefix="/api")


# ---------------------------------------------------------------------------
# Health check (public)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["health"])
def health():
    """Public health probe used by infra and the frontend."""
    return {"status": "ok"}
