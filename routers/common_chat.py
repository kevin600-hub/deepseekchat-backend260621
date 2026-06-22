import json
import httpx

from typing import Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from starlette.requests import Request

from core.config import API_KEY, BASE_URL, MODEL


class ChatRequest(BaseModel):
    messages: list


def stream_ai_response(messages: list, system_prompt: str, request: Optional[Request] = None):
    """Return a StreamingResponse that proxies an async stream from the upstream AI API.

    Uses httpx.AsyncClient so the event loop isn't blocked and checks for client disconnects.
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY is not configured")

    url = f"{BASE_URL.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    final_messages = [
        {"role": "system", "content": system_prompt},
        *messages,
    ]

    payload = {
        "model": MODEL,
        "messages": final_messages,
        "max_tokens": 4096,
        "temperature": 0.7,
        "stream": True,
    }

    async def generate():
        timeout = httpx.Timeout(60.0, read=60.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as resp:
                    if resp.status_code != 200:
                        text = await resp.aread()
                        yield f"ERROR: {text.decode('utf-8', errors='ignore')}"
                        return

                    async for line in resp.aiter_lines():
                        # stop if client disconnected
                        if request is not None and await request.is_disconnected():
                            break

                        if not line:
                            continue

                        if line.startswith("data: "):
                            data = line[6:]

                            if data == "[DONE]":
                                break

                            try:
                                chunk = json.loads(data)
                                content = chunk["choices"][0]["delta"].get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                continue
        except httpx.RequestError as e:
            yield f"ERROR: {str(e)}"
        except Exception as e:
            yield f"ERROR: {str(e)}"

    return StreamingResponse(generate(), media_type="text/plain")