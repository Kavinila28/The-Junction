"""Health and discovery endpoints for THE JUNCTION API."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.config import settings
from app.db.database import list_analyses

router = APIRouter(tags=["system"])


def _model_ready() -> bool:
    try:
        from app.core.detector import get_detector

        get_detector()
        return True
    except Exception:
        return False


@router.get("/health")
def health() -> dict[str, object]:
    """Liveness check used by the frontend and by orchestration tools."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "detection_model_loaded": _model_ready(),
        "database_initialised": True,
        "analyses_count": len(list_analyses()),
    }


@router.get("/meta")
def meta() -> dict[str, object]:
    """Static metadata about the service (used by the dashboard footer)."""
    return {
        "name": settings.app_name,
        "tagline": "Predicting danger before it becomes an accident.",
        "version": settings.app_version,
        "stack": {
            "backend": "FastAPI",
            "vision": "Ultralytics YOLO + OpenCV",
            "database": "SQLite",
        },
    }