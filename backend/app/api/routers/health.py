from fastapi import APIRouter
from app.schemas.health import HealthResponse
from app.core.logging import get_logger

logger = get_logger("api.health")
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    logger.info("Health check requested")
    return HealthResponse(status="ok")


