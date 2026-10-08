"""Main FastAPI application entry point for VrikshaVision."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
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



DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>VrikshaVision - Tree Digital Twin</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #090d0b;
      --card-bg: rgba(18, 28, 23, 0.7);
      --card-border: rgba(52, 211, 153, 0.15);
      --emerald: #10b981;
      --emerald-glow: rgba(16, 185, 129, 0.3);
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
      padding: 2.5rem 1rem;
    }
    .container {
      width: 100%;
      max-width: 980px;
      display: flex;
      flex-direction: column;
      gap: 2rem;
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
      font-size: 2.5rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      background: linear-gradient(135deg, #ffffff 40%, var(--mint) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    p.subtitle {
      color: var(--text-muted);
      font-size: 1.05rem;
      max-width: 650px;
      line-height: 1.5;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1.25rem;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      border-radius: 16px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      transition: transform 0.2s, border-color 0.2s;
    }
    .card:hover {
      transform: translateY(-2px);
      border-color: rgba(52, 211, 153, 0.35);
    }
    .card-title {
      font-size: 0.85rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
      font-weight: 600;
    }
    .card-value {
      font-size: 1.25rem;
      font-weight: 700;
      color: #fff;
    }
    .card-desc {
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .interactive-panel {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(16px);
      border-radius: 20px;
      padding: 2rem;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }
    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
    }
    .panel-header h2 {
      font-size: 1.35rem;
      font-weight: 700;
    }
    .btn-group {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    button, a.btn {
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.65rem 1.25rem;
      border-radius: 10px;
      font-weight: 600;
      font-size: 0.9rem;
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
      transform: translateY(-1px);
    }
    button.secondary, a.btn.secondary {
      background: rgba(255, 255, 255, 0.06);
      color: var(--text-main);
      border: 1px solid rgba(255, 255, 255, 0.12);
    }
    button.secondary:hover, a.btn.secondary:hover {
      background: rgba(255, 255, 255, 0.12);
    }
    .form-row {
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
    }
    input[type="text"] {
      flex: 1;
      min-width: 200px;
      padding: 0.75rem 1rem;
      border-radius: 10px;
      background: rgba(0, 0, 0, 0.4);
      border: 1px solid rgba(255, 255, 255, 0.15);
      color: #fff;
      font-size: 0.95rem;
      font-family: inherit;
      outline: none;
    }
    input[type="text"]:focus {
      border-color: var(--mint);
    }
    .console-box {
      background: var(--code-bg);
      border: 1px solid rgba(52, 211, 153, 0.2);
      border-radius: 12px;
      padding: 1.25rem;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      max-height: 250px;
      overflow-y: auto;
      color: #a7f3d0;
      line-height: 1.6;
      white-space: pre-wrap;
    }
    footer {
      text-align: center;
      color: var(--text-muted);
      font-size: 0.85rem;
      margin-top: 2rem;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">
        <span class="pulse-dot"></span>
        Backend Status: Online & Healthy
      </div>
      <h1>VrikshaVision Digital Twin</h1>
      <p class="subtitle">
        Calibrated tree crown enumeration, conformal uncertainty bounds, and allometric carbon estimation.
      </p>
    </header>

    <div class="grid">
      <div class="card">
        <span class="card-title">Server Host</span>
        <span class="card-value">127.0.0.1:8000</span>
        <span class="card-desc">Uvicorn ASGI Engine</span>
      </div>
      <div class="card">
        <span class="card-title">Database</span>
        <span class="card-value">SQLite 3</span>
        <span class="card-desc">Zero external setup</span>
      </div>
      <div class="card">
        <span class="card-title">ML Backend</span>
        <span class="card-value" style="color: var(--mint);">Mock Adapter</span>
        <span class="card-desc">Synthetic Detections</span>
      </div>
      <div class="card">
        <span class="card-title">API Spec</span>
        <span class="card-value">OpenAPI 3.1</span>
        <span class="card-desc">Fully documented</span>
      </div>
    </div>

    <div class="interactive-panel">
      <div class="panel-header">
        <h2>Interactive Quick Test</h2>
        <div class="btn-group">
          <a href="/docs" target="_blank" class="btn primary">📖 Open Swagger API Docs</a>
          <button onclick="testHealth()" class="btn secondary">🩺 Test Health API</button>
          <button onclick="loadProjects()" class="btn secondary">📁 Fetch Projects</button>
        </div>
      </div>

      <div style="display: flex; flex-direction: column; gap: 0.75rem;">
        <label style="font-size: 0.9rem; font-weight: 600; color: var(--text-muted);">
          Create a New Project:
        </label>
        <div class="form-row">
          <input type="text" id="projName" placeholder="Project name (e.g. Western Ghats 2026)" value="Nilgiri Canopy Audit 2026">
          <input type="text" id="projDesc" placeholder="Description" value="Aerial survey for biodiversity baseline">
          <button onclick="createProject()" class="btn primary">➕ Create Project</button>
        </div>
      </div>

      <div>
        <label style="font-size: 0.9rem; font-weight: 600; color: var(--text-muted); display: block; margin-bottom: 0.5rem;">
          Live Server Response:
        </label>
        <div id="console" class="console-box">Ready. Click any action above to test live backend endpoints!</div>
      </div>
    </div>

    <footer>
      VrikshaVision Tree Digital Twin &bull; Phase 1 Verified &bull; Python 3.11+ / FastAPI / SQLite
    </footer>
  </div>

  <script>
    const consoleBox = document.getElementById('console');

    function logResponse(title, data) {
      const timestamp = new Date().toLocaleTimeString();
      consoleBox.innerText = `[${timestamp}] ${title}\n` + JSON.stringify(data, null, 2);
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
        logResponse("PROJECTS LIST", data);
      } catch (err) {
        consoleBox.innerText = "Error: " + err;
      }
    }

    async function createProject() {
      const name = document.getElementById('projName').value.trim();
      const description = document.getElementById('projDesc').value.trim();
      if (!name) return alert("Please enter a project name.");

      consoleBox.innerText = "Calling POST /projects ...";
      try {
        const res = await fetch('/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, description })
        });
        const data = await res.json();
        logResponse("PROJECT CREATED SUCCESSFULLY", data);
      } catch (err) {
        consoleBox.innerText = "Error: " + err;
      }
    }
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
