"""Active learning verification queue and human audit API endpoints."""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from shapely.geometry import shape

from app.config import settings
from app.database import get_db
from app.models.survey import Survey
from app.models.tree import Tree
from app.models.verification import Verification
from app.schemas.common import ResponseEnvelope
from app.schemas.verification import VerificationCreate, VerificationResponse
from app.services.active_learning import rank_trees_for_verification
from app.core.security import verify_api_key
from app.core.logging import logger

router = APIRouter(prefix="/verify", tags=["Active Learning & Verification"])


@router.get(
    "/queue/{survey_id}",
    response_model=ResponseEnvelope[List[Dict[str, Any]]],
    dependencies=[Depends(verify_api_key)],
)
def get_verification_queue(
    survey_id: str,
    limit: int = Query(50, ge=1, le=200, description="Max trees to return in audit queue"),
    db: Session = Depends(get_db),
):
    """Retrieves prioritized active learning audit queue of uncertain or anomalous trees."""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID '{survey_id}' not found.",
        )

    trees = db.query(Tree).filter(Tree.survey_id == survey_id).all()
    queue = rank_trees_for_verification(trees, limit=limit)

    return ResponseEnvelope(
        success=True,
        data=queue,
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )


@router.post(
    "",
    response_model=ResponseEnvelope[VerificationResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
def submit_verification(
    payload: VerificationCreate,
    db: Session = Depends(get_db),
):
    """Submits human-in-the-loop audit decision (accept, reject, or edit) for a tree crown."""
    tree = db.query(Tree).filter(Tree.tree_id == payload.tree_id).first()
    if not tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree with ID '{payload.tree_id}' not found.",
        )

    # Apply audit action to Tree record
    if payload.action == "accept":
        tree.status = "verified"
    elif payload.action == "reject":
        tree.status = "rejected"
    elif payload.action == "edit":
        tree.status = "edited"
        if payload.edited_geometry_geojson:
            try:
                poly_dict = json.loads(payload.edited_geometry_geojson)
                geom = shape(poly_dict)
                tree.geometry_geojson = payload.edited_geometry_geojson
                tree.crown_area_sqm = max(1.0, round(float(geom.area), 2))
                tree.centroid_x = float(geom.centroid.x)
                tree.centroid_y = float(geom.centroid.y)
            except Exception as exc:
                logger.warning(f"Could not parse edited geometry: {exc}")

    # Record audit log in verifications table
    verification_record = Verification(
        id=str(uuid.uuid4()),
        tree_id=payload.tree_id,
        action=payload.action,
        edited_geometry_geojson=payload.edited_geometry_geojson,
        user_id=payload.user_id,
        notes=payload.notes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(verification_record)
    db.commit()
    db.refresh(verification_record)

    logger.info(f"Auditor '{payload.user_id}' applied action '{payload.action}' to tree {payload.tree_id}")

    return ResponseEnvelope(
        success=True,
        data=VerificationResponse.model_validate(verification_record),
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )
