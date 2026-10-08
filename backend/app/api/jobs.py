"""Background processing and analysis job API endpoints."""

import uuid
from typing import List
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shapely.geometry import box, Polygon
import rasterio

from app.config import settings
from app.database import get_db, SessionLocal
from app.models.survey import Survey
from app.models.job import Job
from app.models.tree import Tree
from app.schemas.common import ResponseEnvelope
from app.schemas.job import JobCreate, JobResponse
from app.services.tiling import generate_tiles, inspect_raster
from app.services.inference import run_tile_inference
from app.services.instances import WatershedInstanceHead
from app.services.stitching import stitch_and_deduplicate
from app.services.registry import create_tree_record
from app.core.security import verify_api_key
from app.core.logging import logger

router = APIRouter(prefix="/jobs", tags=["Jobs & Processing"])


def run_survey_analysis_pipeline(job_id: str, survey_id: str, db: Optional[Session] = None) -> None:
    """Executes the complete tree crown detection pipeline in a background thread."""
    owns_db = False
    if db is None:
        db = SessionLocal()
        owns_db = True
    try:
        job = db.query(Job).filter(Job.id == job_id).first()

        if not job:
            return

        job.status = "processing"
        job.progress = 10
        db.commit()

        survey = db.query(Survey).filter(Survey.id == survey_id).first()
        if not survey:
            job.status = "failed"
            job.error = f"Survey {survey_id} not found."
            db.commit()
            return

        file_path = survey.file_path
        crs = survey.crs
        resolution_m = survey.resolution_m or 0.1
        forest_type = survey.forest_type

        # Inspect dataset master transform
        with rasterio.open(file_path) as src:
            master_transform = src.transform

        logger.info(f"Starting background detection pipeline for Survey {survey_id} on {file_path}")

        # 1. Windowed Tiling + Inference
        candidate_polys: List[Polygon] = []
        candidate_confs: List[float] = []
        candidate_synths: List[bool] = []

        watershed_head = WatershedInstanceHead()

        tiles = list(generate_tiles(file_path, tile_size=512, overlap_pct=0.20))
        total_tiles = max(1, len(tiles))

        for idx, tile in enumerate(tiles):
            tile_detections = run_tile_inference(tile)

            for det in tile_detections:
                gx_min, gy_min, gx_max, gy_max = det.global_bbox
                bbox_poly = box(gx_min, gy_min, gx_max, gy_max)
                candidate_polys.append(bbox_poly)
                candidate_confs.append(det.confidence)
                candidate_synths.append(det.is_synthetic)


            # Update progress between 10% and 65%
            current_progress = 10 + int(55 * (idx + 1) / total_tiles)
            job.progress = current_progress
            db.commit()

        logger.info(f"Extracted {len(candidate_polys)} candidate crowns across {total_tiles} tiles.")
        job.progress = 75
        db.commit()

        # 2. Polygon NMS Deduplication & Real-world GPS Transformation
        stitched_trees = stitch_and_deduplicate(
            pixel_polygons=candidate_polys,
            confidences=candidate_confs,
            synthetic_flags=candidate_synths,
            raster_transform=master_transform,
            crs=crs,
            resolution_m=resolution_m,
            iou_threshold=0.35,
        )

        logger.info(f"Surviving crowns after Polygon NMS: {len(stitched_trees)}")
        job.progress = 85
        db.commit()

        # 3. Create persistent Tree records in SQLite
        # Remove any previous detection runs for this survey
        db.query(Tree).filter(Tree.survey_id == survey_id).delete()
        db.commit()

        # Deduplicate tree records by tree_id to ensure unique primary keys
        seen_ids = set()
        tree_records = []
        for st in stitched_trees:
            rec = create_tree_record(survey_id=survey_id, stitched=st, forest_type=forest_type)
            if rec.tree_id not in seen_ids:
                seen_ids.add(rec.tree_id)
                tree_records.append(rec)

        db.bulk_save_objects(tree_records)
        job.progress = 100
        job.status = "completed"
        db.commit()

        logger.info(f"Pipeline finished successfully for Survey {survey_id}. Registered {len(tree_records)} trees.")

    except Exception as exc:
        logger.error(f"Pipeline error on Job {job_id}: {exc}", exc_info=True)
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if job:
                job.status = "failed"
                job.error = str(exc)
                db.commit()
        except Exception:
            pass
    finally:
        if owns_db:
            db.close()


@router.post(
    "",
    response_model=ResponseEnvelope[JobResponse],
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(verify_api_key)],
)
def create_analysis_job(
    payload: JobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Enqueues an analysis job for a registered aerial survey."""
    survey = db.query(Survey).filter(Survey.id == payload.survey_id).first()
    if not survey:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Survey with ID '{payload.survey_id}' not found.",
        )

    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        survey_id=payload.survey_id,
        job_type="detection",
        status="queued",
        progress=0,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background task via FastAPI BackgroundTasks
    background_tasks.add_task(run_survey_analysis_pipeline, job_id, payload.survey_id)

    return ResponseEnvelope(
        success=True,
        data=JobResponse.model_validate(job),
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )


@router.get(
    "/{job_id}",
    response_model=ResponseEnvelope[JobResponse],
    dependencies=[Depends(verify_api_key)],
)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Polls the status and progress of a background job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found.",
        )

    return ResponseEnvelope(
        success=True,
        data=JobResponse.model_validate(job),
        data_source="synthetic" if settings.MODEL_BACKEND == "mock" else "real",
    )
