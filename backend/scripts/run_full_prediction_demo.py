"""Executes an end-to-end live prediction and calibration pipeline, collecting all results and scores."""

import json
import time
from pathlib import Path
import urllib.request
import urllib.parse
import mimetypes


BASE_URL = "http://127.0.0.1:8000"


def make_request(url: str, method: str = "GET", data: dict = None, headers: dict = None):
    """Makes standard JSON HTTP request using urllib."""
    headers = headers or {}
    encoded_data = None
    if data is not None:
        headers["Content-Type"] = "application/json"
        encoded_data = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            res_body = response.read().decode("utf-8")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {err_body}")
        raise


def upload_multipart_file(url: str, file_path: Path, fields: dict):
    """Uploads file using standard multipart/form-data with urllib."""
    boundary = "----VrikshaVisionBoundary" + str(int(time.time()))
    body = bytearray()

    # Add regular text fields
    for name, value in fields.items():
        body.extend(f"--{boundary}\r\n".encode("utf-8"))
        body.extend(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        body.extend(f"{value}\r\n".encode("utf-8"))

    # Add file field
    filename = file_path.name
    body.extend(f"--{boundary}\r\n".encode("utf-8"))
    body.extend(f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode("utf-8"))
    body.extend(b"Content-Type: application/octet-stream\r\n\r\n")
    with open(file_path, "rb") as f:
        body.extend(f.read())
    body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode("utf-8"))

    req = urllib.request.Request(
        url,
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    root_dir = Path(__file__).resolve().parent.parent
    demo_geotiff = root_dir / "data" / "demo_aerial_tile.tif"
    demo_csv = root_dir / "data" / "demo_ground_plots.csv"

    print("=" * 70)
    print("VRIKSHAVISION: END-TO-END PREDICTION & CALIBRATION PIPELINE")
    print("=" * 70)

    # 1. Create Project
    print("\n[Step 1] Creating Forest Reserve Project...")
    p_res = make_request(
        f"{BASE_URL}/projects",
        method="POST",
        data={
            "name": "Western Ghats Stand - Live Verification",
            "description": "Comprehensive model prediction, segmentation, and calibration demonstration",
        },
    )
    project_id = p_res["data"]["id"]
    print(f"  ✓ Project ID: {project_id}")

    # 2. Upload Aerial GeoTIFF
    print("\n[Step 2] Uploading 1024x1024 Aerial GeoTIFF...")
    u_res = upload_multipart_file(
        f"{BASE_URL}/upload",
        demo_geotiff,
        {"project_id": project_id, "forest_type": "tropical_moist"},
    )
    survey_id = u_res["data"]["id"]
    print(f"  ✓ Survey ID: {survey_id}")
    print(f"  ✓ Raster Resolution: {u_res['data']['image_width']}x{u_res['data']['image_height']} px")
    print(f"  ✓ Forest Biome: {u_res['data']['forest_type']}")

    # 3. Trigger Background Analysis Pipeline
    print("\n[Step 3] Launching Windowed Tiling, Watershed & Allometry Job...")
    j_res = make_request(
        f"{BASE_URL}/jobs",
        method="POST",
        data={"survey_id": survey_id},
    )
    job_id = j_res["data"]["id"]
    print(f"  ✓ Job ID: {job_id}")

    # Poll for completion
    completed = False
    for i in range(60):
        status_res = make_request(f"{BASE_URL}/jobs/{job_id}")
        current_status = status_res["data"]["status"]
        progress_val = status_res["data"]["progress"]
        if current_status == "completed":
            print(f"  ✓ Pipeline Processing Complete (100%)!")
            completed = True
            break
        elif current_status == "failed":
            print(f"  ✗ Pipeline Job Failed: {status_res['data'].get('error')}")
            raise RuntimeError(f"Pipeline job failed: {status_res['data'].get('error')}")
        time.sleep(0.5)

    if not completed:
        raise TimeoutError(f"Job {job_id} timed out. Last status: {current_status}, progress: {progress_val}")

    # 4. Fetch Uncalibrated Results
    print("\n[Step 4] Fetching Initial Uncalibrated Predictions...")
    uncal_res = make_request(f"{BASE_URL}/results/{survey_id}")
    uncal_data = uncal_res["data"]

    # 5. Upload Ground Truth Calibration Plots
    print("\n[Step 5] Uploading 14 Field Audit Plots (Satisfies N >= 10 refusal rule)...")
    cal_upload = upload_multipart_file(
        f"{BASE_URL}/calibration/plots",
        demo_csv,
        {"project_id": project_id},
    )
    print(f"  ✓ {cal_upload['data']['imported_plots']} ground audit plots imported successfully")

    # 6. Fit Negative Binomial GLM & Conformal Prediction Intervals
    print("\n[Step 6] Fitting Negative Binomial GLM & Computing Conformal Non-Conformity Scores...")
    fit_res = make_request(
        f"{BASE_URL}/calibration/fit",
        method="POST",
        data={"project_id": project_id, "method": "negbin_glm", "confidence_level": 0.90},
    )
    fit_data = fit_res["data"]

    # 7. Fetch Calibration Status Details
    cal_status = make_request(f"{BASE_URL}/calibration/status/{project_id}")
    cal_meta = cal_status["data"]

    # 8. Fetch Calibrated Stand Results
    print("\n[Step 7] Fetching Final Calibrated Stand Results...")
    cal_res = make_request(f"{BASE_URL}/results/{survey_id}")
    cal_data = cal_res["data"]

    # 9. Fetch Active Learning Uncertainty Queue
    print("\n[Step 8] Querying Active Learning Priority Queue...")
    queue_res = make_request(f"{BASE_URL}/verify/queue/{survey_id}?limit=5")
    queue_trees = queue_res["data"]

    # 10. Generate PDF Report
    print("\n[Step 9] Generating Audit-Ready PDF Report...")
    pdf_req = urllib.request.Request(f"{BASE_URL}/export/{survey_id}?format=pdf")
    pdf_dest = root_dir / "data" / "Live_Demonstration_Report.pdf"
    with urllib.request.urlopen(pdf_req) as resp, open(pdf_dest, "wb") as f_out:
        f_out.write(resp.read())
    print(f"  ✓ Saved PDF Report: {pdf_dest} ({pdf_dest.stat().st_size:,} bytes)")

    # Output Complete Summary Package
    summary_output = {
        "project_id": project_id,
        "survey_id": survey_id,
        "uncalibrated_results": uncal_data,
        "calibration_model": cal_meta,
        "calibrated_results": cal_data,
        "active_learning_top_5": queue_trees,
    }

    results_file = root_dir / "data" / "live_prediction_summary.json"
    with open(results_file, "w") as f:
        json.dump(summary_output, f, indent=2)

    print(f"\n[+] Full raw results saved to: {results_file}")
    return summary_output


if __name__ == "__main__":
    main()
