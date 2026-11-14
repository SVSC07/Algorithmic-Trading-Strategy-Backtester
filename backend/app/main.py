# STUB, owned by Molik, replaced on merge
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models.base import Base
from app.core.errors import register_error_handlers
from app.api.auth import router as auth_router
from app.api.strategies import router as strategies_router
from app.api.instruments import router as instruments_router
from app.api.backtests import router as backtests_router

# Ensure tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Algorithmic Trading Strategy Backtester API",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom error mapping
register_error_handlers(app)

# Health endpoint
@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}

# Mount API routers under /api
app.include_router(auth_router, prefix="/api")
app.include_router(strategies_router, prefix="/api")
app.include_router(instruments_router, prefix="/api")
app.include_router(backtests_router, prefix="/api")
