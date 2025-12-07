"""
Bot personality management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.postgres_client import get_pool

router = APIRouter()


class PersonalityCreate(BaseModel):
    name: str
    class_: str  # 'class' is reserved
    archetype: str  # tank, healer, dps
    traits: dict = {}
    system_prompt: str = ""

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "name": "Thorgrim",
                "class_": "warrior",
                "archetype": "tank",
                "traits": {"personality": "stoic", "humor": 0.2, "aggression": 0.7},
                "system_prompt": "You are a gruff dwarven warrior..."
            }
        }


class PersonalityUpdate(BaseModel):
    name: Optional[str] = None
    class_: Optional[str] = None
    archetype: Optional[str] = None
    traits: Optional[dict] = None
    system_prompt: Optional[str] = None


@router.get("/")
async def list_personalities():
    """List all bot personalities"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT id, name, class, archetype, traits,
                   created_at, updated_at
            FROM personalities
            ORDER BY name
        """)
        return {
            "personalities": [dict(row) for row in rows]
        }


@router.get("/{bot_id}")
async def get_personality(bot_id: int):
    """Get a specific personality"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM personalities WHERE id = $1",
            bot_id
        )
        if not row:
            raise HTTPException(status_code=404, detail="Personality not found")
        return dict(row)


@router.post("/")
async def create_personality(personality: PersonalityCreate):
    """Create a new bot personality"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow("""
                INSERT INTO personalities (name, class, archetype, traits, system_prompt)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id, name, class, archetype, traits, system_prompt, created_at
            """, personality.name, personality.class_, personality.archetype,
                personality.traits, personality.system_prompt)
            return dict(row)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.put("/{bot_id}")
async def update_personality(bot_id: int, update: PersonalityUpdate):
    """Update a bot personality"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        # Build dynamic update
        updates = []
        values = []
        idx = 1

        if update.name is not None:
            updates.append(f"name = ${idx}")
            values.append(update.name)
            idx += 1
        if update.class_ is not None:
            updates.append(f"class = ${idx}")
            values.append(update.class_)
            idx += 1
        if update.archetype is not None:
            updates.append(f"archetype = ${idx}")
            values.append(update.archetype)
            idx += 1
        if update.traits is not None:
            updates.append(f"traits = ${idx}")
            values.append(update.traits)
            idx += 1
        if update.system_prompt is not None:
            updates.append(f"system_prompt = ${idx}")
            values.append(update.system_prompt)
            idx += 1

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = NOW()")
        values.append(bot_id)

        query = f"""
            UPDATE personalities
            SET {', '.join(updates)}
            WHERE id = ${idx}
            RETURNING *
        """
        row = await conn.fetchrow(query, *values)
        if not row:
            raise HTTPException(status_code=404, detail="Personality not found")
        return dict(row)


@router.delete("/{bot_id}")
async def delete_personality(bot_id: int):
    """Delete a bot personality"""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM personalities WHERE id = $1",
            bot_id
        )
        if result == "DELETE 0":
            raise HTTPException(status_code=404, detail="Personality not found")
        return {"deleted": True, "id": bot_id}
