"""Pydantic schemas for Trees and Survey Results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import TreeCountResult, CarbonEstimateResult


class TreeResponse(BaseModel):
    """Schema for individual tree crown record."""

    tree_id: str
    survey_id: str
    geometry_geojson: str
    centroid_x: float
    centroid_y: float
    crown_area_sqm: float
    confidence: float
    dbh_cm: Optional[float] = None
    biomass_kg: Optional[float] = None
    carbon_kg: Optional[float] = None
    status: str
    data_source: str
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


class SurveyResultsSummary(BaseModel):
    """Aggregated survey results summary."""

    survey_id: str
    forest_type: str
    count: TreeCountResult
    carbon: CarbonEstimateResult
    mean_crown_area_sqm: float
    mean_dbh_cm: float
    total_trees_detected: int
    data_source: str
    geojson: Optional[Dict[str, Any]] = None


class RegionQueryRequest(BaseModel):
    """GeoJSON Polygon for spatial sub-region queries."""

    polygon: Dict[str, Any] = Field(
        ...,
        description="GeoJSON Polygon geometry dictionary with type and coordinates",
    )
