"""
Config file management endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from services import azerothcore

router = APIRouter()


class ConfigUpdate(BaseModel):
    content: str


@router.get("/files")
async def list_config_files():
    """List all config files"""
    return {"files": azerothcore.get_config_files()}


@router.get("/files/{filename}")
async def read_config_file(filename: str):
    """Read a specific config file"""
    content = azerothcore.read_config(filename)
    if content is None:
        return {"error": f"Config file '{filename}' not found"}
    return {"filename": filename, "content": content}


@router.put("/files/{filename}")
async def update_config_file(filename: str, update: ConfigUpdate):
    """Update a config file"""
    success = azerothcore.write_config(filename, update.content)
    return {"success": success, "filename": filename}
