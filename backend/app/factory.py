from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.api.routes import api_router
from app.middleware.logging_middleware import LoggingMiddleware
from dotenv import load_dotenv

# 設置日誌
setup_logging()
logger = get_logger("app")


def create_app() -> FastAPI:
    load_dotenv(override=True)
    
    logger.info("Starting application", app_name=settings.app_name, version=settings.version)
    
    application = FastAPI(title=settings.app_name, version=settings.version)

    # 添加日誌中間件（應該在其他中間件之前）
    application.add_middleware(LoggingMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)
    
    # Handle favicon.ico requests
    @application.get("/favicon.ico")
    async def favicon():
        return Response(status_code=204)  # No Content
    
    logger.info("Application created successfully")
    return application


