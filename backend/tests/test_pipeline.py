"""Integration test for raster upload and background analysis pipeline."""

from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.tree import Tree
from app.api.jobs import run_survey_analysis_pipeline


@pytest.fixture
def test_geotiff_path(tmp_path: Path) -> Path:
    """Creates a small 512x512 GeoTIFF with synthetic green tree clusters."""
    file_path = tmp_path / "survey_test.tif"
    height, width = 512, 512
    transform = from_origin(76.5, 11.2, 0.00001, 0.00001)

    r = np.full((height, width), 50, dtype=np.uint8)
    g = np.full((height, width), 160, dtype=np.uint8)
    b = np.full((height, width), 60, dtype=np.uint8)

    # Add tree cluster
    g[150:220, 150:220] = 240

    with rasterio.open(
        file_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=3,
        dtype=np.uint8,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(np.stack([r, g, b]))

    return file_path


def test_upload_and_job_execution(
    client: TestClient,
    db_session: Session,
    test_geotiff_path: Path,
):
    """Tests project creation, file upload, job enqueuing, and pipeline execution."""
    # 1. Create Project
    p_res = client.post("/projects", json={"name": "Pipeline Integration Project"})
    assert p_res.status_code == 201
    project_id = p_res.json()["data"]["id"]

    # 2. Upload Raster
    with test_geotiff_path.open("rb") as f:
        files = {"file": ("survey_test.tif", f, "image/tiff")}
        data = {
            "project_id": project_id,
            "forest_type": "tropical_moist",
            "capture_date": "2026-10-08",
        }
        u_res = client.post("/upload", files=files, data=data)

    assert u_res.status_code == 201
    survey_data = u_res.json()["data"]
    assert "id" in survey_data
    survey_id = survey_data["id"]
    assert survey_data["image_width"] == 512

    # 3. Create Analysis Job
    j_res = client.post("/jobs", json={"survey_id": survey_id})
    assert j_res.status_code == 202
    job_id = j_res.json()["data"]["id"]

    # 4. Check Job status endpoint (TestClient runs background_tasks automatically)

    # 5. Check Job status endpoint
    status_res = client.get(f"/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()["data"]
    assert job_data["status"] == "completed"
    assert job_data["progress"] == 100

    # 6. Verify detected Tree records exist in DB
    trees = db_session.query(Tree).filter(Tree.survey_id == survey_id).all()
    assert len(trees) > 0
    for tree in trees:
        assert tree.crown_area_sqm > 0
        assert tree.dbh_cm is not None
        assert tree.carbon_kg is not None
        assert tree.data_source == "synthetic"
