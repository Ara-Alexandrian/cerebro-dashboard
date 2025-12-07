"""
Cerebro Dashboard Backend
FastAPI server for managing AzerothCore + AI buddy system
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import server, config, bots, memories, monitor, console, accounts
from services.postgres_client import init_db, close_db
from services.redis_client import init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup database connections"""
    await init_db()
    await init_redis()
    yield
    await close_db()
    await close_redis()


app = FastAPI(
    title="Cerebro Dashboard",
    description="Management interface for AzerothCore AI Buddy System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for SvelteKit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(server.router, prefix="/api/server", tags=["Server"])
app.include_router(config.router, prefix="/api/config", tags=["Config"])
app.include_router(bots.router, prefix="/api/bots", tags=["Bots"])
app.include_router(memories.router, prefix="/api/memories", tags=["Memories"])
app.include_router(monitor.router, prefix="/api/monitor", tags=["Monitor"])
app.include_router(console.router, prefix="/api/console", tags=["Console"])
app.include_router(accounts.router, prefix="/api", tags=["Accounts"])


@app.get("/api/health")
async def health_check():
    """Quick health check endpoint"""
    return {"status": "ok", "service": "cerebro-dashboard"}
