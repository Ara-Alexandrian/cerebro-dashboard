"""
Server management endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services import azerothcore

router = APIRouter()


class CommandRequest(BaseModel):
    command: str


class BotCountRequest(BaseModel):
    count: int


class ConfigSaveRequest(BaseModel):
    content: str


# Server Status & Control
@router.get("/status")
async def get_status():
    """Get WorldServer, AuthServer, and SOAP status"""
    return await azerothcore.get_server_status()


@router.post("/restart")
async def restart_server():
    """Restart the AzerothCore server container"""
    result = await azerothcore.restart_server()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/stop")
async def stop_server():
    """Stop the AzerothCore server container"""
    result = await azerothcore.stop_server()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/start")
async def start_server():
    """Start the AzerothCore server container"""
    result = await azerothcore.start_server()
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.get("/logs")
async def get_logs(lines: int = 100):
    """Get recent server logs"""
    return await azerothcore.get_server_logs(lines)


# GM Commands via SOAP
@router.post("/command")
async def send_command(request: CommandRequest):
    """Execute a GM command via SOAP"""
    result = await azerothcore.send_soap_command(request.command)
    return result


# PlayerBots Control
@router.get("/bots/status")
async def get_bots_status():
    """Get PlayerBots status"""
    return await azerothcore.get_playerbots_status()


@router.post("/bots/add")
async def add_bot(name: Optional[str] = None):
    """Add a bot (random or by name)"""
    return await azerothcore.add_bot(name)


@router.post("/bots/remove-all")
async def remove_all_bots():
    """Remove all active bots"""
    return await azerothcore.remove_all_bots()


@router.post("/bots/count")
async def set_bot_count(request: BotCountRequest):
    """Set the target random bot count"""
    return await azerothcore.set_bot_count(request.count)


@router.post("/bots/reload-config")
async def reload_bots_config():
    """Reload PlayerBots configuration"""
    return await azerothcore.reload_playerbots_config()


# Config Files
@router.get("/configs")
async def list_configs():
    """List available config files"""
    return {"configs": azerothcore.get_config_files()}


@router.get("/configs/{filename:path}")
async def get_config(filename: str):
    """Read a config file"""
    content = azerothcore.read_config(filename)
    if content is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return {"filename": filename, "content": content}


@router.put("/configs/{filename:path}")
async def save_config(filename: str, request: ConfigSaveRequest):
    """Save a config file"""
    success = azerothcore.write_config(filename, request.content)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to save config")
    return {"success": True, "filename": filename}
