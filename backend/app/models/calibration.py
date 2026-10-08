"""SQLAlchemy model for Calibration Models."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class CalibrationModel(Base):
    """Stores fitted calibration model parameters and conformal uncertainty quantiles."""

    __tablename__ = "calibration_models"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String(64), nullable=False)  # "ratio" or "negbin_glm"
    params_json = Column(Text, nullable=False)   # Serialized model coefficients / scaling factors
    residual_quantile_q = Column(Float, nullable=False)  # 90% conformal quantile margin
    coverage = Column(Float, nullable=False)     # Empirical coverage on validation split
    n_plots = Column(Integer, nullable=False)    # Number of ground plots used
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="calibration_models")
