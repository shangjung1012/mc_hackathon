from fastapi import APIRouter
from app.api.routers import health as health_router


api_router = APIRouter()
api_router.include_router(health_router.router)


