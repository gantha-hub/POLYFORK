"""Pydantic schemas for Field Verification and Active Learning."""

from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


class VerificationCreate(BaseModel):
    """Schema for submitting an auditor verification."""

    tree_id: str
    action: Literal["accept", "reject", "edit"]
    edited_geometry_geojson: Optional[str] = None
    user_id: str = "auditor"
    notes: Optional[str] = None


class VerificationResponse(BaseModel):
    """Schema for returning verification record."""

    id: str
    tree_id: str
    action: str
    edited_geometry_geojson: Optional[str] = None
    user_id: str
    notes: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
