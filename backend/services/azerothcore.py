"""
AzerothCore server interaction service
"""
import os
import subprocess
import asyncio
from pathlib import Path
from typing import Optional
import httpx

# Server paths from environment
SERVER_BIN = Path(os.getenv("AC_BIN_PATH", "/mnt/nextorage/appdata/wotlk/server/bin"))
SERVER_ETC = Path(os.getenv("AC_ETC_PATH", "/mnt/nextorage/appdata/wotlk/server/etc"))

# SOAP connection for remote commands
SOAP_HOST = os.getenv("AC_SOAP_HOST", "192.168.1.8")
SOAP_PORT = int(os.getenv("AC_SOAP_PORT", "7878"))
SOAP_USER = os.getenv("AC_SOAP_USER", "scaldor")
SOAP_PASS = os.getenv("AC_SOAP_PASS", "321$")


async def get_server_status() -> dict:
    """Check if WorldServer and AuthServer are running"""
    try:
        # Check worldserver port
        world_up = await _check_port("192.168.1.8", 8085)
        auth_up = await _check_port("192.168.1.8", 3724)

        return {
            "worldserver": "running" if world_up else "stopped",
            "authserver": "running" if auth_up else "stopped"
        }
    except Exception as e:
        return {"error": str(e)}


async def _check_port(host: str, port: int) -> bool:
    """Check if a port is open"""
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=2.0
        )
        writer.close()
        await writer.wait_closed()
        return True
    except (asyncio.TimeoutError, ConnectionRefusedError, OSError):
        return False


def get_config_files() -> list[dict]:
    """List available config files"""
    configs = []
    if SERVER_ETC.exists():
        for f in SERVER_ETC.glob("*.conf"):
            configs.append({
                "name": f.name,
                "path": str(f),
                "size": f.stat().st_size
            })
    return configs


def read_config(filename: str) -> Optional[str]:
    """Read a config file"""
    config_path = SERVER_ETC / filename
    if config_path.exists() and config_path.suffix == ".conf":
        return config_path.read_text()
    return None


def write_config(filename: str, content: str) -> bool:
    """Write a config file (with backup)"""
    config_path = SERVER_ETC / filename
    if not config_path.suffix == ".conf":
        return False

    # Backup existing
    if config_path.exists():
        backup_path = config_path.with_suffix(".conf.bak")
        backup_path.write_text(config_path.read_text())

    config_path.write_text(content)
    return True


async def send_command(command: str) -> dict:
    """Send GM command via SOAP (if enabled) or return instruction"""
    # For now, return the command to execute manually
    # Full SOAP implementation would require zeep or similar
    return {
        "command": command,
        "note": "Execute in-game or via SOAP client",
        "soap_endpoint": f"http://{SOAP_HOST}:{SOAP_PORT}/"
    }
