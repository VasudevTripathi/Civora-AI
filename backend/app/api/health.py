from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.app.core.config import Settings
from backend.app.core.dependencies import get_settings

router = APIRouter()


@router.get("/health", tags=["System"])
async def get_health(settings: Settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENV,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


