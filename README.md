# 🌲 VrikshaVision: Tree Digital Twin

> **High-Precision Aerial Canopy Instance Segmentation, Split-Conformal Calibration, Allometric Carbon Quantification, and Multi-Temporal Stand Dynamics.**

[![GitHub Pages](https://img.shields.io/badge/Deployment-GitHub%20Pages-10b981.svg)](https://gantha-hub.github.io/POLYFORK/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/Frontend-React%2019-61dafb.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/Language-TypeScript-3178c6.svg)](https://www.typescriptlang.org)
[![Tests](https://img.shields.io/badge/Tests-33%20Passed-brightgreen.svg)]()

---

## 🌟 Overview

**VrikshaVision** is an end-to-end Tree Digital Twin observatory built for foresters, carbon auditors, and MRV (Measurement, Reporting, and Verification) practitioners. It ingests high-resolution drone orthomosaics, isolates individual tree canopy crowns via deep instance segmentation, scales crown geometry to stem diameter (DBH) and biomass, and delivers **statistically certified carbon stock intervals** using Split Conformal Prediction.

---

## 🚀 Live Demo & GitHub Pages Deployment

The frontend is deployed to GitHub Pages at:
👉 **[https://gantha-hub.github.io/POLYFORK/](https://gantha-hub.github.io/POLYFORK/)**

### How to Enable GitHub Pages in Repository Settings:
1. Go to your repository on GitHub: `https://github.com/gantha-hub/POLYFORK`
2. Click **Settings** (top tab).
3. On the left menu, click **Pages**.
4. Under **Build and deployment > Source**:
   * **Option A (Automated GitHub Actions - Recommended):** Select **GitHub Actions**. The included `.github/workflows/deploy.yml` will automatically build and publish the app.
   * **Option B (Direct Branch):** Select **Deploy from a branch**, choose `main` branch, and set folder to `/ (root)` or `/docs`. Click **Save**.

Your live app will be published immediately without showing the README!

---

## 🖥️ Running Locally (Windows PowerShell Instructions)

### Prerequisites
* **Python 3.10+** (Python 3.12 or 3.14 recommended)
* **Node.js 18+** (with npm)
* **Git**

---

### Step 1: Start the Backend (FastAPI)

Open a PowerShell terminal:

```powershell
# 1. Enter the backend directory
cd backend

# 2. Create and activate a Python virtual environment (first time only)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Start the FastAPI server on port 8000
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*The API will be running at `http://127.0.0.1:8000` with interactive Swagger docs at `http://127.0.0.1:8000/docs`.*

---

### Step 2: Start the Frontend (Vite + React)

Open a **second** PowerShell terminal:

```powershell
# 1. Enter the frontend directory
cd frontend

# 2. Install Node dependencies (first time only)
npm install

# 3. Start the Vite development server
npm run dev
```

*Open your browser at `http://127.0.0.1:5173` to explore the digital twin!*

---

## 🛠️ Observatory Architecture

```
POLYFORK/
├── .github/workflows/deploy.yml         # Automated GitHub Actions deployment to Pages
├── index.html                           # Root deployment entry point
├── docs/                                # GitHub Pages /docs fallback
├── backend/                             # FastAPI application & AI pipelines
│   ├── app/
│   │   ├── api/                         # 15 REST endpoints
│   │   │   ├── projects.py              # Project management & survey listing
│   │   │   ├── upload.py                # Orthomosaic ingestion & tiling
│   │   │   ├── jobs.py                  # Background AI job scheduler
│   │   │   ├── results.py               # GeoJSON polygons & spatial queries
│   │   │   ├── calibration.py           # Negative Binomial GLM & conformal quantiles
│   │   │   ├── compare.py               # Multi-temporal change detection
│   │   │   ├── verify.py                # Active learning queue & human audits
│   │   │   ├── export.py                # GeoJSON, CSV & PDF MRV reports
│   │   │   └── health.py                # Health & model diagnostic probes
│   │   ├── models/                      # DeepForest/YOLO wrappers & procedural synthetic engine
│   │   ├── schemas/                     # Pydantic v2 validation contracts
│   │   └── services/                    # Conformal prediction, tiling, watershed
│   └── tests/                           # 33 passing pytest test suites
└── frontend/                            # React 19 + TypeScript + Vite SPA
    ├── src/
    │   ├── api/client.ts                # Type-safe API client
    │   ├── context/ProjectContext.tsx   # Global reactive state
    │   ├── components/map/StandMap.tsx  # Leaflet vector GIS digital twin
    │   └── pages/                       # The 6 Observatory Views
    │       ├── MapPage.tsx              # Stand map & conformal KPI cards
    │       ├── SurveysPage.tsx          # Drone orthomosaic upload & job monitor
    │       ├── CalibrationPage.tsx      # Ground plot CSV calibration & GLM fitter
    │       ├── ComparePage.tsx          # Multi-temporal recruitment & mortality
    │       ├── VerifyPage.tsx           # Active learning human-in-the-loop queue
    │       └── ExportPage.tsx           # GeoJSON, CSV & PDF audit dossier exports
```

---

## 📊 Scientific Methodology

1. **Orthomosaic Tiling & Watershed Instance Separation**: Sliding-window windowed reads over large GeoTIFF rasters with non-maximum suppression (NMS) merging polygon boundaries.
2. **Pan-Tropical Allometric Scaling**: Individual crown areas $A$ are transformed into DBH and Aboveground Biomass ($AGB$) using IPCC Tier-3 equations:
   $$\ln(DBH) = \alpha + \beta \ln(A)$$
   $$Biomass = 0.0673 \times (\rho \times DBH^2 \times H)^{0.976}$$
3. **Distribution-Free Split Conformal Prediction**: Uses sample plot ground audits to guarantee $1 - \alpha$ coverage without assuming Gaussian errors:
   $$C(X) = \hat{Y}(X) \pm q_{1-\alpha}(R_i)$$
4. **Verra & Gold Standard Compliance**: Calculates conservative carbon credit baselines using the lower bound of the 90% confidence interval.

---

## 📜 License
MIT License. Free for academic research, forest conservancies, and carbon project developers.
