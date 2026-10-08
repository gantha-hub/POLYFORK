"""Pydantic schemas for Ground Plots and Calibration."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class GroundPlotCreate(BaseModel):
    """Schema for individual ground plot."""

    plot_name: str
    ground_count_G: int = Field(..., ge=0)
    visual_count_V: int = Field(..., ge=0)
    canopy_cover_pct: float = Field(..., ge=0.0, le=100.0)
    crown_area_sqm: float = Field(..., ge=0.0)
    forest_type: str = "tropical_moist"
    geometry_geojson: Optional[str] = None


class CalibrationFitRequest(BaseModel):
    """Schema for triggering calibration model fitting."""

    project_id: str
    method: Literal["ratio", "negbin_glm"] = "negbin_glm"


class CalibrationStatusResponse(BaseModel):
    """Calibration status and metrics for a project."""

    project_id: str
    calibrated: bool
    model_id: Optional[str] = None
    method: Optional[str] = None
    n_plots: int
    residual_quantile_q: Optional[float] = None
    empirical_coverage: Optional[float] = None
    params: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
