"""Pydantic schemas for Background Jobs."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    """Schema for triggering an analysis job."""

    survey_id: str = Field(..., description="ID of the survey to analyze")


class JobResponse(BaseModel):
    """Schema for returning job execution status."""

    id: str
    survey_id: str
    job_type: str
    status: str
    progress: int
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
