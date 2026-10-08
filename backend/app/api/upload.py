"""Raster and imagery upload API endpoint."""

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.survey import Survey
from app.schemas.common import ResponseEnvelope
from app.schemas.survey import SurveyResponse
from app.services.tiling import inspect_raster
from app.core.security import verify_api_key
from app.core.logging import logger

router = APIRouter(tags=["Upload & Surveys"])


@router.post(
    "/upload",
    response_model=ResponseEnvelope[SurveyResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
async def upload_raster(
    file: UploadFile = File(..., description="GeoTIFF or RGB aerial image file"),
    project_id: str = Form(..., description="ID of the parent project"),
    capture_date: Optional[str] = Form(None, description="ISO format capture date (YYYY-MM-DD)"),
    forest_type: str = Form("tropical_moist", description="Forest biome type from carbon.yaml"),
    db: Session = Depends(get_db),
):
    """Uploads an aerial/satellite raster, inspects spatial metadata, and registers a Survey."""
    # 1. Validate project existence
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    # 2. Validate file extension
    ext = file.filename.split(".")[-1].lower() if file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Allowed formats: {settings.ALLOWED_EXTENSIONS}",
        )

    # 3. Save uploaded file to data/uploads
    survey_id = str(uuid.uuid4())
    safe_filename = f"{survey_id}_{file.filename}"
    destination_path = settings.UPLOAD_DIR / safe_filename

    try:
        with destination_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as exc:
        logger.error(f"Failed to save uploaded file: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file to disk: {str(exc)}",
        )

    # 4. Inspect raster spatial metadata (header only)
    try:
        metadata = inspect_raster(destination_path)
    except Exception as exc:
        logger.error(f"Raster inspection failed: {exc}")
        destination_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid or corrupted image/raster file: {str(exc)}",
        )

    # 5. Parse optional capture date
    parsed_date = None
    if capture_date:
        try:
            parsed_date = datetime.fromisoformat(capture_date.replace("Z", "+00:00"))
        except ValueError:
            parsed_date = datetime.now(timezone.utc)

    # 6. Save Survey record to database
    survey = Survey(
        id=survey_id,
        project_id=project_id,
        file_path=str(destination_path),
        original_filename=file.filename or safe_filename,
        crs=metadata.crs,
        resolution_m=round(metadata.resolution_x, 4),
        image_width=metadata.width,
        image_height=metadata.height,
        capture_date=parsed_date or datetime.now(timezone.utc),
        forest_type=forest_type,
    )
    db.add(survey)
    db.commit()
    db.refresh(survey)

    logger.info(f"Survey {survey_id} registered: {metadata.width}x{metadata.height}, CRS={metadata.crs}")

    return ResponseEnvelope(
        success=True,
        data=SurveyResponse.model_validate(survey),
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )
