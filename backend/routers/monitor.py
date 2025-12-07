"""
Real-time monitoring endpoints
"""
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.redis_client import get_redis
from services.postgres_client import get_pool
from services import vllm_client, azerothcore

router = APIRouter()


@router.get("/health")
async def get_health():
    """Get health status of all services"""
    results = {}

    # Check AzerothCore
    results["azerothcore"] = await azerothcore.get_server_status()

    # Check vLLM
    results["vllm"] = await vllm_client.health_check()

    # Check Redis
    try:
        r = await get_redis()
        await r.ping()
        results["redis"] = {"status": "healthy"}
    except Exception as e:
        results["redis"] = {"status": "unhealthy", "error": str(e)}

    # Check PostgreSQL
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        results["postgresql"] = {"status": "healthy"}
    except Exception as e:
        results["postgresql"] = {"status": "unhealthy", "error": str(e)}

    # Overall status
    all_healthy = all(
        s.get("status") in ("healthy", "running")
        for s in results.values()
        if isinstance(s, dict) and "status" in s
    )
    results["overall"] = "healthy" if all_healthy else "degraded"

    return results


@router.get("/stats")
async def get_stats():
    """Get current stats from Redis"""
    try:
        r = await get_redis()

        # Get bot count
        bot_keys = await r.keys("bot:*")

        # Get any cached stats
        stats = await r.hgetall("cerebro:stats")

        return {
            "active_bots": len(bot_keys),
            "stats": stats
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/vllm")
async def get_vllm_status():
    """Get vLLM server status and models"""
    health = await vllm_client.health_check()
    models = await vllm_client.get_models()
    return {
        "health": health,
        "models": models
    }


@router.websocket("/ws")
async def websocket_monitor(websocket: WebSocket):
    """WebSocket for real-time updates via Redis pub/sub"""
    await websocket.accept()

    try:
        r = await get_redis()
        pubsub = r.pubsub()
        await pubsub.subscribe("cerebro:events")

        # Send initial health status
        health = await get_health()
        await websocket.send_json({"type": "health", "data": health})

        # Listen for events
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    await websocket.send_json(data)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "raw",
                        "data": message["data"]
                    })

    except WebSocketDisconnect:
        pass
    finally:
        if 'pubsub' in locals():
            await pubsub.unsubscribe("cerebro:events")
