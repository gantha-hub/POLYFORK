"""SQLAlchemy model for Survey."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Survey(Base):
    """Represents an aerial or satellite raster survey run within a project."""

    __tablename__ = "surveys"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    original_filename = Column(String(255), nullable=False)
    crs = Column(String(64), nullable=True)  # e.g., "EPSG:4326" or "EPSG:32643"
    resolution_m = Column(Float, nullable=True)  # Ground sampling distance in meters
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    capture_date = Column(DateTime, nullable=True)
    forest_type = Column(String(64), default="tropical_moist", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    project = relationship("Project", back_populates="surveys")
    jobs = relationship("Job", back_populates="survey", cascade="all, delete-orphan")
    trees = relationship("Tree", back_populates="survey", cascade="all, delete-orphan")
