"""
AzerothCore server interaction service
"""
import os
import asyncio
import subprocess
from pathlib import Path
from typing import Optional
import httpx
from xml.etree import ElementTree as ET

# Server paths from environment
SERVER_BIN = Path(os.getenv("AC_BIN_PATH", "/mnt/nextorage/appdata/wotlk/server/bin"))
SERVER_ETC = Path(os.getenv("AC_ETC_PATH", "/mnt/nextorage/appdata/wotlk/server/etc"))

# Server host (Docker container or host machine)
SERVER_HOST = os.getenv("AC_SERVER_HOST", "172.21.0.4")
WORLD_PORT = int(os.getenv("AC_WORLD_PORT", "8085"))
AUTH_PORT = int(os.getenv("AC_AUTH_PORT", "3724"))

# SOAP connection for remote commands
SOAP_HOST = os.getenv("AC_SOAP_HOST", SERVER_HOST)
SOAP_PORT = int(os.getenv("AC_SOAP_PORT", "7878"))
SOAP_USER = os.getenv("AC_SOAP_USER", "scaldor")
SOAP_PASS = os.getenv("AC_SOAP_PASS", "321$")

# Docker container name
DOCKER_CONTAINER = os.getenv("AC_DOCKER_CONTAINER", "azerothcore-server")


async def get_server_status() -> dict:
    """Check if WorldServer and AuthServer are running"""
    try:
        world_up = await _check_port(SERVER_HOST, WORLD_PORT)
        auth_up = await _check_port(SERVER_HOST, AUTH_PORT)
        soap_up = await _check_port(SOAP_HOST, SOAP_PORT)

        return {
            "worldserver": "running" if world_up else "stopped",
            "authserver": "running" if auth_up else "stopped",
            "soap": "available" if soap_up else "unavailable",
            "host": SERVER_HOST
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


async def send_soap_command(command: str) -> dict:
    """Send GM command via SOAP interface"""
    soap_envelope = f'''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
                   xmlns:ns1="urn:AC">
  <SOAP-ENV:Body>
    <ns1:executeCommand>
      <command>{command}</command>
    </ns1:executeCommand>
  </SOAP-ENV:Body>
</SOAP-ENV:Envelope>'''

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"http://{SOAP_HOST}:{SOAP_PORT}/",
                content=soap_envelope,
                headers={"Content-Type": "text/xml"},
                auth=(SOAP_USER, SOAP_PASS)
            )

            if response.status_code == 200:
                # Parse SOAP response
                try:
                    root = ET.fromstring(response.text)
                    # Find the result element (no namespace prefix in response)
                    result = root.find('.//{urn:AC}result')
                    if result is None:
                        # Try without namespace (AzerothCore returns result without ns)
                        for elem in root.iter():
                            if elem.tag.endswith('result') or elem.tag == 'result':
                                result = elem
                                break
                    if result is not None and result.text:
                        # Clean up the result text (remove carriage returns)
                        cleaned = result.text.replace('\r', '').strip()
                        return {
                            "success": True,
                            "command": command,
                            "result": cleaned
                        }
                    return {
                        "success": True,
                        "command": command,
                        "result": "Command executed"
                    }
                except ET.ParseError:
                    return {
                        "success": True,
                        "command": command,
                        "result": response.text
                    }
            else:
                return {
                    "success": False,
                    "command": command,
                    "error": f"SOAP error: {response.status_code}",
                    "response": response.text[:500]
                }
    except httpx.ConnectError:
        return {
            "success": False,
            "command": command,
            "error": "SOAP connection failed - server may need restart to enable SOAP"
        }
    except Exception as e:
        return {
            "success": False,
            "command": command,
            "error": str(e)
        }


