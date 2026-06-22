import json
import httpx
import os
from typing import Optional
from datetime import date
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from starlette.requests import Request
from core.config import API_KEY, BASE_URL, MODEL


class ChatRequest(BaseModel):
    messages: list


# ============================================
# 📊 Token 计数器（新增）
# ============================================
DAILY_TOKEN_LIMIT = 2_000_000  # 每日 200 万 Token 限额

def get_today_usage():
    """获取今天已使用的 Token 数"""
    today = date.today().isoformat()
    usage_file = f"token_usage_{today}.txt"
    
    if not os.path.exists(usage_file):
        return 0
    
    try:
        with open(usage_file, "r") as f:
            return int(f.read().strip())
    except:
        return 0

def add_today_usage(tokens):
    """累加今天使用的 Token"""
    today = date.today().isoformat()
    usage_file = f"token_usage_{today}.txt"
    
    current = get_today_usage()
    new_total = current + tokens
    
    with open(usage_file, "w") as f:
        f.write(str(new_total))
    
    return new_total


def stream_ai_response(messages: list, system_prompt: str, request: Optional[Request] = None):
    """Return a StreamingResponse that proxies an async stream from the upstream AI API.

    Uses httpx.AsyncClient so the event loop isn't blocked and checks for client disconnects.
    """
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API_KEY is not configured")

    # ============================================
    # 🛑 检查今日 Token 是否已达限额（新增）
    # ============================================
    today_usage = get_today_usage()
    if today_usage >= DAILY_TOKEN_LIMIT:
        raise HTTPException(
            status_code=429, 
            detail=f"今日 Token 已用尽（{today_usage}/{DAILY_TOKEN_LIMIT}），请明天再试"
        )

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
        # ============================================
        # 📊 记录本次消耗的 Token（新增）
        # ============================================
        total_tokens_used = 0

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
                                    # ============================================
                                    # 📊 累计本次消耗的 Token（新增）
                                    # ============================================
                                    # 粗略估算：中文约 1.5 字/Token，英文约 4 字符/Token
                                    # 这里简单按字符数/2 估算
                                    estimated_tokens = max(1, len(content) // 2)
                                    total_tokens_used += estimated_tokens

                                    yield content
                            except Exception:
                                continue
        except httpx.RequestError as e:
            yield f"ERROR: {str(e)}"
        except Exception as e:
            yield f"ERROR: {str(e)}"

        # ============================================
        # 💾 请求结束后累加 Token 到今日用量（新增）
        # ============================================
        if total_tokens_used > 0:
            new_total = add_today_usage(total_tokens_used)
            # 打印日志（Render 日志中可见）
            print(f"[Token] 本次: {total_tokens_used}, 今日累计: {new_total}/{DAILY_TOKEN_LIMIT}")

    return StreamingResponse(generate(), media_type="text/plain")
