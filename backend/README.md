# VrikshaVision: Tree Digital Twin (Backend)

An open-source, reproducible backend for detecting, enumerating, and calibrating tree crowns from aerial and satellite remote sensing imagery, calculating carbon stocks with Monte Carlo uncertainty propagation, tracking forest change across multi-temporal surveys, and maintaining an auditable digital twin tree registry.

---

## 🌟 Key Features
- **Zero Complex Infrastructure**: Runs 100% on standard Python 3.11+ and SQLite. No Docker, no Redis, no Celery, and no PostgreSQL needed.
- **Scientific Rigor**:
  - Split-conformal prediction intervals for tree counts ($90\%$ finite-sample coverage guarantee).
  - Negative Binomial GLM calibration with $\log(V)$ offset against field audit plots (**strictly refuses fitting with $< 10$ plots**).
  - Allometric carbon scaling ($CPA \to DBH \to AGB \to \text{Carbon}$) with 1,000-draw Monte Carlo uncertainty propagation.
- **Pluggable ML Architecture**:
  - `MockModel`: Runs instant procedural synthetic detections without GPU or training weights.
  - `TorchModel`: Loads deep learning weights from `weights/` with automatic CPU/CUDA fallback.
  - Strict audit provenance: All outputs explicitly flag `"data_source": "synthetic"|"real"` and `"calibrated": true|false`.
- **Canopy Instance Segmentation & Seam Stitching**:
  - Distance transform & marker-controlled watershed for splitting overlapping tree crowns.
  - Polygon Non-Maximum Suppression (Polygon NMS) to eliminate edge duplicates across tile boundaries.
- **Multi-Temporal Change Detection**:
  - Hungarian bipartite matching classifying stand dynamics into `new`, `lost`, `grown` ($>15\%$), and `unchanged`.
- **Active Learning Queue**:
  - Priority ranking for ground truth field audit teams targeting edge-ambiguous and high-uncertainty crowns.
- **Multi-Format Exports**:
  - GeoJSON GIS FeatureCollections, tabular CSV inventories, and executive PDF reports with diagonal `"SYNTHETIC DATA DEMO"` watermarks.

---

## 🚀 Beginner Quickstart (Windows PowerShell)

Follow these exact steps in your Windows PowerShell terminal:

### 1. Open PowerShell and Navigate to the Backend
```powershell
cd vrikshavision/backend
```

### 2. Create and Activate a Python Virtual Environment
A virtual environment keeps all libraries isolated so they do not conflict with other software on your PC.
```powershell
# Create the virtual environment folder named .venv
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1
```
*(If PowerShell shows a script execution policy error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then activate again).*

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
```powershell
Copy-Item .env.example .env
```

### 5. Generate Demo Demonstration Assets
Generate sample $1024 \times 1024$ aerial GeoTIFF and 14-plot field calibration CSV:
```powershell
python scripts/make_synthetic_demo.py
```
This automatically produces:
- `data/demo_aerial_tile.tif` (Multi-band GeoTIFF with EPSG:4326 georeferencing and realistic canopy clusters)
- `data/demo_ground_plots.csv` (14 field inventory audit plots satisfying the $N \ge 10$ calibration threshold)

### 6. Run the Test Suite
Ensure all 32 unit and integration tests pass:
```powershell
python -m pytest -v
```

### 7. Start the Backend Server
```powershell
python -m uvicorn app.main:app --reload --port 8000
```
or double-click `run_backend.bat`.

---

## 🧭 Interactive Web Interfaces

