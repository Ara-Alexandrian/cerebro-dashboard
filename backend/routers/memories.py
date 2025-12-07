"""
Memory browser endpoints (pgvector)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from services.postgres_client import get_pool

router = APIRouter()


class MemoryCreate(BaseModel):
    bot_id: int
    session_id: UUID
    content: str
    memory_type: str  # 'combat', 'social', 'exploration'
    importance: float = 0.5


@router.get("/")
async def list_memories(
    bot_id: Optional[int] = None,
    memory_type: Optional[str] = None,
    limit: int = 50
):
    """List memories with optional filters"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        query = """
            SELECT m.id, m.bot_id, p.name as bot_name, m.session_id,
                   m.content, m.memory_type, m.importance, m.created_at
            FROM memories m
            LEFT JOIN personalities p ON m.bot_id = p.id
            WHERE 1=1
        """
        params = []
        idx = 1

        if bot_id is not None:
            query += f" AND m.bot_id = ${idx}"
            params.append(bot_id)
            idx += 1

        if memory_type is not None:
            query += f" AND m.memory_type = ${idx}"
            params.append(memory_type)
            idx += 1

        query += f" ORDER BY m.created_at DESC LIMIT ${idx}"
        params.append(limit)

        rows = await conn.fetch(query, *params)
        return {"memories": [dict(row) for row in rows]}


@router.get("/search")
async def search_memories(
    query: str,
    bot_id: Optional[int] = None,
    limit: int = 10
):
    """
    Search memories by content (text search).
    Vector search would require embeddings from vLLM.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        sql = """
            SELECT m.id, m.bot_id, p.name as bot_name, m.session_id,
                   m.content, m.memory_type, m.importance, m.created_at
            FROM memories m
            LEFT JOIN personalities p ON m.bot_id = p.id
            WHERE m.content ILIKE $1
        """
        params = [f"%{query}%"]
        idx = 2

        if bot_id is not None:
            sql += f" AND m.bot_id = ${idx}"
            params.append(bot_id)
            idx += 1

        sql += f" ORDER BY m.importance DESC, m.created_at DESC LIMIT ${idx}"
        params.append(limit)

        rows = await conn.fetch(sql, *params)
        return {"memories": [dict(row) for row in rows], "query": query}


@router.post("/")
async def create_memory(memory: MemoryCreate):
    """Create a new memory"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO memories (bot_id, session_id, content, memory_type, importance)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, bot_id, session_id, content, memory_type, importance, created_at
        """, memory.bot_id, memory.session_id, memory.content,
            memory.memory_type, memory.importance)
        return dict(row)


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a memory"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM memories WHERE id = $1",
            memory_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Memory not found")
        return {"deleted": True, "id": memory_id}


@router.get("/sessions")
async def list_sessions(limit: int = 20):
    """List play sessions"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT * FROM sessions
            ORDER BY started_at DESC
            LIMIT $1
        """, limit)
        return {"sessions": [dict(row) for row in rows]}
