"""Unit and integration tests for Report Generation and Multi-Format Exports."""

from pathlib import Path
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from fastapi.testclient import TestClient

from app.schemas.common import ConfidenceInterval, TreeCountResult, CarbonEstimateResult
from app.schemas.tree import SurveyResultsSummary
from app.services.reports import generate_survey_pdf_report


@pytest.fixture
def test_geotiff(tmp_path: Path) -> Path:
    """Creates a 512x512 GeoTIFF for export integration testing."""
    file_path = tmp_path / "export_test.tif"
    height, width = 512, 512
    transform = from_origin(77.0, 12.0, 0.00001, 0.00001)

    r = np.full((height, width), 35, dtype=np.uint8)
    g = np.full((height, width), 160, dtype=np.uint8)
    b = np.full((height, width), 45, dtype=np.uint8)

    # Add tree clusters
    g[50:180, 50:180] = 245
    g[300:420, 300:420] = 240

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


def test_pdf_report_generation_synthetic(tmp_path: Path):
    """Verifies that PDF reports generate properly with synthetic watermark."""
    summary = SurveyResultsSummary(
        survey_id="test-survey-uuid-1234",
        forest_type="tropical_moist",
        data_source="synthetic",
        total_trees_detected=142,
        count=TreeCountResult(
            raw_count=142,
            calibrated_count=138.0,
            calibrated=True,
            interval=ConfidenceInterval(
                low=120.0,
                high=156.0,
                confidence_level=0.90,
            ),
        ),
        carbon=CarbonEstimateResult(
            mean_carbon_kg=45230.5,
            mean_carbon_tonnes=45.23,
            interval_kg=ConfidenceInterval(low=38100.0, high=52500.0, confidence_level=0.90),
            interval_tonnes=ConfidenceInterval(low=38.1, high=52.5, confidence_level=0.90),
            carbon_fraction=0.47,
        ),
        mean_crown_area_sqm=18.4,
        mean_dbh_cm=28.7,
    )

    pdf_out = tmp_path / "synthetic_report.pdf"
    result_path = generate_survey_pdf_report(
        summary=summary,
        output_path=pdf_out,
        project_name="Western Ghats Demo Reserve",
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 1000
    with open(result_path, "rb") as f:
        header = f.read(5)
        assert header == b"%PDF-"


def test_pdf_report_generation_real(tmp_path: Path):
    """Verifies that PDF reports generate properly for real model data."""
    summary = SurveyResultsSummary(
        survey_id="real-survey-uuid-9999",
        forest_type="temperate_broadleaf",
        data_source="real",
        total_trees_detected=85,
        count=TreeCountResult(
            raw_count=85,
            calibrated_count=85.0,
            calibrated=False,
            interval=ConfidenceInterval(
                low=68.0,
                high=102.0,
                confidence_level=0.90,
            ),
        ),
        carbon=CarbonEstimateResult(
            mean_carbon_kg=22100.0,
            mean_carbon_tonnes=22.1,
            interval_kg=ConfidenceInterval(low=18500.0, high=26000.0, confidence_level=0.90),
            interval_tonnes=ConfidenceInterval(low=18.5, high=26.0, confidence_level=0.90),
            carbon_fraction=0.48,
        ),
        mean_crown_area_sqm=14.2,
        mean_dbh_cm=22.1,
    )

    pdf_out = tmp_path / "real_report.pdf"
    result_path = generate_survey_pdf_report(
        summary=summary,
        output_path=pdf_out,
        project_name="Pacific Northwest Survey",
    )

    assert result_path.exists()
    assert result_path.stat().st_size > 1000


def test_export_endpoints_all_formats(client: TestClient, test_geotiff: Path):
    """Tests GET /export/{survey_id} across GeoJSON, CSV, and PDF formats."""
    # 1. Create project, upload survey, and process
    p_res = client.post("/projects", json={"name": "Export Test Stand"})
    assert p_res.status_code == 201
    project_id = p_res.json()["data"]["id"]

    with test_geotiff.open("rb") as f:
        u_res = client.post(
            "/upload",
            files={"file": ("export_test.tif", f, "image/tiff")},
            data={"project_id": project_id, "forest_type": "tropical_moist"},
        )
    assert u_res.status_code == 201
    survey_id = u_res.json()["data"]["id"]

    # Run processing job
    j_res = client.post("/jobs", json={"survey_id": survey_id})
    assert j_res.status_code == 202

    # 2. Test GeoJSON Export
    geo_res = client.get(f"/export/{survey_id}?format=geojson")
    assert geo_res.status_code == 200
    assert "geo+json" in geo_res.headers.get("content-type", "")
    geo_data = geo_res.json()
    assert geo_data["type"] == "FeatureCollection"
    assert "features" in geo_data
    assert len(geo_data["features"]) > 0

    first_feat = geo_data["features"][0]
    assert "geometry" in first_feat
    assert "properties" in first_feat
    assert "crown_area_sqm" in first_feat["properties"]
    assert "carbon_kg" in first_feat["properties"]

    # 3. Test CSV Export
    csv_res = client.get(f"/export/{survey_id}?format=csv")
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    csv_text = csv_res.text
    lines = csv_text.strip().split("\r\n") if "\r\n" in csv_text else csv_text.strip().split("\n")
    assert len(lines) >= 2
    header_cols = lines[0].split(",")
    assert "tree_id" in header_cols
    assert "crown_area_sqm" in header_cols
    assert "biomass_kg" in header_cols
    assert "carbon_kg" in header_cols

    # 4. Test PDF Export
    pdf_res = client.get(f"/export/{survey_id}?format=pdf")
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers.get("content-type", "")
    assert pdf_res.content[:5] == b"%PDF-"
    assert len(pdf_res.content) > 1000

    # 5. Test 404 on nonexistent survey
    bad_res = client.get("/export/nonexistent-survey-uuid?format=geojson")
    assert bad_res.status_code == 404
