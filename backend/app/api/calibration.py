"""Calibration and ground plot audit API endpoints."""

import io
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.ground_plot import GroundPlot
from app.models.calibration import CalibrationModel
from app.schemas.common import ResponseEnvelope
from app.schemas.calibration import (
    CalibrationFitRequest,
    CalibrationStatusResponse,
)
from app.services.calibration import (
    GroundPlotData,
    validate_plot_count,
    fit_ratio_baseline,
    fit_negbin_glm,
    predict_ratio,
    predict_negbin_glm,
)
from app.services.uncertainty import (
    split_conformal_dataset,
    compute_conformal_quantile,
    evaluate_empirical_coverage,
)
from app.core.security import verify_api_key
from app.core.logging import logger

router = APIRouter(prefix="/calibration", tags=["Calibration & Ground Audits"])


@router.post(
    "/plots",
    response_model=ResponseEnvelope[dict],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
async def upload_ground_plots_csv(
    file: UploadFile = File(..., description="CSV file with columns: plot_name, G, V, canopy_cover, crown_area, forest_type"),
    project_id: str = Form(..., description="Project ID to associate with ground plots"),
    db: Session = Depends(get_db),
):
    """Uploads ground audit plots from CSV file."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse CSV file: {str(exc)}",
        )

    # Standardize column naming
    col_map = {
        "G": "ground_count_G",
        "V": "visual_count_V",
        "canopy_cover": "canopy_cover_pct",
        "crown_area": "crown_area_sqm",
    }
    df.rename(columns=col_map, inplace=True)

    required_cols = ["ground_count_G", "visual_count_V", "canopy_cover_pct", "crown_area_sqm"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV missing required columns: {missing}. Expected G, V, canopy_cover, crown_area.",
        )

    imported_count = 0
    for idx, row in df.iterrows():
        plot_name = str(row.get("plot_name", f"Plot_{idx + 1}"))
        g = int(row["ground_count_G"])
        v = int(row["visual_count_V"])
        cc = float(row["canopy_cover_pct"])
        ca = float(row["crown_area_sqm"])
        ft = str(row.get("forest_type", "tropical_moist"))

        plot = GroundPlot(
            plot_id=str(uuid.uuid4()),
            project_id=project_id,
            plot_name=plot_name,
            ground_count_G=g,
            visual_count_V=v,
            canopy_cover_pct=cc,
            crown_area_sqm=ca,
            forest_type=ft,
        )
        db.add(plot)
        imported_count += 1

    db.commit()
    logger.info(f"Imported {imported_count} ground plots for Project {project_id}.")

    return ResponseEnvelope(
        success=True,
        data={"project_id": project_id, "imported_plots": imported_count},
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )


@router.post(
    "/fit",
    response_model=ResponseEnvelope[CalibrationStatusResponse],
    dependencies=[Depends(verify_api_key)],
)
def fit_calibration_model(
    payload: CalibrationFitRequest,
    db: Session = Depends(get_db),
):
    """Fits ratio baseline or Negative Binomial GLM with conformal uncertainty.

    Refuses fitting with fewer than 10 plots.
    """
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{payload.project_id}' not found.",
        )

    plots = db.query(GroundPlot).filter(GroundPlot.project_id == payload.project_id).all()

    # Convert to dataclass for validation
    plot_data = [
        GroundPlotData(
            plot_name=p.plot_name,
            ground_count_G=p.ground_count_G,
            visual_count_V=p.visual_count_V,
            canopy_cover_pct=p.canopy_cover_pct,
            crown_area_sqm=p.crown_area_sqm,
            forest_type=p.forest_type,
        )
        for p in plots
    ]

    # Strict refusal guard: checks N >= 10
    validate_plot_count(plot_data)

    # Convert to DataFrame
    df = pd.DataFrame([
        {
            "ground_count_G": p.ground_count_G,
            "visual_count_V": p.visual_count_V,
            "canopy_cover_pct": p.canopy_cover_pct,
            "crown_area_sqm": p.crown_area_sqm,
            "forest_type": p.forest_type,
        }
        for p in plot_data
    ])

    # Split dataset into calibration (70%) and validation (30%)
    df_cal, df_val = split_conformal_dataset(df, cal_fraction=0.70)

    # Fit model according to selected method
    if payload.method == "ratio":
        params, g_cal_pred = fit_ratio_baseline(df_cal)
        # Validation predictions
        g_val_pred = np.array([predict_ratio(v, params) for v in df_val["visual_count_V"].values])
    else:
        params, g_cal_pred = fit_negbin_glm(df_cal)
        g_val_pred = np.array([
            predict_negbin_glm(v, cc, ca, params)
            for v, cc, ca in zip(
                df_val["visual_count_V"].values,
                df_val["canopy_cover_pct"].values,
                df_val["crown_area_sqm"].values,
            )
        ])

    # Conformal non-conformity quantile q for 90% prediction intervals
    g_cal_true = df_cal["ground_count_G"].values.astype(float)
    q = compute_conformal_quantile(g_cal_true, g_cal_pred, alpha=0.10)

    # Empirical coverage on held-out split
    g_val_true = df_val["ground_count_G"].values.astype(float)
    coverage = evaluate_empirical_coverage(g_val_true, g_val_pred, quantile_q=q)

    # Remove any prior calibration model for this project
    db.query(CalibrationModel).filter(CalibrationModel.project_id == payload.project_id).delete()

    model_id = str(uuid.uuid4())
    cal_record = CalibrationModel(
        id=model_id,
        project_id=payload.project_id,
        method=payload.method,
        params_json=json.dumps(params),
        residual_quantile_q=q,
        coverage=coverage,
        n_plots=len(plots),
    )
    db.add(cal_record)
    db.commit()
    db.refresh(cal_record)

    logger.info(f"Fitted {payload.method} calibration model {model_id}: q={q}, coverage={coverage}")

    response = CalibrationStatusResponse(
        project_id=payload.project_id,
        calibrated=True,
        model_id=model_id,
        method=payload.method,
        n_plots=len(plots),
        residual_quantile_q=q,
        empirical_coverage=coverage,
        params=params,
        created_at=cal_record.created_at,
    )

    return ResponseEnvelope(
        success=True,
        data=response,
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )


@router.get(
    "/status/{project_id}",
    response_model=ResponseEnvelope[CalibrationStatusResponse],
    dependencies=[Depends(verify_api_key)],
)
def get_calibration_status(project_id: str, db: Session = Depends(get_db)):
    """Retrieves current calibration status and metrics for a project."""
    cal_model = (
        db.query(CalibrationModel)
        .filter(CalibrationModel.project_id == project_id)
        .order_by(CalibrationModel.created_at.desc())
        .first()
    )
    plot_count = db.query(GroundPlot).filter(GroundPlot.project_id == project_id).count()

    if not cal_model:
        return ResponseEnvelope(
            success=True,
            data=CalibrationStatusResponse(
                project_id=project_id,
                calibrated=False,
                n_plots=plot_count,
            ),
            data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
        )

    params = json.loads(cal_model.params_json) if cal_model.params_json else {}

    response = CalibrationStatusResponse(
        project_id=project_id,
        calibrated=True,
        model_id=cal_model.id,
        method=cal_model.method,
        n_plots=cal_model.n_plots,
        residual_quantile_q=cal_model.residual_quantile_q,
        empirical_coverage=cal_model.coverage,
        params=params,
        created_at=cal_model.created_at,
    )

    return ResponseEnvelope(
        success=True,
        data=response,
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )
