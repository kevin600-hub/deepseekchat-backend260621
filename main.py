import os
import json
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("MODEL", "deepseek-chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://deepseekchat060621.vercel.app",
        "https://meshbagseller.com",
        "https://www.meshbagseller.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    messages: list

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/chat")
def chat(req: ChatRequest):
    url = f"{BASE_URL.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": req.messages,
        "max_tokens": 4096,
        "temperature": 0.7,
        "stream": True,
    }

    def generate():
        with requests.post(
            url,
            headers=headers,
            json=payload,
            stream=True,
            timeout=60
        ) as resp:
            if resp.status_code != 200:
                yield f"ERROR: {resp.text}"
                return

            for line in resp.iter_lines():
                if not line:
                    continue

                line = line.decode("utf-8")

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

    return StreamingResponse(generate(), media_type="text/plain")
