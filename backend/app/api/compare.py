"""Multi-survey temporal change detection API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.survey import Survey
from app.models.tree import Tree
from app.schemas.common import ResponseEnvelope
from app.schemas.comparison import SurveyComparisonResponse
from app.services.change_detection import (
    match_surveys_change_detection,
    compute_category_metric,
)
from app.core.security import verify_api_key

router = APIRouter(prefix="/compare", tags=["Change Detection"])


@router.get(
    "/{survey_1_id}/{survey_2_id}",
    response_model=ResponseEnvelope[SurveyComparisonResponse],
    dependencies=[Depends(verify_api_key)],
)
def compare_surveys_endpoint(
    survey_1_id: str,
    survey_2_id: str,
    db: Session = Depends(get_db),
):
    """Compares two temporal surveys (T1 and T2) and classifies tree changes.

    Identifies new, lost, grown (>15% crown expansion), and unchanged trees.
    """
    s1 = db.query(Survey).filter(Survey.id == survey_1_id).first()
    if not s1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"First survey '{survey_1_id}' not found.",
        )

    s2 = db.query(Survey).filter(Survey.id == survey_2_id).first()
    if not s2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Second survey '{survey_2_id}' not found.",
        )

    trees_t1 = db.query(Tree).filter(Tree.survey_id == survey_1_id).all()
    trees_t2 = db.query(Tree).filter(Tree.survey_id == survey_2_id).all()

    summary = match_surveys_change_detection(
        trees_t1=trees_t1,
        trees_t2=trees_t2,
        max_centroid_dist_m=3.0,
        growth_threshold_pct=0.15,
    )

    response = SurveyComparisonResponse(
        survey_1_id=survey_1_id,
        survey_2_id=survey_2_id,
        new_trees=compute_category_metric(summary.new_trees),
        lost_trees=compute_category_metric(summary.lost_trees),
        grown_trees=compute_category_metric(summary.grown_trees),
        unchanged_trees=compute_category_metric(summary.unchanged_trees),
        net_tree_change=summary.net_tree_change,
        net_carbon_change_kg=summary.net_carbon_change_kg,
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )

    return ResponseEnvelope(
        success=True,
        data=response,
        data_source=response.data_source,
    )
