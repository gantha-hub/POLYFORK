"""Pydantic schemas for Projects."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Base schema for Project."""

    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Detailed description")


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    pass


class ProjectResponse(ProjectBase):
    """Schema for returning a project."""

    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
