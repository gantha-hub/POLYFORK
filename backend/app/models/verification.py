"""SQLAlchemy model for Field Verifications / Active Learning."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Verification(Base):
    """Tracks field audits and manual verifications of individual tree crowns."""

    __tablename__ = "verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tree_id = Column(String(64), ForeignKey("trees.tree_id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # "accept", "reject", "edit"
    edited_geometry_geojson = Column(Text, nullable=True)
    user_id = Column(String(128), default="auditor", nullable=False)
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    tree = relationship("Tree", back_populates="verifications")
