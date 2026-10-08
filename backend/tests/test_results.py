"""Unit and integration tests for Survey Results and Spatial Region Queries."""

import io
from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from fastapi.testclient import TestClient
from shapely.geometry import box, mapping


@pytest.fixture
def small_geotiff(tmp_path: Path) -> Path:
    """Creates a 512x512 GeoTIFF for survey testing."""
    file_path = tmp_path / "survey_results_test.tif"
    height, width = 512, 512
    transform = from_origin(76.5, 11.2, 0.00001, 0.00001)

    r = np.full((height, width), 40, dtype=np.uint8)
    g = np.full((height, width), 160, dtype=np.uint8)
    b = np.full((height, width), 50, dtype=np.uint8)

    # Add tree cluster in upper-left quadrant
    g[50:150, 50:150] = 245
    # Add another cluster in lower-right quadrant
    g[350:450, 350:450] = 240

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


def test_get_survey_results_uncalibrated_and_calibrated(
    client: TestClient,
    small_geotiff: Path,
):
    """Tests GET /results/{survey_id} transitioning from uncalibrated to calibrated."""
    # 1. Create Project and upload survey
    p_res = client.post("/projects", json={"name": "Results Test Project"})
    project_id = p_res.json()["data"]["id"]

    with small_geotiff.open("rb") as f:
        u_res = client.post(
            "/upload",
            files={"file": ("res.tif", f, "image/tiff")},
            data={"project_id": project_id, "forest_type": "tropical_moist"},
        )
    survey_id = u_res.json()["data"]["id"]

    # Run analysis job
    client.post("/jobs", json={"survey_id": survey_id})

    # 2. Query Results BEFORE Calibration
    res_before = client.get(f"/results/{survey_id}")
    assert res_before.status_code == 200
    data_before = res_before.json()["data"]

    # Critical non-negotiable checks
    assert data_before["count"]["calibrated"] is False
    assert data_before["count"]["interval"]["low"] <= data_before["count"]["raw_count"]
    assert data_before["carbon"]["mean_carbon_kg"] > 0
    assert data_before["carbon"]["interval_kg"]["low"] < data_before["carbon"]["mean_carbon_kg"]
    assert data_before["data_source"] == "synthetic"
    assert data_before["geojson"] is not None
    assert len(data_before["geojson"]["features"]) > 0

    # 3. Fit Calibration with 12 plots
    rows = [f"Plot_{i},{30 + i * 5},{int((30 + i * 5) * 0.9)},65.0,25.0,tropical_moist" for i in range(1, 13)]
    csv_str = "plot_name,G,V,canopy_cover,crown_area,forest_type\n" + "\n".join(rows)
    client.post(
        "/calibration/plots",
        files={"file": ("plots.csv", io.BytesIO(csv_str.encode()), "text/csv")},
        data={"project_id": project_id},
    )
    client.post("/calibration/fit", json={"project_id": project_id, "method": "ratio"})

    # 4. Query Results AFTER Calibration
    res_after = client.get(f"/results/{survey_id}")
    assert res_after.status_code == 200
    data_after = res_after.json()["data"]

    # Must now be calibrated
    assert data_after["count"]["calibrated"] is True
    assert data_after["count"]["interval"]["low"] < data_after["count"]["interval"]["high"]


def test_spatial_region_query(
    client: TestClient,
    small_geotiff: Path,
):
    """Tests sub-region spatial query filtering trees inside a user polygon."""
    p_res = client.post("/projects", json={"name": "Region Query Project"})
    project_id = p_res.json()["data"]["id"]

    with small_geotiff.open("rb") as f:
        u_res = client.post(
            "/upload",
            files={"file": ("reg.tif", f, "image/tiff")},
            data={"project_id": project_id, "forest_type": "tropical_moist"},
        )
    survey_id = u_res.json()["data"]["id"]
    client.post("/jobs", json={"survey_id": survey_id})

    # Fetch total survey results
    full_res = client.get(f"/results/{survey_id}").json()["data"]
    total_trees = full_res["total_trees_detected"]
    assert total_trees > 0

    # Query bounding only the top-left area in EPSG:4326 coords
    # Image origin is 76.5, 11.2, pixel size 0.00001
    poly_top_left = box(76.5, 11.2 - (250 * 0.00001), 76.5 + (250 * 0.00001), 11.2)
    poly_geom = mapping(poly_top_left)

    region_res = client.post(
        f"/results/{survey_id}/region",
        json={"polygon": poly_geom},
    )
    assert region_res.status_code == 200
    reg_data = region_res.json()["data"]

    # Sub-region count must be <= total trees
    assert reg_data["total_trees_detected"] <= total_trees
    assert reg_data["count"]["raw_count"] == reg_data["total_trees_detected"]
    assert reg_data["carbon"]["mean_carbon_kg"] >= 0
