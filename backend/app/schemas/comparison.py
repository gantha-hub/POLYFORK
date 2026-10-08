"""Pydantic schemas for Multi-survey Change Detection Comparison."""

from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ChangeMetric(BaseModel):
    """Counts and aggregate metrics for a category of change."""

    count: int
    mean_crown_area_sqm: float
    total_carbon_kg: float


class SurveyComparisonResponse(BaseModel):
    """Comparison results between two surveys T1 and T2."""

    survey_1_id: str
    survey_2_id: str
    new_trees: ChangeMetric = Field(..., description="Trees present in T2 but not in T1")
    lost_trees: ChangeMetric = Field(..., description="Trees present in T1 but absent in T2")
    grown_trees: ChangeMetric = Field(..., description="Matched trees where crown area expanded by >15%")
    unchanged_trees: ChangeMetric = Field(..., description="Matched trees with stable canopy area")
    net_tree_change: int = Field(..., description="Total trees in T2 minus T1")
    net_carbon_change_kg: float = Field(..., description="Net carbon difference in kg C")
    data_source: str = "synthetic"
