from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

from core.config import ALLOWED_ORIGINS
from routers import pump, mechanical

limiter = Limiter(key_func=get_remote_address)

app = FastAPI()

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "AI Assistant Backend"}

app.include_router(pump.router, prefix="/assistant/pump", tags=["Pump Assistant"])
app.include_router(mechanical.router, prefix="/assistant/mechanical", tags=["Mechanical Assistant"])
app.include_router(chat.router, prefix="/assistant", tags=["General Assistant"])
