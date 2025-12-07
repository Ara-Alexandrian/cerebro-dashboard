"""
PostgreSQL + pgvector client for Cerebro persistent storage
"""
import os
from typing import Optional
import asyncpg

# Connection pool
_pool: Optional[asyncpg.Pool] = None

# Config from environment
PG_HOST = os.getenv("POSTGRES_HOST", "172.21.0.12")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
PG_USER = os.getenv("POSTGRES_USER", "azeroth")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "azeroth")
PG_DB = os.getenv("POSTGRES_DB", "azeroth_vectors")


async def init_db():
    """Initialize connection pool and ensure schema exists"""
    global _pool
    _pool = await asyncpg.create_pool(
        host=PG_HOST,
        port=PG_PORT,
        user=PG_USER,
        password=PG_PASS,
        database=PG_DB,
        min_size=2,
        max_size=10
    )
    await _ensure_schema()


async def close_db():
    """Close connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """Get the connection pool"""
    if not _pool:
        raise RuntimeError("Database not initialized")
    return _pool


async def _ensure_schema():
    """Create tables if they don't exist"""
    async with _pool.acquire() as conn:
        # Enable pgvector extension
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Bot personalities
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS personalities (
                id SERIAL PRIMARY KEY,
                name VARCHAR(64) UNIQUE NOT NULL,
                class VARCHAR(32) NOT NULL,
                archetype VARCHAR(32) NOT NULL,
                traits JSONB NOT NULL DEFAULT '{}',
                system_prompt TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Episodic memories with vector embeddings
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id SERIAL PRIMARY KEY,
                bot_id INTEGER REFERENCES personalities(id) ON DELETE CASCADE,
                session_id UUID NOT NULL,
                content TEXT NOT NULL,
                memory_type VARCHAR(32) NOT NULL,
                embedding vector(1536),
                importance FLOAT DEFAULT 0.5,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Create HNSW index if not exists
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS memories_embedding_idx
            ON memories USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
        """)

        # Play sessions
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                started_at TIMESTAMPTZ DEFAULT NOW(),
                ended_at TIMESTAMPTZ,
                player_name VARCHAR(64),
                zone VARCHAR(128),
                summary TEXT
            );
        """)

        # System prompts and templates
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(64) UNIQUE NOT NULL,
                category VARCHAR(32) NOT NULL,
                content TEXT NOT NULL,
                variables JSONB DEFAULT '{}',
                version INTEGER DEFAULT 1
            );
        """)

        # Account metadata (tags, notes, categories)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS account_meta (
                account_id INTEGER PRIMARY KEY,
                username VARCHAR(64) NOT NULL,
                category VARCHAR(32) NOT NULL DEFAULT 'unknown',
                tags TEXT[] DEFAULT '{}',
                notes TEXT DEFAULT '',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)
