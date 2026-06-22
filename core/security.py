from fastapi import Header, HTTPException
from core.config import FRONTEND_TOKEN

def verify_frontend_token(x_frontend_token: str = Header(None)):
    if not FRONTEND_TOKEN:
        raise HTTPException(status_code=500, detail="FRONTEND_TOKEN is not configured")

    if x_frontend_token != FRONTEND_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden")

    return True