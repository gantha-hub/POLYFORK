# VrikshaVision API Reference & Beginner Guide

Welcome to the **VrikshaVision: Tree Digital Twin** Backend API.

This document provides clear, plain-English explanations and copy-paste examples for every endpoint using both **Windows PowerShell (`Invoke-RestMethod`)** and **standard `curl`**.

---

## Quick Navigation
- [Base URL & Interactive Docs](#base-url--interactive-docs)
- [1. System Health (`/health`)](#1-system-health-health)
- [2. Project Management (`/projects`)](#2-project-management-projects)
- [3. Aerial Survey Upload (`/upload`)](#3-aerial-survey-upload-upload)
- [4. Processing Pipeline Jobs (`/jobs`)](#4-processing-pipeline-jobs-jobs)
- [5. Survey Inventory & Carbon Results (`/results`)](#5-survey-inventory--carbon-results-results)
- [6. Ground Audit Calibration & Uncertainty (`/calibration`)](#6-ground-audit-calibration--uncertainty-calibration)
- [7. Multi-Survey Change Detection (`/compare`)](#7-multi-survey-change-detection-compare)
- [8. Active Learning & Field Verification (`/verify`)](#8-active-learning--field-verification-verify)
- [9. Multi-Format Exports (`/export`)](#9-multi-format-exports-export)

---

## Base URL & Interactive Docs

- **Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Built-in Visual Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)

---

## 1. System Health (`/health`)

Checks if the server is running, reports which ML backend is active (`mock` or `torch`), and verifies SQLite database connectivity.

### Endpoint
`GET /health`

### Windows PowerShell Example
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```

### cURL Example
```bash
curl -X GET "http://127.0.0.1:8000/health"
```

### Example Response
```json
{
  "status": "healthy",
  "app": "VrikshaVision Backend",
  "model_backend": "mock",
  "database": "connected"
}
```

---

## 2. Project Management (`/projects`)

Projects group aerial surveys, ground calibration plots, and tree registries for a specific forest stand or conservation site.

### Create a Project
`POST /projects`

#### Windows PowerShell Example
```powershell
$body = @{
    name = "Western Ghats Stand A"
    description = "Wet evergreen forest canopy survey and biomass monitoring"
} | ConvertTo-Json

$project = Invoke-RestMethod -Uri "http://127.0.0.1:8000/projects" -Method Post -ContentType "application/json" -Body $body
$project.data.id
```

#### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "Western Ghats Stand A", "description": "Wet evergreen forest canopy survey and biomass monitoring"}'
```

### List All Projects
`GET /projects`

#### Windows PowerShell Example
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/projects" -Method Get
```

#### cURL Example
```bash
curl -X GET "http://127.0.0.1:8000/projects"
```

---

## 3. Aerial Survey Upload (`/upload`)

Uploads a multi-band GeoTIFF or high-resolution orthomosaic. The raster metadata (dimensions, CRS, geotransform bounds) is parsed and saved without reading large rasters into system RAM.

### Supported Forest Types
- `tropical_moist` (default, Chave pantropical allometry)
- `tropical_dry`
- `temperate_broadleaf`
- `temperate_conifer`
- `boreal`

### Endpoint
`POST /upload`

### Windows PowerShell Example
```powershell
$form = @{
    file = Get-Item "data\demo_aerial_tile.tif"
    project_id = "YOUR_PROJECT_ID"
    forest_type = "tropical_moist"
}
$survey = Invoke-RestMethod -Uri "http://127.0.0.1:8000/upload" -Method Post -Form $form
$survey.data.id
```

### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/upload" \
  -F "file=@data/demo_aerial_tile.tif" \
  -F "project_id=YOUR_PROJECT_ID" \
  -F "forest_type=tropical_moist"
```

---

## 4. Processing Pipeline Jobs (`/jobs`)

Initiates background computer vision analysis for an uploaded survey:
1. Windowed raster slicing ($512 \times 512$ with $20\%$ overlap).
2. Deep learning / synthetic inference (`mock` or `torch`).
3. Euclidean distance transform & marker-controlled watershed crown splitting.
4. Cross-tile Polygon Non-Maximum Suppression (NMS) stitching.
5. Allometric scaling from Crown Projection Area (CPA) to DBH, Biomass, and Carbon.
6. Deterministic spatial UUID tree registry generation.

### Start a Job
`POST /jobs`

#### Windows PowerShell Example
```powershell
$body = @{ survey_id = "YOUR_SURVEY_ID" } | ConvertTo-Json
$job = Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs" -Method Post -ContentType "application/json" -Body $body
$job.data.job_id
```

#### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/jobs" \
  -H "Content-Type: application/json" \
  -d '{"survey_id": "YOUR_SURVEY_ID"}'
```

### Check Job Status
`GET /jobs/{job_id}`

#### Windows PowerShell Example
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/jobs/YOUR_JOB_ID" -Method Get
```

#### cURL Example
```bash
curl -X GET "http://127.0.0.1:8000/jobs/YOUR_JOB_ID"
```

---

## 5. Survey Inventory & Carbon Results (`/results`)

Retrieves the complete stand-level tree enumeration, split-conformal prediction intervals, Monte Carlo carbon stock estimates, and tree geometry GeoJSON.

### Non-Negotiable Scientific Standards
- Every count includes an explicit prediction interval `[low, high]`.
- Every count includes `calibrated: true|false`.
- Every response reports `data_source: "synthetic"` when mock models are active.

### Get Survey Results
`GET /results/{survey_id}`

#### Windows PowerShell Example
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/results/YOUR_SURVEY_ID" -Method Get
```

#### cURL Example
```bash
curl -X GET "http://127.0.0.1:8000/results/YOUR_SURVEY_ID"
```

### Spatial Sub-Region Polygon Query
`POST /results/{survey_id}/region`

Filters stand trees to only those intersecting a specified boundary polygon.

#### Windows PowerShell Example
```powershell
$polygonGeoJSON = @{
    polygon = @{
        type = "Polygon"
        coordinates = @(
            @(
                @(76.540, 12.150),
                @(76.545, 12.150),
                @(76.545, 12.145),
                @(76.540, 12.145),
                @(76.540, 12.150)
            )
        )
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Uri "http://127.0.0.1:8000/results/YOUR_SURVEY_ID/region" -Method Post -ContentType "application/json" -Body $polygonGeoJSON
```

#### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/results/YOUR_SURVEY_ID/region" \
  -H "Content-Type: application/json" \
  -d '{
    "polygon": {
      "type": "Polygon",
      "coordinates": [[[76.540, 12.150], [76.545, 12.150], [76.545, 12.145], [76.540, 12.145], [76.540, 12.150]]]
    }
  }'
```

---

## 6. Ground Audit Calibration & Uncertainty (`/calibration`)

Calibrates aerial tree counts against ground truth field plots using Ratio Baseline or Negative Binomial Generalized Linear Models (GLM) with an offset of $\log(V)$.

> [!IMPORTANT]
> **Strict Scientific Refusal Rule**: The calibration model will **refuse to train** and return an HTTP 422 error if fewer than 10 ground truth plots ($N < 10$) are provided.

### 6.1 Upload Field Audit Plots
`POST /calibration/upload-plots`

Uploads a CSV file with columns: `plot_name`, `G` (ground count), `V` (visual aerial count), `canopy_cover`, `crown_area`, and `forest_type`.

#### Windows PowerShell Example
```powershell
$form = @{
    file = Get-Item "data\demo_ground_plots.csv"
    project_id = "YOUR_PROJECT_ID"
}
Invoke-RestMethod -Uri "http://127.0.0.1:8000/calibration/upload-plots" -Method Post -Form $form
```

#### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/calibration/upload-plots" \
  -F "file=@data/demo_ground_plots.csv" \
  -F "project_id=YOUR_PROJECT_ID"
```

### 6.2 Fit Calibration Model
`POST /calibration/fit/{project_id}`

Fits the statistical model and computes split-conformal non-conformity scores ($90\%$ coverage).

#### Windows PowerShell Example
```powershell
$body = @{
    method = "negbin_glm"
    confidence_level = 0.90
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/calibration/fit/YOUR_PROJECT_ID" -Method Post -ContentType "application/json" -Body $body
```

#### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/calibration/fit/YOUR_PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d '{"method": "negbin_glm", "confidence_level": 0.90}'
```

### 6.3 Get Calibration Model Status
`GET /calibration/status/{project_id}`

Returns model coefficient $\beta$, dispersion parameter $\alpha$, and empirical coverage percentage.

#### Windows PowerShell Example
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/calibration/status/YOUR_PROJECT_ID" -Method Get
```

#### cURL Example
```bash
curl -X GET "http://127.0.0.1:8000/calibration/status/YOUR_PROJECT_ID"
```

---

## 7. Multi-Survey Change Detection (`/compare`)

Performs spatial bipartite matching between two surveys ($T_1$ baseline and $T_2$ follow-up) across time. Classifies individual trees into four audit categories:
- `new`: Ingrowth trees appearing in $T_2$ that were not in $T_1$.
- `lost`: Deforested or fallen trees present in $T_1$ but absent in $T_2$.
- `grown`: Matched trees whose crown area expanded by $>15\%$.
- `unchanged`: Matched trees with stable crown canopy area.

### Endpoint
`POST /compare`

### Windows PowerShell Example
```powershell
$body = @{
    survey_t1_id = "SURVEY_BASELINE_ID"
    survey_t2_id = "SURVEY_FOLLOWUP_ID"
    distance_threshold_m = 5.0
    growth_threshold_pct = 15.0
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/compare" -Method Post -ContentType "application/json" -Body $body
```

### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/compare" \
  -H "Content-Type: application/json" \
  -d '{
    "survey_t1_id": "SURVEY_BASELINE_ID",
    "survey_t2_id": "SURVEY_FOLLOWUP_ID",
    "distance_threshold_m": 5.0,
    "growth_threshold_pct": 15.0
  }'
```

---

## 8. Active Learning & Field Verification (`/verify`)

Ranks detected tree crowns by uncertainty (low detection confidence, ambiguous boundary watershed lines, and unusually large/small crown areas) to generate a prioritized queue for ground validation.

### 8.1 Fetch Active Learning Queue
`GET /verify/queue/{survey_id}`

#### Windows PowerShell Example
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/verify/queue/YOUR_SURVEY_ID?limit=10" -Method Get
```

#### cURL Example
```bash
curl -X GET "http://127.0.0.1:8000/verify/queue/YOUR_SURVEY_ID?limit=10"
```

### 8.2 Submit Field Verification Action
`POST /verify/{tree_id}`

Actions supported:
- `confirm`: Tree is verified as present and valid.
- `reject`: False positive detection; pruned from inventory.
- `adjust_crown`: Field team measured true crown boundary.

#### Windows PowerShell Example
```powershell
$body = @{
    action = "confirm"
    notes = "Audited on-site via laser rangefinder"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/verify/YOUR_TREE_ID" -Method Post -ContentType "application/json" -Body $body
```

#### cURL Example
```bash
curl -X POST "http://127.0.0.1:8000/verify/YOUR_TREE_ID" \
  -H "Content-Type: application/json" \
  -d '{"action": "confirm", "notes": "Audited on-site via laser rangefinder"}'
```

---

## 9. Multi-Format Exports (`/export`)

Exports complete survey records in GIS GeoJSON, tabular CSV, or audit-ready executive PDF report.

### Export Formats
- `geojson`: Returns standard `FeatureCollection` polygon crowns with all biometric properties.
- `csv`: Returns downloadable tabular CSV with tree coordinates, crown area, DBH, biomass, and carbon.
- `pdf`: Returns an executive audit PDF containing stand summaries, methodology disclosures, and a semi-transparent diagonal `"SYNTHETIC DATA DEMO"` watermark when synthetic models are used.

### Endpoint
`GET /export/{survey_id}?format=geojson|csv|pdf`

### 9.1 Download GeoJSON
#### Windows PowerShell
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/export/YOUR_SURVEY_ID?format=geojson" -OutFile "forest_trees.geojson"
```
#### cURL
```bash
curl -X GET "http://127.0.0.1:8000/export/YOUR_SURVEY_ID?format=geojson" -o forest_trees.geojson
```

### 9.2 Download CSV
#### Windows PowerShell
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/export/YOUR_SURVEY_ID?format=csv" -OutFile "forest_trees.csv"
```
#### cURL
```bash
curl -X GET "http://127.0.0.1:8000/export/YOUR_SURVEY_ID?format=csv" -o forest_trees.csv
```

### 9.3 Download Executive PDF Report
#### Windows PowerShell
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/export/YOUR_SURVEY_ID?format=pdf" -OutFile "audit_report.pdf"
```
#### cURL
```bash
curl -X GET "http://127.0.0.1:8000/export/YOUR_SURVEY_ID?format=pdf" -o audit_report.pdf
```
