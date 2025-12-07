"""
vLLM client for LLM inference and health checks
"""
import os
from typing import Optional
import httpx

VLLM_URL = os.getenv("VLLM_URL", "http://172.21.0.20:8000")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "cerebro")
VLLM_MODEL = os.getenv("VLLM_MODEL", "TheBloke/Llama-3-70B-Instruct-AWQ")


async def health_check() -> dict:
    """Check vLLM server health"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{VLLM_URL}/health")
            if response.status_code == 200:
                return {"status": "healthy", "url": VLLM_URL}
            return {"status": "unhealthy", "code": response.status_code}
    except httpx.RequestError as e:
        return {"status": "unreachable", "error": str(e)}


async def get_models() -> list:
    """Get available models"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"{VLLM_URL}/v1/models",
                headers={"Authorization": f"Bearer {VLLM_API_KEY}"}
            )
            if response.status_code == 200:
                return response.json().get("data", [])
            return []
    except httpx.RequestError:
        return []


async def chat_completion(
    messages: list[dict],
    max_tokens: int = 256,
    temperature: float = 0.7
) -> Optional[str]:
    """Send chat completion request to vLLM"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{VLLM_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {VLLM_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": VLLM_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            return None
    except httpx.RequestError:
        return None
