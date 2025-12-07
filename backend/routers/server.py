"""
Server management endpoints
"""
from fastapi import APIRouter
from services import azerothcore

router = APIRouter()


@router.get("/status")
async def get_status():
    """Get WorldServer and AuthServer status"""
    return await azerothcore.get_server_status()


@router.get("/configs")
async def list_configs():
    """List available config files"""
    return {"configs": azerothcore.get_config_files()}


@router.get("/configs/{filename}")
async def get_config(filename: str):
    """Read a config file"""
    content = azerothcore.read_config(filename)
    if content is None:
        return {"error": "Config not found"}
    return {"filename": filename, "content": content}


@router.put("/configs/{filename}")
async def save_config(filename: str, content: str):
    """Save a config file"""
    success = azerothcore.write_config(filename, content)
    if not success:
        return {"error": "Failed to save config"}
    return {"success": True, "filename": filename}
