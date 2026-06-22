import os

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("MODEL", "deepseek-chat")

FRONTEND_TOKEN = os.getenv("FRONTEND_TOKEN")

ALLOWED_ORIGINS = [
    "https://deepseekchat060621.vercel.app",
    "https://meshbagseller.com",
    "https://www.meshbagseller.com",
    "http://localhost:3000",
    "http://localhost:5173",
]