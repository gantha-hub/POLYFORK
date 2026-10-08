"""SQLAlchemy model for Ground Truth Plots."""

import uuid
from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class GroundPlot(Base):
    """Represents a measured ground plot used for calibration and validation."""

    __tablename__ = "ground_plots"

    plot_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    plot_name = Column(String(128), nullable=False)
    ground_count_G = Column(Integer, nullable=False)  # Ground audited true tree count
    visual_count_V = Column(Integer, nullable=False)  # Remote sensing / detected count
    canopy_cover_pct = Column(Float, nullable=False)  # 0.0 - 100.0%
    crown_area_sqm = Column(Float, nullable=False)    # Average or total crown area in m^2
    forest_type = Column(String(64), default="tropical_moist", nullable=False)
    geometry_geojson = Column(Text, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="ground_plots")
