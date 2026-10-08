"""Project management API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.project import Project
from app.models.survey import Survey
from app.schemas.common import ResponseEnvelope
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.survey import SurveyResponse
from app.core.security import verify_api_key

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ResponseEnvelope[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Creates a new forestry inventory project."""
    project = Project(
        name=payload.name,
        description=payload.description,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    return ResponseEnvelope(
        success=True,
        data=ProjectResponse.model_validate(project),
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )


@router.get(
    "",
    response_model=ResponseEnvelope[List[ProjectResponse]],
    dependencies=[Depends(verify_api_key)],
)
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lists existing projects with pagination."""
    projects = db.query(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit).all()
    project_responses = [ProjectResponse.model_validate(p) for p in projects]

    return ResponseEnvelope(
        success=True,
        data=project_responses,
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )


@router.get(
    "/{project_id}",
    response_model=ResponseEnvelope[ProjectResponse],
    dependencies=[Depends(verify_api_key)],
)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieves a single project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    return ResponseEnvelope(
        success=True,
        data=ProjectResponse.model_validate(project),
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )


@router.get(
    "/{project_id}/surveys",
    response_model=ResponseEnvelope[List[SurveyResponse]],
    dependencies=[Depends(verify_api_key)],
)
def list_project_surveys(project_id: str, db: Session = Depends(get_db)):
    """Lists all surveys registered under a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    surveys = (
        db.query(Survey)
        .filter(Survey.project_id == project_id)
        .order_by(Survey.created_at.desc())
        .all()
    )
    survey_responses = [SurveyResponse.model_validate(s) for s in surveys]

    return ResponseEnvelope(
        success=True,
        data=survey_responses,
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )
