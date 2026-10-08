"""SQLAlchemy model for Tree."""

import uuid
from sqlalchemy import Column, String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


class Tree(Base):
    """Represents an individual detected or verified tree crown."""

    __tablename__ = "trees"

    tree_id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    survey_id = Column(String(36), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    geometry_geojson = Column(Text, nullable=False)  # GeoJSON representation of crown polygon
    centroid_x = Column(Float, nullable=False, index=True)  # Longitude or projected X
    centroid_y = Column(Float, nullable=False, index=True)  # Latitude or projected Y
    crown_area_sqm = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    dbh_cm = Column(Float, nullable=True)
    biomass_kg = Column(Float, nullable=True)
    carbon_kg = Column(Float, nullable=True)
    status = Column(String(32), default="detected", nullable=False)  # detected, verified, rejected, edited
    data_source = Column(String(32), default="synthetic", nullable=False)  # synthetic or real
    notes = Column(Text, nullable=True)

    # Composite Index for spatial lookup
    __table_args__ = (
        Index("ix_trees_spatial", "survey_id", "centroid_x", "centroid_y"),
    )

    # Relationships
    survey = relationship("Survey", back_populates="trees")
    verifications = relationship("Verification", back_populates="tree", cascade="all, delete-orphan")
