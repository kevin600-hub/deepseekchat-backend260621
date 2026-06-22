from fastapi import APIRouter, Depends
from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from core.security import verify_frontend_token
from routers.common_chat import ChatRequest, stream_ai_response

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

PUMP_SYSTEM_PROMPT = """
你是一个专业的泵类设备 AI 助手。
你擅长解释离心泵、隔膜泵、齿轮泵、真空泵、选型、故障诊断、维护保养。
回答要专业、清楚、实用，适合工程人员、采购人员和维修人员理解。
"""


@router.post("/chat")
@limiter.limit("10/minute")
async def pump_chat(
    request: Request,
    req: ChatRequest,
    _: bool = Depends(verify_frontend_token),
):
    return stream_ai_response(req.messages, PUMP_SYSTEM_PROMPT, request)