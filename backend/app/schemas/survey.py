"""Pydantic schemas for Surveys."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SurveyResponse(BaseModel):
    """Schema for returning survey details."""

    id: str
    project_id: str
    original_filename: str
    crs: Optional[str] = None
    resolution_m: Optional[float] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    capture_date: Optional[datetime] = None
    forest_type: str
    created_at: datetime

    model_config = {"from_attributes": True}
