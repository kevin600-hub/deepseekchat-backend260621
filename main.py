import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("MODEL", "deepseek-chat")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://deepseekchat060621.vercel.app/"],  # 上线后建议改成你的前端域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    messages: list

@app.get("/")
def health_check():
    return {"status": "ok", "service": "DeepSeek FastAPI Backend"}

@app.post("/chat")
def chat(req: ChatRequest):
    url = f"{BASE_URL.rstrip('/')}/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": req.messages,
        "max_tokens": 4096,
        "temperature": 0.7
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=60)

    if resp.status_code != 200:
        return {
            "error": True,
            "status_code": resp.status_code,
            "detail": resp.text
        }

    result = resp.json()
    return {
        "reply": result["choices"][0]["message"]["content"]
    }
