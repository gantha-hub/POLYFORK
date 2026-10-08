"""Unit tests for Calibration service and split-conformal prediction intervals."""

import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.ground_plot import GroundPlot
from app.services.calibration import (
    GroundPlotData,
    validate_plot_count,
    fit_ratio_baseline,
    fit_negbin_glm,
)
from app.services.uncertainty import (
    compute_conformal_quantile,
    evaluate_empirical_coverage,
    build_conformal_interval,
)


def test_refuse_calibration_with_fewer_than_10_plots(client: TestClient):
    """Verifies strict refusal with HTTP 422 when fewer than 10 ground plots are provided."""
    # 1. Create project
    p_res = client.post("/projects", json={"name": "Small Audit Project"})
    project_id = p_res.json()["data"]["id"]

    # 2. Upload only 5 plots
    csv_content = """plot_name,G,V,canopy_cover,crown_area,forest_type
Plot_1,45,40,65.0,25.0,tropical_moist
Plot_2,50,48,70.0,30.0,tropical_moist
Plot_3,30,28,55.0,20.0,tropical_moist
Plot_4,60,55,80.0,35.0,tropical_moist
Plot_5,40,38,60.0,22.0,tropical_moist
"""
    files = {"file": ("plots.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    u_res = client.post("/calibration/plots", files=files, data={"project_id": project_id})
    assert u_res.status_code == 201

    # 3. Attempt to fit model -> must refuse with 422
    fit_res = client.post("/calibration/fit", json={"project_id": project_id, "method": "negbin_glm"})
    assert fit_res.status_code == 422
    err_body = fit_res.json()
    assert err_body["success"] is False
    assert err_body["error"]["code"] == "INSUFFICIENT_DATA"
    assert "at least 10" in err_body["error"]["message"].lower()


def test_fit_ratio_and_negbin_with_12_plots(client: TestClient):
    """Verifies successful calibration and conformal intervals when N >= 10 plots exist."""
    # 1. Create project
    p_res = client.post("/projects", json={"name": "Adequate Audit Project"})
    project_id = p_res.json()["data"]["id"]

    # 2. Upload 12 ground audit plots
    rows = []
    for i in range(1, 13):
        g = 30 + i * 5
        v = int(g * 0.90)  # Systematic 10% undercount
        cc = 50.0 + (i * 2.5)
        ca = 15.0 + (i * 1.5)
        rows.append(f"Plot_{i},{g},{v},{cc},{ca},tropical_moist")

    csv_data = "plot_name,G,V,canopy_cover,crown_area,forest_type\n" + "\n".join(rows)
    files = {"file": ("plots_12.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")}
    client.post("/calibration/plots", files=files, data={"project_id": project_id})

    # 3. Fit Ratio Baseline
    ratio_res = client.post("/calibration/fit", json={"project_id": project_id, "method": "ratio"})
    assert ratio_res.status_code == 200
    ratio_data = ratio_res.json()["data"]
    assert ratio_data["calibrated"] is True
    assert ratio_data["method"] == "ratio"
    assert ratio_data["residual_quantile_q"] > 0

    # 4. Fit Negative Binomial GLM
    glm_res = client.post("/calibration/fit", json={"project_id": project_id, "method": "negbin_glm"})
    assert glm_res.status_code == 200
    glm_data = glm_res.json()["data"]
    assert glm_data["calibrated"] is True
    assert glm_data["method"] == "negbin_glm"
    assert "coefficients" in glm_data["params"]
    assert glm_data["n_plots"] == 12

    # 5. Check Calibration Status
    status_res = client.get(f"/calibration/status/{project_id}")
    assert status_res.status_code == 200
    status_data = status_res.json()["data"]
    assert status_data["calibrated"] is True
    assert status_data["n_plots"] == 12


def test_conformal_uncertainty_quantiles():
    """Unit tests for finite-sample split-conformal quantile computation and intervals."""
    import numpy as np

    y_true = np.array([50.0, 60.0, 70.0, 80.0, 90.0, 100.0, 110.0, 120.0, 130.0, 140.0])
    y_pred = np.array([48.0, 62.0, 69.0, 84.0, 88.0, 103.0, 108.0, 122.0, 127.0, 142.0])

    q = compute_conformal_quantile(y_true, y_pred, alpha=0.10)
    assert q > 0

    low, high = build_conformal_interval(100.0, q)
    assert low < 100.0 < high
    assert (high - 100.0) == pytest.approx(q, abs=0.2)

    cov = evaluate_empirical_coverage(y_true, y_pred, quantile_q=q)
    assert cov >= 0.85
