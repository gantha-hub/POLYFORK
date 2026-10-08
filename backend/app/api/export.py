"""Multi-format export API endpoints (GeoJSON, CSV, PDF)."""

import csv
import io
import json
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.survey import Survey
from app.models.project import Project
from app.models.tree import Tree
from app.models.calibration import CalibrationModel
from app.api.results import calculate_survey_metrics
from app.services.registry import trees_to_geojson_feature_collection
from app.services.reports import generate_survey_pdf_report
from app.core.security import verify_api_key
from app.core.logging import logger

router = APIRouter(prefix="/export", tags=["Exports"])


@router.get(
    "/{survey_id}",
    dependencies=[Depends(verify_api_key)],
)
def export_survey_data(
    survey_id: str,
    format: Literal["geojson", "csv", "pdf"] = Query("geojson", description="Export file format: geojson, csv, or pdf"),
    db: Session = Depends(get_db),
):
    """Exports survey analysis results in GeoJSON, CSV, or executive PDF report format."""
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID '{survey_id}' not found.",
        )

    project = db.query(Project).filter(Project.id == survey.project_id).first()
    project_name = project.name if project else "Forest Inventory"

    trees = db.query(Tree).filter(Tree.survey_id == survey_id).all()

    # 1. GeoJSON Format
    if format == "geojson":
        geojson_dict = trees_to_geojson_feature_collection(trees)
        content_str = json.dumps(geojson_dict, indent=2)
        filename = f"{survey.original_filename or survey_id}_trees.geojson"
        return Response(
            content=content_str,
            media_type="application/geo+json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # 2. Tabular CSV Format
    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "tree_id",
            "survey_id",
            "centroid_x",
            "centroid_y",
            "crown_area_sqm",
            "confidence",
            "dbh_cm",
            "biomass_kg",
            "carbon_kg",
            "status",
            "data_source",
        ])
        for t in trees:
            writer.writerow([
                t.tree_id,
                t.survey_id,
                t.centroid_x,
                t.centroid_y,
                t.crown_area_sqm,
                t.confidence,
                t.dbh_cm,
                t.biomass_kg,
                t.carbon_kg,
                t.status,
                t.data_source,
            ])

        csv_content = output.getvalue()
        filename = f"{survey.original_filename or survey_id}_trees.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # 3. Audit PDF Report
    elif format == "pdf":
        cal_model = (
            db.query(CalibrationModel)
            .filter(CalibrationModel.project_id == survey.project_id)
            .order_by(CalibrationModel.created_at.desc())
            .first()
        )
        summary = calculate_survey_metrics(survey, trees, cal_model, include_geojson=False)

        pdf_filename = f"{survey_id}_audit_report.pdf"
        pdf_path = settings.EXPORTS_DIR / pdf_filename

        generate_survey_pdf_report(
            summary=summary,
            output_path=pdf_path,
            project_name=project_name,
        )

        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=pdf_filename,
        )
