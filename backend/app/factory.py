from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from app.core.config import settings
from app.api.routes import api_router
from dotenv import load_dotenv


def create_app() -> FastAPI:
    load_dotenv(override=True)
    application = FastAPI(title=settings.app_name, version=settings.version)

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
    
    return application


