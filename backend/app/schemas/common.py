"""Common response envelopes and measurement schemas."""

from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar("T")


class APIError(BaseModel):
    """Standardized error object."""

    code: str
    message: str
    details: Optional[Any] = None


class ResponseEnvelope(BaseModel, Generic[T]):
    """Standard API response envelope."""

    success: bool = True
    data: Optional[T] = None
    error: Optional[APIError] = None
    data_source: str = "synthetic"  # "synthetic" or "real"


class ConfidenceInterval(BaseModel):
    """Statistical confidence or prediction interval."""

    low: float = Field(..., description="Lower bound")
    high: float = Field(..., description="Upper bound")
    confidence_level: float = Field(default=0.90, description="e.g. 0.90 for 90% confidence")


class TreeCountResult(BaseModel):
    """Every count returned by the API includes interval and calibration status."""

    raw_count: int = Field(..., description="Direct detected tree count from computer vision")
    calibrated_count: float = Field(..., description="Calibrated count or raw count if uncalibrated")
    interval: ConfidenceInterval = Field(..., description="Prediction interval [low, high]")
    calibrated: bool = Field(..., description="True if calibrated using ground plots; False otherwise")


class CarbonEstimateResult(BaseModel):
    """Monte Carlo propagated carbon stock estimate."""

    mean_carbon_kg: float = Field(..., description="Expected aboveground carbon in kg C")
    mean_carbon_tonnes: float = Field(..., description="Expected aboveground carbon in metric tonnes")
    interval_kg: ConfidenceInterval = Field(..., description="90% Monte Carlo interval in kg")
    interval_tonnes: ConfidenceInterval = Field(..., description="90% Monte Carlo interval in tonnes")
    carbon_fraction: float = Field(default=0.47, description="Fraction of dry biomass that is carbon")
