"""
GM command console endpoints
"""
from fastapi import APIRouter
from pydantic import BaseModel
from services import azerothcore, vllm_client

router = APIRouter()


class CommandRequest(BaseModel):
    command: str


class ChatRequest(BaseModel):
    message: str
    personality_id: int | None = None
    context: list[dict] = []


@router.post("/gm")
async def execute_gm_command(request: CommandRequest):
    """Execute a GM command (via SOAP or instruction)"""
    return await azerothcore.send_command(request.command)


@router.post("/chat")
async def test_chat(request: ChatRequest):
    """Test chat with the LLM (for personality testing)"""
    messages = request.context.copy()
    messages.append({"role": "user", "content": request.message})

    response = await vllm_client.chat_completion(messages)

    if response is None:
        return {"error": "Failed to get response from LLM"}

    return {
        "response": response,
        "model": vllm_client.VLLM_MODEL
    }


@router.get("/commands")
async def list_common_commands():
    """List common GM commands for quick access"""
    return {
        "commands": [
            {"cmd": ".server info", "desc": "Show server info"},
            {"cmd": ".account onlinelist", "desc": "List online players"},
            {"cmd": ".lookup creature", "desc": "Search creatures"},
            {"cmd": ".npc add", "desc": "Spawn NPC"},
            {"cmd": ".bot add", "desc": "Add playerbot"},
            {"cmd": ".bot remove", "desc": "Remove playerbot"},
            {"cmd": ".gm on", "desc": "Enable GM mode"},
            {"cmd": ".tele", "desc": "Teleport"},
            {"cmd": ".additem", "desc": "Add item"},
            {"cmd": ".levelup", "desc": "Level up target"},
        ]
    }
