"""Survey results, spatial region queries, and carbon reporting API endpoints."""

import json
import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from shapely.geometry import shape, Point, Polygon

from app.config import settings
from app.database import get_db
from app.models.survey import Survey
from app.models.tree import Tree
from app.models.calibration import CalibrationModel
from app.schemas.common import (
    ResponseEnvelope,
    TreeCountResult,
    ConfidenceInterval,
    CarbonEstimateResult,
)
from app.schemas.tree import SurveyResultsSummary, RegionQueryRequest
from app.services.calibration import predict_ratio, predict_negbin_glm
from app.services.uncertainty import build_conformal_interval
from app.services.carbon import run_monte_carlo_carbon_estimation
from app.services.registry import trees_to_geojson_feature_collection
from app.core.security import verify_api_key
from app.core.logging import logger

router = APIRouter(prefix="/results", tags=["Survey Results & Spatial Queries"])


def calculate_survey_metrics(
    survey: Survey,
    trees: List[Tree],
    calibration_model: Optional[CalibrationModel] = None,
    include_geojson: bool = True,
) -> SurveyResultsSummary:
    """Calculates calibrated tree count, conformal bounds, and Monte Carlo carbon."""
    raw_count = len(trees)
    crown_areas = [t.crown_area_sqm for t in trees]
    dbhs = [t.dbh_cm for t in trees if t.dbh_cm is not None]

    mean_cpa = float(np.mean(crown_areas)) if crown_areas else 0.0
    mean_dbh = float(np.mean(dbhs)) if dbhs else 0.0

    # 1. Tree Count & Interval Computation
    if calibration_model is not None:
        params = json.loads(calibration_model.params_json) if calibration_model.params_json else {}
        q = calibration_model.residual_quantile_q

        if calibration_model.method == "ratio":
            calibrated_count = predict_ratio(visual_count_V=float(raw_count), params=params)
        else:
            # GLM calibration
            calibrated_count = predict_negbin_glm(
                visual_count_V=float(raw_count),
                canopy_cover_pct=70.0,  # Stand average
                mean_crown_area_sqm=mean_cpa,
                params=params,
            )

        calibrated_count = max(0.0, round(calibrated_count, 1))
        low, high = build_conformal_interval(calibrated_count, quantile_q=q, confidence_level=0.90)
        is_calibrated = True

    else:
        # Uncalibrated: use Poisson normal approximation margin for 90% confidence (z = 1.645)
        calibrated_count = float(raw_count)
        margin = 1.645 * math.sqrt(max(1.0, float(raw_count)))
        low = max(0.0, round(raw_count - margin, 1))
        high = round(raw_count + margin, 1)
        is_calibrated = False

    count_result = TreeCountResult(
        raw_count=raw_count,
        calibrated_count=calibrated_count,
        interval=ConfidenceInterval(low=low, high=high, confidence_level=0.90),
        calibrated=is_calibrated,
    )

    # 2. Monte Carlo Allometric Carbon Estimation (1,000 draws)
    carbon_result = run_monte_carlo_carbon_estimation(
        crown_areas_sqm=crown_areas,
        forest_type=survey.forest_type,
        n_draws=1000,
    )

    # 3. GeoJSON Feature Collection
    geojson_data = trees_to_geojson_feature_collection(trees) if include_geojson else None

    # Check data source
    any_synthetic = any(t.data_source == "synthetic" for t in trees) if trees else (settings.MODEL_BACKEND == "mock")
    data_src = "synthetic" if any_synthetic else "real"

    return SurveyResultsSummary(
        survey_id=survey.id,
        forest_type=survey.forest_type,
        count=count_result,
        carbon=carbon_result,
        mean_crown_area_sqm=round(mean_cpa, 2),
        mean_dbh_cm=round(mean_dbh, 2),
        total_trees_detected=raw_count,
        data_source=data_src,
        geojson=geojson_data,
    )


import numpy as np


@router.get(
    "/latest/summary",
    response_model=ResponseEnvelope[SurveyResultsSummary],
    dependencies=[Depends(verify_api_key)],
)
def get_latest_survey_results(db: Session = Depends(get_db)):
    """Retrieves full survey results for the most recent active survey with trees."""
    latest_tree = db.query(Tree).first()
    if not latest_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tree records found in database.",
        )
    survey = db.query(Survey).filter(Survey.id == latest_tree.survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey for latest trees not found.",
        )

    trees = db.query(Tree).filter(Tree.survey_id == survey.id).all()
    cal_model = (
        db.query(CalibrationModel)
        .filter(CalibrationModel.project_id == survey.project_id)
        .order_by(CalibrationModel.created_at.desc())
        .first()
    )

    summary = calculate_survey_metrics(survey, trees, cal_model, include_geojson=True)

    return ResponseEnvelope(
        success=True,
        data=summary,
        data_source=summary.data_source,
    )


@router.get(
    "/latest/geojson",
    dependencies=[Depends(verify_api_key)],
)
def get_latest_survey_geojson(db: Session = Depends(get_db)):
    """Returns pure GeoJSON FeatureCollection of all tree crown polygon vectors for the latest survey."""
    latest_tree = db.query(Tree).first()
    if not latest_tree:
        return {"type": "FeatureCollection", "features": []}

    trees = db.query(Tree).filter(Tree.survey_id == latest_tree.survey_id).all()
    return trees_to_geojson_feature_collection(trees)


@router.get(
    "/{survey_id}",
    response_model=ResponseEnvelope[SurveyResultsSummary],
    dependencies=[Depends(verify_api_key)],
)
def get_survey_results(survey_id: str, db: Session = Depends(get_db)):
    """Retrieves full survey results with calibrated count interval, carbon distribution, and GeoJSON."""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID '{survey_id}' not found.",
        )

    trees = db.query(Tree).filter(Tree.survey_id == survey_id).all()
    cal_model = (
        db.query(CalibrationModel)
        .filter(CalibrationModel.project_id == survey.project_id)
        .order_by(CalibrationModel.created_at.desc())
        .first()
    )

    summary = calculate_survey_metrics(survey, trees, cal_model, include_geojson=True)

    return ResponseEnvelope(
        success=True,
        data=summary,
        data_source=summary.data_source,
    )


@router.post(
    "/{survey_id}/region",
    response_model=ResponseEnvelope[SurveyResultsSummary],
    dependencies=[Depends(verify_api_key)],
)
def query_survey_region(
    survey_id: str,
    payload: RegionQueryRequest,
    db: Session = Depends(get_db),
):
    """Spatial polygon sub-region query returning localized calibrated counts and carbon stock."""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID '{survey_id}' not found.",
        )

    try:
        query_poly = shape(payload.polygon)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid GeoJSON polygon geometry: {str(exc)}",
        )

    all_trees = db.query(Tree).filter(Tree.survey_id == survey_id).all()

    # Filter trees whose centroids fall within the specified region polygon
    filtered_trees = [
        t for t in all_trees
        if query_poly.contains(Point(t.centroid_x, t.centroid_y))
    ]

    cal_model = (
        db.query(CalibrationModel)
        .filter(CalibrationModel.project_id == survey.project_id)
        .order_by(CalibrationModel.created_at.desc())
        .first()
    )

    summary = calculate_survey_metrics(survey, filtered_trees, cal_model, include_geojson=True)

    return ResponseEnvelope(
        success=True,
        data=summary,
        data_source=summary.data_source,
    )
