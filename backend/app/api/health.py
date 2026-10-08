"""Health and status diagnostic endpoint."""

from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.database import get_db
from app.schemas.common import ResponseEnvelope

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ResponseEnvelope[Dict[str, Any]])
def get_health(db: Session = Depends(get_db)):
    """Health check verifying database connection and active ML backend."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    health_info = {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "model_backend": settings.MODEL_BACKEND,
        "environment": settings.ENVIRONMENT,
        "app_name": settings.PROJECT_NAME,
    }

    return ResponseEnvelope(
        success=True,
        data=health_info,
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )
