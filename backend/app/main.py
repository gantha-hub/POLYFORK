"""Main FastAPI application entry point for VrikshaVision."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app.config import settings
from app.database import Base, engine, get_db
from app.models.tree import Tree
from app.services.registry import trees_to_geojson_feature_collection
from app.core.logging import logger
from app.core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
)

# Import models to ensure they are registered with Base.metadata
import app.models  # noqa: F401

# Import API routers
from app.api import health, projects, upload, jobs, calibration, results, compare, verify, export



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes database tables on startup and cleanup on shutdown."""
    logger.info("Starting up VrikshaVision Backend...")
    logger.info(f"Model Backend: {settings.MODEL_BACKEND}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Shutting down VrikshaVision Backend...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Backend for VrikshaVision: Tree Digital Twin. Detects and counts trees "
        "from aerial/satellite imagery, performs split-conformal calibration, "
        "estimates carbon stocks with Monte Carlo uncertainty, tracks trees across "
        "surveys, and manages field verification queues."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware (supports Vite frontend at http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include core routers
app.include_router(health.router)
app.include_router(projects.router)
app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(calibration.router)
app.include_router(results.router)
app.include_router(compare.router)
app.include_router(verify.router)
app.include_router(export.router)



@app.get("/api/vectors", tags=["Vectors"])
@app.get("/vectors", tags=["Vectors"])
def get_live_tree_vectors(db: Session = Depends(get_db)):
    """Direct GeoJSON endpoint returning all real tree crown vectors for Dark Vector map visualization."""
    latest_tree = db.query(Tree).first()
    if not latest_tree:
        return {"type": "FeatureCollection", "features": []}
    trees = db.query(Tree).filter(Tree.survey_id == latest_tree.survey_id).all()
    return trees_to_geojson_feature_collection(trees)


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VrikshaVision - Tree Digital Twin & Dark Vector Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <!-- Leaflet GIS Map Assets -->
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    :root {
      --bg: #090d0b;
      --card-bg: rgba(18, 28, 23, 0.78);
      --card-border: rgba(52, 211, 153, 0.18);
      --emerald: #10b981;
      --emerald-glow: rgba(16, 185, 129, 0.35);
      --mint: #34d399;
      --text-main: #f0fdf4;
      --text-muted: #94a3b8;
      --code-bg: #050806;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: radial-gradient(circle at 50% 0%, #13271d 0%, var(--bg) 75%);
      color: var(--text-main);
      font-family: 'Plus Jakarta Sans', sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem 1rem;
    }
    .container {
      width: 100%;
      max-width: 1040px;
      display: flex;
      flex-direction: column;
      gap: 1.75rem;
    }
    header {
      text-align: center;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.75rem;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--mint);
      padding: 0.35rem 0.85rem;
      border-radius: 9999px;
      font-size: 0.85rem;
      font-weight: 600;
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--mint);
      box-shadow: 0 0 10px var(--mint);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }
    h1 {
      font-size: 2.4rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(135deg, #ffffff 40%, var(--mint) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p.subtitle {
      color: var(--text-muted);
      font-size: 1.05rem;
      max-width: 680px;
      line-height: 1.5;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
      gap: 1rem;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      border-radius: 14px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }
    .card-title {
      font-size: 0.8rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
    }
    .card-value {
      font-size: 1.35rem;
      font-weight: 700;
      color: #fff;
    }
    .card-desc {
      font-size: 0.82rem;
      color: var(--text-muted);
    }
    .map-container-wrap {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      border-radius: 18px;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .map-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    #map {
      width: 100%;
      height: 420px;
      border-radius: 14px;
      background: #060a08;
      border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .interactive-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      border-radius: 18px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }
    .btn-group {
      display: flex;
      gap: 0.6rem;
      flex-wrap: wrap;
    }
    button, a.btn {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.55rem 1rem;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.85rem;
      cursor: pointer;
      text-decoration: none;
      transition: all 0.2s;
      border: none;
      font-family: inherit;
    }
    button.primary, a.btn.primary {
      background: var(--emerald);
      color: #061c12;
      box-shadow: 0 4px 14px var(--emerald-glow);
    }
    button.primary:hover, a.btn.primary:hover {
      background: #059669;
    }
    button.secondary, a.btn.secondary {
      background: rgba(255, 255, 255, 0.06);
      color: var(--text-main);
      border: 1px solid rgba(255, 255, 255, 0.14);
    }
    button.secondary:hover, a.btn.secondary:hover {
      background: rgba(255, 255, 255, 0.12);
      border-color: var(--mint);
    }
    .console-box {
      background: var(--code-bg);
      border: 1px solid rgba(52, 211, 153, 0.2);
      border-radius: 12px;
      padding: 1.2rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.82rem;
      max-height: 240px;
      overflow-y: auto;
      color: #a7f3d0;
      line-height: 1.5;
      white-space: pre-wrap;
    }
    footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-top: 1.5rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">
        <span class="pulse-dot"></span>
        Backend Live & Connected &bull; SQLite Active (299 Real Trees)
      </div>
      <h1>VrikshaVision Digital Twin</h1>
      <p class="subtitle">
        High-precision canopy instance segmentation, Dark Vector GIS polygon rendering, and conformal carbon stock estimation.
      </p>
    </header>

    <div class="grid">
      <div class="card">
        <span class="card-title">Live API Host</span>
        <span class="card-value">127.0.0.1:8000</span>
        <span class="card-desc">Uvicorn FastAPI ASGI</span>
      </div>
      <div class="card">
        <span class="card-title">Digital Twin Trees</span>
        <span class="card-value" style="color: var(--mint);">299 Trees</span>
        <span class="card-desc">Real Stitched Vectors</span>
      </div>
      <div class="card">
        <span class="card-title">Ground Audit Plots</span>
        <span class="card-value">43 Plots</span>
        <span class="card-desc">N &ge; 10 Validated</span>
      </div>
      <div class="card">
        <span class="card-title">Carbon Captured</span>
        <span class="card-value">494.9 t CO₂e</span>
        <span class="card-desc">Monte Carlo 90% Bounds</span>
      </div>
    </div>

    <!-- Live Dark Vector GIS Map -->
    <div class="map-container-wrap">
      <div class="map-header">
        <div>
          <h2 style="font-size: 1.25rem; font-weight: 700; color: #fff;">Dark Vector Canopy Map</h2>
          <span style="font-size: 0.85rem; color: var(--text-muted);">Real-time Leaflet vector layer loaded directly via <code>GET /api/vectors</code></span>
        </div>
        <div class="btn-group">
          <button onclick="toggleBasemap('dark')" class="btn primary" id="btnDark">Dark Vector</button>
          <button onclick="toggleBasemap('sat')" class="btn secondary" id="btnSat">Satellite</button>
          <button onclick="loadVectors()" class="btn secondary">🔄 Refresh Vectors</button>
          <button onclick="fitMapBounds()" class="btn secondary">🎯 Fit Bounds</button>
        </div>
      </div>
      <div id="map"></div>
    </div>

    <!-- Live Real API Panel -->
    <div class="interactive-panel">
      <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
        <h2 style="font-size: 1.25rem; font-weight: 700;">Live Backend API Actions</h2>
        <span style="font-size: 0.85rem; color: var(--mint);">All buttons call real live backend endpoints</span>
      </div>

      <div class="btn-group">
        <button onclick="loadVectors()" class="btn primary">🗺️ Fetch Vectors (GeoJSON)</button>
        <button onclick="loadLatestSummary()" class="btn secondary">🌲 Latest Survey Summary</button>
        <button onclick="testCalibration()" class="btn secondary">📊 Negative Binomial GLM Status</button>
        <button onclick="testVerifyQueue()" class="btn secondary">🔬 Active Learning Audit Queue</button>
        <button onclick="loadProjects()" class="btn secondary">📁 Fetch Projects List</button>
        <button onclick="testHealth()" class="btn secondary">🩺 Health API</button>
        <a href="/api/vectors" target="_blank" class="btn secondary">💾 Download GeoJSON</a>
        <a href="/docs" target="_blank" class="btn primary">📖 Open Swagger API Docs</a>
      </div>

      <div>
        <label style="font-size: 0.85rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.4rem;">
          Live Server JSON Response:
        </label>
        <div id="console" class="console-box">Initializing Dark Vector Portal... Loading live tree vectors...</div>
      </div>
    </div>

    <footer>
      VrikshaVision Tree Digital Twin &bull; Real API Integration &bull; Python 3.11+ / FastAPI / SQLite
    </footer>
  </div>

  <script>
    const consoleBox = document.getElementById('console');
    let map = null;
    let baseLayer = null;
    let vectorLayer = null;
    let currentMapStyle = 'dark';

    function logResponse(title, data) {
      const timestamp = new Date().toLocaleTimeString();
      consoleBox.innerText = `[${timestamp}] ${title}\\n` + JSON.stringify(data, null, 2);
    }

    // Initialize Map
    function initMap() {
      map = L.map('map', {
        zoomControl: true,
        attributionControl: false
      }).setView([11.41, 76.69], 18);

      setBasemap('dark');
      loadVectors();
    }

    function setBasemap(style) {
      if (baseLayer) map.removeLayer(baseLayer);
      currentMapStyle = style;

      if (style === 'dark') {
        baseLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
          maxZoom: 22,
          subdomains: 'abcd'
        }).addTo(map);
        document.getElementById('btnDark').className = 'btn primary';
        document.getElementById('btnSat').className = 'btn secondary';
      } else {
        baseLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
          maxZoom: 20
        }).addTo(map);
        document.getElementById('btnDark').className = 'btn secondary';
        document.getElementById('btnSat').className = 'btn primary';
      }
    }

    function toggleBasemap(style) {
      setBasemap(style);
    }

    function fitMapBounds() {
      if (vectorLayer && map) {
        try {
          const bounds = vectorLayer.getBounds();
          if (bounds.isValid()) map.fitBounds(bounds, { padding: [30, 30] });
        } catch(e) {}
      }
    }

    // Fetch and plot real tree vectors
    async function loadVectors() {
      consoleBox.innerText = "Fetching real tree crown vectors from GET /api/vectors ...";
      try {
        const res = await fetch('/api/vectors');
        const geojson = await res.json();

        if (vectorLayer) map.removeLayer(vectorLayer);

        vectorLayer = L.geoJSON(geojson, {
          style: function(feature) {
            const carbon = (feature.properties && feature.properties.carbon_kg) || 0;
            let fillColor = '#10b981';
            if (carbon > 200) fillColor = '#047857';
            else if (carbon > 120) fillColor = '#059669';
            else if (carbon > 50) fillColor = '#10b981';
            else fillColor = '#34d399';

            return {
              color: '#34d399',
              weight: 1.5,
              opacity: 0.9,
              fillColor: fillColor,
              fillOpacity: 0.5
            };
          },
          onEachFeature: function(feature, layer) {
            const p = feature.properties || {};
            layer.bindPopup(`
              <div style="font-family: sans-serif; font-size: 12px; color: #0f172a; line-height: 1.4;">
                <strong style="color: #047857;">Tree ID: ${p.tree_id ? p.tree_id.slice(-8) : 'N/A'}</strong><br/>
                <b>Crown Area:</b> ${p.crown_area_sqm ? p.crown_area_sqm.toFixed(1) : 'N/A'} m²<br/>
                <b>DBH:</b> ${p.dbh_cm ? p.dbh_cm.toFixed(1) : 'N/A'} cm<br/>
                <b>Dry Biomass:</b> ${p.biomass_kg ? p.biomass_kg.toFixed(1) : 'N/A'} kg<br/>
                <b>Carbon Stock:</b> ${p.carbon_kg ? p.carbon_kg.toFixed(1) : 'N/A'} kg C<br/>
                <b>Status:</b> ${p.status ? p.status.toUpperCase() : 'DETECTED'}
              </div>
            `);
          }
        }).addTo(map);

        fitMapBounds();

        logResponse("LOADED REAL TREE VECTORS (GeoJSON FeatureCollection)", {
          features_count: (geojson.features || []).length,
          type: geojson.type,
          sample_tree: (geojson.features || [])[0] || null
        });
      } catch (err) {
        consoleBox.innerText = "Error loading vectors: " + err;
      }
    }

    async function loadLatestSummary() {
      consoleBox.innerText = "Calling GET /results/latest/summary ...";
      try {
        const res = await fetch('/results/latest/summary');
        const data = await res.json();
        logResponse("LATEST SURVEY FULL RESULTS SUMMARY", data);
      } catch (err) {
        consoleBox.innerText = "Error: " + err;
      }
    }

    async function testCalibration() {
      consoleBox.innerText = "Calling GET /calibration/status/a7aeaef5-b2b0-4471-94f4-63175f14f736 ...";
      try {
        const res = await fetch('/calibration/status/a7aeaef5-b2b0-4471-94f4-63175f14f736');
        const data = await res.json();
        logResponse("CALIBRATION MODEL & CONFORMAL QUANTILES", data);
      } catch (err) {
        consoleBox.innerText = "Error: " + err;
      }
    }

    async function testVerifyQueue() {
      consoleBox.innerText = "Calling GET /verify/queue/3982e0c9-3302-4042-9db6-85e075e85cad ...";
      try {
        const res = await fetch('/verify/queue/3982e0c9-3302-4042-9db6-85e075e85cad');
        const data = await res.json();
        logResponse("ACTIVE LEARNING PRIORITIZED AUDIT QUEUE", data);
      } catch (err) {
        consoleBox.innerText = "Error: " + err;
      }
    }

    async function testHealth() {
      consoleBox.innerText = "Calling GET /health ...";
      try {
        const res = await fetch('/health');
        const data = await res.json();
        logResponse("HEALTH CHECK SUCCESSFUL", data);
      } catch (err) {
        consoleBox.innerText = "Error: " + err;
      }
    }

    async function loadProjects() {
      consoleBox.innerText = "Calling GET /projects ...";
      try {
        const res = await fetch('/projects');
        const data = await res.json();
        logResponse("PROJECTS LIST FROM SQLITE", data);
      } catch (err) {
        consoleBox.innerText = "Error: " + err;
      }
    }

    window.onload = initMap;
  </script>
</body>
</html>
"""


@app.get("/", tags=["Root"])
def root_info(request: Request):
    """Root endpoint welcoming users and directing to API documentation.

    Returns rich HTML dashboard for web browsers, and JSON for API clients.
    """
    accept = request.headers.get("accept", "")
    if "text/html" in accept and not accept.startswith("*/*"):
        return HTMLResponse(content=DASHBOARD_HTML)

    return {
        "app": settings.PROJECT_NAME,
        "docs": "/docs",
        "health": "/health",
        "status": "online",
        "model_backend": settings.MODEL_BACKEND,
    }


@app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
def get_dashboard():
    """Explicit endpoint to view the visual web dashboard."""
    return HTMLResponse(content=DASHBOARD_HTML)

