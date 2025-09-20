from fastapi import APIRouter
from app.api.routers import health as health_router
from app.api.routers import gemini as gemini_router
from app.api.routers import tts as tts_router
from app.api.routers import users as users_router


api_router = APIRouter()
api_router.include_router(health_router.router)
api_router.include_router(gemini_router.router)
api_router.include_router(tts_router.router)
api_router.include_router(users_router.router)


