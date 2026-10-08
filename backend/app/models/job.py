"""SQLAlchemy model for Background Job."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Job(Base):
    """Tracks background processing tasks for survey tiling and tree detection."""

    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    survey_id = Column(String(36), ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type = Column(String(64), default="detection", nullable=False)
    status = Column(String(32), default="queued", nullable=False, index=True)  # queued, processing, completed, failed
    progress = Column(Integer, default=0, nullable=False)  # 0 to 100 percentage
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    survey = relationship("Survey", back_populates="jobs")