With the backend server running, open your web browser:
- **Visual Web Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard) (or [http://127.0.0.1:8000/](http://127.0.0.1:8000/))
- **Interactive Swagger API Explorer**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **System Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 🛠️ Complete End-to-End Walkthrough (PowerShell)

You can run an end-to-end forest inventory from PowerShell in under two minutes:

```powershell
# 1. Create a Project
$pBody = @{ name = "Western Ghats Forest Stand"; description = "Canopy twin demo" } | ConvertTo-Json
$proj = Invoke-RestMethod -Uri "http://127.0.0.1:8000/projects" -Method Post -ContentType "application/json" -Body $pBody
$projId = $proj.data.id

# 2. Upload Aerial GeoTIFF
$form = @{
    file = Get-Item "data\demo_aerial_tile.tif"
    project_id = $projId
    forest_type = "tropical_moist"
}
$survey = Invoke-RestMethod -Uri "http://127.0.0.1:8000/upload" -Method Post -Form $form
$surveyId = $survey.data.id

# 3. Trigger Background Analysis Pipeline
$jBody = @{ survey_id = $surveyId } | ConvertTo-Json
$job = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs" -Method Post -ContentType "application/json" -Body $jBody
Start-Sleep -Seconds 2

# 4. Upload Ground Calibration Plots & Fit Negative Binomial GLM
$calForm = @{
    file = Get-Item "data\demo_ground_plots.csv"
    project_id = $projId
}
Invoke-RestMethod -Uri "http://127.0.0.1:8000/calibration/upload-plots" -Method Post -Form $calForm

$fitBody = @{ method = "negbin_glm"; confidence_level = 0.90 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/calibration/fit/$projId" -Method Post -ContentType "application/json" -Body $fitBody

# 5. Fetch Calibrated Carbon and Tree Enumeration Results
$results = Invoke-RestMethod -Uri "http://127.0.0.1:8000/results/$surveyId" -Method Get
$results.data.count

# 6. Download Audit PDF Report (with diagonal synthetic watermark)
Invoke-WebRequest -Uri "http://127.0.0.1:8000/export/$surveyId?format=pdf" -OutFile "Stand_Audit_Report.pdf"
```

For detailed documentation on all endpoints and parameter options, refer to [docs/api.md](file:///Users/mallisanthosh/.gemini/antigravity-ide/scratch/vrikshavision/backend/docs/api.md).

---

## 📁 Repository Architecture

| Directory / File | Description |
| :--- | :--- |
| `app/config.py` | Pydantic-Settings configuration loading `.env` variables. |
| `app/database.py` | SQLite engine, sessionmaker, and database lifecycle management. |
| `app/core/logging.py` | Clean console logging format. |
| `app/core/errors.py` | Standardized custom exceptions and error envelopes. |
| `app/core/security.py` | Optional header API key verification (`X-API-Key`). |
| `app/models/` | SQLAlchemy 2.0 tables: `Project`, `Survey`, `Job`, `Tree`, `GroundPlot`, `CalibrationModel`, `Verification`. |
| `app/schemas/` | Pydantic v2 schemas: validation and response envelopes. |
| `app/api/` | FastAPI routers: `health`, `projects`, `upload`, `jobs`, `calibration`, `results`, `compare`, `verify`, `export`. |
| `app/ml_adapters/` | Detection backends: `base.py`, `mock_model.py` (synthetic), `torch_model.py` (PyTorch). |
| `app/services/tiling.py` | Memory-safe windowed tile generator ($512\times 512$, $20\%$ overlap) via `rasterio`. |
| `app/services/inference.py` | Tile detection runner mapping local coordinates to master georeferenced coordinates. |
| `app/services/instances.py` | Distance transform & marker-controlled watershed for splitting touching tree crowns. |
| `app/services/stitching.py` | Polygon Non-Maximum Suppression (Polygon NMS) and master Affine georeferencing. |
| `app/services/registry.py` | Deterministic spatial UUID generation and GeoJSON serialization. |
| `app/services/calibration.py` | Ratio and Negative Binomial GLM calibration with $\log(V)$ offset ($N \ge 10$ refusal rule). |
| `app/services/uncertainty.py` | Split-conformal prediction intervals ($[\hat{G}-q, \hat{G}+q]$) with empirical coverage reporting. |
| `app/services/carbon.py` | Allometric carbon scaling ($CPA \to DBH \to AGB \to \text{Carbon}$) with 1,000-draw Monte Carlo draws. |
| `app/services/change_detection.py` | Multi-survey Hungarian bipartite matching: `new`, `lost`, `grown` ($>15\%$), and `unchanged`. |
| `app/services/active_learning.py` | Active learning uncertainty queue ranking based on boundary and confidence metrics. |
| `app/services/reports.py` | ReportLab PDF generator with custom `WatermarkCanvas` for diagonal synthetic watermarks. |
| `scripts/make_synthetic_demo.py` | Procedural demo asset generator creating sample GeoTIFF and ground plot CSV. |
| `docs/api.md` | Comprehensive API documentation with curl and PowerShell commands. |
| `tests/` | 32 passing unit and integration tests covering all services and endpoints. |
| `config/carbon.yaml` | Biophysical allometric scaling constants per forest biome. |