async def restart_server() -> dict:
    """Restart the AzerothCore server container"""
    try:
        # Use docker CLI (requires docker socket mount)
        proc = await asyncio.create_subprocess_exec(
            "docker", "restart", DOCKER_CONTAINER,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        if proc.returncode == 0:
            return {
                "success": True,
                "message": f"Container {DOCKER_CONTAINER} restarted",
                "container": DOCKER_CONTAINER
            }
        else:
            return {
                "success": False,
                "error": stderr.decode() if stderr else "Unknown error",
                "container": DOCKER_CONTAINER
            }
    except asyncio.TimeoutError:
        return {"success": False, "error": "Restart timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "Docker not available - need socket mount"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def stop_server() -> dict:
    """Stop the AzerothCore server container"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "stop", DOCKER_CONTAINER,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode == 0:
            return {"success": True, "message": f"Container {DOCKER_CONTAINER} stopped"}
        else:
            return {"success": False, "error": stderr.decode() if stderr else "Unknown error"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def start_server() -> dict:
    """Start the AzerothCore server container"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "start", DOCKER_CONTAINER,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode == 0:
            return {"success": True, "message": f"Container {DOCKER_CONTAINER} started"}
        else:
            return {"success": False, "error": stderr.decode() if stderr else "Unknown error"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_server_logs(lines: int = 100) -> dict:
    """Get recent server logs"""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker", "logs", "--tail", str(lines), DOCKER_CONTAINER,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        # worldserver logs go to stderr
        logs = stderr.decode() if stderr else stdout.decode()
        return {
            "success": True,
            "logs": logs,
            "lines": lines
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# PlayerBots specific commands
async def get_playerbots_status() -> dict:
    """Get PlayerBots status via server info (shows character count including bots)"""
    result = await send_soap_command(".server info")
    if result.get("success"):
        # Parse the server info to extract player/character counts
        text = result.get("result", "")
        return {
            "success": True,
            "result": text,
            "info": "Character count includes bots"
        }
    return result


async def add_bot(bot_name: str = None) -> dict:
    """Add a random bot or specific bot"""
    # Note: mod-playerbots doesn't have direct add commands via SOAP
    # Bots are managed through configuration and auto-spawn
    return {
        "success": False,
        "error": "Bot add/remove requires direct configuration. Use Config Editor to modify playerbots.conf"
    }


async def remove_all_bots() -> dict:
    """Remove all active bots - sends reload config which can reset bots"""
    return await send_soap_command(".reload config")


async def set_bot_count(count: int) -> dict:
    """Set the target number of random bots - requires config edit"""
    # This would need to modify the config file and reload
    return {
        "success": False,
        "error": "Bot count is set in playerbots.conf. Use Config Editor to modify AiPlayerbot.MinRandomBots and AiPlayerbot.MaxRandomBots"
    }


async def reload_playerbots_config() -> dict:
    """Reload PlayerBots configuration"""
    return await send_soap_command(".reload config")


# Config file management
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
        # Also check modules subdirectory
        modules_etc = SERVER_ETC / "modules"
        if modules_etc.exists():
            for f in modules_etc.glob("*.conf"):
                configs.append({
                    "name": f"modules/{f.name}",
                    "path": str(f),
                    "size": f.stat().st_size
                })
    return configs


def read_config(filename: str) -> Optional[str]:
    """Read a config file"""
    # Handle modules/ prefix
    if filename.startswith("modules/"):
        config_path = SERVER_ETC / filename
    else:
        config_path = SERVER_ETC / filename

    if config_path.exists() and config_path.suffix == ".conf":
        return config_path.read_text()
    return None


def write_config(filename: str, content: str) -> bool:
    """Write a config file (with backup)"""
    if filename.startswith("modules/"):
        config_path = SERVER_ETC / filename
    else:
        config_path = SERVER_ETC / filename

    if not config_path.suffix == ".conf":
        return False

    # Backup existing
    if config_path.exists():
        backup_path = config_path.with_suffix(".conf.bak")
        backup_path.write_text(config_path.read_text())

    config_path.write_text(content)
    return True
