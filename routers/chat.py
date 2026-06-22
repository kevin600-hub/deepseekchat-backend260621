from fastapi import APIRouter, Depends
from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.security import verify_frontend_token
from routers.common_chat import ChatRequest, stream_ai_response

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

GENERAL_SYSTEM_PROMPT = """
你是一个智能AI助手。
你擅长编程、写作、翻译、
商业咨询、学习辅导和日常问答。
回答准确、清晰、友好。
"""

@router.post("/chat")
@limiter.limit("10/minute")
def general_chat(
    request: Request,
    req: ChatRequest,
    _: bool = Depends(verify_frontend_token),
):
    return stream_ai_response(
        req.messages,
        GENERAL_SYSTEM_PROMPT
    )
