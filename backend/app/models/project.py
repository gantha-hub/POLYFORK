"""SQLAlchemy model for Project."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    """Represents a forestry inventory or restoration monitoring project."""

    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    surveys = relationship("Survey", back_populates="project", cascade="all, delete-orphan")
    ground_plots = relationship("GroundPlot", back_populates="project", cascade="all, delete-orphan")
    calibration_models = relationship("CalibrationModel", back_populates="project", cascade="all, delete-orphan")
